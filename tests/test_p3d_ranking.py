from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet

from jobbie_private.catalogue import CatalogueReader, Listing
from jobbie_private.evidence import Evidence
from jobbie_private.ranking import Ranking, WEIGHTS, rank_listing
from jobbie_private.resume import DOCX
from jobbie_private.storage import PrivateStore
from src.adapters.workday import WorkdayAdapter
from src.catalogue import Catalogue
from src.eligibility import classify_eligibility
from src.models import CompensationRange
from tests.test_catalogue import CFG, job, scan
from tests.test_eligibility import _job_from_fixture, _load_fixtures
from tests.test_microsoft_research_adapter import _fetch_with_fixture
from tests.test_p3b_private import OWNER, docx

NOW = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)
FIXTURE = Path(__file__).parent / "fixtures"


def observed_rows():
    """23 observed postings from the existing Workday and Microsoft Research captures."""
    payload = json.loads((FIXTURE / "workday_micron.json").read_text())
    http = MagicMock()
    http.post.return_value.status_code = 200
    http.post.return_value.json.return_value = payload | {"total": len(payload["jobPostings"])}
    adapter = WorkdayAdapter("Micron", {"base_url": "https://micron.wd1.myworkdayjobs.com",
                             "tenant": "micron", "site": "External", "fetch_details": False}, http)
    return [*adapter.fetch(), *_fetch_with_fixture()]


def listing(item, *, date_only=None):
    return Listing(item, "fixture-id", "fixture-source", "a" * 64,
                   "00000000-0000-0000-0000-000000000000", item.url, date_only, None)


@pytest.mark.parametrize("index", range(23))
@pytest.mark.parametrize("known_skills", [{}, {"python": ("f" * 32,)}], ids=["absent-fact", "confirmed-fact"])
def test_source_backed_ranking_fixtures(index, known_skills):
    item = observed_rows()[index]
    result = rank_listing(listing(item), known_skills, {}, NOW)
    assert result.eligibility.status == classify_eligibility(item).status
    if result.eligibility.status == "eligible":
        assert result.weights["salary"] is None
        assert result.weights["freshness"] is None
        assert result.score <= result.known_weight
    else:
        assert result.score is None
    assert result.listing.job.url.startswith("https://")


@pytest.mark.parametrize("item", _load_fixtures(), ids=lambda row: row["id"])
def test_legacy_expected_tri_state_precedes_any_score(item):
    result = rank_listing(listing(_job_from_fixture(item)), {}, {}, NOW)
    assert result.eligibility.status == item["expected_status"]
    if item["expected_status"] != "eligible":
        assert result.score is None


def eligible_job(**kwargs):
    values = {"title": "Software Engineer I", "location": "San Francisco, CA",
              "raw_text": "Full-time software engineer. 0-2 years of experience. Python and SQL."}
    return job(**(values | kwargs))


def test_salary_preference_unknown_and_freshness_are_source_grounded():
    identity = eligible_job(source_platform="ashby")
    base = CompensationRange(Decimal(105_000), Decimal(120_000), "USD", "1 YEAR", "compensation.summaryComponents")
    fresh = listing(replace(identity, compensation=(base,)), date_only=NOW.date())
    ranked = rank_listing(fresh, {"python": ("a" * 32,), "sql": ("b" * 32,)}, {}, NOW)
    assert WEIGHTS == {"role": 30, "skills": 25, "geography": 15, "salary": 10, "freshness": 10, "company": 10}
    assert ranked.weights["salary"] == 10 and ranked.weights["freshness"] == 10
    assert ranked.fact_ids == ("a" * 32, "b" * 32)
    assert rank_listing(listing(identity), {}, {}, NOW).weights["salary"] is None
    lower = replace(base, minimum=Decimal(60_000), maximum=Decimal(80_000))
    low = rank_listing(listing(replace(identity, compensation=(lower,))), {}, {}, NOW)
    assert low.eligibility.status == "eligible" and low.weights["salary"] == 0


def test_readonly_search_and_working_controls_recheck_revoked_facts(tmp_path):
    catalogue_path = tmp_path / "catalogue.sqlite"
    with Catalogue(catalogue_path, create=True) as catalogue:
        scan(catalogue, [eligible_job(), eligible_job(title="Software Engineer Intern", url="https://example.com/intern",
                                                     source_job_id="intern")])
    before = hashlib.sha256(catalogue_path.read_bytes()).hexdigest()
    vault = PrivateStore(tmp_path / "private.sqlite", Fernet.generate_key(), OWNER)
    evidence = Evidence(vault)
    version = vault.store_resume(DOCX, docx(), "Skills: Python", "fixture")
    fact = evidence.propose_resume(version.id)[0]
    evidence.decide(fact.id, "confirm", "accept")
    ranking = Ranking(CatalogueReader(catalogue_path), vault, clock=lambda: NOW)
    output = ranking.search("Software Engineer", top=False)
    assert len(output.rows) == 1
    controls = output.rows[0]["components"]
    assert [row["label"] for row in controls] == ["View", "Save", "Explain"]
    selected = controls[1]["custom_id"].split(":")[1]
    assert fact.id in ranking.explain(selected)
    evidence.decide(fact.id, "revoke", "revoke")
    assert fact.id not in ranking.explain(selected)
    assert "Saved" in ranking.save(selected)
    assert vault.applications() == []
    ranking.feedback(selected, "not_relevant", "event")
    assert ranking.search("Software Engineer", top=False).rows == ()
    assert hashlib.sha256(catalogue_path.read_bytes()).hexdigest() == before


def test_catalogue_declines_partial_files_and_sql_input(tmp_path):
    path = tmp_path / "catalogue.sqlite"
    with Catalogue(path, create=True) as catalogue:
        scan(catalogue, [eligible_job()])
    reader = CatalogueReader(path)
    assert len(reader.find("Software Engineer")) == 1
    assert reader.find("%' OR 1=1 --") == []
    path.with_name(path.name + "-wal").write_bytes(b"fixture")
    with pytest.raises(ValueError, match="snapshot"):
        reader.find("Software Engineer")


def test_signed_job_search_and_component_only_dispatch_for_owner(tmp_path):
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from jobbie_private.discord import DiscordEndpoint
    from jobbie_private.ranking import ranking_commands
    from jobbie_private.tasks import TaskStore
    from tests.test_p3a_discord import APP, OTHER, handle, interaction

    path = tmp_path / "catalogue.sqlite"
    with Catalogue(path, create=True) as catalogue:
        scan(catalogue, [eligible_job()])
    store = PrivateStore(tmp_path / "private.sqlite", Fernet.generate_key(), OWNER)
    key = Ed25519PrivateKey.generate()
    clock = SimpleNamespace(now=int(NOW.timestamp()))
    ranking = Ranking(CatalogueReader(path), store, clock=lambda: NOW)
    endpoint = DiscordEndpoint(key.public_key(), APP, OWNER, TaskStore(store.path, store.key),
                               ranking_commands(ranking), clock=lambda: clock.now)
    rig = SimpleNamespace(endpoint=endpoint, key=key, clock=clock)
    query = interaction(name="jobs", options=[{"type": 1, "name": "find",
                        "options": [{"type": 3, "name": "query", "value": "Software"}]}])
    assert handle(rig, query)[1]["type"] == 5
    replies = []
    assert endpoint.work_once(lambda _, __, data, ___: replies.append(data))
    assert replies[0]["allowed_mentions"] == {"parse": []}
    custom_id = replies[0]["components"][0]["components"][1]["custom_id"]
    component = interaction(2) | {"type": 3, "data": {"component_type": 2, "custom_id": custom_id}}
    assert handle(rig, component | {"member": {"user": {"id": OTHER}}})[0] == 403
    assert handle(rig, component | {"data": {"component_type": 2, "custom_id": "apply:unavailable"}})[0] == 400
    assert handle(rig, component)[1]["type"] == 5
    assert endpoint.work_once(lambda *_: None)
    assert len(store.records("saved_job")) == 1
    assert not store.applications()
    assert {item["name"] for item in endpoint.manifest()} == {"jobs"}


def test_catalogue_payload_digest_is_verified_readonly(tmp_path):
    path = tmp_path / "catalogue.sqlite"
    with Catalogue(path, create=True) as catalogue:
        scan(catalogue, [eligible_job()])
        catalogue.db.execute("UPDATE snapshots SET payload=json_set(payload,'$.title','Tampered')")
        catalogue.db.commit()
    with pytest.raises(ValueError, match="digest"):
        CatalogueReader(path).find()


@pytest.mark.parametrize(("location", "points"), [
    ("New York, NY", 10),
    ("San Mateo, CA", 15),
    ("Fremont, CA", 15),
    ("Los Angeles, CA", 10),
    ("Miami, FL", 10),
    ("Madison, WI", 5),
])
def test_geography_prioritizes_verified_locales(location, points):
    result = rank_listing(listing(eligible_job(location=location)), {}, {}, NOW)
    assert result.eligibility.status == "eligible"
    assert result.weights["geography"] == points


@pytest.mark.parametrize(("location", "points"), [
    ("Fremont, NE; Los Angeles, CA", 10),
    ("Los Angeles, CA | Fremont, NE", 10),
    ("Fremont, CA; Los Angeles, CA", 15),
    ("Tampa Bay Area, FL", 10),
])
def test_geography_does_not_join_location_evidence_across_entries(location, points):
    result = rank_listing(listing(eligible_job(location=location)), {}, {}, NOW)
    assert result.eligibility.status == "eligible"
    assert result.weights["geography"] == points

"""Replay SQLite-only delivery evidence through the real legacy scanner."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

from cryptography.fernet import Fernet
import pytest

from main import do_run
from src.catalogue import Catalogue, CatalogueError
from src.catalogue_checkpoint import seal
from src.catalogue_shadow import Shadow, source_key
from src.models import Job
from src.storage import POLICY_VERSION, _empty_state, is_url_alerted, load_state, mark_backfill_completed

SOURCE = {
    "name": "Salesforce", "adapter": "workday", "enabled": True,
    "config": {"domain": "salesforce.wd12.myworkdayjobs.com", "path": "External_Career_Site"},
}
FILTERS = {"mode": "new_grad_full_time", "freshness_hours": 48}


def job(identity, now):
    return Job(
        id=f"salesforce::{identity}", company=SOURCE["name"], title="Software Engineer, New Grad",
        location="Cupertino, CA", department="Engineering", category="Software",
        url=f"https://example.com/jobs/{identity}?utm_source=source", source_platform="workday",
        posted_at=now - timedelta(hours=6), detected_at=now,
        raw_text="Software Engineer, New Grad. 0-2 years experience. December 2026 graduation. Cupertino, CA.",
        role_type="new-grad", priority="normal", matched_keywords=(), source_job_id=identity,
    )


def retained_case(tmp_path, *, outcome="ack", ambiguous=False):
    now = datetime.now(timezone.utc)
    a, b, old = (job(key, now) for key in ("A", "B", "OLD"))
    initial = _empty_state()
    initial.update(policy_version=POLICY_VERSION, first_run_completed_at=(now - timedelta(days=2)).isoformat())
    mark_backfill_completed(initial, now=now)
    initial["heartbeat_history"] = [{"example": "preserve"}]
    legacy = tmp_path / "retained.json"
    legacy.write_text(json.dumps(initial))
    db = tmp_path / "db.sqlite"
    with Catalogue(db, create=True) as store:
        for run_id, rows, result, when in (
            ("last-legacy", [old], "ack", now - timedelta(minutes=10)),
            ("sqlite-fixture", [a, replace(a, url="https://example.com/jobs/other")] if ambiguous else [a], outcome, now),
        ):
            with Shadow(store, run_id, when, initial, filters=FILTERS, origin="fixture", config_sha="b" * 64) as shadow:
                shadow.observe(SOURCE, rows, status="complete", observed_at=when)
                shadow.delivery(SOURCE, rows[0], result, when)
                shadow.finish(initial, when)
    cipher = tmp_path / "sealed.bin"
    key = Fernet.generate_key()
    checkpoint = seal(db, cipher, key, legacy_path=legacy)
    return checkpoint, cipher, key, legacy, a, b, old


def run_legacy(tmp_path, state_path, jobs, monkeypatch):
    cfg = tmp_path / "fixture.json"
    cfg.write_text(json.dumps({"defaults": {"state_path": str(state_path)}, "filters": FILTERS, "companies": [SOURCE]}))
    args = SimpleNamespace(config=str(cfg), dry_run=False, verbose=False, company=SOURCE["name"],
                           firehose_first_run=False, summary_first_run=False, rerun_backfill=False)
    sends = []
    def send(_notifier, posting):
        sends.append(posting.source_job_id)
        return True
    def forbidden(*args, **kwargs):
        pytest.fail("rollback fixture attempted network access")
    monkeypatch.setattr("main.load_dotenv", lambda: None)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://example.invalid/mock")
    monkeypatch.setenv("JOBBIE_CATALOGUE_MODE", "off")
    monkeypatch.setattr("src.adapters.workday.WorkdayAdapter.fetch", lambda *args, **kwargs: jobs)
    monkeypatch.setattr("src.notifier.Notifier.send_job_alert", send)
    monkeypatch.setattr("requests.sessions.Session.request", forbidden)
    assert do_run(args) == 0
    return sends


def test_legacy_after_fallback_only_sends_new_job(tmp_path, monkeypatch):
    from src.catalogue_fallback import stage_legacy_fallback

    checkpoint, cipher, key, legacy, a, b, old = retained_case(tmp_path)
    original = legacy.read_bytes()
    output = tmp_path / "staged.json"
    assert stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy") == 1
    state = load_state(output, raise_on_corrupt=True)
    assert is_url_alerted(a.url, state)
    assert not is_url_alerted(old.url, state)
    assert state["heartbeat_history"] == [{"example": "preserve"}]
    assert state["companies"][SOURCE["name"]]["seen_jobs"][a.id]["alerted"] is True
    assert run_legacy(tmp_path, output, [a, b], monkeypatch) == ["B"]
    assert legacy.read_bytes() == original


@pytest.mark.parametrize("outcome", ["failed", "dedup"])
def test_unconfirmed_sqlite_attempt_remains_eligible_in_legacy(tmp_path, monkeypatch, outcome):
    from src.catalogue_fallback import stage_legacy_fallback

    checkpoint, cipher, key, legacy, a, b, _ = retained_case(tmp_path, outcome=outcome)
    output = tmp_path / "staged.json"
    assert stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy") == 0
    assert not is_url_alerted(a.url, load_state(output, raise_on_corrupt=True))
    assert run_legacy(tmp_path, output, [a, b], monkeypatch) == ["A", "B"]


def test_fallback_refuses_wrong_input_boundary_and_existing_output(tmp_path):
    from src.catalogue_fallback import stage_legacy_fallback

    checkpoint, cipher, key, legacy, *_ = retained_case(tmp_path)
    output = tmp_path / "staged.json"
    with pytest.raises(CatalogueError, match="boundary"):
        stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="missing")
    assert not output.exists()
    with pytest.raises(CatalogueError, match="already exists"):
        stage_legacy_fallback(checkpoint, cipher, key, legacy, legacy, after_run_id="last-legacy")
    with pytest.raises(CatalogueError):
        stage_legacy_fallback(checkpoint, cipher, Fernet.generate_key(), legacy, output, after_run_id="last-legacy")
    assert not output.exists()
    legacy.write_bytes(legacy.read_bytes() + b"\n")
    with pytest.raises(CatalogueError, match="legacy ledger"):
        stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy")
    assert not output.exists()


def test_fallback_refuses_ambiguous_delivery_mapping(tmp_path):
    from src.catalogue_fallback import stage_legacy_fallback

    checkpoint, cipher, key, legacy, *_ = retained_case(tmp_path, ambiguous=True)
    output = tmp_path / "staged.json"
    with pytest.raises(CatalogueError, match="ambiguous"):
        stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy")
    assert not output.exists()


@pytest.mark.parametrize("scope", ["same_source", "same_company", "other_company"])
def test_fallback_scopes_legacy_id_collisions_by_company(tmp_path, scope):
    from src.catalogue_fallback import stage_legacy_fallback

    now = datetime.now(timezone.utc)
    a = job("A", now)
    b = replace(job("B", now), id=a.id)
    other_source = {**SOURCE, "config": {**SOURCE["config"], "path": "Other_Site"}}
    if scope == "other_company":
        other_source = {**other_source, "name": "Other Company"}
        b = replace(b, company=other_source["name"])
    initial = _empty_state()
    initial.update(policy_version=POLICY_VERSION, first_run_completed_at=(now - timedelta(days=2)).isoformat())
    mark_backfill_completed(initial, now=now)
    legacy = tmp_path / "retained.json"
    legacy.write_text(json.dumps(initial))
    original = legacy.read_bytes()
    db = tmp_path / "db.sqlite"
    with Catalogue(db, create=True) as store:
        with Shadow(store, "last-legacy", now - timedelta(minutes=1), initial, filters=FILTERS) as shadow:
            shadow.observe(SOURCE, [], status="complete", observed_at=now)
            shadow.finish(initial, now)
        with Shadow(store, "sqlite-fixture", now, initial, filters=FILTERS, config_sha="b" * 64) as shadow:
            shadow.observe(SOURCE, [a, b] if scope == "same_source" else [a], status="complete", observed_at=now)
            if scope != "same_source":
                shadow.observe(other_source, [b], status="complete", observed_at=now)
            rows = store.scan_rows("sqlite-fixture", source_key(SOURCE))
            if scope != "same_source":
                rows += store.scan_rows("sqlite-fixture", source_key(other_source))
            payloads = [json.loads(row["payload"]) for row in rows]
            assert len({row["job_id"] for row in rows}) == 2
            assert len({data["source_job_id"] for data in payloads}) == 2
            assert len({data["url"] for data in payloads}) == 2
            assert {data["id"] for data in payloads} == {a.id}
            shadow.delivery(SOURCE, a, "ack", now)
            shadow.finish(initial, now)
    cipher = tmp_path / "sealed.bin"
    key = Fernet.generate_key()
    checkpoint = seal(db, cipher, key, legacy_path=legacy)
    output = tmp_path / "staged.json"
    if scope == "other_company":
        assert stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy") == 1
    else:
        with pytest.raises(CatalogueError, match="ambiguous"):
            stage_legacy_fallback(checkpoint, cipher, key, legacy, output, after_run_id="last-legacy")
        assert not output.exists()
    assert legacy.read_bytes() == original

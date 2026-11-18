import pytest
from cryptography.fernet import Fernet

from jobbie_private.evidence import Evidence
from jobbie_private.github import GitHubEvidence, repository_spec
from jobbie_private.resume import DOCX
from jobbie_private.storage import PrivateStore
from tests.test_p3b_private import OWNER, OTHER, docx

SHA = "a" * 40
REPO = "example-owner/fictional-service"
TEXT = "Technical skills: Python, SQL\nBuilt a sample parser for a class.\nWork authorization: example text"
REPO_SPEC = {"repository": REPO, "repository_id": 1234, "author": "example-owner",
             "author_id": 400, "visibility": "private", "stage": "prototype"}


@pytest.fixture
def vault(tmp_path):
    return PrivateStore(tmp_path / "store.sqlite", Fernet.generate_key(), OWNER)


def upload(vault, text=TEXT, request="fixture"):
    return vault.store_resume(DOCX, docx(), text, request)


def test_proposals_preserve_exact_spans_and_require_confirmation(vault):
    resume = upload(vault)
    evidence = Evidence(vault)
    rows = evidence.propose_resume(resume.id)
    assert evidence.active() == []
    assert rows == evidence.propose_resume(resume.id)
    python = next(r for r in rows if r.data["value"] == "python")
    source = python.data["source"]
    assert source["sha256"] == resume.sha256
    assert resume.text[source["start"]:source["end"]] == "Python"
    assert python.data["privacy"] == "owner-only"
    evidence.decide(python.id, "confirm", "confirm-fixture")
    assert [r.id for r in evidence.active()] == [python.id]
    assert vault.delete_resume(resume.id)
    assert evidence.active() == []


def test_protected_proposal_needs_explicit_confirmation_and_stays_out_of_ranking(vault):
    evidence = Evidence(vault)
    protected = next(r for r in evidence.propose_resume(upload(vault).id) if r.data["protected"])
    with pytest.raises(ValueError, match="Protected"):
        evidence.decide(protected.id, "confirm", "first")
    evidence.decide(protected.id, "confirm", "second", confirm_protected=True)
    assert evidence.active() == []
    assert [item.id for item in evidence.active(include_protected=True)] == [protected.id]


def test_correction_and_revocation_invalidate_immediately(vault):
    evidence = Evidence(vault)
    proposed = evidence.propose_resume(upload(vault).id)
    python = next(r for r in proposed if r.data["value"] == "python")
    sql = next(r for r in proposed if r.data["value"] == "sql")
    evidence.decide(python.id, "confirm", "one")
    evidence.decide(python.id, "correct", "two", replacement_id=sql.id)
    assert [row.id for row in evidence.active()] == [sql.id]
    evidence.decide(sql.id, "revoke", "three")
    assert evidence.active() == []


def transport(filenames, *, author_id=400, repo_id=1234):
    def read(path):
        if path == f"/repos/{REPO}":
            return {"id": repo_id, "full_name": REPO, "private": True}
        assert path == f"/repos/{REPO}/commits/{SHA}?per_page=100"
        return {"sha": SHA, "author": {"login": "example-owner", "id": author_id},
                "files": [{"filename": n, "status": "modified", "patch": "FICTIONAL PATCH"}
                          for n in filenames]}
    return read


def test_unapproved_repo_does_not_acquire_network_access(vault):
    service = GitHubEvidence(vault, lambda _: pytest.fail("unapproved network call"))
    with pytest.raises(ValueError):
        service.propose("f" * 32, SHA)
    for repo in ("example-owner/../fictional-service", "example-owner/%2fhidden", "https://unsafe.invalid"):
        with pytest.raises(ValueError):
            repository_spec(REPO_SPEC | {"repository": repo})


@pytest.mark.parametrize("names,author,repo", [
    (["README.md"], 400, 1234), (["service.py"], 999, 1234), (["service.py"], 400, 999),
])
def test_readme_author_and_repo_mismatch_fail_closed(vault, names, author, repo):
    service = GitHubEvidence(vault, transport(names, author_id=author, repo_id=repo))
    approved = service.approve(REPO_SPEC, "owner-approval", confirmed=True)
    with pytest.raises(ValueError):
        service.propose(approved.id, SHA)


def test_exact_commit_is_proposal_with_private_provenance(vault):
    service = GitHubEvidence(vault, transport(["README.md", "service.py"]))
    approved = service.approve(REPO_SPEC, "owner-approval", confirmed=True)
    proposal = service.propose(approved.id, SHA)
    assert proposal.data["source"]["code_paths"] == ["service.py"]
    assert proposal.data["source"]["commit"] == SHA
    assert proposal.data["source"]["author"] == "example-owner"
    assert proposal.data["stage"] == "prototype"
    assert b"FICTIONAL PATCH" not in vault.path.read_bytes()
    assert Evidence(vault).active() == []
    other = GitHubEvidence(PrivateStore(vault.path, vault.key, OTHER),
                           lambda _: pytest.fail("cross-owner access"))
    with pytest.raises(ValueError):
        other.propose(approved.id, SHA)
    evidence = Evidence(vault)
    evidence.decide(proposal.id, "confirm", "confirm")
    assert [row.id for row in evidence.active()] == [proposal.id]
    service.revoke(approved.id, "revoked", confirmed=True)
    assert evidence.active() == []


def test_deletion_erases_stored_proposal_payload(vault):
    evidence = Evidence(vault)
    version = upload(vault)
    row = evidence.propose_resume(version.id)[0]
    assert vault.delete_resume(version.id)
    assert vault.get("candidate_fact", row.id) is None
    with pytest.raises(ValueError):
        evidence.inspect(row.id)


def test_production_requires_exact_successful_deployment(vault):
    base = f"/repos/{REPO}"
    core = transport(["service.py"])
    deployment_state = {"state": "queued", "id": 23, "environment": "production"}
    def api(path):
        if path == f"{base}/deployments/88":
            return {"id": 88, "sha": SHA, "environment": "production",
                    "production_environment": True, "transient_environment": False}
        if path == f"{base}/deployments/88/statuses?per_page=1":
            return [deployment_state]
        return core(path)

    service = GitHubEvidence(vault, api)
    approved = service.approve(REPO_SPEC, "approval", confirmed=True)
    with pytest.raises(ValueError, match="deployment"):
        service.propose(approved.id, SHA, 88)
    deployment_state["state"] = "success"
    production = service.propose(approved.id, SHA, 88)
    assert production.data["stage"] == "production"
    assert production.data["source"]["deployment"]["status_id"] == 23
    assert service.propose(approved.id, SHA).data["stage"] == "prototype"


@pytest.mark.parametrize("statement", [
    "Bachelor degree, graduation December 2026",
    "Built a parser serving 1000 users",
    "Employer: Fictional Systems",
    "Jan 2025 - Mar 2026",
])
def test_protected_claims_require_separate_confirmation(vault, statement):
    evidence = Evidence(vault)
    fact = evidence.propose_resume(upload(vault, statement).id)[0]
    with pytest.raises(ValueError, match="Protected"):
        evidence.decide(fact.id, "confirm", "regular")
    evidence.decide(fact.id, "confirm", "protected", confirm_protected=True)
    assert not evidence.active()
    assert evidence.active(include_protected=True)[0].id == fact.id


def test_transient_named_production_is_never_promoted(vault):
    base = f"/repos/{REPO}"
    core = transport(["service.py"])
    def api(path):
        if path == f"{base}/deployments/88":
            return {"id": 88, "sha": SHA, "environment": "production",
                    "production_environment": False, "transient_environment": True}
        if path == f"{base}/deployments/88/statuses?per_page=1":
            return [{"state": "success", "id": 23, "environment": "production"}]
        return core(path)

    service = GitHubEvidence(vault, api)
    approved = service.approve(REPO_SPEC, "approval", confirmed=True)
    with pytest.raises(ValueError, match="deployment"):
        service.propose(approved.id, SHA, 88)

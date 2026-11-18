"""Exercise the complete private stack over loopback with fictional data."""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from wsgiref.simple_server import make_server

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jobbie_private.catalogue import CatalogueReader
from jobbie_private.evidence import Evidence
from jobbie_private.github import GitHubEvidence
from jobbie_private.profile import DownloadRoute
from jobbie_private.ranking import Ranking
from jobbie_private.resume import DOCX
from jobbie_private.server import InteractionApp, QuietRequestHandler, endpoint_from_env
from jobbie_private.storage import PrivateStore
from src.catalogue import Catalogue
from tests.test_catalogue import scan
from tests.test_p3a_discord import APP, OTHER, OWNER
from tests.test_p3b_private import docx
from tests.test_p3c_evidence import REPO, REPO_SPEC, SHA, transport
from tests.test_p3d_ranking import eligible_job


@contextmanager
def serve(app):
    with make_server("127.0.0.1", 0, app,
                     handler_class=QuietRequestHandler) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            worker.join(timeout=2)


def test_owner_profile_location_breaks_a_matching_rank_tie(tmp_path):
    path = tmp_path / "catalogue.sqlite"
    a = eligible_job(id="job-a", url="https://example.com/job/a", source_job_id="a", location="Austin, TX")
    b = eligible_job(id="job-b", url="https://example.com/job/b", source_job_id="b", location="Miami, FL")
    with Catalogue(path, create=True) as catalogue:
        scan(catalogue, [a, b])
    vault = PrivateStore(tmp_path / "private.sqlite", Fernet.generate_key(), OWNER)
    ranking = Ranking(CatalogueReader(path), vault)
    before = ranking.search("Engineer", top=True).rows
    preferred = before[1]["components"][0]["url"]
    location = a.location if preferred == a.url else b.location
    vault.set_profile({"target_locations": [location]}, "owner-target")
    after = ranking.search("Engineer", top=True).rows
    assert after[0]["components"][0]["url"] == preferred
    selection = after[0]["components"][2]["custom_id"].split(":")[1]
    assert "Owner location preference matched" in ranking.explain(selection)


def test_signed_upload_evidence_rank_save_and_reverse_on_revocation(tmp_path, monkeypatch):
    path = tmp_path / "catalogue.sqlite"
    database = tmp_path / "private.sqlite"
    with Catalogue(path, create=True) as catalogue:
        scan(catalogue, [eligible_job()])
    immutable_hash = hashlib.sha256(path.read_bytes()).digest()
    key = Ed25519PrivateKey.generate()
    secret = Fernet.generate_key()
    bearer = "r" * 40
    env = {
        "PATH": os.defpath,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "JOBBIE_PRIVATE_DB": str(database),
        "JOBBIE_PRIVATE_KEY": secret.decode(),
        "JOBBIE_DISCORD_OWNER_ID": OWNER,
        "JOBBIE_DISCORD_APPLICATION_ID": APP,
        "JOBBIE_DISCORD_PUBLIC_KEY": key.public_key().public_bytes_raw().hex(),
        "JOBBIE_P3_CATALOGUE_PATH": str(path),
    }
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    vault = PrivateStore(database, secret, OWNER)

    def owner_command(*args, stdin=None, ok=True):
        result = subprocess.run([sys.executable, "-m", "jobbie_private.server", *args],
                                env=env, input=stdin, text=True, capture_output=True, timeout=10)
        assert (result.returncode == 0) is ok
        return result.stdout.strip()

    owner_command("profile-set", "--request-id", "profile-1",
                  stdin=json.dumps({"target_roles": ["Software Engineer"], "target_locations": ["San Francisco"]}))
    manifest = {item["name"] for item in json.loads(owner_command("commands"))}
    assert manifest == {"applications", "github", "health", "jobs", "profile", "resume", "settings", "tasks"}

    attachment_id = "300000000000000001"
    file_bytes = docx("Skills: Python")
    url = f"https://cdn.discordapp.com/attachments/{OWNER}/{attachment_id}/synthetic.docx"
    received = []

    def fixture_attachment(file):
        assert file == {"id": attachment_id, "size": len(file_bytes), "content_type": DOCX, "url": url}
        received.append(file["id"])
        return DOCX, file_bytes

    monkeypatch.setattr("jobbie_private.profile.fetch_attachment", fixture_attachment)
    endpoint = endpoint_from_env(vault)
    with serve(InteractionApp(endpoint, DownloadRoute(vault, bearer))) as port:
        number = 100

        def request(method, path, body=None, headers=None):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                connection.request(method, path, body, headers or {})
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                connection.close()

        def invoke(name=None, sub=None, options=(), actor=OWNER, custom_id=None, forged=False, resolved=None):
            nonlocal number
            number += 1
            interaction_id = str(200000000000000000 + number)
            data = ({"component_type": 2, "custom_id": custom_id} if custom_id else
                    {"name": name, "options": list(options)})
            if sub:
                data = {"name": name, "options": [{"type": 1, "name": sub, "options": list(options)}]}
            if resolved:
                data["resolved"] = resolved
            document = {"type": 3 if custom_id else 2, "id": interaction_id, "application_id": APP,
                        "user": {"id": actor}, "token": "fixture-token-" + str(number), "data": data}
            body = json.dumps(document).encode()
            timestamp = str(int(time.time()))
            signer = Ed25519PrivateKey.generate() if forged else key
            headers = {"Content-Type": "application/json", "X-Signature-Timestamp": timestamp,
                       "X-Signature-Ed25519": signer.sign(timestamp.encode() + body).hex()}
            status, _, response = request("POST", "/interactions", body, headers)
            return status, json.loads(response), interaction_id

        def run_deferred(ack):
            status, body, task_id = ack
            assert status == 200 and body == {"type": 5, "data": {"flags": 64}}
            # The worker starts from the same durable database after the HTTP handler returns.
            restarted = endpoint_from_env(PrivateStore(database, secret, OWNER))
            replies = []
            assert restarted.work_once(lambda app, token, data, expires: replies.append((app, token, data)))
            assert restarted.store.status(OWNER, task_id, int(time.time())) == "done"
            assert len(replies) == 1
            app, token, data = replies[0]
            assert app == APP and token.startswith("fixture-token-")
            assert data["allowed_mentions"] == {"parse": []}
            return data

        assert invoke("health", forged=True)[0] == 401
        assert invoke("health", actor=OTHER)[0] == 403
        assert invoke("health")[1]["data"]["flags"] & 64
        assert "San Francisco" in invoke("profile", "show")[1]["data"]["content"]

        upload = run_deferred(invoke("resume", "upload", [{"type": 11, "name": "file", "value": attachment_id}],
                                    resolved={"attachments": {attachment_id: {"id": attachment_id,
                                        "size": len(file_bytes), "content_type": DOCX, "url": url}}}))
        version = re.search(r"`([a-f0-9]{32})`", upload["content"])[1]
        assert received == [attachment_id]
        assert b"Skills: Python" not in database.read_bytes()
        assert vault.resume(version).body == file_bytes

        output = run_deferred(invoke("resume", "propose", [{"type": 3, "name": "version", "value": version}]))
        assert "1 proposals" in output["content"]
        fact, = vault.records("candidate_fact")
        assert fact.data["source"]["excerpt"] == "Python"
        assert Evidence(vault).active() == []
        owner_command("fact-decide", fact.id, "confirm", "--request-id", "confirmed")
        assert [entry.id for entry in Evidence(vault).active()] == [fact.id]

        approved = owner_command("github-approve", "--owner-confirms", "--request-id", "repository", stdin=json.dumps(REPO_SPEC))
        github_fact = GitHubEvidence(vault, transport(["project.py"])).propose(approved, SHA)
        assert github_fact.data["source"]["commit"] == SHA
        assert github_fact.data["stage"] == "prototype"
        repos = invoke("github", "repos")[1]["data"]["content"]
        assert "1" in repos and REPO not in repos

        search = run_deferred(invoke("jobs", "find", [{"type": 3, "name": "query", "value": "Engineer"}]))
        actions = {row["label"]: row for row in search["components"][0]["components"]}
        assert actions["View"]["url"] == "https://example.com/jobs/1"
        info = run_deferred(invoke(custom_id=actions["Explain"]["custom_id"]))
        assert fact.id in info["content"] and "sql" in info["content"]
        assert "Owner location preference matched" in info["content"]
        assert invoke(actor=OTHER, custom_id=actions["Save"]["custom_id"])[0] == 403
        assert "Saved privately" in run_deferred(invoke(custom_id=actions["Save"]["custom_id"]))["content"]
        assert len(vault.records("saved_job")) == 1 and vault.applications() == []
        snapshot = actions["Save"]["custom_id"].split(":")[1]
        application = owner_command("application-open", snapshot, "--request-id", "record-1")
        owner_command("application-status", application, "applied", "--request-id", "reject", ok=False)
        assert "planning" in invoke("applications")[1]["data"]["content"]

        owner_command("fact-decide", fact.id, "revoke", "--request-id", "revoke")
        updated = run_deferred(invoke(custom_id=actions["Explain"]["custom_id"]))
        assert fact.id not in updated["content"]
        assert "Posting skills without confirmed evidence: python, sql" in updated["content"]
        link = owner_command("resume-link", version)
        assert request("GET", link)[0] == 404
        header = {"Authorization": "Bearer " + bearer}
        status, headers, downloaded = request("GET", link, headers=header)
        assert status == 200 and headers["Cache-Control"] == "no-store" and downloaded == file_bytes

        archive = tmp_path / "backup.sqlite"
        owner_command("backup", str(archive))
        assert PrivateStore(archive, secret, OWNER).resume(version).body == file_bytes
        owner_command("resume-delete", version)
        assert request("GET", link, headers=header)[0] == 404
        assert vault.get("candidate_fact", fact.id) is None
        assert hashlib.sha256(path.read_bytes()).digest() == immutable_hash

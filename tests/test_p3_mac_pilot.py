import hashlib
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jobbie_private.mac_parser import sandbox_command
from jobbie_private.pilot import initialize, runtime_env, verify_parser, write_new
from jobbie_private.storage import PrivateStore
from jobbie_private.tasks import TaskStore
from tests.test_p3a_discord import APP, OTHER, OWNER
from tests.test_p3b_private import docx

GUILD = "300000000000000004"


def credentials(root):
    key = Ed25519PrivateKey.generate()
    ids = {"application": APP, "owner": OWNER, "guild": GUILD,
           "public_key": key.public_key().public_bytes_raw().hex()}
    write_new(root / "discord.json", json.dumps(ids).encode())
    return key


@pytest.mark.skipif(sys.platform != "darwin", reason="probe the actual macOS sandbox")
def test_mac_parser_can_parse_both_formats_and_cannot_read_or_connect(tmp_path, monkeypatch):
    root = initialize(tmp_path / "pilot")
    monkeypatch.setenv("JOBBIE_MAC_PARSER_SANDBOX", "1")
    verify_parser(root)
    command = """import pathlib, socket, sys
private = pathlib.Path(sys.argv[1])
def write():
    private.with_name("sandbox-must-not-create").write_bytes(b"synthetic")
with socket.socket() as connection:
    for operation in (private.read_bytes, write, lambda: connection.connect(("127.0.0.1", int(sys.argv[2])))):
        try:
            operation()
        except PermissionError:
            continue
        raise SystemExit(2)
"""
    with socket.socket() as target:
        target.bind(("127.0.0.1", 0))
        target.listen()
        result = subprocess.run(sandbox_command([sys.executable, "-I", "-B", "-c", command,
                                str(root / "credentials.json"), str(target.getsockname()[1])]),
                                capture_output=True, timeout=6)
    assert result.returncode == 0, (result.returncode, result.stderr)
    assert not (root / "sandbox-must-not-create").exists()


def read_event(log: Path, predicate):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        for line in log.read_text().splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if predicate(value):
                return value
        time.sleep(0.05)
    pytest.fail("Expected redacted local supervisor event was absent")


def request(port, method, path, body=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_supervised_loopback_route_boundaries_deadline_and_restart(tmp_path):
    root = initialize(tmp_path / "pilot")
    key = credentials(root)
    env = runtime_env(root)
    assert "DISCORD_WEBHOOK_URL" not in env and "GH_TOKEN" not in env
    catalogue = root / "synthetic-catalogue.sqlite"
    before = hashlib.sha256(catalogue.read_bytes()).digest()
    vault = PrivateStore(root / "private.sqlite", env["JOBBIE_PRIVATE_KEY"].encode(), OWNER)
    word = docx("Skills: Python")
    version = vault.store_resume("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                 word, "Skills: Python", "fixture")
    ticket = vault.sign_download(version.id, int(time.time()))
    download_path = f"/private/resumes/{version.id}?ticket={ticket}"
    log = tmp_path / "receipt.jsonl"
    args = [sys.executable, "-c",
            "import os; from jobbie_private.pilot import supervise; supervise(dict(os.environ), offline=True, ports=(0, 0))"]
    with log.open("w") as output:
        service = subprocess.Popen(args, env=env, stdout=output, stderr=subprocess.DEVNULL)
        try:
            public = read_event(log, lambda x: x.get("event") == "listener_ready" and x.get("role") == "http")["port"]
            local = read_event(log, lambda x: x.get("event") == "listener_ready" and x.get("role") == "downloads")["port"]
            worker = read_event(log, lambda x: x.get("event") == "process_started" and x.get("role") == "worker")

            read_event(log, lambda x: x.get("event") == "worker_ready")
            task_store = TaskStore(vault.path, vault.key)

            def signed(owner, guild, number, *, signing_key=key, command=None):
                document = {"application_id": APP, "guild_id": guild, "type": 2,
                            "id": str(200000000000000000 + number), "token": "synthetic-request-token",
                            "member": {"user": {"id": owner}}, "data": command or {"name": "health", "options": []}}
                body = json.dumps(document).encode()
                stamp = str(int(time.time()))
                return request(public, "POST", "/interactions", body, {
                    "X-Signature-Ed25519": signing_key.sign(stamp.encode() + body).hex(),
                    "X-Signature-Timestamp": stamp,
                })

            result = signed(OWNER, GUILD, 1)
            assert result[0] == 200 and json.loads(result[2])["data"]["flags"] & 64
            assert signed(OTHER, GUILD, 2)[0] == 403
            assert signed(OWNER, "300000000000000005", 3)[0] == 403
            assert signed(OWNER, GUILD, 4, signing_key=Ed25519PrivateKey.generate())[0] == 401
            assert signed(OWNER, GUILD, 1)[0] == 409
            assert request(public, "GET", download_path, headers={
                "Authorization": "Bearer " + env["JOBBIE_PRIVATE_DOWNLOAD_TOKEN"]})[0] == 404
            assert request(local, "POST", "/interactions", b"{}")[0] == 404
            assert request(local, "GET", download_path)[0] == 404
            downloaded = request(local, "GET", download_path,
                                 headers={"Authorization": "Bearer " + env["JOBBIE_PRIVATE_DOWNLOAD_TOKEN"]})
            assert downloaded[0] == 200 and downloaded[2] == word
            assert request(public, "POST", "/interactions", b"{}", {"Transfer-Encoding": "chunked"})[0] == 400
            assert request(public, "POST", "/interactions", b"", {"Content-Length": "65537"})[0] == 413
            with socket.create_connection(("127.0.0.1", public), timeout=4) as slow:
                started = time.monotonic()
                slow.sendall(b"POST /interactions HTTP/1.0\r\nContent-Length: 6\r\n\r\nab")
                assert slow.recv(100) == b""
                assert time.monotonic() - started < 3

            os.kill(worker["pid"], signal.SIGSTOP)
            queued = signed(OWNER, GUILD, 5, command={"name": "jobs", "options": [{"type": 1, "name": "top"}]})
            assert json.loads(queued[2]) == {"type": 5, "data": {"flags": 64}}
            task_id = str(200000000000000005)
            assert task_store.status(OWNER, task_id, int(time.time())) == "queued"
            os.kill(worker["pid"], signal.SIGKILL)
            restarted = read_event(log, lambda x: x.get("event") == "process_started" and
                                   x.get("role") == "worker" and x.get("restart") == 1)
            assert restarted["pid"] != worker["pid"]
            read_event(log, lambda x: x.get("event") == "task_processed")
            assert task_store.status(OWNER, task_id, int(time.time())) == "done"
            assert signed(OWNER, GUILD, 6)[0] == 200
            assert hashlib.sha256(catalogue.read_bytes()).digest() == before
            report = log.read_text()
            for sensitive in (env["JOBBIE_PRIVATE_KEY"], env["JOBBIE_PRIVATE_DOWNLOAD_TOKEN"], ticket,
                              "synthetic-request-token", OWNER, "/private/resumes/"):
                assert sensitive not in report
        finally:
            service.terminate()
            service.wait(timeout=8)
        assert service.returncode == 0



def test_pilot_refuses_a_replaced_catalogue(tmp_path):
    root = initialize(tmp_path / "pilot")
    credentials(root)
    catalogue = root / "synthetic-catalogue.sqlite"
    catalogue.chmod(0o600)
    catalogue.write_bytes(b"not the approved synthetic snapshot")
    with pytest.raises(ValueError, match="fixture did not match"):
        runtime_env(root)


def test_pilot_upload_refuses_non_fixture_before_provider_fetch(tmp_path, monkeypatch):
    from jobbie_private.discord import Interaction
    from jobbie_private.profile import private_commands

    root = initialize(tmp_path / "pilot")
    credentials(root)
    env = runtime_env(root)
    monkeypatch.setenv("JOBBIE_PILOT_UPLOADS", env["JOBBIE_PILOT_UPLOADS"])
    monkeypatch.setattr("jobbie_private.profile.fetch_attachment", lambda _: pytest.fail("unexpected upload fetch"))
    vault = PrivateStore(root / "private.sqlite", env["JOBBIE_PRIVATE_KEY"].encode(), OWNER)
    upload = next(command.handler for command in private_commands(vault) if command.path == ("resume", "upload"))
    result = upload(Interaction("synthetic", OWNER, {"file": {"filename": "real-resume.pdf", "size": 42}}))
    assert "supplied synthetic" in result
    assert not vault.records("resume_version")


def test_registration_targets_only_configured_guild_and_preserves_existing_commands(tmp_path, monkeypatch):
    from jobbie_private import pilot

    root = initialize(tmp_path / "pilot")
    credentials(root)
    env = runtime_env(root)
    monkeypatch.setattr(pilot, "local_prompt", lambda _: "a" * 40)
    raw_manifest = b'[{"name":"health","description":"Synthetic health"}]'
    monkeypatch.setattr(pilot.subprocess, "check_output", lambda *a, **kw: raw_manifest)
    methods = []
    already_present = True

    class Connection:
        def __init__(self, host, timeout):
            assert host == "discord.com" and timeout == 3

        def request(self, method, path, body=None, headers=None):
            assert path == f"/api/v10/applications/{APP}/guilds/{GUILD}/commands"
            assert headers["Authorization"] == "Bot " + "a" * 40
            if method == "PUT":
                assert body == raw_manifest
            methods.append(method)

        def getresponse(self):
            class Response:
                status = 200

                def read(self, limit):
                    return raw_manifest if already_present or methods[-1] == "PUT" else b"[]"

            return Response()

        def close(self):
            pass

    monkeypatch.setattr(pilot.http.client, "HTTPSConnection", Connection)
    with pytest.raises(ValueError, match="already has"):
        pilot.register_commands(root, env)
    assert methods == ["GET"]
    already_present = False
    pilot.register_commands(root, env)
    assert methods == ["GET", "GET", "PUT"]


@pytest.mark.parametrize("lifecycle", ["shutdown", "replacement"])
def test_supervisor_reaps_worker_descendants(tmp_path, lifecycle):
    child = tmp_path / "role.py"
    child.write_text("""import json, os, subprocess, sys, time
if sys.argv[1] == "worker":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    print(json.dumps({"event":"fixture_descendant","pid":child.pid,"parent":os.getpid()}), flush=True)
time.sleep(60)
""")
    script = """import subprocess, sys
from jobbie_private import pilot
launch = subprocess.Popen
def substitute(args, **kwargs):
    if args[1:4] == ["-m", "jobbie_private.pilot", "_child"]:
        args = [sys.executable, sys.argv[1], args[4]]
    return launch(args, **kwargs)
pilot.subprocess.Popen = substitute
pilot._supervise({}, offline=True, ports=(0, 0))
"""
    log = tmp_path / "supervisor.jsonl"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    with log.open("w") as output:
        supervisor = subprocess.Popen([sys.executable, "-c", script, str(child)],
                                      env=env, stdout=output, stderr=subprocess.DEVNULL)
        try:
            descendant = read_event(log, lambda x: x.get("event") == "fixture_descendant")
            if lifecycle == "shutdown":
                supervisor.terminate()
                supervisor.wait(timeout=8)
            else:
                os.kill(descendant["parent"], signal.SIGKILL)
                read_event(log, lambda x: x.get("event") == "process_started"
                           and x.get("role") == "worker" and x.get("restart") == 1)
            state = subprocess.run(["ps", "-o", "stat=", "-p", str(descendant["pid"])],
                                   capture_output=True, text=True, timeout=5).stdout.strip()
            assert not state or state.startswith("Z"), f"{lifecycle} left a live descendant"
        finally:
            if supervisor.poll() is None:
                supervisor.terminate()
                supervisor.wait(timeout=8)
            for line in log.read_text().splitlines():
                event = json.loads(line)
                if event.get("event") == "fixture_descendant":
                    try:
                        os.kill(event["pid"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass

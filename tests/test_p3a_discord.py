import json
from io import BytesIO
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jobbie_private.discord import Command, DiscordEndpoint, default_commands
from jobbie_private.server import InteractionApp
from jobbie_private.tasks import TaskStore

OWNER = "100000000000000001"
APP = "100000000000000002"
OTHER = "100000000000000003"


@pytest.fixture
def rig(tmp_path):
    key = Ed25519PrivateKey.generate()
    secret = Fernet.generate_key()
    clock = SimpleNamespace(now=1_800_000_000)
    store = TaskStore(tmp_path / "private.sqlite", secret)
    calls = []

    def slow(interaction):
        calls.append(interaction.options["query"])
        return "Done"

    commands = (*default_commands(store, lambda: clock.now),
                Command(("jobs", "find"), "Search jobs", slow, ("query",), deferred=True))
    endpoint = DiscordEndpoint(key.public_key(), APP, OWNER, store, commands,
                               clock=lambda: clock.now)
    return SimpleNamespace(key=key, store=store, clock=clock, endpoint=endpoint,
                           database=tmp_path / "private.sqlite", secret=secret, calls=calls)


def interaction(number=1, *, owner=OWNER, name="health", options=None):
    return {"type": 2, "id": str(200000000000000000 + number), "application_id": APP,
            "member": {"user": {"id": owner}}, "token": "fixture-token",
            "data": {"name": name, "options": options or []}}


def find(number=1):
    return interaction(number, name="jobs", options=[{
        "type": 1, "name": "find", "options": [{"type": 3, "name": "query", "value": "@everyone"}],
    }])


def signed(rig, document, *, ts=None, key=None):
    body = json.dumps(document, separators=(",", ":")).encode()
    stamp = str(rig.clock.now if ts is None else ts)
    return body, {"X-Signature-Ed25519": (key or rig.key).sign(stamp.encode() + body).hex(),
                  "X-Signature-Timestamp": stamp}


def handle(rig, doc, **kwargs):
    return rig.endpoint.handle(*signed(rig, doc, **kwargs))


def test_wire_ping_and_ephemeral_health(rig):
    assert handle(rig, {"type": 1}) == (200, {"type": 1})
    status, reply = handle(rig, interaction())
    assert status == 200 and reply["type"] == 4
    assert reply["data"]["flags"] & 64
    assert reply["data"]["allowed_mentions"] == {"parse": []}


@pytest.mark.parametrize("offset", [-301, 301])
def test_timestamp_outside_window_is_rejected(rig, offset):
    assert handle(rig, interaction(), ts=rig.clock.now + offset)[0] == 401


def test_forgery_and_mutated_body_are_rejected(rig):
    assert handle(rig, interaction(), key=Ed25519PrivateKey.generate())[0] == 401
    body, headers = signed(rig, interaction())
    assert rig.endpoint.handle(body + b" ", headers)[0] == 401


def test_wrong_owner_and_ambiguous_actor_are_denied(rig):
    assert handle(rig, find(2) | {"member": {"user": {"id": OTHER}}})[0] == 403
    assert handle(rig, find(3) | {"user": {"id": OTHER}})[0] == 403
    assert handle(rig, find(4) | {"application_id": OTHER})[0] == 403
    assert rig.calls == []


def test_deferred_ack_replay_and_status_across_restart(rig):
    status, reply = handle(rig, find())
    task_id = find()["id"]
    assert status == 200 and reply == {"type": 5, "data": {"flags": 64}}
    assert rig.calls == []
    assert handle(rig, find())[0] == 409
    assert rig.store.status(OTHER, task_id, rig.clock.now) is None
    restarted = TaskStore(rig.database, rig.secret)
    assert restarted.status(OWNER, task_id, rig.clock.now) == "queued"
    status_query = interaction(2, name="tasks", options=[{"type": 1, "name": "status"}])
    assert handle(rig, status_query)[1]["data"]["content"] == f"{task_id} queued"
    assert b"fixture-token" not in rig.database.read_bytes()
    replies = []
    assert rig.endpoint.work_once(lambda *args: replies.append(args))
    assert rig.calls == ["@everyone"]
    assert replies[0][0:2] == (APP, "fixture-token")
    assert replies[0][2]["allowed_mentions"] == {"parse": []}
    assert restarted.status(OWNER, task_id, rig.clock.now) == "done"
    assert not rig.endpoint.work_once(lambda *args: pytest.fail("duplicate reply"))


def test_expired_task_does_not_execute(rig):
    handle(rig, find())
    rig.clock.now += 900
    assert not rig.endpoint.work_once(lambda *args: pytest.fail("expired reply"))
    assert rig.store.status(OWNER, find()["id"], rig.clock.now) == "expired"
    assert rig.calls == []


def test_rate_limits_are_durable(rig):
    for i in range(1, 11):
        assert handle(rig, interaction(i))[0] == 200
    assert handle(rig, interaction(11))[0] == 429
    rig.clock.now += 61
    assert handle(rig, interaction(12))[0] == 200


def test_hostile_payload_and_absent_backend_do_not_dispatch(rig):
    doc = find()
    doc["data"]["options"][0]["options"][0]["value"] = "bad\u0000input"
    assert handle(rig, doc)[0] == 400
    assert handle(rig, interaction(2, name="resume"))[0] == 404
    assert rig.calls == []


def test_wsgi_rejects_oversized_requests_and_plain_endpoint(rig):
    app = InteractionApp(rig.endpoint)
    status = []
    def start_response(value, _headers):
        status.append(value)
    app({"REQUEST_METHOD": "POST", "PATH_INFO": "/interactions",
         "CONTENT_LENGTH": "10000000", "wsgi.input": BytesIO()}, start_response)
    assert status.pop().startswith("413")
    app({"REQUEST_METHOD": "GET", "PATH_INFO": "/interactions"}, start_response)
    assert status.pop().startswith("405")


def test_deferred_delivery_timeout_does_not_retry_ambiguous_reply(rig):
    handle(rig, find())

    def timeout(*args):
        raise TimeoutError("private fixture token")

    assert rig.endpoint.work_once(timeout)
    assert rig.store.status(OWNER, find()["id"], rig.clock.now) == "reply_uncertain"
    assert not rig.endpoint.work_once(lambda *args: pytest.fail("unsafe retry"))


def test_manifest_only_contains_usable_commands(rig):
    manifest = {item["name"]: item for item in rig.endpoint.manifest()}
    assert set(manifest) == {"health", "settings", "tasks", "jobs"}
    assert manifest["jobs"]["options"][0]["name"] == "find"
    assert manifest["jobs"]["options"][0]["options"][0]["type"] == 3

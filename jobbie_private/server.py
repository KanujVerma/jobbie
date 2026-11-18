"""Standalone WSGI endpoint and explicitly enabled Discord reply worker."""
from __future__ import annotations

import argparse
import http.client
import json
import os
import sqlite3
import sys
from pathlib import Path
import time
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, make_server

from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from src.config import load_config

from .catalogue import CatalogueReader
from .discord import DiscordEndpoint, MAX_BODY, ReplyUnavailable, default_commands, reject_duplicate
from .evidence import Evidence, evidence_commands
from .github import GitHubEvidence, GitHubRead
from .profile import DownloadRoute, private_commands, safe_profile
from .ranking import Ranking, ranking_commands
from .storage import PrivateStore, STATUSES
from .tasks import TaskStore

HTTP = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 409: "Conflict",
        413: "Payload Too Large", 429: "Too Many Requests", 503: "Service Unavailable"}


class InteractionApp:
    def __init__(self, endpoint: DiscordEndpoint, download: DownloadRoute | None = None):
        self.endpoint = endpoint
        self.download = download

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/private/resumes/") and self.download and environ.get("REQUEST_METHOD") == "GET":
            query = environ.get("QUERY_STRING", "")
            try:
                parameters = parse_qs(query, max_num_fields=1, strict_parsing=True) if len(query) < 100 else {}
                tickets = parameters.get("ticket", [])
                status, headers, response = self.download(path, environ.get("HTTP_AUTHORIZATION", ""),
                                                          tickets[0] if len(tickets) == 1 else "")
            except (ValueError, InvalidToken, sqlite3.Error):
                status, headers, response = 404, [("Cache-Control", "no-store")], b""
            start_response(f"{status} {HTTP[status]}", [*headers, ("Content-Length", str(len(response)))])
            return [response]
        if path != "/interactions":
            status, reply = 404, {}
        elif environ.get("REQUEST_METHOD") != "POST":
            status, reply = 405, {}
        else:
            status, reply = self._post(environ)
        response = json.dumps(reply, separators=(",", ":")).encode()
        start_response(f"{status} {HTTP[status]}", [
            ("Content-Type", "application/json"), ("Cache-Control", "no-store"),
            ("Content-Length", str(len(response))),
        ])
        return [response]

    def _post(self, environ):
        try:
            length = int(environ.get("CONTENT_LENGTH") or "")
        except (TypeError, ValueError):
            return 400, {}
        if not 0 <= length <= MAX_BODY:
            return 413, {}
        body = environ["wsgi.input"].read(length)
        if len(body) != length:
            return 400, {}
        return self.endpoint.handle(body, {
            "X-Signature-Ed25519": environ.get("HTTP_X_SIGNATURE_ED25519", ""),
            "X-Signature-Timestamp": environ.get("HTTP_X_SIGNATURE_TIMESTAMP", ""),
        })


class QuietRequestHandler(WSGIRequestHandler):
    def log_message(self, _format, *args):
        pass


def endpoint_from_env(vault: PrivateStore) -> DiscordEndpoint:
    store = TaskStore(vault.path, vault.key)
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(os.environ["JOBBIE_DISCORD_PUBLIC_KEY"]))
    commands = (*default_commands(store), *private_commands(vault), *evidence_commands(vault))
    path = os.environ.get("JOBBIE_P3_CATALOGUE_PATH")
    if path:
        reader = CatalogueReader(Path(path))
        try:
            reader.verify()
            filters = load_config().filters
        except (ValueError, OSError):
            # Preserve the existing private capabilities if the catalogue input is unavailable.
            pass
        else:
            commands += ranking_commands(Ranking(reader, vault, filters=filters))
    return DiscordEndpoint(key, os.environ["JOBBIE_DISCORD_APPLICATION_ID"], vault.owner, store, commands,
                           guild=os.environ.get("JOBBIE_DISCORD_GUILD_ID"))


def edit_original(application: str, token: str, reply: dict, expires: int) -> None:
    path = f"/api/v10/webhooks/{application}/{token}/messages/@original"
    body = json.dumps(reply, ensure_ascii=True)
    for delay in (0, 0.25, 0.5, 1, 2):
        if delay:
            time.sleep(delay)
        remaining = expires - time.time()
        if remaining <= 0:
            break
        connection = http.client.HTTPSConnection("discord.com", timeout=min(3, remaining))
        try:
            connection.request("PATCH", path, body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            if response.status == 200:
                return
            if response.status == 404:
                detail = json.loads(response.read(4097))
                if isinstance(detail, dict) and detail.get("code") in (10008, 10015):
                    continue
            raise OSError("Discord reply did not return success")
        finally:
            connection.close()
    raise ReplyUnavailable("Discord original response is unavailable")


def owner_action(args, vault: PrivateStore) -> None:
    match args.mode:
        case "profile-set":
            body = sys.stdin.buffer.read(4097)
            if len(body) > 4096:
                raise ValueError("Profile input exceeds limit")
            fields = safe_profile(json.loads(body, object_pairs_hook=reject_duplicate))
            print(vault.set_profile(fields, args.request_id).id)
        case "resume-delete":
            print("Deleted." if vault.delete_resume(args.version_id) else "Resume version unavailable.")
        case "resume-link":
            ticket = vault.sign_download(args.version_id, int(time.time()))
            print(f"/private/resumes/{args.version_id}?ticket={ticket}")
        case "application-open":
            print(vault.create_application(args.snapshot_id, args.request_id).id)
        case "application-status":
            event = vault.record_attempt(args.application_id, args.status, args.request_id,
                                         confirmed=args.owner_confirms is True)
            print(event.id)
        case "facts-propose":
            rows = Evidence(vault).propose_resume(args.version_id)
            print(json.dumps([row.id for row in rows]))
        case "fact-inspect":
            print(json.dumps(Evidence(vault).inspect(args.fact_id), ensure_ascii=True))
        case "fact-decide":
            event = Evidence(vault).decide(args.fact_id, args.decision, args.request_id,
                                           confirm_protected=args.confirm_protected,
                                           replacement_id=args.replacement_id)
            print(event.id)
        case "github-approve":
            body = sys.stdin.buffer.read(4097)
            if len(body) > 4096:
                raise ValueError("Repository approval input exceeds limit")
            spec = json.loads(body, object_pairs_hook=reject_duplicate)
            print(GitHubEvidence(vault, None).approve(spec, args.request_id,
                                                      confirmed=args.owner_confirms).id)
        case "github-revoke":
            print(GitHubEvidence(vault, None).revoke(args.approval_id, args.request_id,
                                                     confirmed=args.owner_confirms).id)
        case "github-propose":
            read = GitHubRead(os.environ.get("JOBBIE_GITHUB_READ_TOKEN"))
            proposal = GitHubEvidence(vault, read).propose(args.approval_id, args.commit, args.deployment_id)
            print(proposal.id)
        case "backup":
            vault.backup(args.destination)
            print("Encrypted database backup created.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jobbie's optional private Discord service")
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("serve").add_argument("--port", type=int, default=8765)
    modes.add_parser("worker")
    modes.add_parser("commands")
    modes.add_parser("profile-set").add_argument("--request-id", required=True)
    modes.add_parser("resume-delete").add_argument("version_id")
    modes.add_parser("resume-link").add_argument("version_id")
    modes.add_parser("backup").add_argument("destination", type=Path)
    application = modes.add_parser("application-open")
    application.add_argument("snapshot_id")
    application.add_argument("--request-id", required=True)
    attempt = modes.add_parser("application-status")
    attempt.add_argument("application_id")
    attempt.add_argument("status", choices=sorted(STATUSES))
    attempt.add_argument("--request-id", required=True)
    attempt.add_argument("--owner-confirms", action="store_true", required=True)
    modes.add_parser("facts-propose").add_argument("version_id")
    modes.add_parser("fact-inspect").add_argument("fact_id")
    decision = modes.add_parser("fact-decide")
    decision.add_argument("fact_id")
    decision.add_argument("decision", choices=("confirm", "revoke", "correct"))
    decision.add_argument("--request-id", required=True)
    decision.add_argument("--confirm-protected", action="store_true")
    decision.add_argument("--replacement-id")
    approve = modes.add_parser("github-approve")
    approve.add_argument("--request-id", required=True)
    approve.add_argument("--owner-confirms", action="store_true", required=True)
    revoke = modes.add_parser("github-revoke")
    revoke.add_argument("approval_id")
    revoke.add_argument("--request-id", required=True)
    revoke.add_argument("--owner-confirms", action="store_true", required=True)
    github = modes.add_parser("github-propose")
    github.add_argument("approval_id")
    github.add_argument("commit")
    github.add_argument("--deployment-id", type=int)
    args = parser.parse_args()
    try:
        vault = PrivateStore(Path(os.environ["JOBBIE_PRIVATE_DB"]), os.environ["JOBBIE_PRIVATE_KEY"].encode(),
                             os.environ["JOBBIE_DISCORD_OWNER_ID"])
        if args.mode not in ("commands", "serve", "worker"):
            owner_action(args, vault)
            return
        endpoint = endpoint_from_env(vault)
        bearer = os.environ.get("JOBBIE_PRIVATE_DOWNLOAD_TOKEN")
        download = DownloadRoute(vault, bearer) if bearer else None
    except (ValueError, OSError, KeyError, sqlite3.Error):
        raise SystemExit("Private configuration or request is invalid.") from None
    if args.mode == "commands":
        print(json.dumps(endpoint.manifest(), indent=2))
    elif args.mode == "serve":
        with make_server("127.0.0.1", args.port, InteractionApp(endpoint, download),
                         handler_class=QuietRequestHandler) as server:
            server.serve_forever()
    else:
        while True:
            if not endpoint.work_once(edit_original):
                time.sleep(0.5)


if __name__ == "__main__":
    main()

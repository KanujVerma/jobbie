"""Standalone WSGI endpoint and explicitly enabled Discord reply worker."""
from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import time
from wsgiref.simple_server import WSGIRequestHandler, make_server

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .discord import DiscordEndpoint, MAX_BODY, default_commands
from .tasks import TaskStore

HTTP = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 409: "Conflict",
        413: "Payload Too Large", 429: "Too Many Requests", 503: "Service Unavailable"}


class InteractionApp:
    def __init__(self, endpoint: DiscordEndpoint):
        self.endpoint = endpoint

    def __call__(self, environ, start_response):
        if environ.get("PATH_INFO") != "/interactions":
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


def endpoint_from_env() -> DiscordEndpoint:
    store = TaskStore(Path(os.environ["JOBBIE_PRIVATE_DB"]), os.environ["JOBBIE_PRIVATE_KEY"].encode())
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(os.environ["JOBBIE_DISCORD_PUBLIC_KEY"]))
    return DiscordEndpoint(key, os.environ["JOBBIE_DISCORD_APPLICATION_ID"],
                           os.environ["JOBBIE_DISCORD_OWNER_ID"], store, default_commands(store))


def edit_original(application: str, token: str, reply: dict) -> None:
    connection = http.client.HTTPSConnection("discord.com", timeout=3)
    try:
        connection.request("PATCH", f"/api/v10/webhooks/{application}/{token}/messages/@original",
                           body=json.dumps(reply, ensure_ascii=True),
                           headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise OSError("Discord reply did not return success")
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Jobbie's optional private Discord service")
    parser.add_argument("mode", choices=("serve", "commands", "worker"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        endpoint = endpoint_from_env()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit("Private endpoint configuration is missing or invalid.") from None
    if args.mode == "commands":
        print(json.dumps(endpoint.manifest(), indent=2))
    elif args.mode == "serve":
        with make_server("127.0.0.1", args.port, InteractionApp(endpoint),
                         handler_class=QuietRequestHandler) as server:
            server.serve_forever()
    else:
        while True:
            if not endpoint.work_once(edit_original):
                time.sleep(0.5)


if __name__ == "__main__":
    main()

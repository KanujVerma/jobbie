"""Discord interaction verification, bounded routing, and deferred replies."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sqlite3
import time
from typing import Callable

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .tasks import TASK_LIFETIME, TaskStore

MAX_BODY = 64 * 1024
MAX_CLOCK_SKEW = 300
EPHEMERAL = 64
TOKEN = re.compile(r"[A-Za-z0-9._-]{1,512}")
SNOWFLAKE = re.compile(r"[1-9][0-9]{16,19}")


class ReplyUnavailable(Exception):
    """Discord definitively rejected the edit because the original is absent."""


def snowflake(value: object) -> bool:
    return isinstance(value, str) and SNOWFLAKE.fullmatch(value) is not None


def user_text(value: object, limit: int) -> bool:
    return (isinstance(value, str) and 0 < len(value) <= limit
            and not re.search(r"[\x00-\x1f\x7f\ud800-\udfff]", value))


def reject_duplicate(fields: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in fields:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


@dataclass(frozen=True)
class Interaction:
    key: str
    owner: str
    options: dict


@dataclass(frozen=True)
class Message:
    content: str
    rows: tuple[dict, ...] = ()


@dataclass(frozen=True)
class Command:
    path: tuple[str, ...]
    description: str
    handler: Callable[[Interaction], str | Message]
    options: tuple[str, ...] = ()
    deferred: bool = False
    attachments: tuple[str, ...] = ()


def response_data(content: str | Message) -> dict:
    message = content if isinstance(content, Message) else Message(content)
    bounded = message.content.encode("utf-16-le", errors="replace")[:3800].decode("utf-16-le", errors="ignore")
    data = {"content": bounded, "allowed_mentions": {"parse": []}, "flags": EPHEMERAL | 4}
    if message.rows:
        data["components"] = list(message.rows)
    return data


def default_commands(store: TaskStore, clock: Callable[[], float] = time.time) -> tuple[Command, ...]:
    def task_status(request: Interaction) -> str:
        tasks = store.recent(request.owner, int(clock()))
        return "\n".join(f"{key} {status}" for key, status in tasks) or "No recent tasks."

    return (
        Command(("health",), "Check the private endpoint", lambda _: "Private endpoint is responding."),
        Command(("settings",), "Show private service settings",
                lambda _: "Owner-only commands. Replies are ephemeral. Delivery authority is legacy JSON."),
        Command(("tasks", "status"), "Inspect recent deferred tasks", task_status),
    )


class DiscordEndpoint:
    def __init__(self, key: Ed25519PublicKey, application: str, owner: str, store: TaskStore,
                 commands: tuple[Command, ...], *, clock: Callable[[], float] = time.time):
        if not snowflake(application) or not snowflake(owner):
            raise ValueError("Discord application and owner IDs must be snowflakes")
        self.key, self.application, self.owner, self.store = key, application, owner, store
        self.commands = {command.path: command for command in commands}
        if len(self.commands) != len(commands):
            raise ValueError("Duplicate command path")
        self.clock = clock

    def manifest(self) -> list[dict]:
        roots: dict[str, dict] = {}
        for command in self.commands.values():
            if command.path[0] == "component":
                continue
            spec = {"name": command.path[-1], "description": command.description}
            if command.options:
                spec["options"] = [{"name": name, "description": name.replace("_", " "),
                                    "type": 11 if name in command.attachments else 3,
                                    "required": True} for name in command.options]
            if len(command.path) == 1:
                roots[command.path[0]] = spec
            else:
                group = roots.setdefault(command.path[0], {
                    "name": command.path[0], "description": f"Private {command.path[0]} commands",
                    "options": [],
                })
                group["options"].append(spec | {"type": 1})
        return list(roots.values())

    def _verify(self, body: bytes, headers: dict, now: int) -> int | None:
        signature = headers.get("X-Signature-Ed25519", "")
        stamp = headers.get("X-Signature-Timestamp", "")
        if not re.fullmatch(r"[0-9A-Fa-f]{128}", signature) or not re.fullmatch(r"[0-9]{1,11}", stamp):
            return None
        signed_at = int(stamp)
        if abs(now - signed_at) > MAX_CLOCK_SKEW:
            return None
        try:
            self.key.verify(bytes.fromhex(signature), stamp.encode("ascii") + body)
        except InvalidSignature:
            return None
        return signed_at

    def handle(self, body: bytes, headers: dict) -> tuple[int, dict]:
        if len(body) > MAX_BODY:
            return 413, {}
        now = int(self.clock())
        signed_at = self._verify(body, headers, now)
        if signed_at is None:
            return 401, {}
        try:
            document = json.loads(body.decode("utf-8"), object_pairs_hook=reject_duplicate)
        except (ValueError, RecursionError):
            return 400, {}
        if not isinstance(document, dict) or type(document.get("type")) is not int:
            return 400, {}
        if document["type"] == 1:
            return 200, {"type": 1}
        if document["type"] not in (2, 3):
            return 404, {}

        if not self._owner_interaction(document):
            return 403, {}
        interaction_id, token = document.get("id"), document.get("token")
        if not snowflake(interaction_id) or not isinstance(token, str) or not TOKEN.fullmatch(token):
            return 400, {}
        try:
            parse = self._parse_component if document["type"] == 3 else self._parse_command
            command, options = parse(document.get("data"))
        except ValueError:
            return 400, {}
        if command is None:
            return 404, {}
        request = Interaction(interaction_id, self.owner, options)
        payload = {"path": command.path, "options": options, "token": token,
                   "key": interaction_id, "owner": self.owner} if command.deferred else None
        expires = min(signed_at, now) + TASK_LIFETIME
        try:
            status = self.store.accept(self.owner, interaction_id, now, expires, payload)
            if status != 200:
                return status, {}
            if payload is not None:
                return 200, {"type": 5, "data": {"flags": EPHEMERAL}}
        except sqlite3.Error:
            return 503, {}
        try:
            return 200, {"type": 4, "data": response_data(command.handler(request))}
        except Exception:
            return 503, {}

    def _owner_interaction(self, document: dict) -> bool:
        if document.get("application_id") != self.application:
            return False
        if "member" in document:
            member = document["member"]
            if not isinstance(member, dict) or "user" in document:
                return False
            user = member.get("user")
        else:
            user = document.get("user")
        return isinstance(user, dict) and user.get("id") == self.owner

    def _parse_component(self, data: object) -> tuple[Command | None, dict]:
        if not isinstance(data, dict) or data.get("component_type") != 2:
            raise ValueError("Invalid component")
        custom_id = data.get("custom_id")
        match = re.fullmatch(r"(save|explain):([0-9a-f]{32})", custom_id) if isinstance(custom_id, str) else None
        if match is None:
            raise ValueError("Invalid component")
        return self.commands.get(("component", match[1])), {"result": match[2]}

    def _parse_command(self, data: object) -> tuple[Command | None, dict]:
        if not isinstance(data, dict) or not user_text(data.get("name"), 32):
            raise ValueError("Invalid command")
        path = (data["name"],)
        options = data.get("options", [])
        if not isinstance(options, list):
            raise ValueError("Invalid options")
        if len(options) == 1 and isinstance(options[0], dict) and options[0].get("type") == 1:
            subcommand = options[0]
            if not user_text(subcommand.get("name"), 32):
                raise ValueError("Invalid subcommand")
            path += (subcommand["name"],)
            options = subcommand.get("options", [])
        command = self.commands.get(path)
        if command is None:
            return None, {}
        if not isinstance(options, list) or len(options) != len(command.options):
            raise ValueError("Invalid arguments")
        values = {}
        for option in options:
            if not isinstance(option, dict) or option.get("name") not in command.options:
                raise ValueError("Invalid argument")
            name, value = option["name"], option.get("value")
            if name in command.attachments:
                if option.get("type") != 11 or not snowflake(value):
                    raise ValueError("Invalid attachment")
                resolved = data.get("resolved")
                files = resolved.get("attachments") if isinstance(resolved, dict) else None
                file = files.get(value) if isinstance(files, dict) else None
                if not isinstance(file, dict) or file.get("id") != value:
                    raise ValueError("Attachment was not resolved")
                values[name] = {key: file.get(key) for key in ("id", "size", "content_type", "url")}
            else:
                if option.get("type") != 3 or not user_text(value, 300):
                    raise ValueError("Invalid argument")
                values[name] = value
        if set(values) != set(command.options):
            raise ValueError("Duplicate or missing argument")
        return command, values

    def work_once(self, deliver: Callable[[str, str, dict, int], None]) -> bool:
        task = self.store.take(self.owner, int(self.clock()))
        if task is None:
            return False
        task_id, expires, sealed = task
        try:
            data = json.loads(self.store.cipher.decrypt(sealed))
            if data["owner"] != self.owner or data["key"] != task_id:
                raise ValueError("Task identity changed")
            command = self.commands[tuple(data["path"])]
            if not command.deferred or not TOKEN.fullmatch(data["token"]):
                raise ValueError("Invalid task")
        except (ValueError, TypeError, KeyError, InvalidToken):
            self.store.finish(self.owner, task_id, "failed")
            return True
        try:
            content = command.handler(Interaction(task_id, self.owner, data["options"]))
        except Exception:
            self.store.finish(self.owner, task_id, "failed")
            return True
        if int(self.clock()) >= expires:
            self.store.finish(self.owner, task_id, "expired")
            return True
        try:
            reply = response_data(content)
            # Discord fixes ephemerality at the initial deferred ACK.
            reply["flags"] &= ~EPHEMERAL
            deliver(self.application, data["token"], reply, expires)
        except ReplyUnavailable:
            self.store.finish(self.owner, task_id, "failed")
        except Exception:
            self.store.finish(self.owner, task_id, "reply_uncertain")
        else:
            self.store.finish(self.owner, task_id, "done")
        return True

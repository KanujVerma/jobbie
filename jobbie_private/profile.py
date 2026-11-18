"""Private storage commands and owner-authenticated resume downloads."""
from __future__ import annotations

from dataclasses import dataclass
import hmac
import re
import time
from typing import Callable

from .discord import Command, Interaction, user_text
from .resume import PDF, fetch_attachment, parse_resume
from .storage import PrivateStore, RECORD_ID


@dataclass(frozen=True)
class DownloadRoute:
    vault: PrivateStore
    bearer: str
    clock: Callable[[], float] = time.time

    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", self.bearer):
            raise ValueError("Use a separate high-entropy download credential")

    def __call__(self, path: str, authorization: str, ticket: str) -> tuple[int, list, bytes]:
        key = path.removeprefix("/private/resumes/")
        headers = [("Cache-Control", "no-store"), ("Referrer-Policy", "no-referrer"),
                   ("X-Content-Type-Options", "nosniff")]
        if (not path.startswith("/private/resumes/") or not RECORD_ID.fullmatch(key)
                or not authorization.isascii() or not hmac.compare_digest(authorization, "Bearer " + self.bearer)):
            return 404, headers, b""
        version = self.vault.authorize_download(key, ticket, int(self.clock()))
        if version is None:
            return 404, headers, b""
        extension = "pdf" if version.media_type == PDF else "docx"
        headers += [("Content-Type", version.media_type),
                    ("Content-Disposition", f'attachment; filename="resume.{extension}"')]
        return 200, headers, version.body


def safe_profile(fields: dict) -> dict:
    if not isinstance(fields, dict) or not fields or set(fields) - {"display_name", "target_roles", "target_locations"}:
        raise ValueError("Profile fields are unsupported")
    if "display_name" in fields and not user_text(fields["display_name"], 80):
        raise ValueError("Display name is invalid")
    for key in ("target_roles", "target_locations"):
        if key in fields and (not isinstance(fields[key], list) or len(fields[key]) > 12
                              or not all(user_text(item, 80) for item in fields[key])):
            raise ValueError("Profile preferences are invalid")
    return fields


def private_commands(vault: PrivateStore) -> tuple[Command, ...]:
    def show_profile(request: Interaction) -> str:
        if request.owner != vault.owner:
            return "Profile unavailable."
        profile = vault.profile()
        if profile is None:
            return "Profile setup is available through the owner console."
        data = profile.data
        lines = [data["display_name"]] if "display_name" in data else []
        lines.extend(data.get("target_roles", []))
        lines.extend(data.get("target_locations", []))
        return "\n".join(lines) or "Profile contains no display preferences."

    def upload_resume(request: Interaction) -> str:
        if request.owner != vault.owner:
            return "Resume upload unavailable."
        try:
            media_type, body = fetch_attachment(request.options["file"])
            text = parse_resume(media_type, body)
            version = vault.store_resume(media_type, body, text, request.key)
        except ValueError:
            return "Resume upload failed validation. Use a readable PDF or DOCX under 5 MiB."
        return f"Resume version saved privately. ID: `{version.id}`"

    def applications(request: Interaction) -> str:
        if request.owner != vault.owner:
            return "Applications unavailable."
        rows = vault.applications(limit=10)
        return "\n".join(f"`{row.id}` {row.status}" for row in rows) or "No application records."

    return (
        Command(("profile", "show"), "Show private profile preferences", show_profile),
        Command(("resume", "upload"), "Upload a PDF or DOCX privately", upload_resume,
                ("file",), deferred=True, attachments=("file",)),
        Command(("applications",), "List owner-confirmed application records", applications),
    )

"""Bound and isolate parsing of owner-uploaded documents."""
from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_UPLOAD = 5 * 1024 * 1024
MAX_TEXT = 100_000
ATTACHMENT_TIMEOUT = 8
ATTACHMENT_WORKER = Path(__file__).resolve()
ATTACHMENT_HOSTS = {"cdn.discordapp.com", "media.discordapp.net"}
ATTACHMENT_PATH = re.compile(r"/attachments/[0-9]{17,20}/[0-9]{17,20}/[^/?#\\]{1,240}")


def validate_format(media_type: str, body: bytes) -> None:
    magic = {PDF: b"%PDF-", DOCX: b"PK\x03\x04"}.get(media_type)
    if magic is None or not 0 < len(body) <= MAX_UPLOAD or not body.startswith(magic):
        raise ValueError("Upload must be a bounded PDF or DOCX matching its declared format")


def parse_resume(media_type: str, body: bytes) -> str:
    validate_format(media_type, body)
    worker = str(Path(__file__).with_name("resume_worker.py").resolve())
    with TemporaryDirectory() as isolated:
        try:
            result = subprocess.run(
                [sys.executable, "-I", worker, media_type], input=body, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, cwd=isolated, env={"PATH": os.defpath}, timeout=6, check=True,
            )
            text = result.stdout.decode("utf-8")
        except (subprocess.SubprocessError, UnicodeError, OSError):
            raise ValueError("Document cannot be parsed safely") from None
    if not 0 < len(text) <= MAX_TEXT:
        raise ValueError("Document needs readable text within the extraction limit")
    return text


def _attachment_request(attachment: dict):
    media_type, length, url = attachment.get("content_type"), attachment.get("size"), attachment.get("url")
    if media_type not in (PDF, DOCX) or type(length) is not int or not 0 < length <= MAX_UPLOAD:
        raise ValueError("Attachment format or size is unsupported")
    if not isinstance(url, str) or len(url) > 2000 or re.search(r"[\x00-\x20\x7f]", url):
        raise ValueError("Attachment URL is invalid")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc not in ATTACHMENT_HOSTS or parsed.fragment
            or not ATTACHMENT_PATH.fullmatch(parsed.path)):
        raise ValueError("Only Discord attachments are readable")
    segments = parsed.path.split("/")
    if segments[3] != attachment.get("id"):
        raise ValueError("Attachment identity changed")
    return media_type, length, parsed


def _download(attachment: dict) -> bytes:
    media_type, length, parsed = _attachment_request(attachment)
    conn = http.client.HTTPSConnection(parsed.netloc, timeout=3)
    try:
        target = parsed.path + ("?" + parsed.query if parsed.query else "")
        conn.request("GET", target, headers={"Accept-Encoding": "identity"})
        response = conn.getresponse()
        actual_type = (response.getheader("Content-Type", "") or "").split(";", 1)[0]
        response_type = response.getheader("Content-Encoding", "identity")
        if (response.status != 200 or actual_type not in {media_type, "application/octet-stream"}
                or response_type != "identity"):
            raise ValueError("Discord attachment is unavailable or invalid")
        body = response.read(length + 1)
    except (OSError, http.client.HTTPException):
        raise ValueError("Discord attachment could not be read") from None
    finally:
        conn.close()
    if len(body) != length:
        raise ValueError("Discord attachment size changed")
    validate_format(media_type, body)
    return body


def fetch_attachment(attachment: dict) -> tuple[str, bytes]:
    media_type, length, _ = _attachment_request(attachment)
    record = {key: attachment[key] for key in ("id", "content_type", "size", "url")}
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(ATTACHMENT_WORKER)], input=json.dumps(record).encode(),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env={"PATH": os.defpath},
            timeout=ATTACHMENT_TIMEOUT, check=True,
        )
    except (subprocess.SubprocessError, OSError):
        raise ValueError("Discord attachment could not be read") from None
    if len(result.stdout) != length:
        raise ValueError("Discord attachment size changed")
    validate_format(media_type, result.stdout)
    return media_type, result.stdout


if __name__ == "__main__":
    sys.stdout.buffer.write(_download(json.loads(sys.stdin.buffer.read(4096))))

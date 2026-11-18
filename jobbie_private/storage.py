"""Encrypted, owner-scoped SQLite records for the private service."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
from time import time
from uuid import uuid4

from cryptography.fernet import Fernet

from .discord import snowflake
from .tasks import private_file

DOWNLOAD_TTL = 300
STATUSES = frozenset({"applied", "interviewing", "rejected", "withdrawn", "offer"})
RECORD_ID = re.compile(r"[a-f0-9]{32}")


@dataclass(frozen=True)
class Record:
    id: str
    data: dict
    created: int


@dataclass(frozen=True)
class ResumeVersion:
    id: str
    media_type: str
    body: bytes
    text: str
    sha256: str


@dataclass(frozen=True)
class JobSnapshot:
    id: str
    job: dict


@dataclass(frozen=True)
class Application:
    id: str
    snapshot_id: str
    status: str


@dataclass(frozen=True)
class ApplicationAttempt:
    id: str
    application_id: str
    status: str
    occurred: int


class PrivateStore:
    def __init__(self, path: Path, key: bytes, owner: str):
        if not snowflake(owner):
            raise ValueError("Invalid owner")
        self.cipher = Fernet(key)
        self.key = key
        raw = base64.urlsafe_b64decode(key)
        self.signing_key = hmac.digest(raw, b"jobbie-private-download-v1", "sha256")
        self.index_key = hmac.digest(raw, b"jobbie-private-idempotency-v1", "sha256")
        self.owner = owner
        self.path = private_file(path)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS private_records_v1 (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, kind TEXT NOT NULL,
                    idem BLOB, parent BLOB, created INTEGER NOT NULL, sealed BLOB,
                    UNIQUE(owner,kind,idem)
                );
                CREATE INDEX IF NOT EXISTS private_record_index_v1
                    ON private_records_v1(owner,kind,parent,created);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=0.5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA secure_delete=ON")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _json(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

    def _open(self, row: sqlite3.Row, kind: str) -> Record:
        body = json.loads(self.cipher.decrypt(row["sealed"]))
        if (body["owner"], body["kind"], body["id"], body["created"]) != (
            self.owner, kind, row["id"], row["created"]
        ):
            raise ValueError("Private record authentication failed")
        return Record(row["id"], body["data"], row["created"])

    def _parent(self, kind: str, key: str) -> bytes:
        return hmac.digest(self.index_key, self._json(["parent", self.owner, kind, key]), "sha256")

    def put(self, kind: str, data: dict, request_id: str | None = None, *,
            parent_id: str | None = None) -> Record:
        """Append an immutable encrypted record with scoped idempotency."""
        idem = (hmac.digest(self.index_key, self._json([self.owner, kind, request_id]), "sha256")
                if request_id is not None else None)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if idem is not None:
                old = db.execute("SELECT * FROM private_records_v1 WHERE owner=? AND kind=? AND idem=?",
                                 (self.owner, kind, idem)).fetchone()
                if old is not None:
                    if old["sealed"] is None:
                        raise ValueError("This request was already deleted")
                    record = self._open(old, kind)
                    if self._json(record.data) != self._json(data):
                        raise ValueError("Request ID already recorded with different data")
                    return record
            key, created = uuid4().hex, int(time())
            plain = self._json({"owner": self.owner, "kind": kind, "id": key,
                                "created": created, "data": data})
            if len(plain) > 8 * 1024 * 1024:
                raise ValueError("Private record exceeds its size limit")
            parent = self._parent(kind, parent_id) if parent_id is not None else None
            db.execute("INSERT INTO private_records_v1 VALUES (?,?,?,?,?,?,?)",
                       (key, self.owner, kind, idem, parent, created, self.cipher.encrypt(plain)))
            return Record(key, data, created)

    def get(self, kind: str, key: str) -> Record | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM private_records_v1 WHERE owner=? AND kind=? AND id=? "
                             "AND sealed IS NOT NULL", (self.owner, kind, key)).fetchone()
            return self._open(row, kind) if row is not None else None

    def records(self, kind: str, *, limit: int = 100, parent_id: str | None = None) -> list[Record]:
        if not 1 <= limit <= 10_000:
            raise ValueError("Invalid list limit")
        query = "SELECT * FROM private_records_v1 WHERE owner=? AND kind=? AND sealed IS NOT NULL"
        args = [self.owner, kind]
        if parent_id is not None:
            query += " AND parent=?"
            args.append(self._parent(kind, parent_id))
        with self.connect() as db:
            rows = db.execute(query + " ORDER BY rowid DESC LIMIT ?", (*args, limit)).fetchall()
            return [self._open(row, kind) for row in rows]

    def set_profile(self, fields: dict, request_id: str) -> Record:
        return self.put("profile", fields, request_id)

    def profile(self) -> Record | None:
        return next(iter(self.records("profile", limit=1)), None)

    def snapshot(self, job: dict, request_id: str) -> JobSnapshot:
        record = self.put("job_snapshot", job, request_id)
        return JobSnapshot(record.id, record.data)

    def save_job(self, snapshot_id: str) -> Record:
        if self.get("job_snapshot", snapshot_id) is None:
            raise ValueError("Job snapshot unavailable")
        return self.put("saved_job", {"snapshot_id": snapshot_id}, snapshot_id)

    def store_resume(self, media_type: str, body: bytes, text: str, request_id: str) -> ResumeVersion:
        from .resume import validate_format
        validate_format(media_type, body)
        if not text or len(text) > 100_000:
            raise ValueError("Resume text unavailable or exceeds its limit")
        record = self.put("resume_version", {"media_type": media_type, "sha256": hashlib.sha256(body).hexdigest(),
                                            "body": base64.b64encode(body).decode(), "text": text}, request_id)
        return self._resume(record)

    @staticmethod
    def _resume(record: Record) -> ResumeVersion:
        data = record.data
        return ResumeVersion(record.id, data["media_type"], base64.b64decode(data["body"]),
                             data["text"], data["sha256"])

    def resume(self, version_id: str) -> ResumeVersion | None:
        record = self.get("resume_version", version_id)
        return self._resume(record) if record is not None else None

    def delete_resume(self, version_id: str) -> bool:
        with self.connect() as db:
            result = db.execute("UPDATE private_records_v1 SET sealed=NULL WHERE owner=? AND kind='resume_version' "
                                "AND id=? AND sealed IS NOT NULL", (self.owner, version_id))
            return result.rowcount == 1

    def _signature(self, version_id: str, expiry: int) -> str:
        return hmac.digest(self.signing_key, self._json([self.owner, version_id, expiry]), "sha256").hex()

    def sign_download(self, version_id: str, now: int) -> str:
        if self.get("resume_version", version_id) is None:
            raise ValueError("Resume version unavailable")
        expiry = now + DOWNLOAD_TTL
        return f"{expiry}.{self._signature(version_id, expiry)}"

    def authorize_download(self, version_id: str, ticket: str, now: int) -> ResumeVersion | None:
        if not RECORD_ID.fullmatch(version_id) or not re.fullmatch(r"[0-9]{1,11}\.[0-9a-f]{64}", ticket):
            return None
        raw_expiry, signature = ticket.split(".")
        expiry = int(raw_expiry)
        if not now < expiry <= now + DOWNLOAD_TTL:
            return None
        if not hmac.compare_digest(signature, self._signature(version_id, expiry)):
            return None
        return self.resume(version_id)

    def create_application(self, snapshot_id: str, request_id: str) -> Application:
        if self.get("job_snapshot", snapshot_id) is None:
            raise ValueError("Job snapshot unavailable")
        record = self.put("application", {"snapshot_id": snapshot_id}, request_id)
        return Application(record.id, snapshot_id, "planning")

    def record_attempt(self, application_id: str, status: str, request_id: str, *,
                       confirmed: bool) -> ApplicationAttempt:
        if confirmed is not True:
            raise ValueError("Owner confirmation is required")
        if status not in STATUSES or self.get("application", application_id) is None:
            raise ValueError("Application or status unavailable")
        record = self.put("application_attempt", {"application_id": application_id, "status": status},
                          request_id, parent_id=application_id)
        return self._attempt(record)

    @staticmethod
    def _attempt(record: Record) -> ApplicationAttempt:
        return ApplicationAttempt(record.id, record.data["application_id"],
                                  record.data["status"], record.created)

    def attempts(self, application_id: str) -> list[ApplicationAttempt]:
        return [self._attempt(row) for row in self.records("application_attempt", limit=10_000,
                                                         parent_id=application_id)]

    def applications(self, *, limit: int = 100) -> list[Application]:
        result = []
        for row in self.records("application", limit=limit):
            events = self.records("application_attempt", parent_id=row.id, limit=1)
            status = events[0].data["status"] if events else "planning"
            result.append(Application(row.id, row.data["snapshot_id"], status))
        return result

    def backup(self, destination: Path) -> None:
        destination = Path(destination)
        target = private_file(destination, new=True)
        try:
            with self.connect() as source:
                copy = sqlite3.connect(target)
                try:
                    source.backup(copy)
                finally:
                    copy.close()
            os.chmod(target, 0o600)
        except Exception:
            target.unlink(missing_ok=True)
            raise

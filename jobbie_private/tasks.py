"""Owner-scoped Discord replay ledger and encrypted durable task queue."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import stat

from cryptography.fernet import Fernet, InvalidToken

TASK_LIFETIME = 15 * 60
RETENTION = 24 * 60 * 60
RATE_WINDOW = 60
MAX_REQUESTS = 10
_KEY_MARKER = b"jobbie-private-db-key-v1"


def private_file(path: Path) -> Path:
    path = Path(path).expanduser().absolute()
    root = Path(__file__).resolve().parents[1]
    if path.resolve().is_relative_to(root):
        raise ValueError("Use an owner-only directory outside the repository")
    parent = path.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o077:
        raise ValueError("Private data directory must be owner-only")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        pass
    else:
        os.close(fd)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Private database must be an owner-only regular file")
    return path


def verify_database_key(db: sqlite3.Connection, cipher: Fernet) -> None:
    """Bind one key to the database before either process can change private data."""
    db.execute("BEGIN IMMEDIATE")
    db.execute("CREATE TABLE IF NOT EXISTS jobbie_private_key_v1 "
               "(id INTEGER PRIMARY KEY CHECK(id=1), encrypted_marker BLOB NOT NULL)")
    marker = db.execute("SELECT encrypted_marker FROM jobbie_private_key_v1 WHERE id=1").fetchone()
    try:
        if marker is not None:
            if cipher.decrypt(marker[0]) != _KEY_MARKER:
                raise InvalidToken
            return

        # An existing unbound store must authenticate all retained ciphertext
        # before recording a key, otherwise mixed-key data could be adopted.
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "discord_tasks" in tables:
            for (payload,) in db.execute("SELECT payload FROM discord_tasks WHERE payload IS NOT NULL"):
                cipher.decrypt(payload)
        if "private_records_v1" in tables:
            for (sealed,) in db.execute("SELECT sealed FROM private_records_v1 WHERE sealed IS NOT NULL"):
                cipher.decrypt(sealed)
    except (InvalidToken, TypeError):
        raise ValueError("Private database encryption key does not match retained data") from None
    db.execute("INSERT INTO jobbie_private_key_v1 VALUES (1,?)", (cipher.encrypt(_KEY_MARKER),))


class TaskStore:
    def __init__(self, path: Path, key: bytes):
        self.cipher = Fernet(key)
        self.path = private_file(path)
        with self.connect() as db:
            verify_database_key(db, self.cipher)
            db.executescript("""
                CREATE TABLE IF NOT EXISTS interaction_receipts (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, received INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS interaction_rate
                    ON interaction_receipts (owner, received);
                CREATE TABLE IF NOT EXISTS discord_tasks (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, expires INTEGER NOT NULL,
                    status TEXT NOT NULL, payload BLOB
                );
                CREATE INDEX IF NOT EXISTS discord_pending
                    ON discord_tasks(owner, status, expires, id);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=0.20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _expire(self, db, now: int) -> None:
        db.execute("UPDATE discord_tasks SET status='expired', payload=NULL "
                   "WHERE expires<=? AND status='queued'", (now,))
        db.execute("UPDATE discord_tasks SET status='reply_uncertain' "
                   "WHERE expires<=? AND status='running'", (now,))
        db.execute("DELETE FROM discord_tasks WHERE expires<=?", (now - RETENTION,))
        db.execute("DELETE FROM interaction_receipts WHERE received<=?", (now - RETENTION,))

    def accept(self, owner: str, key: str, now: int, expires: int, payload: dict | None) -> int:
        """Reserve the interaction once and enqueue within the same transaction."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire(db, now)
            if db.execute("SELECT 1 FROM interaction_receipts WHERE id=?", (key,)).fetchone():
                return 409
            count, = db.execute("SELECT count(*) FROM interaction_receipts WHERE owner=? AND received>?",
                                (owner, now - RATE_WINDOW)).fetchone()
            if count >= MAX_REQUESTS:
                return 429
            db.execute("INSERT INTO interaction_receipts VALUES (?,?,?)", (key, owner, now))
            if payload is not None:
                encrypted = self.cipher.encrypt(json.dumps(payload, ensure_ascii=True).encode())
                db.execute("INSERT INTO discord_tasks VALUES (?,?,?,'queued',?)",
                           (key, owner, expires, encrypted))
            return 200

    def status(self, owner: str, key: str, now: int) -> str | None:
        with self.connect() as db:
            row = db.execute("SELECT status,expires FROM discord_tasks WHERE owner=? AND id=?",
                             (owner, key)).fetchone()
        if row is None or row["expires"] <= now - RETENTION:
            return None
        if row["expires"] <= now:
            return {"queued": "expired", "running": "reply_uncertain"}.get(row["status"], row["status"])
        return row["status"]

    def recent(self, owner: str, now: int) -> list[tuple[str, str]]:
        with self.connect() as db:
            return [(row["id"], row["status"]) for row in db.execute("""
                SELECT id, CASE WHEN expires<=? THEN
                    CASE status WHEN 'queued' THEN 'expired' WHEN 'running' THEN 'reply_uncertain'
                         ELSE status END
                    ELSE status END AS status
                FROM discord_tasks WHERE owner=? AND expires>?
                ORDER BY expires DESC,id DESC LIMIT 10
            """, (now, owner, now - RETENTION))]

    def take(self, owner: str, now: int) -> tuple[str, int, bytes] | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._expire(db, now)
            row = db.execute("SELECT id,expires,payload FROM discord_tasks "
                             "WHERE owner=? AND status='queued' ORDER BY expires,id LIMIT 1", (owner,)).fetchone()
            if row is None:
                return None
            db.execute("UPDATE discord_tasks SET status='running',payload=NULL WHERE owner=? AND id=?",
                       (owner, row["id"]))
            return row["id"], row["expires"], row["payload"]

    def finish(self, owner: str, key: str, status: str) -> None:
        if status not in {"done", "failed", "expired", "reply_uncertain"}:
            raise ValueError("Unknown terminal task status")
        with self.connect() as db:
            db.execute("UPDATE discord_tasks SET status=? WHERE owner=? AND id=? "
                       "AND status IN ('running','reply_uncertain')",
                       (status, owner, key))

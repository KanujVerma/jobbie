"""Versioned read-only projection from an owner-approved catalogue snapshot."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

from src.catalogue import Catalogue, CatalogueError
from src.job_identity import canonical_job_url
from src.models import Job

PROJECTION_VERSION = "p2-catalogue-v2/ranking-v1"
MAX_LISTINGS = 25_000
_QUERY = """
    SELECT j.job_id,o.source_id,o.snapshot_sha,ss.last_listing_at,
           ss.adapter_posted_at,s.payload
    FROM jobs j
    JOIN source_state ss ON ss.rowid=(
        SELECT candidate.rowid FROM source_state candidate
        JOIN observations previous ON previous.id=candidate.latest_observation_id
        JOIN snapshots available ON available.sha=previous.snapshot_sha
        WHERE candidate.job_id=j.job_id AND candidate.status='open'
          AND json_extract(available.payload,'$.source_enabled')=1
        ORDER BY candidate.last_listing_at DESC,candidate.latest_observation_id DESC LIMIT 1
    )
    JOIN observations o ON o.id=ss.latest_observation_id
    JOIN snapshots s ON s.sha=o.snapshot_sha
    WHERE j.status IN ('open','reopened')
"""


@dataclass(frozen=True)
class Listing:
    job: Job
    id: str
    source_id: str
    snapshot_sha: str
    catalogue_id: str
    url: str
    posted_date: date | None
    posted_at: datetime | None

    def reference(self) -> dict:
        return {"job_id": self.id, "source_id": self.source_id, "snapshot_sha": self.snapshot_sha,
                "catalogue_id": self.catalogue_id, "title": self.job.title, "url": self.url,
                "projection": PROJECTION_VERSION}


class CatalogueReader:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser().absolute()

    def _open(self) -> Catalogue:
        try:
            root = Path(__file__).resolve().parents[1]
            info = self.path.lstat()
            partial = any(self.path.with_name(self.path.name + suffix).exists()
                          for suffix in ("-wal", "-journal", "-shm"))
            if (self.path.resolve().is_relative_to(root) or info.st_uid != os.getuid()
                    or info.st_mode & 0o077 or not stat.S_ISREG(info.st_mode) or partial):
                raise ValueError("Use a complete owner-only catalogue snapshot outside Git")
            catalogue = Catalogue(self.path, readonly=True)
            catalogue.db.execute("PRAGMA query_only=ON")
            return catalogue
        except (OSError, CatalogueError, sqlite3.Error) as error:
            raise ValueError("Catalogue snapshot is unavailable") from error

    def verify(self) -> None:
        with self._open():
            pass

    @staticmethod
    def _listing(row: sqlite3.Row, catalogue_id: str) -> Listing | None:
        if hashlib.sha256(row["payload"].encode()).hexdigest() != row["snapshot_sha"]:
            raise ValueError("Catalogue snapshot digest does not match its source row")
        snapshot = json.loads(row["payload"])
        url = canonical_job_url(snapshot["url"])
        if url is None or url != snapshot["canonical_url"]:
            return None
        precision = snapshot["posted_precision"]
        source_date = date.fromisoformat(snapshot["source_posted_date"]) if precision == "date" else None
        exact_date = datetime.fromisoformat(snapshot["posted_at"]) if precision == "instant" and snapshot["posted_at"] else None
        snapshot["_observed_at"] = row["last_listing_at"]
        if precision != "instant":
            snapshot["adapter_posted_at"] = row["adapter_posted_at"]
        job = Catalogue.job_from_snapshot(snapshot)
        return Listing(replace(job, id=row["job_id"], url=url), row["job_id"], row["source_id"],
                       row["snapshot_sha"], catalogue_id, url, source_date, exact_date)

    def _query(self, suffix: str, args: tuple, limit: int) -> list[Listing]:
        try:
            with self._open() as catalogue:
                catalogue.db.execute("BEGIN")
                (catalogue_id,) = catalogue.db.execute("SELECT value FROM meta WHERE key='catalogue_uuid'").fetchone()
                rows = catalogue.db.execute(_QUERY + suffix + " ORDER BY j.job_id LIMIT ?", (*args, limit + 1))
                results = []
                for index, row in enumerate(rows):
                    if index >= limit:
                        raise ValueError("Catalogue snapshot is too broad for this query")
                    listing = self._listing(row, catalogue_id)
                    if listing is not None:
                        results.append(listing)
                return results
        except (sqlite3.Error, CatalogueError, KeyError, TypeError):
            raise ValueError("Catalogue snapshot is unavailable") from None

    def find(self, query: str = "") -> list[Listing]:
        if len(query) > 120:
            raise ValueError("Search text is too long")
        if not query.strip():
            return self._query("", (), MAX_LISTINGS)
        escaped = "%" + query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        suffix = """ AND (json_extract(s.payload,'$.title') LIKE ? ESCAPE '\\'
                      OR json_extract(s.payload,'$.location') LIKE ? ESCAPE '\\'
                      OR json_extract(s.payload,'$.company') LIKE ? ESCAPE '\\')"""
        return self._query(suffix, (escaped, escaped, escaped), MAX_LISTINGS)

    def get(self, job_id: str) -> Listing | None:
        return next(iter(self._query(" AND j.job_id=?", (job_id,), 1)), None)

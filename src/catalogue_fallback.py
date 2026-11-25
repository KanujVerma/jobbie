"""Stage a detached JSON fallback from confirmed, retained delivery receipts."""
from datetime import datetime
from hashlib import sha256
from itertools import groupby
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from src.catalogue import Catalogue, CatalogueError
from src.catalogue_checkpoint import _read, unseal
from src.storage import load_state, normalize_url, record_alerted_url, save_state

_MAX_LEGACY_BYTES = 32 * 1024 * 1024


def _confirmed_receipts(store, after_run_id, through_run_id):
    def ordinal(run_id):
        row = store.db.execute("SELECT rowid, status FROM shadow_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row["status"] == "running":
            raise CatalogueError("missing or unfinished fallback run boundary")
        return row["rowid"]

    first, last = ordinal(after_run_id), ordinal(through_run_id)
    if first > last:
        raise CatalogueError("invalid fallback run boundary order")
    if store.db.execute("SELECT 1 FROM shadow_runs WHERE rowid>? AND rowid<=? AND status='running'",
                        (first, last)).fetchone():
        raise CatalogueError("unfinished fallback receipt window")
    rows = store.db.execute("""
        SELECT d.run_id, d.source_id, d.job_id, d.legacy_id, d.observed_at, s.result
        FROM shadow_delivery d JOIN shadow_runs r ON r.run_id=d.run_id
        LEFT JOIN shadow_sources s ON s.run_id=d.run_id AND s.source_id=d.source_id
        WHERE r.rowid>? AND r.rowid<=? AND d.outcome='ack'
        ORDER BY r.rowid, d.source_id, d.id
    """, (first, last))
    for (run_id, source_id), group in groupby(rows, lambda row: (row["run_id"], row["source_id"])):
        urls = {}
        for observation in store.scan_rows(run_id, source_id):
            data = json.loads(observation["payload"])
            key = (observation["job_id"], data["id"])
            urls.setdefault(key, set()).add(normalize_url(data["url"]))
        for receipt in group:
            key = (receipt["job_id"], receipt["legacy_id"])
            matches = urls.get(key, set())
            if len(matches) != 1 or receipt["result"] is None:
                raise CatalogueError("unmapped or ambiguous confirmed delivery receipt")
            (url,) = matches
            company = json.loads(receipt["result"])["company"]
            when = datetime.fromisoformat(receipt["observed_at"])
            if not url or not isinstance(company, str) or not company or when.tzinfo is None:
                raise CatalogueError("invalid confirmed delivery receipt")
            yield company, receipt["legacy_id"], url, when


def stage_legacy_fallback(checkpoint, cipher_path, key, legacy_path, output_path, *, after_run_id):
    """Create a new fallback file and return the number of replayed ACK receipts.

    The boundary is the last run still owned by JSON. This stages a file only:
    it neither replaces the input ledger nor activates any delivery authority.
    """
    output = Path(output_path)
    if output.exists() or output.is_symlink():
        raise CatalogueError("fallback output already exists")
    with TemporaryDirectory(prefix=".jobbie-fallback-", dir=output.parent) as directory:
        db = Path(directory) / "retained.sqlite"
        unseal(checkpoint, cipher_path, db, key)
        raw = _read(legacy_path, _MAX_LEGACY_BYTES)
        if sha256(raw).hexdigest() != checkpoint["legacy_file_sha256"]:
            raise CatalogueError("legacy ledger differs from the authenticated checkpoint")
        staged = Path(directory) / "seen.json"
        staged.write_bytes(raw)
        state = load_state(staged, raise_on_corrupt=True, persist_migration=False)
        if state != json.loads(raw):
            raise CatalogueError("legacy ledger requires a separate migration")

        count = 0
        with Catalogue(db, readonly=True) as store:
            for company, job_id, url, when in _confirmed_receipts(store, after_run_id, checkpoint["run_id"]):
                company_state = state["companies"].setdefault(company, {"last_checked_at": None})
                rows = company_state.setdefault("seen_jobs", {})
                entry = rows.setdefault(job_id, {"first_seen": when.isoformat(), "last_seen": when.isoformat()})
                entry["alerted"] = True
                entry.pop("cap_suppressed", None)
                if url not in state["alerted_urls"]:
                    record_alerted_url(url, company, job_id, state, when)
                count += 1
        save_state(state, staged)
        try:
            os.link(staged, output)  # Atomic publication, never replace another file.
        except FileExistsError as error:
            raise CatalogueError("fallback output already exists") from error
    return count

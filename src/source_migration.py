"""Silent first observation of a replacement provider for an existing source.

This is not delivery acknowledgement. Existing ACKs and URL history survive.
"""
from __future__ import annotations

import re
from datetime import datetime

from src.models import Job


def validate_source_revision(company: dict) -> str | None:
    revision = company.get("source_revision")
    if revision is not None and (
        not isinstance(revision, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", revision)
    ):
        raise ValueError("source_revision must be a nonempty version identifier of at most 80 characters")
    return revision


def apply_source_baseline(
    jobs: list[Job], company: str, company_config: dict, state: dict,
    now: datetime, *, fetch_succeeded: bool,
) -> bool:
    """Return whether this scan belongs to a pending/new source baseline.

    Every returned posting is recorded before filtering. Only a complete fetch
    finishes the revision; partial observations stay suppressed until then.
    Callers also suppress migration backfill during this scan.
    """
    revision = validate_source_revision(company_config)
    if revision is None:
        return False
    if now.tzinfo is None:
        raise ValueError("source baseline requires an aware observation time")
    cs = state["companies"].setdefault(company, {"seen_jobs": {}})
    pending = cs.get("source_revision") != revision
    seen = cs.setdefault("seen_jobs", {})
    for job in jobs:
        entry = seen.get(job.id)
        if pending:
            entry = seen.setdefault(job.id, {
                "first_seen": now.isoformat(), "last_seen": now.isoformat(), "alerted": False,
            })
            if not entry.get("alerted"):
                entry["baseline_suppressed"] = True
        if entry and entry.get("baseline_suppressed"):
            entry["last_seen"] = now.isoformat()
    if pending and fetch_succeeded:
        cs["source_revision"] = revision
        cs.setdefault("source_baselines", {})[revision] = {
            "completed_at": now.isoformat(), "observed_count": len({j.id for j in jobs}),
            "delivery_acknowledged": False,
        }
    return pending

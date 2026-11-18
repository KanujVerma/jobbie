"""Deterministic, evidence-based matching over an isolated catalogue reader."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import re

from src.eligibility import EligibilityVerdict, classify_eligibility
from src.filtering import _check_single_location

from .catalogue import CatalogueReader, Listing, PROJECTION_VERSION
from .discord import Command, Interaction, Message
from .evidence import Evidence
from .storage import PrivateStore, RECORD_ID

WEIGHTS = {"role": 30, "skills": 25, "geography": 15, "salary": 10, "freshness": 10, "company": 10}
POLICY = "jobbie-fit-v1"
DEFAULT_ROLES = ("software engineer", "software developer", "backend engineer", "frontend engineer",
                 "full stack", "product engineer", "ai engineer", "forward deployed engineer",
                 "machine learning engineer", "data engineer", "platform engineer", "swe", "sde")
SKILLS = ("python", "javascript", "typescript", "java", "c++", "c#", "sql", "postgresql", "react",
          "node.js", "aws", "azure", "kubernetes", "docker", "git", "golang", "rust", "swift",
          "pytorch", "tensorflow", "redis", "graphql", "linux", "html", "css", "spark", "terraform")
BAY = re.compile(r"\b(?:san francisco|sf bay area)\b")
BAY_CITIES = re.compile(r"\b(?:san jose|oakland|mountain view|palo alto|santa clara|sunnyvale|"
                        r"san mateo|redwood city|cupertino|menlo park|fremont|berkeley|bay area)\b")
CALIFORNIA = re.compile(r"\b(?:california|ca)\b")
PRIORITY = re.compile(r"\b(?:new york city|nyc|manhattan|brooklyn|chicago|texas|florida)\b"
                      r"|\bnew york,\s*ny\b|,\s*(?:tx|fl)\b")


@dataclass(frozen=True)
class Ranked:
    listing: Listing
    eligibility: EligibilityVerdict
    weights: dict[str, int | None]
    score: int | None
    known_weight: int
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    fact_ids: tuple[str, ...]


def mentioned(text: str, value: str) -> bool:
    return re.search(r"(?<![\w+#])" + re.escape(value) + r"(?![\w+#])", text, re.I) is not None


def annual_base_preference(listing: Listing) -> int | None:
    if listing.job.source_platform != "ashby":
        return None
    result = []
    for item in listing.job.compensation:
        if item.currency != "USD" or item.interval != "1 YEAR" or not item.source_field.startswith("compensation."):
            continue
        lower, upper = item.minimum, item.maximum
        if any(not isinstance(n, Decimal) or not n.is_finite() or n < 0 for n in (lower, upper) if n is not None):
            continue
        if lower is not None and upper is not None and lower > upper:
            continue
        if lower is not None and lower >= 100_000:
            result.append(10)
        elif upper is not None and upper >= 100_000:
            result.append(5)
        elif upper is not None:
            result.append(0)
    return min(result) if result else None


def source_freshness(listing: Listing, now: datetime) -> int | None:
    if listing.posted_at is not None and listing.posted_at.utcoffset() is not None:
        age = (now - listing.posted_at).total_seconds() / 86_400
    elif listing.posted_date is not None:
        age = (now.astimezone(timezone.utc).date() - listing.posted_date).days
    else:
        return None
    if age < 0:
        return None
    return 10 if age <= 3 else 5 if age <= 14 else 0


def rank_listing(listing: Listing, skills: dict[str, tuple[str, ...]], filters: dict, now: datetime,
                 roles: tuple[str, ...] = DEFAULT_ROLES) -> Ranked:
    job = listing.job
    eligibility = classify_eligibility(job, filters)
    if eligibility.status != "eligible":
        return Ranked(listing, eligibility, dict.fromkeys(WEIGHTS), None, 0, (), (), ())
    title = re.sub(r"[-–]+", " ", job.title.casefold())
    role = 30 if any(mentioned(title, value.casefold().replace("-", " ")) for value in roles) else 0
    evidence = tuple(skill for skill in SKILLS if mentioned(job.raw_text, skill))
    matching = tuple(skill for skill in evidence if skills.get(skill))
    missing = tuple(skill for skill in evidence if skill not in matching)
    supported = tuple(sorted({key for name in matching for key in skills[name]}))
    geography = None
    if "US_LOCATION_CONFIRMED" in eligibility.reasons:
        entries = re.split(r"[;\n|]", job.location or "")
        locations = [entry.casefold().strip() for entry in entries if _check_single_location(entry)[0] is True]
        if any(BAY.search(entry) or (CALIFORNIA.search(entry) and BAY_CITIES.search(entry)) for entry in locations):
            geography = 15
        elif any(CALIFORNIA.search(entry) or PRIORITY.search(entry) for entry in locations):
            geography = 10
        else:
            geography = 5
    weights = {
        "role": role, "skills": 25 * len(matching) // len(evidence) if evidence else None,
        "geography": geography, "salary": annual_base_preference(listing),
        "freshness": source_freshness(listing, now), "company": 10 if job.network_priority else 0,
    }
    score = sum(points for points in weights.values() if points is not None)
    known = sum(WEIGHTS[key] for key, points in weights.items() if points is not None)
    return Ranked(listing, eligibility, weights, score, known, matching, missing, supported)


def display(value: str, limit: int = 120) -> str:
    text = re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", " ", value)
    return re.sub(r"([\\`*_{}\[\]()<>|~@])", r"\\\1", text)[:limit]


class Ranking:
    def __init__(self, reader: CatalogueReader, vault: PrivateStore, *, filters=None,
                 clock=lambda: datetime.now(timezone.utc)):
        self.reader = reader
        self.vault = vault
        self.filters = filters or {}
        self.clock = clock

    def _context(self) -> tuple[dict, tuple[str, ...]]:
        skills: dict[str, list[str]] = {}
        for record in Evidence(self.vault).active():
            if record.data["kind"] == "skill":
                skills.setdefault(record.data["value"], []).append(record.id)
        profile = self.vault.profile()
        roles = tuple(profile.data.get("target_roles", ())) if profile else ()
        return {key: tuple(value) for key, value in skills.items()}, roles or DEFAULT_ROLES

    def _selection(self, snapshot_id: str) -> tuple[Listing, dict]:
        if not RECORD_ID.fullmatch(snapshot_id):
            raise ValueError("Private result unavailable")
        record = self.vault.get("job_snapshot", snapshot_id)
        if record is None:
            raise ValueError("Private result unavailable")
        ref = record.data
        if ref.get("projection") != PROJECTION_VERSION:
            raise ValueError("Refresh this result through job search")
        current = self.reader.get(ref["job_id"])
        if current is None or current.reference() != ref:
            raise ValueError("Job source has changed. Search again for fresh evidence")
        return current, ref

    def search(self, query: str, *, top: bool) -> Message:
        skills, roles = self._context()
        now = self.clock()
        feedback = {}
        for event in self.vault.records("rank_feedback", limit=10_000):
            feedback.setdefault(event.data["job_id"], event.data["rating"])
        ranks = [rank_listing(item, skills, self.filters, now, roles) for item in self.reader.find(query)
                 if feedback.get(item.id) != "not_relevant"]
        visible = [item for item in ranks if item.eligibility.status != "excluded"
                   and (not top or item.eligibility.status == "eligible")]
        visible.sort(key=lambda row: (row.eligibility.status != "eligible", -(row.score or 0),
                                      -row.known_weight, feedback.get(row.listing.id) != "relevant", row.listing.id))
        if not visible:
            return Message("No matching listings in the approved catalogue snapshot.")
        descriptions, rows = [], []
        for match in visible[:5]:
            item = match.listing
            ref = item.reference()
            identity = f"{item.catalogue_id}:{item.id}:{item.source_id}:{item.snapshot_sha}"
            selected = self.vault.snapshot(ref, identity)
            score = f"{match.score}/{match.known_weight} evidence points" if match.score is not None else "needs review"
            descriptions.append(f"{display(item.job.title)} | {display(item.job.company, 60)} | {score}\n"
                                f"Result `{selected.id}`")
            components = []
            if len(item.url) <= 512:
                components.append({"type": 2, "style": 5, "label": "View", "url": item.url})
            components += [{"type": 2, "style": 2, "label": action.title(), "custom_id": f"{action}:{selected.id}"}
                           for action in ("save", "explain")]
            rows.append({"type": 1, "components": components})
        return Message("\n\n".join(descriptions), tuple(rows))

    def save(self, snapshot_id: str) -> str:
        item, _ = self._selection(snapshot_id)
        if classify_eligibility(item.job, self.filters).status == "excluded":
            raise ValueError("This listing is no longer eligible for saving")
        self.vault.save_job(snapshot_id)
        return "Saved privately."

    def explain(self, snapshot_id: str) -> str:
        item, _ = self._selection(snapshot_id)
        skills, roles = self._context()
        match = rank_listing(item, skills, self.filters, self.clock(), roles)
        lines = [f"{display(item.job.title)} | {display(item.job.company, 60)}",
                 f"Catalogue job `{item.id}` · snapshot `{item.snapshot_sha[:12]}`",
                 f"Source: {display(item.source_id, 100)}",
                 f"Eligibility {match.eligibility.status} · {', '.join(match.eligibility.reasons)}"]
        if match.score is not None:
            lines.append(f"Fit {match.score}/{match.known_weight} available evidence points.")
            lines.append("Factors: " + ", ".join(f"{name} {'unknown' if value is None else value}"
                                                 for name, value in match.weights.items()))
            lines.append("Matched posting skills: " + (", ".join(match.matched) or "none confirmed"))
            if match.missing:
                lines.append("Posting skills without confirmed evidence: " + ", ".join(match.missing))
            if match.fact_ids:
                lines.append("Verified fact IDs: " + ", ".join(f"`{key}`" for key in match.fact_ids[:12]))
        return "\n".join(lines)

    def feedback(self, snapshot_id: str, rating: str, request_id: str) -> str:
        item, _ = self._selection(snapshot_id)
        if rating not in ("relevant", "not_relevant"):
            raise ValueError("Use relevant or not_relevant")
        self.vault.put("rank_feedback", {"job_id": item.id, "snapshot_id": snapshot_id, "rating": rating}, request_id)
        return "Feedback recorded privately."


def ranking_commands(ranking: Ranking) -> tuple[Command, ...]:
    def own(function):
        def call(request: Interaction):
            if request.owner != ranking.vault.owner:
                return "Ranked result unavailable."
            try:
                return function(request)
            except ValueError:
                return "The result or catalogue snapshot is unavailable. Search again or check the private configuration."
        return call

    return (
        Command(("jobs", "find"), "Search the approved catalogue",
                own(lambda request: ranking.search(request.options["query"], top=False)), ("query",), deferred=True),
        Command(("jobs", "top"), "Rank eligible listings in the approved catalogue",
                own(lambda _: ranking.search("", top=True)), deferred=True),
        Command(("jobs", "feedback"), "Record private relevance feedback",
                own(lambda req: ranking.feedback(req.options["job"], req.options["rating"], req.key)),
                ("job", "rating"), deferred=True),
        Command(("component", "save"), "Save this listing",
                own(lambda req: ranking.save(req.options["result"])), ("result",), deferred=True),
        Command(("component", "explain"), "Explain match evidence",
                own(lambda req: ranking.explain(req.options["result"])), ("result",), deferred=True),
    )

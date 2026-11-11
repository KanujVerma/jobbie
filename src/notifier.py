from __future__ import annotations
import re
import time
import threading
import logging

import requests

from src.models import Job

logger = logging.getLogger(__name__)

ROLE_TYPE_EMOJI = {
    "internship": "🎓",
    "new-grad": "🆕",
    "entry-level": "📌",
    "unknown": "❓",
}

# Discord's hard limit on an embed title; a longer one is rejected with 400.
_DISCORD_TITLE_MAX = 256

_PT_FORMAT = "PT"
_UTC_FORMAT = "UTC"


def _fmt_ts(dt, zone_label: str) -> str:
    """"2026-05-06 1:05 PM PT" — 12-hour clock, no leading zero on the hour.

    The hour is built explicitly rather than with strftime("%-I"): that flag is
    a glibc/BSD extension, absent on Windows, and this formats user-facing text
    so a silent platform difference would be a real defect. "%I" is portable and
    zero-padded, so strip the pad; midnight formats as "12", which lstrip("0")
    would empty, hence the fallback.
    """
    hour = dt.strftime("%I").lstrip("0") or "12"
    return f"{dt.strftime('%Y-%m-%d')} {hour}:{dt.strftime('%M %p')} {zone_label}"


class TokenBucket:
    """Thread-safe token bucket: rate=4/sec, capacity=8."""

    def __init__(self, rate: float = 4.0, capacity: float = 8.0):
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity  # start full
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        added = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + added)
        self._last_refill = now

    def consume(self, tokens: float = 1.0) -> None:
        """Block until a token is available."""
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                # Calculate how long to wait for enough tokens
                deficit = tokens - self._tokens
                wait = deficit / self._rate
            time.sleep(wait)


def sanitize_discord_text(text: str, max_len: int = 1024) -> str:
    """Strip control characters, neutralize disallowed mentions, and truncate safely."""
    if not text:
        return ""
    zwsp = "\u200b"
    clean = re.sub(r"@everyone\b", f"@{zwsp}everyone", text)
    clean = re.sub(r"@here\b", f"@{zwsp}here", clean)
    clean = re.sub(r"<@&?(\d+)>", f"@{zwsp}[\\g<1>]", clean)
    clean = re.sub(r"<@!?(\d+)>", f"@{zwsp}[\\g<1>]", clean)
    # Strip non-printable control chars except \n and \t
    clean = "".join(c for c in clean if c in ("\n", "\t") or (ord(c) >= 32 and ord(c) != 127))
    if len(clean) > max_len:
        clean = clean[: max_len - 1].rstrip() + "…"
    return clean


def sanitize_url(url: str) -> str:
    """Ensure URL uses http or https, otherwise return placeholder."""
    clean = (url or "").strip()
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    return "https://invalid-url"


def _safe_text(value: object, limit: int) -> str:
    """Escape untrusted Discord markdown and keep within a UTF-16 budget."""
    value = "".join(c for c in str(value or "") if not 0xD800 <= ord(c) <= 0xDFFF)
    value = sanitize_discord_text(value, limit)
    value = re.sub(r"([\\`*_{}\[\]()<>|~])", r"\\\1", value)
    out = ""
    for char in value:
        if len((out + char).encode("utf-16-le", "surrogatepass")) // 2 > limit - 1:
            return out.rstrip() + "…"
        out += char
    return out


def _date_text(value) -> str:
    if value is None or value.tzinfo is None or value.utcoffset() is None:
        return "Unknown"
    try:
        from zoneinfo import ZoneInfo
        local = value.astimezone(ZoneInfo("America/Chicago"))
        return _fmt_ts(local, local.tzname() or "CT")
    except Exception:
        from datetime import timezone
        return _fmt_ts(value.astimezone(timezone.utc), "UTC")


def _base_compensation(job: Job) -> str:
    # Ashby normalizes only explicit Salary components; Greenhouse ranges and
    # legacy strings do not consistently identify base pay or its period.
    from decimal import Decimal
    from src.adapters.public_board import format_pay
    if job.source_platform != "ashby":
        return "Not disclosed"
    ranges = tuple(item for item in job.compensation
                   if item.source_field.startswith("compensation.")
                   and item.interval in {"1 HOUR", "1 MONTH", "1 YEAR"}
                   and re.fullmatch(r"[A-Z]{3}", item.currency or "")
                   and (item.minimum is not None or item.maximum is not None)
                   and all(isinstance(n, Decimal) and n.is_finite() and n >= 0
                           for n in (item.minimum, item.maximum) if n is not None)
                   and (item.minimum is None or item.maximum is None or item.minimum <= item.maximum))
    return (format_pay(ranges) or "Not disclosed").replace("–", "-")



def _display_url(value: object, limit: int) -> str | None:
    from src.adapters.public_board import public_https_url
    is_http = isinstance(value, str) and value.startswith("http://")
    candidate = "https://" + value[7:] if is_http else value
    url = public_https_url(candidate)
    if url and is_http:
        url = "http://" + url[8:]
    if not url or any(c in url for c in "@`|") or any(0xD800 <= ord(c) <= 0xDFFF for c in url):
        return None
    return url if len(url.encode("utf-16-le")) // 2 <= limit else None


def build_job_embed(job: Job) -> dict:
    """Build a bounded source-grounded card without changing delivery behavior."""
    title = _safe_text(job.title or "Untitled job", 185)
    company = _safe_text(job.company or "Unknown company", 65)
    title = f"{title} | {company}"
    location = _safe_text(job.location or "Location unknown", 400)
    network = bool(job.network_priority)
    badge = "⭐ NETWORK PRIORITY | Referral: Unconfirmed" if network else "DISCOVERED"
    # Legacy text can mention full-time in an unrelated context.
    employment = job.employment_type
    if employment == "full_time":
        employment_label = "Full-time"
    elif employment in {"internship", "co_op", "contract", "part_time", "temporary"}:
        employment_label = employment.replace("_", " ").title()
    elif job.role_type == "internship":
        employment_label = "Internship"
    else:
        employment_label = "Full-time: Unknown"
    level = getattr(job.verdict, "career_level", None)
    level = {"new_grad": "New grad", "entry_level": "Entry-level", "junior": "Junior"}.get(level)
    if not level and job.verdict is None:
        level = {"new-grad": "New grad", "entry-level": "Entry-level"}.get(job.role_type)
    level = level or "Career level: Unknown"
    description = f"{badge}\n{location}\n{employment_label} | {level}"

    verdict = job.verdict
    status = getattr(verdict, "status", None)
    screen = {"eligible": "Pass", "needs_review": "Needs review", "excluded": "Excluded"}.get(status, "Not assessed")
    reasons = list(getattr(verdict, "reasons", ()) or ())[:2]
    unknowns = list(getattr(verdict, "unknowns", ()) or ())
    if employment_label == "Full-time: Unknown" and "employment_type" not in unknowns:
        unknowns.append("employment_type")
    if job.description_complete is False and "full_job_description" not in unknowns:
        unknowns.append("full_job_description")
    elif job.description_complete is None and "description_completeness" not in unknowns:
        unknowns.append("description_completeness")
    if reasons:
        screen += " | Reasons: " + ", ".join(str(r).replace("_", " ").lower() for r in reasons)
    if unknowns:
        screen += " | Unknown: " + ", ".join(str(u).replace("_", " ").lower() for u in unknowns)
    screen += " | Deterministic screen, not hiring confirmation"

    if job.posted_at is not None and job.posted_at_kind in ("first_published", "last_published"):
        date_name = "First published" if job.posted_at_kind == "first_published" else "Last published"
        date_value = _date_text(job.posted_at)
    elif job.posted_at is not None and job.posted_at_kind == "posted" and job.source_platform not in ("workday",):
        # Legacy adapters may turn a date-only source into midnight UTC.
        date_name = "Employer posted date" if job.source_platform in ("apple_jobs", "amazon_jobs") else "Source date"
        date_value = job.posted_at.strftime("%Y-%m-%d")
    else:
        date_name, date_value = "Observed by Jobbie", _date_text(job.detected_at)
    url = _display_url(job.url, 2048)
    trusted_board = bool(url and url.startswith("https://") and job.source_platform in ("greenhouse", "ashby"))
    prefix = "" if trusted_board else "Employer link unverified: "
    if not url:
        link = "Unavailable or unsafe URL"
    elif len((prefix + url).encode("utf-16-le")) // 2 <= 1024:
        link = prefix + url
    else:
        link = "Open job title for posting" + (" (employer link unverified)" if not trusted_board else "")
    footer_parts = [job.source_platform, job.source_board, job.source_job_id]
    footer = " | ".join(_safe_text(p, 100) for p in footer_parts if p)
    fields = [
        {"name": "Base compensation", "value": _safe_text(_base_compensation(job), 500), "inline": False},
        {"name": "Eligibility screen", "value": _safe_text(screen, 900), "inline": False},
        {"name": date_name, "value": date_value, "inline": True},
        {"name": "Employer posting", "value": link, "inline": False},
    ]
    embed = {"title": title, "description": description, "fields": fields,
             "footer": {"text": footer or "Source unknown"},
             "color": 0xFEE75C if network else 0x5865F2}
    if url and link.startswith("Open job title"):
        embed["url"] = url
    return embed


def build_review_digest(items: list[dict], total: int) -> str:
    """Format bounded, untrusted review entries without changing digest state."""
    lines = [f"Needs review: {total} positions (showing up to {len(items)})."]
    for item in items:
        company = _safe_text(item.get("company"), 45)
        title = _safe_text(item.get("title"), 75)
        entries = [str(r) for r in item.get("reasons", [])]
        eligibility = next((r for r in entries if r.startswith("eligibility: needs_review:")), "")
        codes = [code.strip() for code in eligibility.partition("needs_review:")[2].split(",")]
        review_codes = {
            "COHORT_2027_UNSPECIFIED", "AMBIGUOUS_LEVEL", "EXPERIENCE_UNSPECIFIED",
            "EXPERIENCE_PATHWAY_UNKNOWN", "SOURCE_EMPLOYMENT_UNKNOWN",
            "SOURCE_DESCRIPTION_INCOMPLETE", "LOCATION_UNKNOWN", "WORK_AUTH_UNKNOWN",
            "EXPERIENCE_EXCEEDS_RANGE",
        }
        blockers = [code.replace("_", " ").lower() for code in codes if code in review_codes]
        reasons = _safe_text(", ".join(blockers[:2]) if blockers else eligibility or ", ".join(entries[:2]), 60)
        url = _display_url(item.get("url"), 200) or "Link unavailable or too long"
        lines.append(f"• {company}: {title} | {reasons or 'Review required'}\n{url}")
    return "\n".join(lines)


class Notifier:
    def __init__(self, webhook_url: str):
        self._url = webhook_url
        self._bucket = TokenBucket()

    def send_job_alert(self, job: Job) -> bool:
        """Send one Discord embed for a job. Returns True on success."""
        embed = build_job_embed(job)
        return self._send_embed(embed)

    def send_summary(self, title: str, description: str) -> bool:
        """Send a plain text summary embed."""
        embed = {"title": title, "description": description, "color": 0x57F287}
        return self._send_embed(embed)

    def _send_embed(self, embed: dict) -> bool:
        """POST the embed to Discord. Handle 429 with retry-after."""
        self._bucket.consume()
        payload = {"embeds": [embed]}
        try:
            resp = requests.post(self._url, json=payload, timeout=10)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("retry-after", 5))
                logger.warning(f"Discord 429 rate limit; sleeping {retry_after}s")
                time.sleep(retry_after)
                # Retry once
                resp = requests.post(self._url, json=payload, timeout=10)
            if resp.ok:
                logger.info("Discord webhook acknowledged (HTTP %d)", resp.status_code)
                return True
            logger.warning("Discord webhook error (HTTP %d)", resp.status_code)
            return False
        except requests.RequestException as e:
            logger.warning("Discord webhook request failed (%s)", type(e).__name__)
            return False

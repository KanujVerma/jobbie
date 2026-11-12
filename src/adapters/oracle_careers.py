# oracle_careers.py
"""Oracle's documented public Candidate Experience requisition search.

The site-specific findReqs finder is required. The root collection contains
one search envelope; its count/hasMore do not page requisitionList. Page the
inner list against TotalJobsCount, with bounded reads and incomplete-read
failure reporting. Legacy fixture/config mode is retained without site_number.

Current Oracle site/location IDs are verified from its public careers HTML.
No session handshake, login or browser is needed for the documented finder.
Date-only source values retain calendar precision without a guessed timestamp.
Missing qualifications/employment remain unknown and cannot become eligible
from a junior title alone.

https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-recruitingcejobrequisitions-get.html
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import date, datetime, timezone
import re
from urllib.parse import urlsplit

import requests

from src.adapters.base import BaseAdapter
from src.filtering import make_job_id
from src.models import Job
from src.adapters.public_board import PublicBoardError, description, public_https_url, read_public_json, text

logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 25


class OracleAdapter(BaseAdapter):
    source_platform = "oracle_careers"

    @staticmethod
    def validate_source_config(config: dict) -> None:
        if config.get("site_number") is None:
            return  # retain the legacy configuration/fixture contract
        site = config.get("site_number")
        if not isinstance(site, str) or not re.fullmatch(r"CX_[0-9]{1,12}", site):
            raise ValueError("Oracle site_number must be the verified CX_<number>")
        location = config.get("location_id")
        if location is not None and (not isinstance(location, str) or not re.fullmatch(r"[0-9]{1,24}", location)):
            raise ValueError("Oracle location_id must be a verified numeric ID")
        base = public_https_url(config.get("base_url"))
        if not base or not urlsplit(base).hostname.endswith(".oraclecloud.com") or urlsplit(base).path.strip("/") or urlsplit(base).query:
            raise ValueError("Oracle finder requires a public HTTPS Oracle Cloud tenant origin")
        if config.get("api_path", "/hcmRestApi/resources/latest/recruitingCEJobRequisitions") != "/hcmRestApi/resources/latest/recruitingCEJobRequisitions":
            raise ValueError("Oracle finder uses only the documented requisitions endpoint")
        careers = public_https_url(config.get("careers_url"))
        if not careers or urlsplit(careers).hostname != "careers.oracle.com" or urlsplit(careers).query or not re.fullmatch(r"/en/sites/[A-Za-z0-9_-]+/?", urlsplit(careers).path):
            raise ValueError("Oracle careers_url must be the verified public site root")
        for key, default, maximum in (("limit", 100, 100), ("max_pages", 50, 100)):
            value = config.get(key, default)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"Oracle {key} must be 1..{maximum}")

    def _fetch_finder(self) -> Iterator[Job]:
        self.validate_source_config(self.config)
        limit = self.config.get("limit", 100)
        endpoint = self.config["base_url"].rstrip("/") + "/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        offset = 0
        seen = set()
        prior_total = None
        for _ in range(self.config.get("max_pages", 50)):
            finder = f"findReqs;siteNumber={self.config['site_number']},limit={limit},offset={offset}"
            if self.config.get("location_id"):
                finder += f",locationId={self.config['location_id']}"
            payload = read_public_json(self.http, endpoint, {"onlyData": "true", "expand": "requisitionList", "finder": finder})
            items = payload.get("items")
            if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
                raise PublicBoardError("Oracle finder must return one search envelope")
            envelope = items[0]
            rows, total = envelope.get("requisitionList"), envelope.get("TotalJobsCount")
            if not isinstance(rows, list) or type(total) is not int or total < 0:
                raise PublicBoardError("Oracle finder has invalid job list/total")
            if prior_total is not None and prior_total != total:
                self.record_fetch_error("SEARCH_TOTAL_CHANGED")
            prior_total = total
            if not rows:
                if offset < total:
                    raise PublicBoardError("Oracle finder returned an incomplete search page")
                return
            before = len(seen)
            for row in rows:
                if not isinstance(row, dict):
                    self.record_fetch_error("INVALID_REQUISITION")
                    continue
                job = self._parse_requisition(row)
                if job is None:
                    self.record_fetch_error("INVALID_REQUISITION")
                elif job.id not in seen:
                    seen.add(job.id)
                    yield job
                else:
                    # Overlap can hide an omitted row even when the raw page
                    # offsets reach TotalJobsCount. Keep unique observations,
                    # but do not certify the source baseline complete.
                    self.record_fetch_error("DUPLICATE_REQUISITION")
            if len(seen) == before:
                raise PublicBoardError("Oracle finder repeated a page; scan incomplete")
            offset += len(rows)
            if offset >= total:
                return
            self.http.polite_delay(1.0, 2.0)
        raise PublicBoardError("Oracle finder page cap reached; scan incomplete")

    def fetch(self) -> Iterator[Job]:
        if self.config.get("site_number") is not None:
            yield from self._fetch_finder()
            return
        base_url = self.config.get("base_url", "https://eeho.fa.us2.oraclecloud.com")
        api_path = self.config.get(
            "api_path",
            "/hcmRestApi/resources/latest/recruitingCEJobRequisitions",
        )
        limit = int(self.config.get("limit", _DEFAULT_LIMIT))
        url = base_url.rstrip("/") + api_path

        offset = 0
        total = None

        while True:
            params = {
                "onlyData": "true",
                "limit": limit,
                "offset": offset,
                "expand": "requisitionList",
            }

            try:
                resp = self.http.get(url, params=params)
            except requests.HTTPError as exc:
                logger.error(
                    "Oracle HCM API HTTP error at offset %d: %s", offset, exc
                )
                self.record_fetch_error(exc)
                return
            except requests.RequestException as exc:
                logger.error(
                    "Oracle HCM API request failed at offset %d: %s", offset, exc
                )
                self.record_fetch_error(exc)
                return

            try:
                data = resp.json()
            except ValueError as exc:
                logger.error("Oracle HCM API returned invalid JSON: %s", exc)
                self.record_fetch_error(exc)
                return

            count = data.get("count", 0)
            has_more = data.get("hasMore", False)

            # totalResults may be present (spec says so) but some tenant versions
            # omit it — fall back to has_more flag.
            if total is None:
                total = data.get("totalResults")

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                req_list = item.get("requisitionList", [])
                for req in req_list:
                    job = self._parse_requisition(req)
                    if job is not None:
                        yield job

            # Advance pagination
            offset += count if count > 0 else limit

            # Stop conditions
            if not has_more:
                break
            if total is not None and offset >= total:
                break
            if count == 0:
                break

            self.http.polite_delay(1.0, 2.0)

    def _parse_requisition(self, req: dict) -> Job | None:
        official_id = str(req.get("Id", "")).strip()
        title = text(req.get("Title"))
        finder_mode = self.config.get("site_number") is not None
        if not title or finder_mode and (not re.fullmatch(r"[0-9]{1,32}", official_id) or len(title) > 4096):
            return None

        location = text(req.get("PrimaryLocation"))
        department = text(req.get("JobFunction")) or None
        posted_at = _parse_iso_date(req.get("PostedDate"))

        external_url = text(req.get("ExternalURL"))
        if finder_mode:
            external_url = self.config["careers_url"].rstrip("/") + f"/job/{official_id}"
        elif not external_url and official_id:
            external_url = f"https://careers.oracle.com/jobs/{official_id}"

        short_desc = text(req.get("ShortDescription"))
        complete = None
        employment = None
        if finder_mode:
            sections = []
            flags = []
            for key, heading in (("ShortDescriptionStr", "About the role"),
                                 ("ExternalResponsibilitiesStr", "Responsibilities"),
                                 ("ExternalQualificationsStr", "Qualifications")):
                value, full = description(req.get(key), is_html=True)
                sections.append(f"{heading}\n{value}" if value else "")
                flags.append(full)
            short_desc = "\n".join(sections)
            complete = all(flags)
            employment = {"full time": "full_time", "full-time": "full_time", "part time": "part_time",
                          "part-time": "part_time", "internship": "internship", "contract": "contract"}.get(
                              str(req.get("JobSchedule") or "").lower(), "unknown")
        raw_parts = [title, location]
        if department:
            raw_parts.append(department)
        if short_desc:
            raw_parts.append(short_desc)
        raw_text = " ".join(raw_parts).lower()

        job_id = make_job_id(
            company=self.company,
            source_platform=self.source_platform,
            title=title,
            location=location,
            official_id=official_id if official_id else None,
        )

        return Job(
            id=job_id,
            company=self.company,
            title=title,
            location=location,
            department=department,
            category=None,
            url=external_url,
            source_platform=self.source_platform,
            posted_at=posted_at,
            detected_at=datetime.now(tz=timezone.utc),
            raw_text=raw_text,
            role_type="unknown",
            priority="normal",
            matched_keywords=(),
            source_posted_date=_calendar_date(req.get("PostedDate")),
            source_job_id=official_id if finder_mode else None,
            source_board=self.config.get("site_number"),
            source_url=self.config.get("careers_url"),
            description_complete=complete,
            employment_type=employment,
        )


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Python 3.7+ handles ISO 8601 with timezone offset
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def _calendar_date(value: object) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None

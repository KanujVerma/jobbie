"""
Tests for Phase 1 P1-B: Immutable original cohort, network priority badges,
safe Discord embed formatting, and referral status invariants.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
import pytest

from src.config import load_config
from src.models import Job
from src.notifier import build_job_embed, sanitize_discord_text, sanitize_url

_NOW = datetime(2026, 11, 4, 12, 0, 0, tzinfo=timezone.utc)
_POSTED = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)

ORIGINAL_13_COMPANIES = {
    "Micron",
    "Salesforce",
    "CrowdStrike",
    "Intel",
    "Applied Materials",
    "Western Digital",
    "SanDisk",
    "Plaid",
    "Oracle",
    "Microsoft Research",
    "Microsoft",
    "Amazon",
    "Apple",
}

DISABLED_2_COMPANIES = {
    "Snowflake",
    "Applied Digital",
}


def _make_sample_job(**kwargs) -> Job:
    defaults = dict(
        id="sample-job-1",
        company="Micron",
        title="Software Engineer, New Grad",
        location="San Jose, CA",
        department="Engineering",
        category="Software",
        url="https://example.com/job/1",
        source_platform="workday",
        posted_at=_POSTED,
        detected_at=_NOW,
        raw_text="software engineer new grad san jose ca",
        role_type="new-grad",
        priority="preferred",
        matched_keywords=("new grad", "software engineer"),
        verdict=None,
        network_priority=True,
        cohort="original_2026_11_04",
        referral_status="unconfirmed",
        salary=None,
    )
    defaults.update(kwargs)
    return Job(**defaults)


class TestNetworkCohortConfig:
    """Validate exact 13 enabled flagged and 2 disabled unflagged companies in companies.yaml."""

    def test_exact_13_enabled_and_2_disabled(self):
        config = load_config("companies.yaml")
        enabled_companies = [c for c in config.companies if c.get("enabled", True)]
        disabled_companies = [c for c in config.companies if not c.get("enabled", True)]

        assert len(enabled_companies) == 13
        assert len(disabled_companies) == 2

        enabled_names = {c["name"] for c in enabled_companies}
        disabled_names = {c["name"] for c in disabled_companies}

        assert enabled_names == ORIGINAL_13_COMPANIES
        assert disabled_names == DISABLED_2_COMPANIES

    def test_original_13_have_network_priority_and_unconfirmed_referral(self):
        config = load_config("companies.yaml")
        for company in config.companies:
            cname = company["name"]
            if cname in ORIGINAL_13_COMPANIES:
                assert company.get("network_priority") is True, f"{cname} must have network_priority: true"
                assert company.get("cohort") == "original_2026_11_04", f"{cname} must have cohort: original_2026_11_04"
                assert company.get("referral_status") == "unconfirmed", f"{cname} must have referral_status: unconfirmed"

    def test_disabled_companies_are_not_flagged_network_priority(self):
        config = load_config("companies.yaml")
        for company in config.companies:
            cname = company["name"]
            if cname in DISABLED_2_COMPANIES:
                assert company.get("network_priority", False) is False, f"Disabled {cname} must not have network_priority"
                assert company.get("cohort") != "original_2026_11_04"

    def test_new_discovered_company_defaults_to_unflagged(self):
        job = Job(
            id="test-new-co",
            company="NewCo",
            title="Software Engineer",
            location="Austin, TX",
            department=None,
            category=None,
            url="https://newco.com/job/1",
            source_platform="greenhouse",
            posted_at=None,
            detected_at=_NOW,
            raw_text="software engineer",
            role_type="new-grad",
            priority="normal",
            matched_keywords=(),
        )
        assert job.network_priority is False
        assert job.cohort == "discovered"
        assert job.referral_status == "unavailable"


class TestNotifierEmbedFormatting:
    def test_network_priority_embed_badge_and_color(self):
        embed = build_job_embed(_make_sample_job())
        assert embed["title"].startswith("Software Engineer, New Grad")
        assert "⭐ NETWORK PRIORITY" in embed["description"]
        assert "Referral: Unconfirmed" in embed["description"]
        assert embed["color"] == 0xFEE75C

    def test_discovered_embed_badge_and_color(self):
        embed = build_job_embed(_make_sample_job(network_priority=False, company="StartupX"))
        assert embed["description"].startswith("DISCOVERED")
        assert "Referral" not in embed["description"]
        assert embed["color"] == 0x5865F2

    def test_location_and_microsoft_research_remain_distinct(self):
        embed = build_job_embed(_make_sample_job(company="Microsoft Research", location="San Francisco, CA; Redmond, WA"))
        assert "Microsoft Research" in embed["title"]
        assert "San Francisco, CA; Redmond, WA" in embed["description"]

    def test_unknown_date_uses_observation(self):
        embed = build_job_embed(_make_sample_job(posted_at=None))
        fields = {f["name"]: f["value"] for f in embed["fields"]}
        assert "Observed by Jobbie" in fields
        assert "Posted" not in fields

    def test_legacy_salary_is_not_assumed_to_be_base(self):
        embed = build_job_embed(_make_sample_job(salary="$135,000 - $155,000"))
        assert next(f["value"] for f in embed["fields"] if f["name"] == "Base compensation") == "Not disclosed"


class TestNotifierSanitizationAndLimits:
    """Validate protection against mentions, control characters, bad URLs, and length overflows."""

    def test_disallowed_mentions_neutralized(self):
        text = "Hello @everyone and @here and <@123456789> and <@&987654321>"
        cleaned = sanitize_discord_text(text)
        assert "@everyone" not in cleaned
        assert "@here" not in cleaned
        assert "<@" not in cleaned
        assert "@\u200beveryone" in cleaned
        assert "@\u200bhere" in cleaned

    def test_control_characters_stripped(self):
        text = "Job Title\x00\x08\x0b\x0cWith\x1fNulls"
        cleaned = sanitize_discord_text(text)
        assert "\x00" not in cleaned
        assert "\x08" not in cleaned
        assert "\x1f" not in cleaned
        assert cleaned == "Job TitleWithNulls"

    def test_bad_url_sanitization(self):
        assert sanitize_url("javascript:alert(1)") == "https://invalid-url"
        assert sanitize_url("data:text/html,...") == "https://invalid-url"
        assert sanitize_url("https://careers.micron.com/job/123") == "https://careers.micron.com/job/123"
        assert sanitize_url("http://insecure.com/job/456") == "http://insecure.com/job/456"

    def test_long_title_safely_budgeted(self):
        long_loc = "A" * 300
        job = _make_sample_job(location=long_loc, priority="preferred")
        embed = build_job_embed(job)
        assert len(embed["title"]) <= 256
        assert "A" * 300 in embed["description"]

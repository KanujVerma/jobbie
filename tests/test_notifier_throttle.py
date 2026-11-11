"""Tests for TokenBucket and Notifier in src/notifier.py."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.notifier import TokenBucket, Notifier
from src.models import Job

_NOW = datetime(2026, 5, 6, 12, 0, 0, tzinfo=timezone.utc)


def make_job(**kwargs) -> Job:
    defaults = dict(
        id="test-job-1",
        company="Acme",
        title="Software Engineering Intern",
        location="San Francisco, CA",
        department="Engineering",
        category="Software",
        url="https://example.com/job/1",
        source_platform="workday",
        posted_at=None,
        detected_at=_NOW,
        raw_text="software engineering intern san francisco ca",
        role_type="internship",
        priority="preferred",
        matched_keywords=("intern", "software"),
    )
    defaults.update(kwargs)
    return Job(**defaults)


# ---------------------------------------------------------------------------
# TokenBucket tests
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_bucket_starts_full_can_consume_immediately(self):
        bucket = TokenBucket(rate=4.0, capacity=8.0)
        start = time.monotonic()
        # Should be able to consume 8 tokens immediately (bucket starts full)
        for _ in range(8):
            bucket.consume(1.0)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Consuming 8 tokens from full bucket took too long: {elapsed:.2f}s"

    def test_consuming_faster_than_rate_blocks(self):
        """Consuming 12 tokens at 4/sec should take ~1 second (4 immediate, 8 after refill)."""
        bucket = TokenBucket(rate=4.0, capacity=8.0)
        start = time.monotonic()
        for _ in range(12):  # 8 from full capacity + 4 more = ~1s wait
            bucket.consume(1.0)
        elapsed = time.monotonic() - start
        # Should have blocked for at least ~0.8s (some slack for CI)
        assert elapsed >= 0.5, f"Expected blocking but elapsed only {elapsed:.2f}s"

    def test_tokens_refill_over_time(self):
        bucket = TokenBucket(rate=4.0, capacity=8.0)
        # Drain the bucket
        for _ in range(8):
            bucket.consume(1.0)
        # Wait enough for 2 tokens to refill
        time.sleep(0.6)
        # Should be able to consume 2 quickly
        start = time.monotonic()
        bucket.consume(1.0)
        bucket.consume(1.0)
        elapsed = time.monotonic() - start
        assert elapsed < 0.5

    def test_custom_capacity(self):
        bucket = TokenBucket(rate=10.0, capacity=3.0)
        start = time.monotonic()
        for _ in range(3):
            bucket.consume(1.0)
        elapsed = time.monotonic() - start
        assert elapsed < 0.5


# ---------------------------------------------------------------------------
# Notifier tests (mocked HTTP)
# ---------------------------------------------------------------------------

class TestNotifierSendJobAlert:
    def test_success_returns_true(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.ok = True

        with patch("src.notifier.requests.post", return_value=mock_resp) as mock_post:
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job()
            result = notifier.send_job_alert(job)

        assert result is True
        mock_post.assert_called_once()

    def test_embed_title_contains_company(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.ok = True

        captured = {}
        def capture_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("src.notifier.requests.post", side_effect=capture_post):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job(company="Acme Corp", priority="normal")
            notifier.send_job_alert(job)

        embed = captured["payload"]["embeds"][0]
        assert "Acme Corp" in embed["title"]

    def test_embed_description_is_job_title(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.ok = True

        captured = {}
        def capture_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("src.notifier.requests.post", side_effect=capture_post):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job(title="Data Engineering Intern")
            notifier.send_job_alert(job)

        embed = captured["payload"]["embeds"][0]
        assert embed["title"].startswith("Data Engineering Intern")

    def test_preferred_priority_appended_to_title(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.ok = True

        captured = {}
        def capture_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("src.notifier.requests.post", side_effect=capture_post):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job(priority="preferred", location="San Francisco, CA")
            notifier.send_job_alert(job)

        embed = captured["payload"]["embeds"][0]
        assert "San Francisco, CA" in embed["description"]

    def test_http_500_returns_false(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.ok = False
        mock_resp.text = "Internal Server Error"

        with patch("src.notifier.requests.post", return_value=mock_resp):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job()
            result = notifier.send_job_alert(job)

        assert result is False

    def test_429_retries_once(self):
        """On 429, should sleep retry-after and retry once."""
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.ok = False
        resp_429.headers = {"retry-after": "0.01"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.ok = True

        call_count = {"n": 0}

        def side_effect(url, json=None, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return resp_429
            return resp_200

        with patch("src.notifier.requests.post", side_effect=side_effect):
            with patch("src.notifier.time.sleep"):  # don't actually sleep
                notifier = Notifier("https://discord.com/api/webhooks/test/token")
                job = make_job()
                result = notifier.send_job_alert(job)

        assert result is True
        assert call_count["n"] == 2

    def test_request_exception_returns_false(self):
        import requests as req_lib

        with patch("src.notifier.requests.post", side_effect=req_lib.RequestException("conn failed")):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            job = make_job()
            result = notifier.send_job_alert(job)

        assert result is False


class TestNotifierSendSummary:
    def test_success_returns_true(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True

        with patch("src.notifier.requests.post", return_value=mock_resp):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            result = notifier.send_summary("Test Title", "Test body")

        assert result is True

    def test_embed_has_correct_title_and_description(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True

        captured = {}
        def capture_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("src.notifier.requests.post", side_effect=capture_post):
            notifier = Notifier("https://discord.com/api/webhooks/test/token")
            notifier.send_summary("My Title", "My Description")

        embed = captured["payload"]["embeds"][0]
        assert embed["title"] == "My Title"
        assert embed["description"] == "My Description"


# ---------------------------------------------------------------------------
# Timestamp formatting — 12-hour clock (requested 2026-08-20)
# ---------------------------------------------------------------------------

class TestTwelveHourTimestamps:
    def test_observation_has_twelve_hour_clock(self):
        from src.notifier import build_job_embed
        fields = {f["name"]: f["value"] for f in build_job_embed(make_job())["fields"]}
        assert fields["Observed by Jobbie"] == "2026-05-06 7:00 AM CDT"

    def test_utc_fallback(self):
        from src.notifier import build_job_embed
        with patch.dict("sys.modules", {"zoneinfo": None}):
            fields = {f["name"]: f["value"] for f in build_job_embed(make_job())["fields"]}
        assert fields["Observed by Jobbie"] == "2026-05-06 12:00 PM UTC"


class TestEmbedTitleLength:
    """Discord rejects an embed title over 256 characters with HTTP 400.

    The title appends the full location for preferred-priority jobs, and the
    Microsoft PCSX adapter joins up to 8 sites with "; " — measured max 290
    chars on the live corpus, with 9 of 207 postings producing a title over the
    limit. A 400 means the send fails, mark_alerted never runs, and the job
    re-fires every 15 minutes for the whole 48h freshness window (~192 failed
    sends). Same failure mode the adapter already guards for an empty URL.
    """

    DISCORD_TITLE_MAX = 256

    @staticmethod
    def _title_for(job) -> str:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.ok = True
        captured = {}

        def capture_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("src.notifier.requests.post", side_effect=capture_post):
            Notifier("https://discord.com/api/webhooks/test/token").send_job_alert(job)
        return captured["payload"]["embeds"][0]["title"]

    def test_long_location_does_not_overflow_the_title(self):
        """A real 8-site Microsoft posting shape."""
        location = "; ".join(
            f"United States, {state}, {city}" for state, city in [
                ("Washington", "Redmond"), ("California", "Mountain View"),
                ("New York", "New York City"), ("Georgia", "Atlanta"),
                ("Texas", "Austin"), ("Massachusetts", "Cambridge"),
                ("Illinois", "Chicago"), ("North Carolina", "Charlotte"),
            ]
        )
        assert len(location) > 256, "test fixture must actually be long"
        title = self._title_for(make_job(location=location, priority="preferred"))
        assert len(title) <= self.DISCORD_TITLE_MAX, f"{len(title)} chars: {title!r}"

    def test_truncated_title_still_names_the_company(self):
        """Truncation must not eat the information the reader needs first."""
        location = "; ".join(["United States, Washington, Redmond"] * 12)
        title = self._title_for(
            make_job(company="Microsoft", location=location, priority="preferred")
        )
        assert "Microsoft" in title
        assert len(title) <= self.DISCORD_TITLE_MAX

    def test_long_title_is_visibly_truncated(self):
        title = self._title_for(make_job(title="Engineer " * 80, company="Acme"))
        assert "…" in title
        assert "Acme" in title
        assert len(title) <= self.DISCORD_TITLE_MAX

    def test_location_is_in_description(self):
        from src.notifier import build_job_embed
        embed = build_job_embed(make_job(location="Redmond, WA"))
        assert "Redmond, WA" in embed["description"]

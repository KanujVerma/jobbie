"""Original-source outages must not masquerade as successful empty scans."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import requests

from src.adapters import ADAPTER_REGISTRY
from src.config import load_config
from src.health import update_health
from src.storage import load_state


@pytest.mark.parametrize('name', ['Micron', 'Western Digital', 'SanDisk', 'Oracle', 'Microsoft Research', 'Microsoft', 'Amazon', 'Apple', 'Plaid'])
@pytest.mark.parametrize('status', [403, 404, 429])
def test_original_adapter_exposes_http_outage(name, status):
    company = next(c for c in load_config().companies if c['name'] == name)
    http = MagicMock()
    response = requests.Response()
    response.status_code = status
    error = requests.HTTPError(f'HTTP {status}', response=response)
    http.get.side_effect = error
    http.post.side_effect = error
    adapter = ADAPTER_REGISTRY[company['adapter']](name, company['config'], http)
    try:
        list(adapter.fetch())
    except requests.HTTPError:
        return  # propagated errors are also visible to the orchestrator
    assert adapter.fetch_errors == [f"HTTP {status}"]


def test_dry_read_does_not_persist_v1_migration(tmp_path):
    path = tmp_path / 'state.json'
    path.write_text(json.dumps({'version': 1, 'companies': {'Acme': {'seen_ids': ['a']}}}))
    before = path.read_bytes()
    state = load_state(str(path), raise_on_corrupt=True, persist_migration=False)
    assert state['version'] == 2
    assert state['companies']['Acme']['seen_jobs']['a']['alerted']
    assert path.read_bytes() == before


def test_failed_fetch_does_not_recover_nonempty_partial_scan():
    now = datetime(2026, 11, 11, tzinfo=timezone.utc)
    state = {'health': {'first_tracked_at': now.isoformat(), 'last_nonempty_at': None, 'alerted': True}}
    assert update_health(state, 3, now, 24, fetch_succeeded=False) is None
    assert state['health']['alerted'] is True
    assert state['health']['last_fetch_status'] == 'failed'
    assert state['health']['consecutive_failures'] == 1
    update_health(state, 0, now, 24, fetch_succeeded=True)
    assert state['health']['last_fetch_status'] == 'empty'
    assert state['health']['consecutive_failures'] == 0


@pytest.mark.parametrize('change', [
    {'companies': {'Acme': []}},
    {'companies': {'Acme': {'seen_jobs': []}}},
    {'companies': {'Acme': {'seen_jobs': {'a': {'first_seen': 'bad'}}}}},
    {'companies': {'Acme': {'seen_jobs': {'a': {'first_seen': '2026-11-11'}}}}},
    {'review_queue': []}, {'alerted_urls': []}, {'migrations': []},
    {'heartbeat_history': {}}, {'last_heartbeat': []}, {'version': 99},
])
def test_corrupt_state_schema_fails_closed_without_mutation(tmp_path, change):
    from src.storage import StateCorruptionError
    path = tmp_path / 'state.json'
    path.write_text(json.dumps({'version': 2, 'companies': {}, **change}))
    before = path.read_bytes()
    with pytest.raises(StateCorruptionError):
        load_state(str(path), raise_on_corrupt=True, persist_migration=False)
    assert path.read_bytes() == before


def test_health_snapshot_has_unknowns_and_omits_raw_errors():
    from src.health import health_report, render_health_markdown
    now = datetime(2026, 11, 11, tzinfo=timezone.utc)
    state = {'last_heartbeat': {'finished_at': now.isoformat(), 'per_adapter_breakdown': {
        '<script>|Acme': {'status': 'failed', 'error': 'https://secret.example/token', 'fetched': 0}}}}
    report = health_report(state, now)
    assert report['sources']['<script>|Acme']['has_error'] is True
    assert report['sources']['<script>|Acme']['candidates'] is None
    assert report['snapshot_stale'] is False
    markdown = render_health_markdown(report)
    assert 'secret' not in markdown
    assert '<script>' not in markdown
    assert '&lt;script&gt;&#124;Acme' in markdown
    assert health_report({}, now)['snapshot_stale'] is True


def test_failed_send_logs_neither_secret_url_nor_response_body(caplog):
    from unittest.mock import patch
    from src.notifier import Notifier
    sender = Notifier('https://discord.com/api/webhooks/private/token')
    with patch('src.notifier.requests.post', side_effect=requests.ConnectionError('private/token')):
        assert sender.send_summary('test', 'synthetic') is False
    assert 'private/token' not in caplog.text
    caplog.clear()
    response = MagicMock(ok=False, status_code=403, text='PRIVATE BODY')
    with patch('src.notifier.requests.post', return_value=response):
        assert sender.send_summary('test', 'synthetic') is False
    assert 'PRIVATE BODY' not in caplog.text


def test_partial_scan_keeps_observations_but_is_not_healthy(monkeypatch):
    import main
    from src.config import Config
    from src.storage import _empty_state
    from tests.test_main_exit_code import _make_job, EmptyAdapter
    from types import SimpleNamespace

    class Partial:
        def __init__(self, *args, **kwargs):
            pass
        def fetch(self):
            yield _make_job()
            raise requests.ConnectionError('page 2 failed')

    config = Config(defaults={'request_delay_seconds': [0, 0]}, filters={}, companies=[
        {'name': 'Acme', 'adapter': 'partial', 'config': {}},
        {'name': 'Other', 'adapter': 'empty', 'config': {}},
    ])
    state = _empty_state()
    monkeypatch.setattr(main, 'load_config', lambda _: config)
    monkeypatch.setattr(main, 'load_state', lambda *args, **kwargs: state)
    monkeypatch.setattr(main, 'ADAPTER_REGISTRY', {'partial': Partial, 'empty': EmptyAdapter})
    monkeypatch.setenv('DISCORD_WEBHOOK_URL', '')
    assert main.do_run(SimpleNamespace(config='unused', dry_run=True)) == 0
    row = state['last_heartbeat']['per_adapter_breakdown']['Acme']
    assert row['fetched'] == 1
    assert row['status'] == 'failed'
    assert state['companies']['Acme']['health']['last_fetch_status'] == 'failed'
    assert state['last_heartbeat']['adapters_succeeded'] == 1


def test_all_legacy_query_failures_fail_the_run(monkeypatch):
    import main
    from src.adapters.base import BaseAdapter
    from src.config import Config
    from src.storage import _empty_state
    from types import SimpleNamespace

    class FailedQueries(BaseAdapter):
        def fetch(self):
            self.record_fetch_error('SOURCE_ERROR')
            return iter(())

    config = Config(defaults={'request_delay_seconds': [0, 0]}, filters={}, companies=[
        {'name': 'Acme', 'adapter': 'failed', 'config': {}}])
    state = _empty_state()
    monkeypatch.setattr(main, 'load_config', lambda _: config)
    monkeypatch.setattr(main, 'load_state', lambda *args, **kwargs: state)
    monkeypatch.setattr(main, 'ADAPTER_REGISTRY', {'failed': FailedQueries})
    monkeypatch.setenv('DISCORD_WEBHOOK_URL', '')
    assert main.do_run(SimpleNamespace(config='unused', dry_run=True)) == 1
    assert state['last_heartbeat']['adapters_failed'] == 1
    assert state['first_run_completed_at'] is None

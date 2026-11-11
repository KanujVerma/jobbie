"""State-safe repairs for existing employers, with no roster expansion."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.adapters.amazon_jobs import AmazonJobsAdapter


def test_amazon_gated_mapping_sends_category_text():
    http = MagicMock()
    response = MagicMock()
    response.json.return_value = {'hits': 0, 'jobs': []}
    http.get.return_value = response
    adapter = AmazonJobsAdapter('Amazon', {
        'include_internship_search': False,
        'gated_categories': [{'category': 'Research Science', 'require_early_career': True}],
    }, http)
    assert list(adapter.fetch()) == []
    assert http.get.call_args.kwargs['params']['category[]'] == 'Research Science'


def _job(identifier='a'):
    from src.models import Job
    now = datetime(2026, 11, 11, tzinfo=timezone.utc)
    return Job(id=identifier, company='Plaid', title='Software Engineer I', location='US',
               department='Engineering', category=None,
               url=f'https://jobs.ashbyhq.com/plaid/{identifier}', source_platform='ashby',
               posted_at=now, detected_at=now, raw_text='full time software engineer 0-2 years',
               role_type='entry-level', priority='normal', matched_keywords=())


def _state():
    from src.storage import _empty_state
    return _empty_state()


def test_new_source_baseline_has_no_delivery_ack():
    from src.source_migration import apply_source_baseline
    from src.storage import classify_jobs
    now = _job().detected_at
    state = _state()
    jobs = [_job('a'), _job('b')]
    assert apply_source_baseline(jobs, 'Plaid', {'source_revision': 'ashby-v1'}, state, now,
                                 fetch_succeeded=True) is True
    cs = state['companies']['Plaid']
    assert cs['source_revision'] == 'ashby-v1'
    assert len(cs['seen_jobs']) == 2
    assert all(r['baseline_suppressed'] and r['alerted'] is False for r in cs['seen_jobs'].values())
    assert classify_jobs(jobs, 'Plaid', state, 48, now) == []
    assert state['alerted_urls'] == {}


def test_next_scan_alerts_only_new_provider_ids():
    from src.source_migration import apply_source_baseline
    from src.storage import classify_jobs
    now = _job().detected_at
    state = _state()
    cfg = {'source_revision': 'ashby-v1'}
    apply_source_baseline([_job('a')], 'Plaid', cfg, state, now, fetch_succeeded=True)
    jobs = [_job('a'), _job('new')]
    assert apply_source_baseline(jobs, 'Plaid', cfg, state, now, fetch_succeeded=True) is False
    assert [j.id for j in classify_jobs(jobs, 'Plaid', state, 48, now)] == ['new']


def test_partial_transition_stays_pending_until_complete_scan():
    from src.source_migration import apply_source_baseline
    from src.storage import classify_jobs
    now = _job().detected_at
    state = _state()
    cfg = {'source_revision': 'ashby-v1'}
    assert apply_source_baseline([_job('a')], 'Plaid', cfg, state, now, fetch_succeeded=False)
    assert state['companies']['Plaid'].get('source_revision') is None
    assert classify_jobs([_job('a')], 'Plaid', state, 48, now) == []
    assert apply_source_baseline([_job('a'), _job('b')], 'Plaid', cfg, state, now, fetch_succeeded=True)
    assert state['companies']['Plaid']['source_revision'] == 'ashby-v1'
    assert classify_jobs([_job('a'), _job('b')], 'Plaid', state, 48, now) == []


def test_source_baseline_preserves_historical_ack_and_url_ledger():
    from src.source_migration import apply_source_baseline
    now = _job().detected_at
    state = _state()
    state['companies']['Plaid'] = {'seen_jobs': {'old-lever': {
        'first_seen': now.isoformat(), 'last_seen': now.isoformat(), 'alerted': True}}}
    state['alerted_urls']['https://jobs.lever.co/plaid/old'] = {'company': 'Plaid', 'alerted_at': now.isoformat()}
    import copy
    old = copy.deepcopy(state)
    apply_source_baseline([_job('a')], 'Plaid', {'source_revision': 'ashby-v1'}, state, now, fetch_succeeded=True)
    assert state['companies']['Plaid']['seen_jobs']['old-lever'] == old['companies']['Plaid']['seen_jobs']['old-lever']
    assert state['alerted_urls'] == old['alerted_urls']


def test_source_baseline_cannot_enter_policy_backfill():
    from src.source_migration import apply_source_baseline
    from src.storage import get_backfill_candidates
    now = _job().detected_at
    state = _state()
    apply_source_baseline([_job('a')], 'Plaid', {'source_revision': 'ashby-v1'}, state, now, fetch_succeeded=True)
    assert get_backfill_candidates([_job('a')], state, now) == []


def test_source_without_revision_is_unchanged():
    from src.source_migration import apply_source_baseline
    state = _state()
    assert apply_source_baseline([_job()], 'Plaid', {}, state, _job().detected_at, fetch_succeeded=True) is False
    assert state['companies'] == {}


def _run_source(tmp_path, monkeypatch, jobs, *, revision='ashby-v1', state=None, send_success=True):
    import main
    from src.config import Config
    from src.storage import POLICY_VERSION
    from types import SimpleNamespace
    import json

    class Stub:
        def __init__(self, *args, **kwargs):
            pass
        def fetch(self):
            yield from jobs

    path = tmp_path / 'state.json'
    if state is None:
        state = _state()
        state['first_run_completed_at'] = _job().detected_at.isoformat()
        state['policy_version'] = POLICY_VERSION
        state['migrations'] = {POLICY_VERSION: {'backfill_completed': True}}
    path.write_text(json.dumps(state))
    config = Config(defaults={'state_path': str(path), 'request_delay_seconds': [0, 0]},
                    filters={'freshness_hours': 48}, companies=[{
                        'name': 'Plaid', 'adapter': 'stub', 'config': {}, 'source_revision': revision}])
    sender = MagicMock()
    sender.send_job_alert.return_value = send_success
    factory = MagicMock(return_value=sender)
    monkeypatch.setattr(main, 'load_config', lambda _: config)
    monkeypatch.setattr(main, 'ADAPTER_REGISTRY', {'stub': Stub})
    monkeypatch.setattr(main, 'HTTPClient', MagicMock())
    monkeypatch.setattr(main, 'Notifier', factory)
    monkeypatch.setattr(main, 'apply_filter_pipeline', lambda job, *args: (job, []))
    monkeypatch.setenv('DISCORD_WEBHOOK_URL', 'https://discord.com/api/webhooks/synthetic')
    rc = main.do_run(SimpleNamespace(config='unused', dry_run=False))
    return rc, json.loads(path.read_text()), sender, factory


def test_runtime_baselines_before_candidate_delivery(tmp_path, monkeypatch):
    rc, state, sender, _ = _run_source(tmp_path, monkeypatch, [_job('a'), _job('b')])
    assert rc == 0
    sender.send_job_alert.assert_not_called()
    assert state['companies']['Plaid']['source_revision'] == 'ashby-v1'
    assert state['last_heartbeat']['per_adapter_breakdown']['Plaid']['baseline_suppressed'] == 2
    assert not state['alerted_urls']


def test_runtime_subsequent_new_job_uses_existing_ack_path(tmp_path, monkeypatch):
    rc, state, _, _ = _run_source(tmp_path, monkeypatch, [_job('a')])
    rc, state, sender, _ = _run_source(tmp_path, monkeypatch, [_job('a'), _job('b')], state=state)
    assert rc == 0
    sender.send_job_alert.assert_called_once_with(_job('b'))
    assert state['companies']['Plaid']['seen_jobs']['a']['alerted'] is False
    assert state['companies']['Plaid']['seen_jobs']['b']['alerted'] is True


import pytest


@pytest.mark.parametrize('revision', ['', 'bad revision', False, 9])
def test_invalid_source_revision_rejected_before_sender(tmp_path, monkeypatch, revision):
    rc, _, _, factory = _run_source(tmp_path, monkeypatch, [_job('a')], revision=revision)
    assert rc == 1
    factory.assert_not_called()


@pytest.mark.parametrize('change', [
    {'source_revision': []}, {'source_baselines': []},
    {'source_baselines': {'a': []}},
    {'seen_jobs': {'a': {'baseline_suppressed': 'false'}}},
])
def test_malformed_source_baseline_state_is_rejected(tmp_path, change):
    from src.storage import load_state, StateCorruptionError
    import json
    path = tmp_path / 'state.json'
    state = _state()
    state['companies']['Plaid'] = {'seen_jobs': {}, **change}
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    with pytest.raises(StateCorruptionError):
        load_state(str(path), raise_on_corrupt=True)
    assert path.read_bytes() == before


def test_plaid_repair_preserves_production_roster_and_unconfirmed_referrals():
    from src.config import load_config, validate_config
    from src.adapters import ADAPTER_REGISTRY
    from src.storage import ORIGINAL_NETWORK_COMPANIES
    config = load_config()
    enabled = [c for c in config.companies if c['enabled']]
    assert len(config.companies) == 15
    assert {c['name'] for c in enabled} == ORIGINAL_NETWORK_COMPANIES
    assert len(enabled) == 13
    assert all(c['network_priority'] is True and c['referral_status'] == 'unconfirmed' for c in enabled)
    assert {c['name'] for c in config.companies if not c['enabled']} == {'Snowflake', 'Applied Digital'}
    plaid = next(c for c in enabled if c['name'] == 'Plaid')
    assert plaid['adapter'] == 'ashby'
    assert plaid['source_revision'] == 'plaid-ashby-2026-11-11'
    assert validate_config(config, ADAPTER_REGISTRY, dry_run=True) == []


def test_failed_send_after_baseline_is_not_acknowledged(tmp_path, monkeypatch):
    rc, state, _, _ = _run_source(tmp_path, monkeypatch, [_job('a')])
    rc, state, sender, _ = _run_source(tmp_path, monkeypatch, [_job('a'), _job('b')],
                                      state=state, send_success=False)
    assert rc == 0
    sender.send_job_alert.assert_called_once_with(_job('b'))
    assert state['companies']['Plaid']['seen_jobs']['a']['alerted'] is False
    assert state['companies']['Plaid']['seen_jobs']['b']['alerted'] is False
    assert state['alerted_urls'] == {}
    assert state['last_heartbeat']['alert_failure_count'] == 1
    rc, state, sender, _ = _run_source(tmp_path, monkeypatch, [_job('a'), _job('b')], state=state)
    sender.send_job_alert.assert_called_once_with(_job('b'))
    assert state['companies']['Plaid']['seen_jobs']['b']['alerted'] is True

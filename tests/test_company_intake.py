"""Portable owner requests and OFF proposals; no production writes or sends."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from src.company_intake import normalize_request, parse_issue_request, request_digest, build_proposal

NOW = datetime(2026, 11, 11, 21, tzinfo=timezone.utc)


def request(**changes):
    return normalize_request({'schema_version': 1, 'name': 'Example Labs', 'roles': ['Software Engineer'],
                              'locations': ['San Francisco, CA'], **changes})


def evidence(**changes):
    return {'schema_version': 1, 'company_name': 'Example Labs', 'verified_aliases': [],
            'provider': 'ashby', 'board_id': 'example-labs',
            'board_url': 'https://jobs.ashbyhq.com/example-labs',
            'employer_careers_url': 'https://example.com/careers',
            'ownership': {'status': 'verified', 'url': 'https://example.com/careers',
                          'span': 'Example Labs careers links to the named hosted board.',
                          'board_url': 'https://jobs.ashbyhq.com/example-labs',
                          'retrieved_at': '2026-11-11T20:00:00Z'},
            'permission': {'status': 'permitted', 'basis': 'Synthetic fixture, not live permission.',
                           'url': 'https://example.com/policy', 'checked_at': '2026-11-11T20:00:00Z'},
            **changes}


def job():
    from src.models import Job
    return Job(id='example-1', company='Example Labs', title='Software Engineer',
               location='San Francisco, CA', department=None, category=None,
               url='https://jobs.ashbyhq.com/example-labs/1', source_platform='ashby',
               posted_at=None, detected_at=NOW, raw_text='', role_type='unknown',
               priority='normal', matched_keywords=())


def stub_http(monkeypatch, jobs=None, error=None):
    import src.company_intake as module
    fetch = MagicMock(return_value=iter(jobs if jobs is not None else [job()]), side_effect=error)
    class Stub:
        def __init__(self, *args, **kwargs):
            self.fetch_errors = []
        def fetch(self):
            return fetch()
    monkeypatch.setattr(module, 'SOURCE_ADAPTERS', {'ashby': Stub, 'greenhouse': Stub})
    return fetch


def test_request_defaults_keep_source_and_referral_authority_absent():
    r = request()
    assert r['intent'] == 'monitor' and r['priority'] == 'normal'
    assert r['careers_url'] is None and r['aliases'] == []
    assert 'enabled' not in r and 'referral_status' not in r
    assert normalize_request(json.loads(json.dumps(r))) == r
    assert request_digest(r) == request_digest(normalize_request(r))


@pytest.mark.parametrize('change', [
    {'schema_version': True}, {'schema_version': 2}, {'name': ''}, {'name': 'bad\nname'},
    {'name': 'x'*161}, {'priority': 'network'}, {'intent': 'apply'}, {'aliases': 'not-list'},
    {'roles': [4]}, {'locations': ['x']*21}, {'referral_status': 'referral_confirmed'},
    {'network_priority': True}, {'enabled': True}, {'careers_url': 'http://example.com'},
    {'careers_url': 'https://user:secret@example.com'}, {'careers_url': 'https://127.0.0.1'},
    {'careers_url': 'https://localhost/careers'}, {'careers_url': 'https://example.com?token=secret'},
])
def test_invalid_or_authority_broadening_request_rejected(change):
    with pytest.raises(ValueError):
        request(**change)


def test_issue_form_parses_same_portable_request():
    body = '''### Company name
Example Labs

### Careers URL
_No response_

### Aliases
Example Incorporated

### Roles
Software Engineer

### Locations
San Francisco, CA

### Priority
normal

### Request type
monitor
'''
    assert parse_issue_request(body) == request(aliases=['Example Incorporated'])
    with pytest.raises(ValueError):
        parse_issue_request(body+'\n### Company name\nInjected\n')
    with pytest.raises(ValueError):
        parse_issue_request(body+'\n### Approval\nenabled=true\n')


def test_existing_names_aliases_and_historical_disabled_never_create_new_source():
    existing = [{'name': 'Plaid', 'enabled': True, 'network_priority': True, 'config': {}},
                {'name': 'Snowflake', 'enabled': False, 'config': {}}]
    before = copy.deepcopy(existing)
    for r in [request(name='PLＡID'), request(aliases=['Plaid']), request(name='Snowflake')]:
        out = build_proposal(r, existing, now=NOW)
        assert out['state'] == 'existing_source'
        assert out['config_proposal'] is None
    assert existing == before


def test_research_intent_never_fetches_or_builds_monitor(monkeypatch):
    fetch = stub_http(monkeypatch)
    out = build_proposal(request(intent='startup-research'), [], evidence(), live_check=True, now=NOW)
    assert out['state'] == 'research_request'
    assert out['config_proposal'] is None
    assert out['request']['roles'] == ['Software Engineer']
    fetch.assert_not_called()


def test_no_evidence_or_permission_never_fetches(monkeypatch):
    fetch = stub_http(monkeypatch)
    for packet in [None, evidence(permission={'status': 'unknown'}), evidence(permission={'status': 'prohibited'})]:
        out = build_proposal(request(), [], packet, live_check=True, now=NOW)
        assert out['config_proposal'] is None
    fetch.assert_not_called()


@pytest.mark.parametrize('packet', [
    evidence(board_id='other'), evidence(provider='custom'),
    evidence(company_name='Unrelated Company'),
    evidence(ownership={'status': 'verified', 'url': 'https://evil.example', 'span': 'x',
                        'board_url': 'https://jobs.ashbyhq.com/example-labs',
                        'retrieved_at': '2026-11-11T20:00:00Z'}),
    evidence(board_url='https://jobs.ashbyhq.com/other'),
    evidence(ownership={'status': 'verified', 'url': 'https://example.com/careers', 'span': 'x',
                        'board_url': 'https://jobs.ashbyhq.com/example-labs', 'retrieved_at': 'bad-date'}),
])
def test_inconsistent_or_unsafe_evidence_stays_unverified(monkeypatch, packet):
    fetch = stub_http(monkeypatch)
    out = build_proposal(request(), [], packet, live_check=True, now=NOW)
    assert out['state'] == 'needs_review'
    assert out['config_proposal'] is None
    fetch.assert_not_called()


def test_complete_evidence_still_requires_live_check(monkeypatch):
    fetch = stub_http(monkeypatch)
    out = build_proposal(request(), [], evidence(), now=NOW)
    assert out['state'] == 'needs_live_check'
    assert out['config_proposal'] is None
    fetch.assert_not_called()


def test_live_source_produces_only_disabled_discovered_proposal(monkeypatch):
    fetch = stub_http(monkeypatch)
    r = request(priority='high')
    out = build_proposal(r, [], evidence(), live_check=True, now=NOW)
    assert out['state'] == 'proposal'
    c = out['config_proposal']
    assert c['enabled'] is False and c['network_priority'] is False
    assert c['cohort'] == 'discovered' and c['referral_status'] == 'unavailable'
    assert out['approval_status'] == 'BLOCKED_APPROVAL'
    assert out['ownership_check'] == 'manual_evidence_supplied_requires_review'
    assert out['health']['returned_count'] == 1
    assert out['preference_screen']['literal_match_count'] == 1
    assert out['request'] == r and out['request_digest'] == request_digest(r)
    fetch.assert_called_once()


def test_empty_source_is_not_an_outage_or_hiring_claim(monkeypatch):
    stub_http(monkeypatch, jobs=[])
    out = build_proposal(request(), [], evidence(), live_check=True, now=NOW)
    assert out['state'] == 'proposal'
    assert out['health']['status'] == 'empty'
    assert out['health']['returned_count'] == 0
    assert out['config_proposal']['enabled'] is False


@pytest.mark.parametrize('code', [403, 404, 429])
def test_source_http_error_is_failed_not_empty(monkeypatch, code):
    response = requests.Response(); response.status_code = code
    stub_http(monkeypatch, error=requests.HTTPError('https://secret.example/token', response=response))
    out = build_proposal(request(), [], evidence(), live_check=True, now=NOW)
    assert out['state'] == 'source_failed'
    assert out['health']['status'] == 'failed'
    assert out['config_proposal'] is None
    assert 'secret.example' not in json.dumps(out)


def test_canonical_alias_and_board_collision_preserve_original_roster(monkeypatch):
    fetch = stub_http(monkeypatch)
    original = [{'name': 'Microsoft', 'enabled': True, 'network_priority': True, 'config': {}},
                {'name': 'Other', 'adapter': 'ashby', 'config': {'board_name': 'example-labs'}}]
    out = build_proposal(request(name='MSFT'), original,
                         evidence(company_name='Microsoft', verified_aliases=['MSFT']), live_check=True, now=NOW)
    assert out['state'] == 'existing_source'
    out = build_proposal(request(), original, evidence(), live_check=True, now=NOW)
    assert out['state'] == 'source_collision'
    assert out['config_proposal'] is None
    fetch.assert_not_called()


def test_unknown_nested_evidence_cannot_echo_private_material(monkeypatch):
    fetch = stub_http(monkeypatch)
    packet = evidence()
    packet['ownership']['private_resume'] = 'PRIVATE FIXTURE CONTENT'
    out = build_proposal(request(), [], packet, live_check=True, now=NOW)
    assert out['config_proposal'] is None
    assert 'PRIVATE FIXTURE CONTENT' not in json.dumps(out)
    fetch.assert_not_called()


def test_cli_request_round_trip_and_missing_evidence_do_not_mutate(tmp_path):
    import subprocess, sys, hashlib
    paths = ['companies.yaml', 'state/seen_jobs.json']
    before = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    cmd = [sys.executable, 'main.py', 'company-request', '--name', 'Example Labs',
           '--role', 'Software Engineer', '--location', 'San Francisco, CA', '--priority', 'high']
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    portable = json.loads(result.stdout)
    assert portable == request(priority='high')
    path = tmp_path / 'request.json'; path.write_text(result.stdout)
    result = subprocess.run([sys.executable, 'main.py', 'company-proposal', '--request', str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out['state'] == 'needs_review'
    assert out['config_proposal'] is None
    assert before == {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def test_cli_issue_parser_matches_form(tmp_path):
    import subprocess, sys
    body = '\n\n'.join(f'### {k}\n{v}' for k,v in {
        'Company name': 'Example Labs', 'Careers URL': '_No response_', 'Aliases': '_No response_',
        'Roles': 'Software Engineer', 'Locations': 'San Francisco, CA',
        'Priority': 'normal', 'Request type': 'monitor'}.items())
    path = tmp_path / 'issue.md'; path.write_text(body)
    result = subprocess.run([sys.executable, 'main.py', 'company-request', '--issue-file', str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == request()
    import yaml
    form = yaml.safe_load(Path('.github/ISSUE_TEMPLATE/company-request.yml').read_text())
    headings = {row['attributes']['label'] for row in form['body'] if row['type'] != 'markdown'}
    from src.company_intake import ISSUE_FIELDS
    assert headings == set(ISSUE_FIELDS)


def test_cli_invalid_request_emits_no_source_or_approval(tmp_path):
    import subprocess, sys
    path = tmp_path / 'request.json'
    path.write_text(json.dumps({'schema_version': 1, 'name': 'Example Labs', 'enabled': True}))
    result = subprocess.run([sys.executable, 'main.py', 'company-proposal', '--request', str(path)],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert 'config_proposal' not in result.stdout


def test_intake_commands_do_not_construct_notifier(monkeypatch, capsys):
    import main, sys
    sender = MagicMock()
    monkeypatch.setattr(main, 'Notifier', sender)
    monkeypatch.setattr(sys, 'argv', ['main.py', 'company-request', '--name', 'Example Labs'])
    with pytest.raises(SystemExit) as result:
        main.main()
    assert result.value.code == 0
    sender.assert_not_called()
    assert json.loads(capsys.readouterr().out)['name'] == 'Example Labs'


def test_issue_form_uses_supported_top_level_schema():
    import yaml
    form = yaml.safe_load(Path('.github/ISSUE_TEMPLATE/company-request.yml').read_text())
    assert set(form) <= {'name', 'description', 'title', 'labels', 'assignees', 'type', 'projects', 'body'}
    assert {'name', 'description', 'body'} <= set(form)


@pytest.mark.parametrize('code', [403, 404, 429])
def test_public_adapter_wrapped_http_status_remains_actionable(monkeypatch, code):
    from src.adapters.public_board import PublicBoardError
    stub_http(monkeypatch, error=PublicBoardError(f'public board HTTP {code}'))
    out = build_proposal(request(), [], evidence(), live_check=True, now=NOW)
    assert out['health']['http_status'] == code


def test_real_public_adapter_normalizes_fixture_via_fixed_endpoint():
    payload = json.loads(Path('tests/fixtures/ashby_public_synthetic.json').read_text())
    from urllib.parse import urlsplit
    board = urlsplit(payload['jobs'][0]['jobUrl']).path.strip('/').split('/')[0]
    packet = evidence(board_id=board, board_url=f'https://jobs.ashbyhq.com/{board}')
    packet['ownership']['board_url'] = packet['board_url']
    http = MagicMock()
    http.get.return_value = MagicMock(status_code=200, headers={},
        iter_content=MagicMock(return_value=[json.dumps(payload).encode()]))
    out = build_proposal(request(), [], packet, live_check=True, http=http, now=NOW)
    assert out['state'] == 'proposal'
    assert out['health']['returned_count'] > 0
    assert out['config_proposal']['enabled'] is False
    assert http.get.call_args.args[0] == f'https://api.ashbyhq.com/posting-api/job-board/{board}'
    assert http.get.call_args.kwargs['allow_redirects'] is False
    assert http.get.call_args.kwargs['stream'] is True


def test_real_greenhouse_adapter_uses_token_and_preserves_disabled_output():
    payload = json.loads(Path('tests/fixtures/greenhouse_public_synthetic.json').read_text())
    packet = evidence(provider='greenhouse', board_id='example',
                      board_url='https://boards.greenhouse.io/example')
    packet['ownership']['board_url'] = packet['board_url']
    http = MagicMock()
    http.get.return_value = MagicMock(status_code=200, headers={},
        iter_content=MagicMock(return_value=[json.dumps(payload).encode()]))
    out = build_proposal(request(), [], packet, live_check=True, http=http, now=NOW)
    assert out['state'] == 'proposal'
    assert out['config_proposal']['config']['board_token'] == 'example'
    assert out['config_proposal']['enabled'] is False
    assert http.get.call_args.args[0] == 'https://boards-api.greenhouse.io/v1/boards/example/jobs'


def test_synthetic_examples_cannot_authorize_source_fetch(monkeypatch):
    fetch = stub_http(monkeypatch)
    r = json.loads(Path('examples/company-intake/request.synthetic.json').read_text())
    e = json.loads(Path('examples/company-intake/evidence.synthetic.json').read_text())
    out = build_proposal(r, [], e, live_check=True, now=NOW)
    assert 'BLOCKED_SOURCE_RIGHTS' in out['gates']
    assert out['config_proposal'] is None
    fetch.assert_not_called()


def test_verified_aliases_survive_proposal_and_prevent_future_duplicate(monkeypatch):
    fetch = stub_http(monkeypatch)
    r = request(aliases=['Example Incorporated'])
    out = build_proposal(r, [], evidence(verified_aliases=['Example Incorporated']), live_check=True, now=NOW)
    config = out['config_proposal']
    assert config['aliases'] == ['Example Incorporated']
    again = build_proposal(request(name='Example Incorporated'), [config], now=NOW)
    assert again['state'] == 'existing_source'
    fetch.assert_called_once()


def test_full_cli_proposal_keeps_scope_off_and_no_sender(tmp_path, monkeypatch, capsys):
    import main, sys, hashlib
    stub_http(monkeypatch)
    sender = MagicMock()
    monkeypatch.setattr(main, 'Notifier', sender)
    request_path = tmp_path / 'request.json'; request_path.write_text(json.dumps(request(priority='high')))
    evidence_path = tmp_path / 'evidence.json'; evidence_path.write_text(json.dumps(evidence()))
    before = {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['companies.yaml','state/seen_jobs.json']}
    monkeypatch.setattr(sys, 'argv', ['main.py', 'company-proposal', '--request', str(request_path),
                                    '--evidence', str(evidence_path), '--live-check'])
    with pytest.raises(SystemExit) as result:
        main.main()
    assert result.value.code == 0
    out = json.loads(capsys.readouterr().out)
    assert out['state'] == 'proposal' and out['config_proposal']['enabled'] is False
    assert out['request']['priority'] == 'high'
    assert out['request']['locations'] == ['San Francisco, CA']
    assert before == {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
    sender.assert_not_called()


def test_oversized_local_document_rejected_before_processing(tmp_path):
    import main
    path = tmp_path / 'large.json'; path.write_bytes(b'x'*(1024*1024+1))
    with pytest.raises(ValueError, match='1 MiB'):
        main._intake_file(str(path))


def test_unknown_ownership_never_queries_even_with_permission(monkeypatch):
    fetch = stub_http(monkeypatch)
    packet = evidence()
    packet['ownership']['status'] = 'unknown'
    out = build_proposal(request(), [], packet, live_check=True, now=NOW)
    assert out['config_proposal'] is None
    assert 'MISSING_OWNERSHIP_VERIFICATION' in out['gates']
    fetch.assert_not_called()

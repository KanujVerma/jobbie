"""Portable company requests and disabled proposals. No activation or sends.

Ownership/permission are supplied manual source evidence, never inferred from
an issue or proved by a board responding. Network reads use fixed ATS adapters.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from src.adapters.ashby import AshbyAdapter
from src.adapters.greenhouse import GreenhouseAdapter
from src.adapters.public_board import PublicBoardError, public_https_url, validate_public_board_config
from src.http import HTTPClient

SOURCE_ADAPTERS = {'ashby': AshbyAdapter, 'greenhouse': GreenhouseAdapter}
REQUEST_FIELDS = {'schema_version', 'name', 'careers_url', 'aliases', 'roles', 'locations', 'priority', 'intent'}
ISSUE_FIELDS = {'Company name': 'name', 'Careers URL': 'careers_url', 'Aliases': 'aliases',
                'Roles': 'roles', 'Locations': 'locations', 'Priority': 'priority', 'Request type': 'intent'}


def _text(value, field, limit=200):
    if not isinstance(value, str):
        raise ValueError(f'{field} must be text')
    value = unicodedata.normalize('NFKC', value).strip()
    if not value or len(value) > limit or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise ValueError(f'{field} is empty, too long, or contains control characters')
    return value


def _names(value, field):
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError(f'{field} must be a list of at most 20 entries')
    result = []
    keys = set()
    for item in value:
        item = _text(item, field, 160 if field == 'aliases' else 200)
        if item.casefold() not in keys:
            result.append(item)
            keys.add(item.casefold())
    return result


def _url(value, field):
    result = public_https_url(value)
    if not result:
        raise ValueError(f'{field} must be a public HTTPS URL without credentials')
    return result


def _name_key(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())


def normalize_request(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) - REQUEST_FIELDS:
        raise ValueError('unsupported company request fields')
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('company request schema_version must be 1')
    priority, intent = data.get('priority', 'normal'), data.get('intent', 'monitor')
    if priority not in ('normal', 'high', 'low') or intent not in ('monitor', 'startup-research'):
        raise ValueError('unsupported request priority or intent')
    return {'schema_version': 1, 'name': _text(data.get('name'), 'name', 160),
            'careers_url': _url(data['careers_url'], 'careers_url') if data.get('careers_url') is not None else None,
            'aliases': _names(data.get('aliases', []), 'aliases'),
            'roles': _names(data.get('roles', []), 'roles'),
            'locations': _names(data.get('locations', []), 'locations'),
            'priority': priority, 'intent': intent}


def request_digest(request: dict) -> str:
    wire = json.dumps(normalize_request(request), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(wire.encode()).hexdigest()


def parse_issue_request(body: str) -> dict:
    if not isinstance(body, str) or len(body) > 32768:
        raise ValueError('issue body must be bounded text')
    headings = list(re.finditer(r'^### (.+)\s*$', body, re.MULTILINE))
    if not headings:
        raise ValueError('company issue form headings are missing')
    data = {'schema_version': 1}
    for i, heading in enumerate(headings):
        label = heading.group(1).strip()
        if label not in ISSUE_FIELDS or ISSUE_FIELDS[label] in data:
            raise ValueError('unknown or duplicate company issue form heading')
        key = ISSUE_FIELDS[label]
        value = body[heading.end():headings[i+1].start() if i+1 < len(headings) else len(body)].strip()
        if value == '_No response_':
            value = ''
        if key in ('aliases', 'roles', 'locations'):
            data[key] = [line.strip().removeprefix('- ').strip() for line in value.splitlines() if line.strip()]
        elif key == 'careers_url':
            data[key] = value or None
        elif value:
            data[key] = value
    return normalize_request(data)


def _collision(names, companies):
    requested = {_name_key(n) for n in names}
    return [c['name'] for c in companies if requested & {
        _name_key(n) for n in [c['name'], *c.get('aliases', [])]}]


def _checked_time(value, field, now):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f'{field} requires an ISO timestamp with timezone') from None
    if parsed.tzinfo is None or parsed > now + timedelta(minutes=5):
        raise ValueError(f'{field} requires a past timezone-aware timestamp')
    return parsed.isoformat()


def _source_evidence(request, evidence, now):
    fields = {'schema_version', 'company_name', 'verified_aliases', 'provider', 'board_id',
              'board_url', 'employer_careers_url', 'ownership', 'permission'}
    if not isinstance(evidence, dict) or set(evidence) - fields or type(evidence.get('schema_version')) is not int or evidence['schema_version'] != 1:
        raise ValueError('unsupported source evidence schema')
    company = _text(evidence.get('company_name'), 'company_name', 160)
    aliases = _names(evidence.get('verified_aliases', []), 'aliases')
    verified = {_name_key(n) for n in [company, *aliases]}
    if any(_name_key(n) not in verified for n in [request['name'], *request['aliases']]):
        raise ValueError('request name or aliases lack matching supplied source evidence')
    provider = evidence.get('provider')
    if provider not in SOURCE_ADAPTERS:
        raise ValueError('source provider requires a separate supported-adapter review')
    key = 'board_name' if provider == 'ashby' else 'board_token'
    config = {key: evidence.get('board_id'), 'board_url': evidence.get('board_url'),
              'employer_careers_url': evidence.get('employer_careers_url')}
    board = validate_public_board_config(provider, config)
    ownership, permission = evidence.get('ownership'), evidence.get('permission')
    if not isinstance(ownership, dict) or not isinstance(permission, dict):
        raise ValueError('ownership and permission evidence are required')
    if set(ownership) - {'status', 'url', 'span', 'board_url', 'retrieved_at'} or set(permission) - {'status', 'basis', 'url', 'checked_at'}:
        raise ValueError('unsupported ownership or permission evidence fields')
    ownership_url = _url(ownership.get('url'), 'ownership.url')
    if urlsplit(ownership_url).hostname != urlsplit(board.employer_careers_url).hostname:
        raise ValueError('ownership evidence must be on the supplied official employer host')
    if _url(ownership.get('board_url'), 'ownership.board_url') != board.board_url:
        raise ValueError('ownership evidence must identify the exact hosted board')
    if request['careers_url'] and urlsplit(request['careers_url']).hostname != urlsplit(board.employer_careers_url).hostname and request['careers_url'] != board.board_url:
        raise ValueError('requested careers URL contradicts supplied employer/board evidence')
    _text(ownership.get('span'), 'ownership.span', 600)
    _checked_time(ownership.get('retrieved_at'), 'ownership.retrieved_at', now)
    _text(permission.get('basis'), 'permission.basis', 600)
    _url(permission.get('url'), 'permission.url')
    _checked_time(permission.get('checked_at'), 'permission.checked_at', now)
    return company, aliases, provider, config


def build_proposal(request: dict, companies: list[dict], evidence: dict | None = None, *,
                   live_check=False, http=None, now=None) -> dict:
    request = normalize_request(request)
    now = now or datetime.now(timezone.utc)
    result = {'schema_version': 1, 'request': request, 'request_digest': request_digest(request),
              'state': 'needs_review', 'approval_status': 'BLOCKED_APPROVAL',
              'config_proposal': None, 'ownership_check': 'not_checked',
              'health': {'status': 'not_checked', 'returned_count': None}, 'gates': []}
    matches = _collision([request['name'], *request['aliases']], companies)
    if matches:
        result.update(state='existing_source', existing_sources=matches)
        return result
    if request['intent'] == 'startup-research':
        result.update(state='research_request', opening_status='unknown',
                      research_scope={'roles': request['roles'], 'locations': request['locations'],
                                      'priority': request['priority']})
        return result
    if evidence is None:
        result['gates'] = ['MISSING_SOURCE_EVIDENCE', 'BLOCKED_APPROVAL']
        return result
    permission = evidence.get('permission', {}) if isinstance(evidence, dict) else {}
    if not isinstance(permission, dict) or permission.get('status') != 'permitted':
        result['gates'] = ['BLOCKED_SOURCE_RIGHTS', 'BLOCKED_APPROVAL']
        return result
    ownership = evidence.get('ownership', {}) if isinstance(evidence, dict) else {}
    if not isinstance(ownership, dict) or ownership.get('status') != 'verified':
        result['gates'] = ['MISSING_OWNERSHIP_VERIFICATION', 'BLOCKED_APPROVAL']
        return result
    try:
        company, aliases, provider, config = _source_evidence(request, evidence, now)
    except (TypeError, ValueError) as error:
        result['verification_errors'] = [str(error)]
        return result
    matches = _collision([company, *aliases], companies)
    if matches:
        result.update(state='existing_source', existing_sources=matches)
        return result
    key = 'board_name' if provider == 'ashby' else 'board_token'
    collisions = [c['name'] for c in companies if c.get('adapter') == provider and
                  str(c.get('config', {}).get(key, '')).casefold() == str(config[key]).casefold()]
    if collisions:
        result.update(state='source_collision', existing_sources=collisions)
        return result
    result['ownership_check'] = 'manual_evidence_supplied_requires_review'
    result['source_evidence'] = evidence
    if not live_check:
        result['state'] = 'needs_live_check'
        return result
    own_http = http is None
    client = http if http is not None else HTTPClient('jobbie-company-intake/1.0', timeout=15, max_retries=1)
    try:
        adapter = SOURCE_ADAPTERS[provider](company, config, client)
        jobs = list(adapter.fetch())
        if getattr(adapter, 'fetch_errors', []) or len({j.id for j in jobs}) != len(jobs):
            raise ValueError('source scan incomplete or contains duplicate IDs')
    except Exception as error:
        response = getattr(error, 'response', None)
        status = getattr(response, 'status_code', None)
        if status is None and isinstance(error, PublicBoardError):
            match = re.search(r'\bHTTP (\d{3})\b', str(error))
            status = int(match.group(1)) if match else None
        result.update(state='source_failed', health={'status': 'failed', 'returned_count': None,
                      'error_type': type(error).__name__, 'http_status': status if isinstance(status, int) else None})
        return result
    finally:
        if own_http:
            client.session.close()
    result['health'] = {'status': 'nonempty' if jobs else 'empty', 'returned_count': len(jobs),
                        'checked_at': now.isoformat(), 'scope': 'configured public board only'}
    result['preference_screen'] = {
        'method': 'literal title/location preference check, not eligibility or candidate fit',
        'literal_match_count': sum((not request['roles'] or any(r.casefold() in j.title.casefold() for r in request['roles'])) and
                                   (not request['locations'] or any(loc.casefold() in j.location.casefold() for loc in request['locations'])) for j in jobs),
        'unknown_location_count': sum(not bool(j.location) for j in jobs),
        'samples': [{'source_job_id': j.source_job_id, 'title': j.title, 'location': j.location, 'url': j.url} for j in jobs[:3]],
    }
    result.update(state='proposal', config_proposal={
        'name': company, 'aliases': aliases, 'adapter': provider, 'enabled': False, 'network_priority': False,
        'cohort': 'discovered', 'referral_status': 'unavailable', 'config': config,
    })
    result['gates'] = ['BLOCKED_APPROVAL', 'ACTIVATION_REQUIRES_REVIEWED_SCOPE_BASELINE_AND_ROLLBACK']
    return result

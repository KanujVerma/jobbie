"""Synthetic Oracle CE finder contracts based on the documented public response."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
import requests
import json

from src.adapters.oracle_careers import OracleAdapter

CFG = {
    'base_url': 'https://eeho.fa.us2.oraclecloud.com',
    'api_path': '/hcmRestApi/resources/latest/recruitingCEJobRequisitions',
    'site_number': 'CX_45001', 'location_id': '300000000149325',
    'careers_url': 'https://careers.oracle.com/en/sites/jobsearch', 'limit': 2,
}


def row(identifier='1', **changes):
    return {'Id': identifier, 'Title': 'Software Engineer I', 'PrimaryLocation': 'United States',
            'PostedDate': '2026-11-11', 'JobFunction': 'Engineering', 'JobSchedule': 'Full time',
            'ShortDescriptionStr': '<p>Build software.</p>',
            'ExternalQualificationsStr': '<p>Required qualifications: BS in CS and 0-2 years of experience.</p>',
            'ExternalResponsibilitiesStr': '<p>Develop and test full-time systems software.</p>', **changes}


def payload(rows, total):
    return {'count': 1, 'hasMore': False, 'items': [{'TotalJobsCount': total, 'requisitionList': rows}]}


def adapter(*pages, config=None):
    http = MagicMock()
    http.get.side_effect = [MagicMock(status_code=200, headers={}, iter_content=MagicMock(return_value=[json.dumps(p).encode()])) for p in pages]
    return OracleAdapter('Oracle', config or CFG, http)


def test_finder_uses_verified_site_and_pages_inner_job_rows():
    a = adapter(payload([row('1'), row('2')], 3), payload([row('3')], 3))
    jobs = list(a.fetch())
    assert len(jobs) == 3
    first = a.http.get.call_args_list[0].kwargs['params']['finder']
    second = a.http.get.call_args_list[1].kwargs['params']['finder']
    assert 'siteNumber=CX_45001' in first and 'locationId=300000000149325' in first
    assert 'offset=0' in first and 'offset=2' in second
    assert not a.fetch_errors


def test_date_only_preserves_calendar_value_without_fake_time():
    j = next(adapter(payload([row()], 1)).fetch())
    assert j.posted_at is None
    assert j.source_posted_date == '2026-11-11'
    assert j.url == 'https://careers.oracle.com/en/sites/jobsearch/job/1'
    assert j.source_job_id == '1'


def test_real_qualification_fields_reach_eligibility():
    from src.eligibility import classify_eligibility
    j = next(adapter(payload([row(ExternalQualificationsStr='<p>Required: 5 years of professional software engineering experience.</p>')], 1)).fetch())
    assert '5 years' in j.raw_text
    assert classify_eligibility(j).status == 'excluded'


def test_missing_qualifications_remains_review_not_eligible():
    from src.eligibility import classify_eligibility
    j = next(adapter(payload([row(ExternalQualificationsStr=None)], 1)).fetch())
    assert j.description_complete is False
    assert classify_eligibility(j).status == 'needs_review'


def test_aware_source_timestamp_is_retained_and_naive_time_is_unknown():
    a = adapter(payload([row('1', PostedDate='2026-11-11T12:00:00Z'),
                         row('2', PostedDate='2026-11-11T12:00:00')], 2))
    jobs = list(a.fetch())
    assert jobs[0].posted_at == datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    assert jobs[1].posted_at is None


def test_untrusted_external_url_cannot_replace_fixed_official_req_link():
    j = next(adapter(payload([row(ExternalURL='https://evil.example/steal')], 1)).fetch())
    assert j.url == 'https://careers.oracle.com/en/sites/jobsearch/job/1'


@pytest.mark.parametrize('change', [
    {'site_number': 'CX_1,offset=999'}, {'location_id': '1,limit=999'},
    {'base_url': 'http://localhost'}, {'base_url': 'https://evil.example'},
    {'base_url': 'https://eeho.fa.us2.oraclecloud.com/private'},
    {'careers_url': 'https://evil.example/en/sites/jobsearch'},
    {'careers_url': 'https://user:secret@careers.oracle.com/en/sites/jobsearch'},
    {'api_path': '/arbitrary'}, {'limit': 0}, {'limit': True}, {'max_pages': 0},
])
def test_finder_rejects_unsafe_or_unbounded_config_before_request(change):
    a = adapter(config={**CFG, **change})
    with pytest.raises(ValueError):
        list(a.fetch())
    a.http.get.assert_not_called()


@pytest.mark.parametrize('code', [403, 404, 429])
def test_finder_http_failure_is_not_empty_success(code):
    from src.adapters.public_board import PublicBoardError
    a = adapter()
    response = requests.Response()
    response.status_code = code
    response.raw = MagicMock()
    a.http.get.side_effect = requests.HTTPError('source error', response=response)
    with pytest.raises(PublicBoardError, match=str(code)):
        list(a.fetch())


def test_repeated_page_fails_without_duplicate_rows():
    from src.adapters.public_board import PublicBoardError
    a = adapter(payload([row('1'), row('2')], 4), payload([row('1'), row('2')], 4))
    it = a.fetch()
    assert [next(it).source_job_id, next(it).source_job_id] == ['1', '2']
    with pytest.raises(PublicBoardError, match='repeated'):
        list(it)


def test_incomplete_empty_page_is_an_error():
    from src.adapters.public_board import PublicBoardError
    a = adapter(payload([row('1'), row('2')], 3), payload([], 3))
    it = a.fetch()
    assert next(it).source_job_id == '1'
    assert next(it).source_job_id == '2'
    with pytest.raises(PublicBoardError, match='incomplete'):
        list(it)


def test_explicit_zero_job_envelope_is_successful_empty():
    a = adapter(payload([], 0))
    assert list(a.fetch()) == []
    assert not a.fetch_errors


def test_page_cap_is_partial_failure():
    from src.adapters.public_board import PublicBoardError
    a = adapter(payload([row('1'), row('2')], 3), config={**CFG, 'max_pages': 1})
    it = a.fetch()
    assert next(it).source_job_id == '1'
    assert next(it).source_job_id == '2'
    with pytest.raises(PublicBoardError, match='cap'):
        list(it)


def test_changed_search_total_is_not_complete_health():
    a = adapter(payload([row('1'), row('2')], 3), payload([row('3')], 4), payload([row('4')], 4))
    assert len(list(a.fetch())) == 4
    assert 'SEARCH_TOTAL_CHANGED' in a.fetch_errors


@pytest.mark.parametrize('data', [{}, {'items': []}, {'items': [{}]},
                                  {'items': [{'TotalJobsCount': -1, 'requisitionList': []}]}])
def test_invalid_search_envelope_is_an_error(data):
    from src.adapters.public_board import PublicBoardError
    with pytest.raises(PublicBoardError):
        list(adapter(data).fetch())


def test_date_only_card_does_not_invent_midnight_or_timezone():
    from src.notifier import build_job_embed
    j = next(adapter(payload([row()], 1)).fetch())
    fields = build_job_embed(j)['fields']
    field = next(f for f in fields if f['name'] == 'Source date (time unknown)')
    assert field['value'] == '2026-11-11'


def test_incomplete_and_non_full_time_metadata_stay_truthful():
    from src.eligibility import classify_eligibility
    for schedule in ['Part time', 'Internship', 'Contract']:
        j = next(adapter(payload([row(JobSchedule=schedule)], 1)).fetch())
        assert classify_eligibility(j).status == 'excluded'
    j = next(adapter(payload([row(JobSchedule=None)], 1)).fetch())
    assert j.employment_type == 'unknown'


def test_full_qualification_citizenship_requirement_is_not_lost():
    from src.eligibility import classify_eligibility
    j = next(adapter(payload([row(ExternalQualificationsStr='<p>Required: United States citizenship.</p>')], 1)).fetch())
    assert classify_eligibility(j).status == 'excluded'


@pytest.mark.parametrize('qualification', [
    'Not required: United States citizenship.',
    'Preferred: United States citizenship.',
    'United States citizenship is not required.',
])
def test_optional_citizenship_does_not_become_required(qualification):
    from src.eligibility import classify_eligibility
    j = next(adapter(payload([row(ExternalQualificationsStr='<p>'+qualification+'</p>')], 1)).fetch())
    assert 'US_CITIZEN_REQUIRED' not in classify_eligibility(j).reasons


def test_malformed_requisition_does_not_hide_other_rows_or_complete_health():
    a = adapter(payload([row('1'), row('2', Title={'unexpected': 'shape'}), row('3')], 3))
    jobs = list(a.fetch())
    assert [j.source_job_id for j in jobs] == ['1', '3']
    assert 'INVALID_REQUISITION' in a.fetch_errors


def test_review_state_preserves_source_calendar_date():
    from src.storage import _empty_state, record_review_job
    j = next(adapter(payload([row()], 1)).fetch())
    state = _empty_state()
    record_review_job(state, j, ['needs_review'], j.detected_at)
    assert state['review_queue'][j.id]['source_posted_date'] == '2026-11-11'


def test_overlapping_pages_cannot_complete_source_baseline():
    from src.source_migration import apply_source_baseline
    from src.storage import _empty_state
    a = adapter(payload([row('1'), row('2')], 4), payload([row('2'), row('3')], 4))
    jobs = list(a.fetch())
    assert [j.source_job_id for j in jobs] == ['1', '2', '3']
    assert 'DUPLICATE_REQUISITION' in a.fetch_errors
    state = _empty_state()
    pending = apply_source_baseline(jobs, 'Oracle', {'source_revision': 'finder-v1'}, state,
                                    datetime.now(timezone.utc), fetch_succeeded=not a.fetch_errors)
    assert pending is True
    assert state['companies']['Oracle'].get('source_revision') is None
    assert all(entry['alerted'] is False for entry in state['companies']['Oracle']['seen_jobs'].values())
    complete = adapter(payload([row('1'), row('2')], 4), payload([row('3'), row('4')], 4))
    current = list(complete.fetch())
    apply_source_baseline(current, 'Oracle', {'source_revision': 'finder-v1'}, state,
                          datetime.now(timezone.utc), fetch_succeeded=not complete.fetch_errors)
    from src.storage import classify_jobs
    assert classify_jobs(current, 'Oracle', state, 48, datetime.now(timezone.utc)) == []
    assert state['companies']['Oracle']['source_baselines']['finder-v1']['observed_count'] == 4


@pytest.mark.parametrize('clause',[
    'Required: United States citizenship or permanent residency.',
    'Required: US citizenship or lawful permanent residency.',
    'Must be a US citizen or a permanent resident.',
    'US citizenship required, or green card holder accepted.',
])
def test_acceptable_residency_alternatives_do_not_require_citizenship(clause):
    from src.eligibility import classify_eligibility
    j=next(adapter(payload([row(ExternalQualificationsStr='<p>'+clause+'</p>')],1)).fetch())
    verdict=classify_eligibility(j)
    assert 'US_CITIZEN_REQUIRED' not in verdict.reasons
    assert verdict.status=='eligible'


def test_separate_mandatory_citizenship_clause_is_not_overridden_by_alternative():
    from src.eligibility import classify_eligibility
    j=next(adapter(payload([row(ExternalQualificationsStr='<p>Required: US citizenship or permanent residency.</p><p>US citizenship required for this contract.</p>')],1)).fetch())
    verdict=classify_eligibility(j)
    assert verdict.status=='excluded' and 'US_CITIZEN_REQUIRED' in verdict.reasons

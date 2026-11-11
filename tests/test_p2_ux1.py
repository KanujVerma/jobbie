from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from src.eligibility import EligibilityVerdict
from src.models import CompensationRange
from src.notifier import build_job_embed
from tests.test_network import _make_sample_job


def verdict(status='eligible', **kwargs):
    values = dict(job_id='sample-job-1', policy_version='test', status=status,
                  employment_type='unknown', career_level='new_grad',
                  reasons=('CONFIRMED_NEW_GRAD',), evidence_spans=(), unknowns=('employment_type',))
    values.update(kwargs)
    return EligibilityVerdict(**values)


def fields(embed):
    return {field['name']: field['value'] for field in embed['fields']}


def test_title_first_and_unknowns_are_honest():
    embed = build_job_embed(_make_sample_job(verdict=verdict(), employment_type='unknown', description_complete=False))
    assert embed['title'].startswith('Software Engineer, New Grad')
    assert 'NETWORK PRIORITY' in embed['description']
    assert 'Unconfirmed' in embed['description']
    assert 'Full-time: Unknown' in embed['description']
    assert '(verified)' not in str(embed).lower()
    assert fields(embed)['Base compensation'] == 'Not disclosed'
    assert 'employment type' in fields(embed)['Eligibility screen'].lower()
    assert 'description' in fields(embed)['Eligibility screen'].lower()


def test_source_salary_and_hourly_unit():
    pay = CompensationRange(Decimal('25'), Decimal('35'), 'USD', '1 HOUR', 'compensation.summaryComponents[0]')
    embed = build_job_embed(_make_sample_job(source_platform='ashby', compensation=(pay,), salary='contradictory'))
    assert fields(embed)['Base compensation'] == 'USD 25-35 / hour'


def test_unknown_date_and_unsafe_link():
    embed = build_job_embed(_make_sample_job(posted_at=None, url='javascript:alert(1)'))
    assert 'Observed by Jobbie' in fields(embed)
    assert 'unavailable' in fields(embed)['Employer posting'].lower()
    assert 'javascript:' not in str(embed)


def test_dst_and_source_publication():
    job = _make_sample_job(source_platform='ashby', posted_at_kind='last_published',
                           posted_at=datetime(2026, 11, 1, 7, 30, tzinfo=timezone.utc))
    assert '1:30 AM CST' in fields(build_job_embed(job))['Last published']


def test_hostile_values_and_discord_limits():
    job = _make_sample_job(title='😀@everyone *' * 4000, company='<@123>' * 500,
                           location='@here ' * 1000, source_job_id='x' * 10000,
                           url='https://example.com/' + 'a' * 2100)
    embed = build_job_embed(job)
    text = str(embed)
    assert '@everyone' not in text and '@here' not in text and '<@123>' not in text
    assert len(embed['title'].encode('utf-16-le')) // 2 <= 256
    assert len(embed['description'].encode('utf-16-le')) // 2 <= 4096
    assert len(embed['fields']) <= 25
    for field in embed['fields']:
        assert len(field['name'].encode('utf-16-le')) // 2 <= 256
        assert len(field['value'].encode('utf-16-le')) // 2 <= 1024
    assert sum(len(x.encode('utf-16-le')) // 2 for x in [embed['title'], embed['description'], embed['footer']['text']] + [s for f in embed['fields'] for s in (f['name'], f['value'])]) <= 6000
    assert 'Unavailable' in fields(embed)['Employer posting']


def test_review_and_untrusted_compensation():
    bonus = CompensationRange(Decimal('1'), Decimal('100'), 'USD', '1 YEAR', 'bonus', 'Bonus')
    job = _make_sample_job(source_platform='ashby', compensation=(bonus,), verdict=verdict('needs_review'))
    result = fields(build_job_embed(job))
    assert result['Eligibility screen'].startswith('Needs review')
    assert result['Base compensation'] == 'Not disclosed'


def test_greenhouse_and_legacy_dates_never_claim_exact_time():
    job = _make_sample_job(source_platform='apple', posted_at=datetime(2026, 11, 2, tzinfo=timezone.utc))
    assert fields(build_job_embed(job))['Source date'] == '2026-11-02'
    job = replace(job, source_platform='greenhouse', posted_at_kind='first_published')
    assert 'CST' in fields(build_job_embed(job))['First published']


def test_synthetic_review_digest_is_bounded_and_safe():
    from src.notifier import build_review_digest
    items = [{'company': '@everyone' * 100, 'title': '<@123>' * 100,
              'url': 'javascript:alert(1)', 'reasons': ['@here' * 500]}] * 10
    description = build_review_digest(items, 10)
    assert 'Needs review' in description
    assert '@everyone' not in description and '@here' not in description and '<@123>' not in description
    assert 'javascript:' not in description
    assert len(description.encode('utf-16-le')) // 2 <= 4096


def test_original_cohort_and_disabled_render():
    from src.config import load_config
    config = load_config('companies.yaml')
    starred = []
    for source in config.companies:
        embed = build_job_embed(_make_sample_job(company=source['name'], network_priority=source.get('network_priority', False)))
        if 'NETWORK PRIORITY' in embed['description']:
            starred.append(source['name'])
        if not source.get('enabled', True):
            assert embed['description'].startswith('DISCOVERED')
    assert len(starred) == 13


def test_untrusted_employment_type_does_not_inject_mentions():
    embed = build_job_embed(_make_sample_job(employment_type='@everyone'))
    assert '@everyone' not in str(embed)
    assert 'Full-time: Unknown' in embed['description']


def test_original_card_snapshot():
    embed = build_job_embed(_make_sample_job(title='Software Engineer I', company='Example', location='Chicago, IL',
                                             posted_at=None, employment_type='full_time', description_complete=True, verdict=verdict('eligible', employment_type='full_time', career_level='entry_level', reasons=('ENTRY_LEVEL_TITLE',), unknowns=())))
    assert embed == {
        'title': 'Software Engineer I | Example',
        'description': '⭐ NETWORK PRIORITY | Referral: Unconfirmed\nChicago, IL\nFull-time | Entry-level',
        'fields': [
            {'name': 'Base compensation', 'value': 'Not disclosed', 'inline': False},
            {'name': 'Eligibility screen', 'value': 'Pass \\| Reasons: entry level title \\| Deterministic screen, not hiring confirmation', 'inline': False},
            {'name': 'Observed by Jobbie', 'value': '2026-11-04 6:00 AM CST', 'inline': True},
            {'name': 'Employer posting', 'value': 'Employer link unverified: https://example.com/job/1', 'inline': False},
        ], 'footer': {'text': 'workday'}, 'color': 0xFEE75C,
    }


def test_legacy_free_text_does_not_prove_full_time():
    job = _make_sample_job(raw_text='software engineer. Must have previous full-time experience.', employment_type=None)
    embed = build_job_embed(job)
    assert 'Full-time: Unknown' in embed['description']
    assert 'description completeness' in fields(embed)['Eligibility screen']


def test_surrogate_in_url_is_not_rendered():
    embed = build_job_embed(_make_sample_job(url='https://example.com/\ud800'))
    assert 'Unavailable' in fields(embed)['Employer posting']


def test_long_valid_posting_remains_clickable_without_overflow():
    url = 'https://example.com/jobs/' + 'a' * 1100
    embed = build_job_embed(_make_sample_job(url=url))
    assert embed['url'] == url
    assert 'Open job title' in fields(embed)['Employer posting']
    assert len(fields(embed)['Employer posting']) <= 1024


def test_dst_fall_back_distinguishes_both_hours():
    base = _make_sample_job(source_platform='ashby', posted_at_kind='last_published')
    earlier = replace(base, posted_at=datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc))
    later = replace(base, posted_at=datetime(2026, 11, 1, 7, 30, tzinfo=timezone.utc))
    assert fields(build_job_embed(earlier))['Last published'] == '2026-11-01 1:30 AM CDT'
    assert fields(build_job_embed(later))['Last published'] == '2026-11-01 1:30 AM CST'


def test_legacy_http_posting_remains_visible():
    embed = build_job_embed(_make_sample_job(url='http://careers.example.com/jobs/1'))
    assert 'http://careers.example.com/jobs/1' in fields(embed)['Employer posting']
    assert 'unverified' in fields(embed)['Employer posting']


def test_date_only_employer_posting_is_not_shifted_or_given_a_time():
    for platform in ('apple_jobs', 'amazon_jobs'):
        job = _make_sample_job(source_platform=platform, posted_at=datetime(2026, 11, 2, tzinfo=timezone.utc))
        assert fields(build_job_embed(job))['Employer posted date'] == '2026-11-02'


def test_review_digest_prioritizes_pipeline_cohort_blocker():
    from src.filtering import apply_filter_pipeline
    from src.notifier import build_review_digest
    job = _make_sample_job(title='Software Engineer, New Grad', posted_at=None,
                           location='San Jose, CA', role_type='unknown',
                           raw_text='Software Engineer, New Grad. Class of 2027. San Jose, CA.')
    result, reasons = apply_filter_pipeline(job, {'mode': 'new_grad_full_time', 'freshness_hours': 48}, {})
    assert result is None
    assert any('COHORT_2027_UNSPECIFIED' in r for r in reasons)
    digest = build_review_digest([{'company': job.company, 'title': job.title,
                                   'url': job.url, 'reasons': reasons}], 1)
    assert 'cohort 2027 unspecified' in digest.lower()


def test_card_does_not_replace_unknown_pipeline_career_level():
    from src.filtering import apply_filter_pipeline
    job = _make_sample_job(title='Software Engineer', posted_at=None, role_type='unknown',
                           raw_text='Software Engineer. Full time. 0-2 years experience. San Jose, CA.')
    result, _ = apply_filter_pipeline(job, {'mode': 'new_grad_full_time'}, {})
    assert result is not None
    assert result.verdict.career_level == 'unknown'
    assert result.role_type == 'new-grad'
    assert 'Career level: Unknown' in build_job_embed(result)['description']
    assert 'New grad' not in build_job_embed(result)['description']

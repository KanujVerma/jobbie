"""Catalogue evidence never changes legacy delivery or guesses title identity."""
import csv
import io
import json
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path

import pytest
from src.models import Job
from src.catalogue import Catalogue, CatalogueError, normalized_snapshot

NOW=datetime(2026,11,12,tzinfo=timezone.utc)
CFG={'name':'Example Labs','enabled':True,'network_priority':True,
     'cohort':'original_2026_11_04','referral_status':'unconfirmed'}


def job(identifier='1',**kwargs):
    values=dict(id=f'example|fixture|{identifier}',company='Example Labs',title='Engineer',
        location='United States',department=None,category=None,url=f'https://example.com/jobs/{identifier}',
        source_platform='fixture',posted_at=None,detected_at=NOW,raw_text='Full time software engineer',
        role_type='unknown',priority='normal',matched_keywords=(),source_job_id=identifier)
    return Job(**{**values,**kwargs})


@pytest.fixture
def cat(tmp_path):
    with Catalogue(tmp_path/'catalogue.sqlite',create=True) as db:
        yield db


def scan(cat,jobs,run='r1',source='s1',cfg=CFG,status='complete',when=NOW):
    cat.start_run(run,when,origin='fixture')
    return cat.observe_scan(run,source,cfg,jobs,status=status,observed_at=when)


def test_all_normalized_rows_retained_before_user_filtering(cat):
    result=scan(cat,[job('1'),job('2',raw_text='Internship in Germany'),job('3',raw_text='10 years experience')])
    assert result['observed']==3 and cat.stats()['jobs']==3
    assert {x['source_record_id'] for x in cat.history()}=={'1','2','3'}
    assert all(x['snapshot']['network_priority'] for x in cat.history())
    assert all(x['snapshot']['referral_status']=='unconfirmed' for x in cat.history())


@pytest.mark.parametrize('n',range(15))
def test_distinct_provider_ids_never_merge_by_title_location(cat,n):
    a,b=str(n*2),str(n*2+1)
    scan(cat,[job(a),job(b)])
    assert cat.stats()['jobs']==2


@pytest.mark.parametrize('urls,same',[
    (('https://example.com/jobs/1','https://EXAMPLE.com/jobs/1?utm_source=feed'),True),
    (('https://example.com/jobs?reqId=1','https://example.com/jobs?reqId=2'),False),
    (('https://example.com/Jobs/A','https://example.com/jobs/a'),False),
    (('https://jobs.ashbyhq.com/labs/abcd','https://jobs.ashbyhq.com/labs/abcd/application'),True),
    (('https://boards.greenhouse.io/labs/jobs/123','https://job-boards.greenhouse.io/labs/jobs/123?gh_jid=123'),True),
    (('https://example.com/jobs?ref=1','https://example.com/jobs?ref=2'),False),
    (('https://example.com/jobs?id=1&id=2','https://example.com/jobs?id=2&id=1'),False),
])
def test_cross_source_url_identity_is_conservative(cat,urls,same):
    scan(cat,[job(url=urls[0],source_job_id=None)],source='a')
    scan(cat,[job('other',url=urls[1],source_platform='other',source_job_id=None)],run='r2',source='b')
    assert cat.stats()['jobs']==(1 if same else 2)


def test_employer_requisition_links_distinct_provider_urls(cat):
    scan(cat,[job(official_req_id='REQ-1')],source='a')
    scan(cat,[job('other',source_platform='other',url='https://official.example/requisition/1',official_req_id='REQ-1')],run='r2',source='b')
    assert cat.stats()['jobs']==1 and len(cat.history())==2


def test_distinct_requisitions_at_same_url_are_retained_as_conflict(cat):
    scan(cat,[job('1',official_req_id='REQ-1')])
    r=scan(cat,[job('2',url=job().url,official_req_id='REQ-2')],run='r2',source='b')
    assert cat.stats()['jobs']==2 and r['conflicts']>=1
    assert cat.conflicts()[0]['code']=='IDENTITY_CONFLICT'


def test_employer_names_are_not_implicitly_aliased(cat):
    scan(cat,[job()])
    scan(cat,[job(company='Other Labs')],run='r2',source='other',cfg={**CFG,'name':'Other Labs'})
    assert cat.stats()['jobs']==2


def test_explicit_verified_employer_key_links_alias_only(cat):
    scan(cat,[job()],cfg={**CFG,'catalogue_employer_key':'verified-example'})
    scan(cat,[job(company='Example Research')],run='r2',source='b',cfg={**CFG,'name':'Example Research','catalogue_employer_key':'verified-example'})
    assert cat.stats()['jobs']==1


def test_source_id_reuse_with_new_req_does_not_overwrite_old(cat):
    scan(cat,[job(official_req_id='R1')])
    scan(cat,[job(official_req_id='R2')],run='r2')
    assert cat.stats()['jobs']==2 and cat.stats()['conflicts']>=1
    assert {x['snapshot']['official_req_id'] for x in cat.history()}=={'R1','R2'}


def test_duplicates_retain_observations_without_duplicate_jobs_or_payloads(cat):
    scan(cat,[job(),job()])
    scan(cat,[replace(job(),detected_at=NOW+timedelta(hours=1))],run='r2',when=NOW+timedelta(hours=1))
    assert cat.stats()['jobs']==1 and cat.stats()['snapshots']==1
    assert cat.stats()['observations']==3
    assert cat.query()[0]['first_observed_at']==NOW.isoformat()
    assert cat.query()[0]['last_observed_at']==(NOW+timedelta(hours=1)).isoformat()


def test_contradictory_duplicate_retains_both_versions(cat):
    r=scan(cat,[job(),replace(job(),raw_text='Different published text')])
    assert r['conflicts']>=1 and cat.stats()['snapshots']==2
    assert len(cat.history())==2


def test_absence_is_unknown_never_fabricated_closed(cat):
    scan(cat,[job()])
    scan(cat,[],run='r2',when=NOW+timedelta(hours=1))
    assert cat.query()[0]['status']=='unknown'
    assert cat.status_history()[1]['evidence_kind']=='complete_scan_absence'


@pytest.mark.parametrize('status',['partial','failed'])
def test_outage_or_partial_scan_cannot_close_or_erase(cat,status):
    scan(cat,[job()])
    scan(cat,[],run='r2',status=status)
    assert cat.query()[0]['status']=='open' and len(cat.history())==1


def test_explicit_closed_then_listing_reopens_with_evidence(cat):
    scan(cat,[job()]);identity=cat.query()[0]['job_id']
    cat.record_closed(identity,'s1','1',NOW+timedelta(hours=1),evidence_url=job().url,evidence='Official source explicitly reports closed')
    assert cat.query()[0]['status']=='closed'
    scan(cat,[job()],run='r2',when=NOW+timedelta(hours=2))
    assert cat.query()[0]['status']=='reopened'
    assert [x['status'] for x in cat.status_history(identity)]==['open','closed','reopened']


def test_one_closed_source_cannot_close_other_open_source(cat):
    scan(cat,[job()],source='a');scan(cat,[job()],run='r2',source='b')
    identity=cat.query()[0]['job_id']
    cat.record_closed(identity,'a','1',NOW,evidence_url=job().url,evidence='Explicit close')
    assert cat.query()[0]['status']=='open'


def test_dates_precision_and_observation_are_separate(cat):
    scan(cat,[job(source_posted_date='2026-11-01'),job('2',source_updated_at=NOW-timedelta(days=2),posted_at_kind='updated')])
    rows={x['source_record_id']:x['snapshot'] for x in cat.history()}
    assert rows['1']['source_posted_date']=='2026-11-01' and rows['1']['posted_at'] is None
    assert rows['2']['source_updated_at']==(NOW-timedelta(days=2)).isoformat()
    assert rows['2']['posted_at'] is None
    assert cat.query()[0]['first_observed_at']==NOW.isoformat()


def test_legacy_provider_timestamps_are_not_claimed_exact():
    data=normalized_snapshot(job(source_platform='workday',posted_at=NOW),CFG)
    assert data['posted_at'] is None and data['adapter_posted_at']==NOW.isoformat()
    assert data['posted_precision']=='unknown'


@pytest.mark.parametrize('url',['http://example.com/x','https://127.0.0.1/x','https://user:secret@example.com/x','file:///tmp/x'])
def test_hostile_url_rejected_without_fetch_or_false_complete(cat,url):
    r=scan(cat,[job(url=url)])
    assert r['rejected']==1 and r['status']=='partial' and cat.stats()['jobs']==0


def test_reclassification_is_versioned_and_does_not_mutate_snapshots(cat):
    scan(cat,[job()]);old=cat.history()
    count=cat.reclassify('policy-v2',lambda data:{'status':'needs_review','reasons':['UNKNOWN_DATE']},NOW)
    assert count==1 and cat.history()==old
    assert cat.query(policy='policy-v2')[0]['classification']['status']=='needs_review'
    with pytest.raises(CatalogueError):cat.reclassify('policy-v2',lambda data:{'status':'eligible'},NOW)
    assert cat.query(policy='policy-v2')[0]['classification']['status']=='needs_review'


def test_reclassification_failure_rolls_back_every_row(cat):
    scan(cat,[job(),job('2')])
    def classify(data):
        if data['source_job_id']=='2':raise ValueError('fixture failure')
        return {'status':'eligible'}
    with pytest.raises(ValueError):cat.reclassify('failed-policy',classify,NOW)
    assert all(x.get('classification') is None for x in cat.query(policy='failed-policy'))


def test_search_export_is_bounded_literal_and_csv_safe(cat):
    scan(cat,[job(title='=HYPERLINK("evil")'),job('2',title='100% Software')])
    assert len(cat.query(text='%'))==1
    assert len(cat.query(limit=1))==1
    assert len([json.loads(x) for x in cat.export('jsonl')])==2
    rows=list(csv.DictReader(io.StringIO(''.join(cat.export('csv')))))
    assert any(r['title'].startswith("'=") for r in rows)
    with pytest.raises(ValueError):cat.query(limit=5001)


def test_lead_stays_unverified_until_linked_to_actual_observation(cat):
    from src.public_feeds import FeedLead
    lead=FeedLead('lead1','feed','https://example.com/feed','1','Example Labs','Engineer','US',job().url,NOW,'f'*64)
    cat.observe_leads('r1',[lead])
    assert cat.stats()['leads']==1 and cat.stats()['jobs']==0
    with pytest.raises(CatalogueError):cat.confirm_lead('feed','lead1','s1','1',NOW)
    scan(cat,[job()])
    cat.confirm_lead('feed','lead1','s1','1',NOW)
    assert cat.leads()[0]['official_job_id']==cat.query()[0]['job_id']


def test_missing_corrupt_readonly_and_unknown_version_never_reset(tmp_path):
    missing=tmp_path/'missing.sqlite'
    with pytest.raises(CatalogueError):Catalogue(missing,readonly=True)
    assert not missing.exists()
    corrupt=tmp_path/'corrupt.sqlite';corrupt.write_bytes(b'original corrupt data')
    for create in [False,True]:
        with pytest.raises(CatalogueError):Catalogue(corrupt,create=create)
        assert corrupt.read_bytes()==b'original corrupt data'
    with Catalogue(tmp_path/'valid.sqlite',create=True) as db:
        db.db.execute('PRAGMA user_version=999')
    with pytest.raises(CatalogueError):Catalogue(tmp_path/'valid.sqlite')


def test_readonly_does_not_modify_database_and_symlinks_rejected(tmp_path):
    p=tmp_path/'db.sqlite'
    with Catalogue(p,create=True) as db:scan(db,[job()])
    before=p.read_bytes()
    with Catalogue(p,readonly=True) as db:
        assert len(db.query())==1
        with pytest.raises(CatalogueError):scan(db,[job()],run='other')
    assert p.read_bytes()==before
    alias=tmp_path/'alias.sqlite';alias.symlink_to(p)
    with pytest.raises(CatalogueError):Catalogue(alias)


def test_snapshot_roundtrip_retains_unknowns_source_and_compensation(cat):
    from decimal import Decimal
    from src.models import CompensationRange
    value=job(compensation=(CompensationRange(Decimal('100000'),None,'USD','year','published_base'),))
    scan(cat,[value])
    data=cat.history()[0]['snapshot']
    restored=cat.job_from_snapshot(data)
    assert restored.compensation==value.compensation and restored.source_job_id=='1'
    assert restored.description_complete is None and restored.posted_at is None


def test_title_derived_legacy_hash_is_opaque_not_provider_identity(cat):
    a=job(id='abc123opaquehash',source_job_id=None)
    b=replace(a,url='https://example.com/another-requisition')
    scan(cat,[a,b])
    assert cat.stats()['jobs']==2
    assert all(x['snapshot']['source_job_id'] is None for x in cat.history())


def test_out_of_order_scan_retains_history_without_regressing_current_status(cat):
    scan(cat,[job()],when=NOW+timedelta(hours=2))
    scan(cat,[],run='earlier',when=NOW+timedelta(hours=1))
    assert cat.query()[0]['status']=='open'
    assert cat.query()[0]['last_observed_at']==(NOW+timedelta(hours=2)).isoformat()


def test_source_closure_evidence_survives_other_open_sources(cat):
    scan(cat,[job()],source='a');scan(cat,[job()],source='b',run='r2')
    identity=cat.query()[0]['job_id']
    cat.record_closed(identity,'a','1',NOW,evidence_url=job().url,evidence='Employer says no longer accepting')
    assert any(e['evidence_kind']=='explicit_closed' for e in cat.status_history(identity))


def test_canonical_network_label_and_all_provenance_survive_secondary_source(cat):
    scan(cat,[job()],source='original')
    scan(cat,[job(source_platform='other')],run='r2',source='secondary',cfg={**CFG,'network_priority':False,'cohort':'discovered','referral_status':'unavailable'})
    row=cat.query()[0]
    assert row['network_priority'] is True and row['referral_status']=='unconfirmed'
    assert {s['source_id'] for s in row['sources']}=={'original','secondary'}


def test_confirmation_requires_exact_employer_url_and_compatible_source_id(cat):
    from src.public_feeds import FeedLead
    scan(cat,[job()])
    wrong=FeedLead('wrong','feed','https://example.com/feed','1','Other Labs','Engineer','US',job().url,NOW,'f'*64)
    cat.observe_leads('r1',[wrong])
    with pytest.raises(CatalogueError):cat.confirm_lead('feed','wrong','s1','1',NOW)
    correct=replace(wrong,employer='Example Labs',url='https://example.com/other')
    cat.observe_leads('r2',[correct])
    with pytest.raises(CatalogueError):cat.confirm_lead('feed','wrong','s1','1',NOW)


def test_source_scan_transaction_rolls_back_on_late_failure(cat,monkeypatch):
    cat.start_run('r1',NOW,origin='fixture')
    original=cat._identity
    def fail(run,source,employer,data,when):
        if data['source_job_id']=='2':raise RuntimeError('fixture late crash')
        return original(run,source,employer,data,when)
    monkeypatch.setattr(cat,'_identity',fail)
    with pytest.raises(RuntimeError):cat.observe_scan('r1','s1',CFG,[job(),job('2')],status='complete',observed_at=NOW)
    assert cat.stats()['jobs']==cat.stats()['snapshots']==cat.stats()['observations']==0


def test_explicit_legacy_composite_id_recovers_provider_id_only_for_matching_namespace():
    a=job(id='Example Labs::amazon_jobs::123',source_platform='amazon_jobs',source_job_id=None)
    assert normalized_snapshot(a,CFG)['source_job_id']=='123'
    assert normalized_snapshot(replace(a,company='Other'),{**CFG,'name':'Other'})['source_job_id'] is None


def test_changed_lead_facts_clear_prior_confirmation(cat):
    from src.public_feeds import FeedLead
    scan(cat,[job()])
    lead=FeedLead('x','feed','https://example.com/feed','1','Example Labs','Engineer','US',job().url,NOW,'f'*64)
    cat.observe_leads('r1',[lead]);cat.confirm_lead('feed','x','s1','1',NOW)
    cat.observe_leads('r2',[replace(lead,url='https://example.com/changed',observed_at=NOW+timedelta(hours=1))])
    assert cat.leads()[0]['official_job_id'] is None


def test_provider_id_missing_never_merges_identical_titles_with_distinct_urls(cat):
    from hypothesis import given,settings,strategies as st
    # Separate DB per example avoids leaking committed examples into this fixture.
    import tempfile
    @settings(max_examples=30,deadline=None)
    @given(st.lists(st.text(alphabet='0123456789abcdef',min_size=2,max_size=12),min_size=2,max_size=4,unique=True))
    def separate(ids):
        with tempfile.TemporaryDirectory() as directory:
            with Catalogue(Path(directory)/'db.sqlite',create=True) as store:
                scan(store,[job(id='same-title-derived-hash',source_job_id=None,url=f'https://example.com/req/{x}') for x in ids])
                assert store.stats()['jobs']==len(ids)
    separate()


def test_cli_readonly_missing_database_never_initializes(tmp_path):
    import subprocess,sys
    missing=tmp_path/'missing.sqlite'
    result=subprocess.run([sys.executable,'main.py','catalogue','query','--db',str(missing)],capture_output=True,text=True)
    assert result.returncode==1 and not missing.exists()


def test_cli_init_query_export_and_reclassify_use_explicit_db(tmp_path):
    import subprocess,sys
    p=tmp_path/'db.sqlite'
    result=subprocess.run([sys.executable,'main.py','catalogue','init','--db',str(p)],capture_output=True,text=True)
    assert result.returncode==0
    with Catalogue(p) as db:scan(db,[job(title='Software Engineer')])
    for args in [['query'],['history'],['export','--format','csv'],['reclassify','--policy-version','fixture-v2']]:
        result=subprocess.run([sys.executable,'main.py','catalogue',*args,'--db',str(p)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    with Catalogue(p,readonly=True) as db:
        assert db.query(policy='fixture-v2')[0]['classification']['status']=='needs_review'


def test_same_explicit_employer_req_survives_provider_posting_id_change(cat):
    scan(cat,[job('post1',official_req_id='EMPLOYER-REQ')])
    scan(cat,[job('post2',official_req_id='EMPLOYER-REQ')],run='r2')
    assert cat.stats()['jobs']==1


def test_ambiguity_does_not_create_a_new_identity_on_each_retry(cat):
    a=job('1',official_req_id='REQ-1');b=job('2',url=a.url,official_req_id='REQ-2')
    scan(cat,[a,b])
    before=cat.stats()['jobs']
    scan(cat,[a,b],run='r2')
    assert cat.stats()['jobs']==before


def test_closed_or_stale_official_record_cannot_confirm_new_lead(cat):
    from src.public_feeds import FeedLead
    scan(cat,[job()]);identity=cat.query()[0]['job_id']
    lead=FeedLead('x','feed','https://example.com/feed','1','Example Labs','Engineer','US',job().url,NOW,'f'*64)
    cat.observe_leads('r1',[lead])
    with pytest.raises(CatalogueError):cat.confirm_lead('feed','x','s1','1',NOW+timedelta(days=2))
    cat.record_closed(identity,'s1','1',NOW,evidence_url=job().url,evidence='Explicit source closure')
    with pytest.raises(CatalogueError):cat.confirm_lead('feed','x','s1','1',NOW)


def test_schema_version_alone_does_not_prove_supported_database(tmp_path):
    import sqlite3
    p=tmp_path/'incomplete.sqlite'
    with sqlite3.connect(p) as connection:connection.execute('PRAGMA user_version=1')
    before=p.read_bytes()
    with pytest.raises(CatalogueError):Catalogue(p)
    assert p.read_bytes()==before


def test_bridge_between_existing_identities_is_reported_without_retry_inflation(cat):
    scan(cat,[job('1',official_req_id='REQ')],source='a')
    scan(cat,[job('2')],source='b',run='r2')
    bridge=job('2',url=job('1').url,official_req_id='REQ')
    scan(cat,[bridge],source='b',run='r3')
    before=cat.stats()['jobs']
    scan(cat,[bridge],source='b',run='r4')
    assert cat.stats()['jobs']==before==2 and cat.stats()['conflicts']>=2


def test_new_historical_listing_respects_newer_complete_absence(tmp_path):
    statuses=[]
    for order in ['chronological','reverse']:
        with Catalogue(tmp_path/(order+'.sqlite'),create=True) as db:
            evidence=[([job()],'listed',NOW),([], 'absent',NOW+timedelta(hours=1))]
            if order=='reverse':evidence.reverse()
            for rows,run,when in evidence:scan(db,rows,run=run,when=when)
            statuses.append(db.query()[0]['status'])
            assert len(db.history())==1
    assert statuses==['unknown','unknown']


def test_later_presence_after_absence_stays_open_when_old_row_arrives(cat):
    scan(cat,[],run='absence',when=NOW+timedelta(hours=1))
    scan(cat,[job()],run='new-presence',when=NOW+timedelta(hours=2))
    scan(cat,[job()],run='old-presence',when=NOW)
    assert cat.query()[0]['status']=='open'

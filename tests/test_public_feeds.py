"""Unverified public leads are gated away from alerts and arbitrary URL fetches."""
import copy
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import requests

from src.public_feeds import fetch_feed, confirm_lead, load_manifest
from src.job_identity import canonical_job_url

NOW = datetime(2026, 11, 11, 23, tzinfo=timezone.utc)
ENDPOINT = 'https://raw.githubusercontent.com/example/public-jobs/main/jobs.json'


def source(**changes):
    return {'id':'fixture', 'enabled':True, 'endpoint':ENDPOINT, 'format':'json',
            'rows_key':'jobs', 'refresh_seconds':3600,
            'rights':{'status':'permitted','url':'https://example.com/data-policy',
                      'basis':'Synthetic fixture only','checked_at':'2026-11-11T20:00:00Z'},
            'owner_approval':{'endpoint':ENDPOINT,'reference':'fixture-owner-approval',
                              'approved_at':'2026-11-11T20:00:00Z'}, **changes}


def row(identifier='1', **changes):
    return {'id':identifier,'company':'Example Labs','title':'Software Engineer',
            'location':'United States','url':f'https://example.com/jobs/{identifier}', **changes}


def http_for(payload, status=200):
    http=MagicMock()
    http.get.return_value=MagicMock(status_code=status,headers={},
        iter_content=MagicMock(return_value=[json.dumps(payload).encode()]))
    return http


def test_disabled_rights_and_approval_gates_make_no_requests():
    http=http_for({'jobs':[row()]})
    for cfg in [source(enabled=False),source(rights={'status':'unknown'}),
                source(rights={'status':'prohibited'}),source(owner_approval=None)]:
        leads,report=fetch_feed(cfg,{},http=http,now=NOW)
        assert leads==[] and report['returned_count'] is None
    http.get.assert_not_called()


@pytest.mark.parametrize('endpoint', ['http://raw.githubusercontent.com/a/b/main/x.json',
    'https://127.0.0.1/x.json','https://evil.example/jobs.json',
    'https://user:secret@raw.githubusercontent.com/a/b/main/x.json',
    'https://raw.githubusercontent.com/a/b/main/x.json?token=secret'])
def test_hostile_endpoint_never_fetched(endpoint):
    http=http_for({'jobs':[]});cfg=source(endpoint=endpoint)
    cfg['owner_approval']['endpoint']=endpoint
    leads,report=fetch_feed(cfg,{},http=http,now=NOW)
    assert not leads and report['status']=='invalid_config'
    http.get.assert_not_called()


def test_normalized_leads_preserve_provenance_and_unknowns():
    http=http_for({'updated_at':'2026-11-10T12:00:00Z','jobs':[row()]})
    leads,report=fetch_feed(source(),{},http=http,now=NOW)
    assert report['status']=='ok' and report['returned_count']==1
    lead=leads[0]
    assert lead.confirmation_status=='lead'
    assert lead.source_id=='fixture' and lead.source_url==ENDPOINT
    assert lead.observed_at==NOW
    assert lead.employer_posted_at is None
    assert lead.feed_updated_at.isoformat()=='2026-11-10T12:00:00+00:00'
    assert lead.reported_posted_at is None
    assert http.get.call_args.kwargs['allow_redirects'] is False
    assert http.get.call_args.kwargs['stream'] is True


def test_empty_response_is_successful_empty_not_source_failure():
    leads,r=fetch_feed(source(),{},http=http_for({'jobs':[]}),now=NOW)
    assert leads==[] and r['status']=='empty' and r['returned_count']==0


@pytest.mark.parametrize('code',[403,404,429])
def test_http_failure_is_isolated_without_empty_success(code):
    http=MagicMock();response=requests.Response();response.status_code=code;response.raw=MagicMock()
    http.get.side_effect=requests.HTTPError('https://secret.example/token',response=response)
    leads,r=fetch_feed(source(),{},http=http,now=NOW)
    assert not leads and r['status']=='failed' and r['http_status']==code
    assert r['returned_count'] is None
    assert 'secret.example' not in json.dumps(r)


def test_redirect_is_not_followed_or_parsed():
    http=http_for({'jobs':[row()]},status=302)
    leads,r=fetch_feed(source(),{},http=http,now=NOW)
    assert not leads and r['status']=='failed'
    assert http.get.call_args.kwargs['allow_redirects'] is False


def test_source_identity_duplicates_and_distinct_requisitions():
    http=http_for({'jobs':[row('1'),row('1'),row('2')]})
    leads,r=fetch_feed(source(),{},http=http,now=NOW)
    assert len(leads)==2 and r['duplicate_count']==1
    assert leads[0].lead_id!=leads[1].lead_id
    http=http_for({'jobs':[row('1'),row('1',url='https://example.com/other')]})
    leads,r=fetch_feed(source(),{},http=http,now=NOW)
    assert not leads and r['status']=='failed'


def test_refresh_interval_uses_health_without_network():
    state={}
    fetch_feed(source(),state,http=http_for({'jobs':[row()]}),now=NOW)
    http=http_for({'jobs':[row('2')]})
    leads,r=fetch_feed(source(),state,http=http,now=NOW+timedelta(minutes=30))
    assert not leads and r['status']=='not_due'
    http.get.assert_not_called()


def test_canonical_url_strips_tracking_but_keeps_requisition_parameters():
    assert canonical_job_url('https://EXAMPLE.com/jobs?job_id=1&utm_source=feed#x')=='https://example.com/jobs?job_id=1'
    assert canonical_job_url('https://example.com/jobs?source=1')!=canonical_job_url('https://example.com/jobs?source=2')
    assert canonical_job_url('https://example.com/jobs?job_id=1')!=canonical_job_url('https://example.com/jobs?job_id=2')
    assert canonical_job_url('https://example.com/Jobs/A')!=canonical_job_url('https://example.com/jobs/a')


def official_job(url='https://example.com/jobs/1', company='Example Labs'):
    from src.models import Job
    return Job(id='official1',company=company,title='Software Engineer',location='United States',
        department=None,category=None,url=url,source_platform='fixture',posted_at=None,
        detected_at=NOW,raw_text='full time',role_type='unknown',priority='normal',matched_keywords=())


def test_lead_requires_exact_approved_employer_job_confirmation():
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row()]}),now=NOW)
    cfg={'name':'Example Labs','enabled':True,'aliases':[]}
    assert confirm_lead(leads[0],[official_job()],cfg,now=NOW).official_job_id=='official1'
    assert confirm_lead(leads[0],[official_job(url='https://example.com/jobs/2')],cfg,now=NOW) is None
    assert confirm_lead(leads[0],[official_job()],{**cfg,'enabled':False},now=NOW) is None
    assert confirm_lead(leads[0],[official_job()],{'name':'Other','enabled':True},now=NOW) is None


def test_default_manifest_is_off_and_has_explicit_rights_block():
    feeds=load_manifest('public-feeds.yaml')
    assert len(feeds)==3 and all(f['enabled'] is False for f in feeds)
    http=MagicMock()
    for f in feeds:
        leads,r=fetch_feed(f,{},http=http,now=NOW)
        assert not leads and 'BLOCKED_SOURCE_RIGHTS' in r['gates']
    http.get.assert_not_called()


def test_url_normalization_idempotent_and_retains_meaningful_ids():
    from hypothesis import given, settings, strategies as st
    from urllib.parse import urlencode, parse_qsl, urlsplit
    @settings(max_examples=100, deadline=None)
    @given(st.sampled_from(['job_id','reqId','source','ref','gh_jid']),
           st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789',min_size=1,max_size=40))
    def invariant(key,value):
        url='https://EXAMPLE.com/Jobs/A?'+urlencode([(key,value),('utm_source','feed')])
        result=canonical_job_url(url)
        assert canonical_job_url(result)==result
        assert (key,value) in parse_qsl(urlsplit(result).query)
    invariant()


def test_distinct_requisition_query_values_never_collapse():
    from hypothesis import given, settings, strategies as st
    from urllib.parse import urlencode
    @settings(max_examples=100, deadline=None)
    @given(st.lists(st.text(alphabet='abcdef0123456789',min_size=1,max_size=30),min_size=2,max_size=2,unique=True))
    def invariant(values):
        urls=['https://example.com/jobs?'+urlencode({'job_id':v,'utm_campaign':'x'}) for v in values]
        assert canonical_job_url(urls[0])!=canonical_job_url(urls[1])
    invariant()


@pytest.mark.parametrize('payload',[None,{}, {'jobs':'bad'}, {'jobs':[{'id':'1','url':'https://127.0.0.1/x'}]},
                                    {'jobs':[row()]*5001}])
def test_corrupt_or_oversized_shape_is_not_empty_success(payload):
    leads,r=fetch_feed(source(),{},http=http_for(payload),now=NOW)
    assert leads==[] and r['status']=='failed' and r['returned_count'] is None


def test_oversized_wire_is_bounded():
    from src.public_feeds import MAX_BYTES
    http=MagicMock()
    http.get.return_value=MagicMock(status_code=200,headers={},
        iter_content=MagicMock(return_value=[b'x'*(MAX_BYTES+1)]))
    leads,r=fetch_feed(source(),{},http=http,now=NOW)
    assert not leads and r['status']=='failed'


def test_feed_dates_never_become_verified_employer_time():
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(posted_at='2026-11-10')]}),now=NOW)
    assert leads[0].reported_posted_date=='2026-11-10'
    assert leads[0].reported_posted_at is None and leads[0].employer_posted_at is None


def test_unverified_req_conflict_cannot_confirm_same_url():
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(official_req_id='different')]}),now=NOW)
    assert confirm_lead(leads[0],[official_job()],{'name':'Example Labs','enabled':True},now=NOW) is None


def test_unknown_employer_cannot_confirm_by_title_and_url():
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(company=None)]}),now=NOW)
    assert confirm_lead(leads[0],[official_job()],{'name':'Example Labs','enabled':True},now=NOW) is None


def test_conflicting_same_id_title_is_not_silently_lost():
    leads,r=fetch_feed(source(),{},http=http_for({'jobs':[row(),row(title='Different requisition')]}),now=NOW)
    assert not leads and r['status']=='failed'


def test_corrupt_optional_health_is_reported_without_reset():
    from src.public_feeds import collect_feeds
    broken=['retained malformed metadata']
    before=copy.deepcopy(broken)
    leads,reports=collect_feeds('public-feeds.yaml',broken)
    assert not leads and reports[0]['status']=='corrupt_health'
    assert broken==before


def test_optional_feed_failure_does_not_drop_original_delivery(tmp_path,monkeypatch):
    import main
    from src.config import Config
    from src.storage import _empty_state,POLICY_VERSION
    from types import SimpleNamespace
    state=_empty_state();state['first_run_completed_at']=NOW.isoformat();state['policy_version']=POLICY_VERSION
    state['migrations']={POLICY_VERSION:{'backfill_completed':True}}
    path=tmp_path/'state.json';path.write_text(json.dumps(state))
    class Official:
        def __init__(self,*a,**kw):pass
        def fetch(self):return [official_job()]
    cfg=Config(defaults={'state_path':str(path),'request_delay_seconds':[0,0],
                         'public_feeds_manifest':'fixture.yaml'},filters={},companies=[
                             {'name':'Example Labs','adapter':'official','config':{}}])
    sender=MagicMock();sender.send_job_alert.return_value=True
    monkeypatch.setattr(main,'load_config',lambda _:cfg)
    monkeypatch.setattr(main,'ADAPTER_REGISTRY',{'official':Official})
    monkeypatch.setattr(main,'HTTPClient',MagicMock())
    monkeypatch.setattr(main,'Notifier',MagicMock(return_value=sender))
    monkeypatch.setattr(main,'apply_filter_pipeline',lambda j,*a:(j,[]))
    monkeypatch.setattr(main,'collect_feeds',lambda *a,**kw:([],[{'source_id':'bad','status':'failed','returned_count':None}]))
    monkeypatch.setenv('DISCORD_WEBHOOK_URL','https://discord.com/api/webhooks/synthetic')
    assert main.do_run(SimpleNamespace(config='unused',dry_run=False))==0
    sender.send_job_alert.assert_called_once()
    saved=json.loads(path.read_text())
    assert saved['companies']['Example Labs']['seen_jobs']['official1']['alerted'] is True
    assert saved['last_heartbeat']['optional_feeds'][0]['status']=='failed'


def test_feed_cli_defaults_to_off_without_production_mutation():
    import subprocess,sys,hashlib
    from pathlib import Path
    before={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['companies.yaml','state/seen_jobs.json']}
    r=subprocess.run([sys.executable,'main.py','feed-check','--manifest','public-feeds.yaml'],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    data=json.loads(r.stdout)
    assert data['leads']==[] and all(x['status']=='disabled' for x in data['sources'])
    assert before=={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}


def test_known_ats_posting_application_urls_share_identity():
    assert canonical_job_url('https://jobs.ashbyhq.com/Example/abc-123/application?utm_source=x')==canonical_job_url('https://jobs.ashbyhq.com/Example/abc-123')
    assert canonical_job_url('https://boards.greenhouse.io/example/jobs/123?gh_jid=123')==canonical_job_url('https://job-boards.greenhouse.io/example/jobs/123')
    assert canonical_job_url('https://boards.greenhouse.io/example/jobs/123?gh_jid=456')!=canonical_job_url('https://job-boards.greenhouse.io/example/jobs/123')


def test_alternate_ats_url_confirms_against_actual_official_posting():
    lead_url='https://jobs.ashbyhq.com/Example/abc-123'
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(url=lead_url)]}),now=NOW)
    verified=official_job(url=lead_url+'/application')
    assert confirm_lead(leads[0],[verified],{'name':'Example Labs','enabled':True},now=NOW) is not None


def test_field_mapping_is_literal_and_preserves_unknowns():
    cfg=source(rows_key='listings',field_map={'url':'apply_url','company':'employer_name','id':'req'})
    leads,r=fetch_feed(cfg,{},http=http_for({'listings':[{'req':'A','apply_url':'https://example.com/jobs/A','employer_name':'Example Labs'}]}),now=NOW)
    assert r['status']=='ok' and leads[0].source_record_id=='A'
    assert leads[0].title is None and leads[0].location is None
    assert leads[0].confirmation_status=='lead'


def test_corrupt_feed_health_timestamp_is_retained_and_not_used():
    state={'fixture':{'last_attempt_at':'corrupt'}};before=copy.deepcopy(state)
    http=http_for({'jobs':[row()]})
    leads,r=fetch_feed(source(),state,http=http,now=NOW)
    assert not leads and r['status']=='invalid_config' and state==before
    http.get.assert_not_called()


def test_feed_failure_cadence_is_recorded_without_losing_previous_success():
    state={'fixture':{'last_success_at':(NOW-timedelta(days=1)).isoformat()}}
    http=http_for({},status=403)
    leads,r=fetch_feed(source(),state,http=http,now=NOW)
    assert not leads and r['status']=='failed'
    assert state['fixture']['last_success_at']==(NOW-timedelta(days=1)).isoformat()
    assert state['fixture']['last_attempt_at']==NOW.isoformat()


def test_incomplete_optional_manifest_does_not_raise_or_reset_health(tmp_path):
    from src.public_feeds import collect_feeds
    path=tmp_path/'bad.yaml';path.write_text('schema_version: 1\nfeeds: invalid\n')
    state={'retained':{'last_attempt_at':NOW.isoformat()}};before=copy.deepcopy(state)
    leads,reports=collect_feeds(str(path),state)
    assert not leads and reports[0]['status']=='invalid_manifest' and state==before


@pytest.mark.parametrize('platform', ['greenhouse','ashby','oracle_careers'])
def test_official_source_posting_id_confirmation_and_conflict(platform):
    from dataclasses import replace
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(official_req_id='123')]}),now=NOW)
    job=replace(official_job(),source_platform=platform,source_job_id='123')
    cfg={'name':'Example Labs','enabled':True}
    assert confirm_lead(leads[0],[job],cfg,now=NOW) is not None
    assert confirm_lead(replace(leads[0],official_req_id='456'),[job],cfg,now=NOW) is None


@pytest.mark.parametrize('dates', [('2026-11-01','2026-11-10'),('2026-11-10','2026-11-01')])
def test_conflicting_same_source_id_posting_dates_fail_in_both_orders(dates):
    leads,r=fetch_feed(source(),{},http=http_for({'jobs':[row(posted_at=d) for d in dates]}),now=NOW)
    assert not leads and r['status']=='failed'


def test_equivalent_posting_instants_are_identical_duplicates():
    leads,r=fetch_feed(source(),{},http=http_for({'jobs':[
        row(posted_at='2026-11-10T12:00:00Z'),row(posted_at='2026-11-10T07:00:00-05:00')]}),now=NOW)
    assert len(leads)==1 and r['duplicate_count']==1


def test_normal_poller_indexes_official_jobs_once_for_feed_confirmation(tmp_path,monkeypatch):
    import main
    import src.public_feeds as feeds
    from src.config import Config
    from src.storage import _empty_state
    from types import SimpleNamespace
    from dataclasses import replace
    state=tmp_path/'state.json';state.write_text(json.dumps(_empty_state()));before=state.read_bytes()
    official=[replace(official_job(url=f'https://example.com/jobs/{i}'),id=f'official-{i}') for i in range(100)]
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(str(i),url=f'https://example.com/unmatched/{i}') for i in range(20)]}),now=NOW)
    class Adapter:
        def __init__(self,*a,**kw):pass
        def fetch(self):return official
    cfg=Config(defaults={'state_path':str(state),'request_delay_seconds':[0,0],'public_feeds_manifest':'fixture.yaml'},
        filters={},companies=[{'name':'Example Labs','adapter':'official','enabled':True,'config':{}}])
    monkeypatch.setattr(main,'load_config',lambda _:cfg)
    monkeypatch.setattr(main,'ADAPTER_REGISTRY',{'official':Adapter})
    monkeypatch.setattr(main,'HTTPClient',MagicMock())
    monkeypatch.setattr(main,'Notifier',MagicMock())
    monkeypatch.setattr(main,'apply_filter_pipeline',lambda *a:(None,['excluded']))
    monkeypatch.setattr(main,'collect_feeds',lambda *a,**kw:(leads,[]))
    actual=feeds.canonical_job_url;calls=[]
    def count(value):calls.append(value);return actual(value)
    monkeypatch.setattr(feeds,'canonical_job_url',count)
    assert main.do_run(SimpleNamespace(config='unused',dry_run=True))==0
    print(f'confirmation_url_normalizations={len(calls)}')
    assert len(calls)<=len(official)+len(leads)+10
    assert state.read_bytes()==before


def test_conflicting_official_ids_at_same_url_cannot_confirm():
    from dataclasses import replace
    leads,_=fetch_feed(source(),{},http=http_for({'jobs':[row(official_req_id='123')]}),now=NOW)
    a=replace(official_job(),source_platform='greenhouse',source_job_id='123')
    b=replace(a,source_job_id='456')
    assert confirm_lead(leads[0],[a,b],{'name':'Example Labs','enabled':True},now=NOW) is None

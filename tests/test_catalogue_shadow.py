"""Shadow compares actual legacy decisions without owning sends or resetting ledgers."""
import copy
import json
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from src.catalogue import Catalogue,CatalogueError
from src.catalogue_shadow import Shadow,open_shadow,source_key,evidence_gate
from src.models import Job
from src.storage import _empty_state,POLICY_VERSION,classify_jobs

NOW=datetime(2026,11,12,tzinfo=timezone.utc)
CFG={'name':'Example Labs','adapter':'fixture','enabled':True,'config':{},'network_priority':True,
     'cohort':'original_2026_11_04','referral_status':'unconfirmed'}


def job(identifier='1',**kwargs):
    data=dict(id='Example Labs::fixture::'+identifier,company='Example Labs',title='Software Engineer',
        location='United States',department=None,category=None,url='https://example.com/jobs/'+identifier,
        source_platform='fixture',posted_at=NOW,detected_at=NOW,raw_text='software engineer full time',
        role_type='unknown',priority='normal',matched_keywords=(),source_job_id=identifier)
    return Job(**{**data,**kwargs})


def state():
    data=_empty_state();data['first_run_completed_at']=NOW.isoformat();data['policy_version']=POLICY_VERSION
    data['migrations']={POLICY_VERSION:{'backfill_completed':True}}
    return data


@pytest.fixture
def shadow(tmp_path):
    with Catalogue(tmp_path/'db.sqlite',create=True) as store:
        with Shadow(store,'fixture-run',NOW,state(),filters={},origin='fixture',config_sha='a'*64) as monitor:
            yield monitor


def capture(monitor,jobs,*,cfg=CFG,status='complete',when=NOW):
    return monitor.observe(cfg,jobs,status=status,observed_at=when)


def test_prefilter_capture_includes_excluded_unknown_and_partial_rows(shadow):
    capture(shadow,[job(),job('2',raw_text='internship in Germany'),job('3')],status='partial')
    assert shadow.store.stats()['jobs']==3
    assert shadow.report()['sources'][source_key(CFG)]['scan_status']=='partial'
    assert shadow.report()['delivery_authority']=='legacy_json'


def test_independent_candidate_projection_matches_legacy_without_mutating_state(shadow):
    current=state();before=copy.deepcopy(current);rows=[job()]
    capture(shadow,rows)
    expected=shadow.project(CFG,rows,current,freshness_hours=48,now=NOW)
    assert current==before
    legacy=classify_jobs(rows,CFG['name'],copy.deepcopy(current),48,NOW)
    result=shadow.compare(CFG,rows,legacy,expected)
    assert result['candidate_mismatches']==0 and result['canonical_candidates']==1


def test_injected_different_legacy_candidate_is_a_real_parity_failure(shadow):
    capture(shadow,[job()])
    projection=shadow.project(CFG,[job()],state(),freshness_hours=48,now=NOW)
    result=shadow.compare(CFG,[job()],[],projection)
    assert result['candidate_mismatches']==1
    assert 'BLOCKED_PARITY' in shadow.report()['gates']


def test_baseline_suppression_is_not_an_ack(shadow):
    rows=[job()];capture(shadow,rows)
    current=state();current['companies'][CFG['name']]={'seen_jobs':{rows[0].id:{'first_seen':NOW.isoformat(),'last_seen':NOW.isoformat(),'alerted':False,'baseline_suppressed':True}}}
    projected=shadow.project(CFG,rows,current,freshness_hours=48,now=NOW)
    assert not projected
    shadow.finish(current,NOW)
    assert shadow.report()['ack_count']==0
    assert shadow.store.stats()['jobs']==1


def test_failed_send_does_not_ack_and_retries_next_run(tmp_path):
    current=state()
    with Catalogue(tmp_path/'db.sqlite',create=True) as store:
        with Shadow(store,'r1',NOW,current,filters={},origin='fixture',config_sha='a'*64) as monitor:
            capture(monitor,[job()]);monitor.delivery(CFG,job(),'failed',NOW);monitor.finish(current,NOW)
            assert monitor.report()['ack_count']==0
        with Shadow(store,'r2',NOW+timedelta(hours=1),current,filters={},origin='fixture',config_sha='a'*64) as monitor:
            capture(monitor,[job()],when=NOW+timedelta(hours=1))
            assert monitor.project(CFG,[job()],current,freshness_hours=48,now=NOW+timedelta(hours=1))


def test_canonical_dedup_preserves_distinct_req_ids_and_reports_duplicate_groups(shadow):
    a=job(official_req_id='REQ1');b=job('2',url=a.url,official_req_id='REQ2')
    capture(shadow,[a,b]);projection=shadow.project(CFG,[a,b],state(),freshness_hours=48,now=NOW)
    assert len(projection)==2
    assert 'BLOCKED_IDENTITIES' in shadow.report()['gates']


def test_active_legacy_url_ack_prevents_canonical_duplicate_candidate(shadow):
    a=job();capture(shadow,[a]);current=state()
    current['alerted_urls'][a.url]={'company':a.company,'job_id':'old-provider-id','alerted_at':NOW.isoformat()}
    assert not shadow.project(CFG,[a],current,freshness_hours=48,now=NOW)


def test_stale_first_seen_and_old_ack_history_retained(shadow):
    a=job();current=state();old=NOW-timedelta(days=3)
    current['companies'][a.company]={'seen_jobs':{a.id:{'first_seen':old.isoformat(),'last_seen':NOW.isoformat(),'alerted':False}}}
    capture(shadow,[a]);assert not shadow.project(CFG,[a],current,freshness_hours=48,now=NOW)


def test_off_and_unsupported_cutover_never_create_or_reset(tmp_path,monkeypatch):
    path=tmp_path/'missing.sqlite'
    assert open_shadow(path,'off','r1',NOW,state(),filters={}) is None
    assert not path.exists()
    with pytest.raises(CatalogueError):open_shadow(path,'canonical','r1',NOW,state(),filters={})
    assert not path.exists()
    path.write_bytes(b'corrupt retained ledger')
    with pytest.raises(CatalogueError):open_shadow(path,'shadow','r1',NOW,state(),filters={})
    assert path.read_bytes()==b'corrupt retained ledger'


def test_dry_run_shadow_uses_memory_copy_and_keeps_sqlite_bytes(tmp_path):
    path=tmp_path/'db.sqlite'
    with Catalogue(path,create=True):pass
    before=path.read_bytes()
    monitor=open_shadow(path,'shadow','r1',NOW,state(),filters={},dry_run=True)
    with monitor:
        capture(monitor,[job()]);monitor.finish(state(),NOW)
        assert monitor.store.stats()['jobs']==1
    assert path.read_bytes()==before


def test_evidence_gate_never_accepts_fixture_or_unattested_timestamps():
    fake=[{'run_id':'1','origin':'schedule','started_at':NOW.isoformat(),'finished_at':(NOW+timedelta(hours=73)).isoformat(),'parity_ok':True}]
    result=evidence_gate(fake,github_runs=[],owner_approval=None,rollback_proof=False)
    assert not result['cutover_ready']
    assert {'BLOCKED_72H_EVIDENCE','BLOCKED_APPROVAL','BLOCKED_ROLLBACK'}<=set(result['gates'])


def test_real_receipts_require_contiguous_coverage_and_still_exact_cutover_approval():
    receipts=[];stored=[]
    for i in range(4):
        when=NOW+timedelta(hours=i*24)
        receipts.append({'id':i+1,'event':'schedule','head_branch':'main','head_sha':'a'*40,'status':'completed','conclusion':'success','run_started_at':when.isoformat(),'updated_at':(when+timedelta(minutes=5)).isoformat()})
        stored.append({'run_id':str(i+1),'origin':'schedule','head_sha':'a'*40,'started_at':when.isoformat(),'finished_at':(when+timedelta(minutes=5)).isoformat(),'parity_ok':True,'custody_verified':True})
    result=evidence_gate(stored,github_runs=receipts,owner_approval=None,rollback_proof=True)
    assert result['shadow_hours']>=72 and result['gates']==['BLOCKED_APPROVAL']
    result=evidence_gate(stored[:-1],github_runs=receipts,owner_approval=None,rollback_proof=True)
    assert 'BLOCKED_72H_EVIDENCE' in result['gates']


@pytest.mark.parametrize('mode',['off','shadow'])
@pytest.mark.parametrize('sent',[False,True])
def test_shadow_poller_keeps_original_sends_and_failed_send_ack(tmp_path,monkeypatch,mode,sent):
    import main
    import src.filtering
    from src.config import Config
    path=tmp_path/'seen.json';path.write_text(json.dumps(state()))
    db_path=tmp_path/'db.sqlite'
    with Catalogue(db_path,create=True):pass
    db_before=db_path.read_bytes()
    all_rows=[job(),job('2')]
    class Adapter:
        def __init__(self,*a,**kw):pass
        def fetch(self):return all_rows
    cfg=Config(defaults={'state_path':str(path),'request_delay_seconds':[0,0]},filters={},companies=[CFG])
    def pipeline(value,*args):
        if mode=='shadow':
            with Catalogue(db_path,readonly=True) as db:assert db.stats()['observations']==2
        return (value,[]) if value.id==all_rows[0].id else (None,['excluded'])
    sender=MagicMock();sender.send_job_alert.return_value=sent
    monkeypatch.setattr(main,'load_config',lambda _:cfg)
    monkeypatch.setattr(main,'ADAPTER_REGISTRY',{'fixture':Adapter})
    monkeypatch.setattr(main,'HTTPClient',MagicMock())
    monkeypatch.setattr(main,'Notifier',MagicMock(return_value=sender))
    monkeypatch.setattr(main,'apply_filter_pipeline',pipeline)
    monkeypatch.setattr(src.filtering,'apply_filter_pipeline',pipeline)
    monkeypatch.setenv('JOBBIE_CATALOGUE_MODE',mode);monkeypatch.setenv('JOBBIE_CATALOGUE_DB',str(db_path))
    monkeypatch.setenv('DISCORD_WEBHOOK_URL','https://discord.com/api/webhooks/synthetic-only')
    assert main.do_run(SimpleNamespace(config='fixture',dry_run=False))==0
    sender.send_job_alert.assert_called_once()
    final=json.loads(path.read_text())
    assert final['companies'][CFG['name']]['seen_jobs'][all_rows[0].id]['alerted'] is sent
    if mode=='off':assert db_path.read_bytes()==db_before
    else:
        with Catalogue(db_path,readonly=True) as db:
            assert db.stats()['jobs']==2
            result=json.loads(db.db.execute('SELECT result FROM shadow_runs').fetchone()[0])
            assert result['ack_count']==int(sent) and result['ack_mismatches']==0
            assert result['parity_ok'] is True


def test_shadow_storage_failure_does_not_skip_original_delivery(tmp_path,monkeypatch):
    import main
    from src.config import Config
    path=tmp_path/'seen.json';path.write_text(json.dumps(state()))
    db_path=tmp_path/'db.sqlite';db_path.write_bytes(b'retained corrupt database')
    class Adapter:
        def __init__(self,*a,**kw):pass
        def fetch(self):return [job()]
    cfg=Config(defaults={'state_path':str(path),'request_delay_seconds':[0,0]},filters={},companies=[CFG])
    sender=MagicMock();sender.send_job_alert.return_value=True
    monkeypatch.setattr(main,'load_config',lambda _:cfg);monkeypatch.setattr(main,'ADAPTER_REGISTRY',{'fixture':Adapter})
    monkeypatch.setattr(main,'HTTPClient',MagicMock());monkeypatch.setattr(main,'Notifier',MagicMock(return_value=sender))
    monkeypatch.setattr(main,'apply_filter_pipeline',lambda value,*a:(value,[]))
    monkeypatch.setenv('JOBBIE_CATALOGUE_MODE','shadow');monkeypatch.setenv('JOBBIE_CATALOGUE_DB',str(db_path))
    monkeypatch.setenv('DISCORD_WEBHOOK_URL','https://discord.com/api/webhooks/synthetic-only')
    assert main.do_run(SimpleNamespace(config='fixture',dry_run=False))==0
    sender.send_job_alert.assert_called_once()
    final=json.loads(path.read_text())
    assert final['companies'][CFG['name']]['seen_jobs'][job().id]['alerted'] is True
    assert 'BLOCKED_STORAGE' in final['last_heartbeat']['catalogue_shadow']['gates']
    assert db_path.read_bytes()==b'retained corrupt database'


def test_normal_shadow_dry_run_keeps_production_ledgers_byte_identical(tmp_path,monkeypatch):
    import main,src.filtering
    from src.config import Config
    path=tmp_path/'seen.json';path.write_text(json.dumps(state()))
    db_path=tmp_path/'db.sqlite'
    with Catalogue(db_path,create=True):pass
    before=(path.read_bytes(),db_path.read_bytes())
    class Adapter:
        def __init__(self,*a,**kw):pass
        def fetch(self):return [job()]
    cfg=Config(defaults={'state_path':str(path),'request_delay_seconds':[0,0]},filters={},companies=[CFG])
    sender=MagicMock()
    monkeypatch.setattr(main,'load_config',lambda _:cfg);monkeypatch.setattr(main,'ADAPTER_REGISTRY',{'fixture':Adapter})
    monkeypatch.setattr(main,'HTTPClient',MagicMock());monkeypatch.setattr(main,'Notifier',MagicMock(return_value=sender))
    monkeypatch.setattr(main,'apply_filter_pipeline',lambda value,*a:(value,[]))
    monkeypatch.setattr(src.filtering,'apply_filter_pipeline',lambda value,*a:(value,[]))
    monkeypatch.setenv('JOBBIE_CATALOGUE_MODE','shadow');monkeypatch.setenv('JOBBIE_CATALOGUE_DB',str(db_path))
    monkeypatch.setenv('DISCORD_WEBHOOK_URL','https://discord.com/api/webhooks/synthetic-only')
    assert main.do_run(SimpleNamespace(config='fixture',dry_run=True))==0
    sender.send_job_alert.assert_not_called()
    assert before==(path.read_bytes(),db_path.read_bytes())


def test_failed_individual_is_acked_only_after_explicit_exact_summary_receipt(shadow):
    capture(shadow,[job()]);shadow.delivery(CFG,job(),'failed',NOW)
    final=state();final['companies'][CFG['name']]={'seen_jobs':{job().id:{'first_seen':NOW.isoformat(),'last_seen':NOW.isoformat(),'alerted':True}}}
    shadow.finish(final,NOW,summary_acks={(CFG['name'],job().id)})
    assert shadow.report()['ack_mismatches']==0 and shadow.report()['summary_ack_count']==1
    assert shadow.report()['notifier_ack_count']==0


def test_failed_individual_cannot_gain_ack_without_a_positive_receipt(shadow):
    capture(shadow,[job()]);shadow.delivery(CFG,job(),'failed',NOW)
    final=state();final['companies'][CFG['name']]={'seen_jobs':{job().id:{'first_seen':NOW.isoformat(),'last_seen':NOW.isoformat(),'alerted':True}}}
    shadow.finish(final,NOW)
    assert 'BLOCKED_ACK_PARITY' in shadow.report()['gates']


def test_optional_leads_are_stored_before_confirmation_and_never_send_themselves(shadow):
    from src.public_feeds import FeedLead,LeadConfirmation
    lead=FeedLead('x','feed','https://example.com/feed','1','Example Labs','Engineer','US',job().url,NOW,'f'*64)
    shadow.leads([lead]);assert shadow.store.stats()['jobs']==0
    capture(shadow,[job()])
    confirmation=LeadConfirmation('feed','x',job().id,job().url,CFG['name'],NOW)
    assert shadow.confirm(lead,CFG,confirmation,now=NOW)
    assert shadow.store.leads()[0]['official_job_id'] is not None
    assert shadow.report()['feed_confirmed_count']==1 and shadow.report()['notifier_ack_count']==0


def test_ambiguous_official_requisitions_keep_feed_lead_unconfirmed(shadow):
    from src.public_feeds import FeedLead,LeadConfirmation
    a=job(official_req_id='R1');b=job('2',url=a.url,official_req_id='R2')
    lead=FeedLead('x','feed','https://example.com/feed','1','Example Labs','Engineer','US',a.url,NOW,'f'*64)
    shadow.leads([lead]);capture(shadow,[a,b])
    confirmation=LeadConfirmation('feed','x',a.id,a.url,CFG['name'],NOW)
    assert not shadow.confirm(lead,CFG,confirmation,now=NOW)
    assert shadow.store.leads()[0]['official_job_id'] is None


def test_retained_snapshot_lookup_is_indexed_once_per_source(shadow):
    rows=[job(str(i)) for i in range(100)];capture(shadow,rows)
    statements=[];shadow.store.db.set_trace_callback(statements.append)
    shadow.replay_filter(CFG,rows,[])
    shadow.project(CFG,[],state(),freshness_hours=48,now=NOW)
    lookups=[sql for sql in statements if sql.startswith('SELECT') and 'observations' in sql]
    assert len(lookups)<=5


def test_legacy_cli_starts_without_optional_crypto_package(tmp_path):
    import subprocess,sys,os
    program='''import builtins,runpy,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
 if name.startswith('cryptography'):raise ModuleNotFoundError('optional transport unavailable')
 return original(name,*args,**kwargs)
builtins.__import__=guarded
sys.argv=['main.py','validate-config']
runpy.run_path('main.py',run_name='__main__')
'''
    result=subprocess.run([sys.executable,'-c',program],capture_output=True,text=True,
        env={**os.environ,'JOBBIE_CATALOGUE_MODE':'off','DISCORD_WEBHOOK_URL':''})
    assert result.returncode==0,result.stderr
    assert 'Config is valid' in result.stdout


def test_prior_failed_window_does_not_fabricate_or_permanently_block_new_real_window():
    records=[];receipts=[]
    for i in range(6):
        when=NOW+timedelta(hours=i*24);good=i>=2
        receipts.append({'id':i+1,'event':'schedule','head_branch':'main','head_sha':'a'*40,'status':'completed','conclusion':'success' if good else 'failure','run_started_at':when.isoformat(),'updated_at':(when+timedelta(minutes=5)).isoformat()})
        records.append({'run_id':str(i+1),'origin':'schedule','head_sha':'a'*40,'started_at':when.isoformat(),'finished_at':(when+timedelta(minutes=5)).isoformat(),'parity_ok':good,'custody_verified':True})
    result=evidence_gate(records,github_runs=receipts,owner_approval=None,rollback_proof=True)
    assert result['shadow_hours']>=72 and result['window_first_run_id']=='3'
    assert result['gates']==['BLOCKED_APPROVAL']
    assert result['invalid_run_ids']==['1','2']


def test_legacy_projection_history_is_lossless_and_compact(shadow):
    from src.catalogue_shadow import legacy_snapshot,digest,compact
    value=state();value['companies']['Example Labs']={'seen_jobs':{
        str(i):{'first_seen':NOW.isoformat(),'last_seen':NOW.isoformat(),'alerted':False,'baseline_suppressed':True} for i in range(1000)}}
    shadow._retain_legacy(value,NOW);sha=digest(legacy_snapshot(value))
    assert shadow.retained_legacy(sha)==legacy_snapshot(value)
    stored=shadow.store.db.execute('SELECT length(payload) FROM legacy_history WHERE sha=?',(sha,)).fetchone()[0]
    assert stored<len(compact(legacy_snapshot(value)).encode())//4

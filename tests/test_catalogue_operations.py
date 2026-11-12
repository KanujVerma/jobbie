"""Operational stages use synthetic cache copies; never production window evidence."""
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace

from cryptography.fernet import Fernet
from src.catalogue import Catalogue
from src.catalogue_operations import cmd_shadow
from src.catalogue_shadow import Shadow
from src.storage import _empty_state


def args(tmp_path,operation,**changes):
    return SimpleNamespace(operation=operation,directory=str(tmp_path/'private'),checkpoint=str(tmp_path/'checkpoint.json'),
        legacy=str(tmp_path/'seen.json'),health=str(tmp_path/'health.json'),cache_hit='false',cache_usage=None,
        allow_bootstrap=False,approval_comment_id=None,**changes)


def test_plan_is_readonly_and_missing_secret_cannot_bootstrap(tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_OUTPUT',str(tmp_path/'output'))
    monkeypatch.delenv('JOBBIE_CATALOGUE_KEY',raising=False)
    assert cmd_shadow(args(tmp_path,'plan'))==0
    assert not (tmp_path/'private').exists()
    value=args(tmp_path,'restore');value.allow_bootstrap=True
    assert cmd_shadow(value)==1
    assert not (tmp_path/'private/jobs.sqlite').exists()
    assert json.loads((tmp_path/'health.json').read_text())['gates']==['BLOCKED_SECRET']


def test_malformed_checkpoint_does_not_authorize_new_database(tmp_path,monkeypatch):
    monkeypatch.setenv('JOBBIE_CATALOGUE_KEY',Fernet.generate_key().decode())
    (tmp_path/'checkpoint.json').write_text('{bad retained data')
    value=args(tmp_path,'restore');value.allow_bootstrap=True
    assert cmd_shadow(value)==1 and not (tmp_path/'private/jobs.sqlite').exists()
    assert (tmp_path/'checkpoint.json').read_text()=='{bad retained data'


def test_synthetic_transport_cycle_proves_stage_gates_and_keeps_legacy(tmp_path,monkeypatch):
    key=Fernet.generate_key().decode();monkeypatch.setenv('JOBBIE_CATALOGUE_KEY',key)
    legacy=tmp_path/'seen.json';legacy.write_text(json.dumps(_empty_state()));before=legacy.read_bytes()
    value=args(tmp_path,'restore');value.allow_bootstrap=True
    assert cmd_shadow(value)==0
    now=datetime.now(timezone.utc)
    with Catalogue(tmp_path/'private/jobs.sqlite') as store:
        with Shadow(store,'fixture-run',now,_empty_state(),filters={},origin='fixture',config_sha='a'*64) as shadow:
            shadow.finish(_empty_state(),now)
    usage=tmp_path/'usage.json';usage.write_text(json.dumps({'active_caches_size_in_bytes':0,'tier':'synthetic'}))
    value=args(tmp_path,'seal');value.cache_usage=str(usage)
    assert cmd_shadow(value)==0
    assert cmd_shadow(args(tmp_path,'probe-prepare'))==0
    assert not (tmp_path/'private/sealed.bin').exists()
    # Explicit offline simulation of a remote cache restore, not live proof.
    shutil.copyfile(tmp_path/'private/probe-retained.bin',tmp_path/'private/sealed.bin')
    value=args(tmp_path,'publish');value.cache_hit='false'
    assert cmd_shadow(value)==1 and not (tmp_path/'checkpoint.json').exists()
    value.cache_hit='true';assert cmd_shadow(value)==0
    cp=json.loads((tmp_path/'checkpoint.json').read_text())
    assert cp['rollback_verified'] is True
    assert legacy.read_bytes()==before
    assert key not in (tmp_path/'health.json').read_text()
    second=tmp_path/'second';second.mkdir()
    restore=args(tmp_path,'restore');restore.directory=str(second);restore.cache_hit='false'
    assert cmd_shadow(restore)==1 and not (second/'jobs.sqlite').exists()
    shutil.copyfile(tmp_path/'private/sealed.bin',second/'sealed.bin')
    restore.cache_hit='true';assert cmd_shadow(restore)==0
    with Catalogue(second/'jobs.sqlite',readonly=True) as store:
        assert store.stats()['runs']==1


def test_audit_recent_window_is_independent_of_more_than_1000_retained_runs(tmp_path,monkeypatch):
    import base64
    from datetime import timedelta
    import src.catalogue_operations as operations
    from src.catalogue_checkpoint import seal
    key=Fernet.generate_key();legacy=tmp_path/'seen.json';legacy.write_text(json.dumps(_empty_state()))
    db=tmp_path/'db.sqlite';now=datetime.now(timezone.utc)
    with Catalogue(db,create=True) as store:
        with store.db:
            for i in range(1001):
                when=now-timedelta(days=30)+timedelta(minutes=i*15);rid=str(1000+i)
                store.db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(rid,when.isoformat(),'schedule','a'*40,(when+timedelta(minutes=5)).isoformat()))
                store.db.execute('INSERT INTO shadow_runs VALUES(?,?,?,?,?,?)',(rid,'b'*64,'c'*64,'d'*64,'{"parity_ok":false}','degraded'))
        with Shadow(store,'9000001.1',now,_empty_state(),filters={},origin='fixture',head_sha='a'*40,config_sha='b'*64) as shadow:shadow.finish(_empty_state(),now)
    cipher=tmp_path/'sealed.bin';cp=seal(db,cipher,key,legacy_path=legacy);cp.update(rollback_verified=True,cache_roundtrip_verified=True)
    calls=[]
    def primary(path,params=None):
        calls.append((path,params))
        if path.endswith('/runs'):
            start=datetime.fromisoformat(params['created'][2:])
            if start<now-timedelta(hours=98):
                # The old implementation keeps asking for all old history and
                # exhausts its10-page cap, despite the healthy recent interval.
                return {'workflow_runs':[{'id':i} for i in range(100)]}
            return {'workflow_runs':[]}
        if path.endswith('/jobs'):return {'jobs':[]}
        raise AssertionError(path)
    monkeypatch.setattr(operations,'_primary',primary)
    result=operations._audit(cp,cipher,key,None)
    assert 'BLOCKED_72H_EVIDENCE' in result['gates']  # fixture data never qualifies
    queries=[p for path,p in calls if path.endswith('/runs')]
    assert len(queries)==1 and datetime.fromisoformat(queries[0]['created'][2:])>=now-timedelta(hours=98)
    with Catalogue(db,readonly=True) as store:assert store.stats()['runs']==1002

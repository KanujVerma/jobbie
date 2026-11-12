"""Encrypted cache custody never reseeds missing ledgers or publishes plaintext."""
import json
from datetime import datetime,timezone
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from src.catalogue import Catalogue,CatalogueError
from src.catalogue_checkpoint import seal,unseal,publish_checkpoint,rollback_check,cache_budget
from src.catalogue_shadow import Shadow
from src.storage import _empty_state

NOW=datetime(2026,11,12,tzinfo=timezone.utc)


@pytest.fixture
def bundle(tmp_path):
    legacy=tmp_path/'seen.json';legacy.write_text(json.dumps(_empty_state()))
    db=tmp_path/'db.sqlite'
    with Catalogue(db,create=True) as store:
        with Shadow(store,'123.1',NOW,_empty_state(),filters={},origin='fixture',head_sha='a'*40,config_sha='b'*64) as monitor:
            monitor.finish(_empty_state(),NOW)
    return db,legacy,Fernet.generate_key()


def test_encrypted_roundtrip_preserves_uuid_rows_and_legacy_bytes(bundle,tmp_path):
    db,legacy,key=bundle;before=legacy.read_bytes()
    cp=seal(db,tmp_path/'sealed.bin',key,legacy_path=legacy)
    assert b'SQLite format' not in (tmp_path/'sealed.bin').read_bytes()
    unseal(cp,tmp_path/'sealed.bin',tmp_path/'restored.sqlite',key)
    with Catalogue(tmp_path/'restored.sqlite',readonly=True) as restored:
        assert restored.stats()['runs']==1
    proof=rollback_check(cp,tmp_path/'sealed.bin',key,legacy)
    assert proof['legacy_unchanged'] and proof['cipher_roundtrip']
    assert legacy.read_bytes()==before


def test_wrong_key_tamper_missing_cipher_or_existing_destination_never_reseeds(bundle,tmp_path):
    db,legacy,key=bundle;cipher=tmp_path/'sealed.bin';cp=seal(db,cipher,key,legacy_path=legacy)
    missing=tmp_path/'missing.sqlite'
    with pytest.raises(CatalogueError):unseal(cp,cipher,missing,Fernet.generate_key())
    assert not missing.exists()
    data=cipher.read_bytes();cipher.write_bytes(data[:-4]+b'bad!')
    with pytest.raises(CatalogueError):unseal(cp,cipher,missing,key)
    assert not missing.exists()
    cipher.write_bytes(data)
    with pytest.raises(CatalogueError):unseal(cp,cipher,db,key)
    with pytest.raises(CatalogueError):unseal(cp,tmp_path/'absent.bin',missing,key)
    assert not missing.exists()


def test_checkpoint_publish_requires_remote_roundtrip_and_unchanged_legacy(bundle,tmp_path):
    db,legacy,key=bundle;cipher=tmp_path/'sealed.bin';cp=seal(db,cipher,key,legacy_path=legacy)
    dest=tmp_path/'checkpoint.json'
    with pytest.raises(CatalogueError):publish_checkpoint(cp,dest,cipher,legacy_path=legacy,cache_hit=False)
    assert not dest.exists()
    publish_checkpoint(cp,dest,cipher,legacy_path=legacy,cache_hit=True)
    assert json.loads(dest.read_text())['cache_key']==cp['cache_key']
    legacy.write_text('changed retained ledger')
    with pytest.raises(CatalogueError):publish_checkpoint(cp,tmp_path/'other.json',cipher,legacy_path=legacy,cache_hit=True)


def test_cache_budget_uses_included_allowance_without_changing_paid_settings():
    assert cache_budget(155096679,1000000)
    assert not cache_budget(8*1024**3,1000000)
    assert not cache_budget(None,1000000)


def test_cipher_and_decompression_bounds_are_enforced(bundle,tmp_path,monkeypatch):
    import src.catalogue_checkpoint as module
    db,legacy,key=bundle;cipher=tmp_path/'sealed.bin'
    monkeypatch.setattr(module,'MAX_CIPHER_BYTES',10)
    with pytest.raises(CatalogueError):seal(db,cipher,key,legacy_path=legacy)
    assert not cipher.exists()


def test_explicit_v1_migration_keeps_backup_and_source_history(tmp_path):
    import sqlite3
    from src.models import Job
    db=tmp_path/'db.sqlite'
    with Catalogue(db,create=True) as store:
        store.start_run('original',NOW)
        record=Job('id','Example','Engineer','US',None,None,'https://example.com/jobs/1',
                   'fixture',None,NOW,'software','unknown','normal',(),source_job_id='1')
        store.observe_scan('original','source',{'name':'Example'},[record],status='complete',observed_at=NOW)
        identity=store.query()[0]['job_id']
        store.db.executescript('DROP TABLE scan_memberships; DROP TABLE observation_spans; DROP INDEX observation_content; ALTER TABLE source_state DROP COLUMN latest_observation_id; ALTER TABLE source_state DROP COLUMN last_listing_at; ALTER TABLE source_state DROP COLUMN adapter_posted_at; DROP TABLE shadow_runs; DROP TABLE shadow_sources; DROP TABLE shadow_delivery; DROP TABLE legacy_history; DROP INDEX observation_snapshot; DROP INDEX snapshot_legacy_id; PRAGMA user_version=1;')
    before=db.read_bytes()
    with pytest.raises(CatalogueError):Catalogue(db)
    assert db.read_bytes()==before
    with Catalogue(db,migrate=True) as store:
        assert store.query()[0]['job_id']==identity and len(store.history())==1
    with sqlite3.connect(tmp_path/'db.sqlite.v1-backup') as backup:
        assert backup.execute('PRAGMA user_version').fetchone()[0]==1
        assert backup.execute('SELECT job_id FROM jobs').fetchone()[0]==identity
        assert backup.execute('SELECT count(*) FROM observations').fetchone()[0]==1


def test_interrupted_shadow_can_be_retained_only_as_incomplete_evidence(tmp_path):
    legacy=tmp_path/'seen.json';legacy.write_text(json.dumps(_empty_state()));key=Fernet.generate_key()
    db=tmp_path/'db.sqlite'
    with Catalogue(db,create=True) as store:
        with Shadow(store,'123.1',NOW,_empty_state(),filters={},origin='fixture',config_sha='b'*64):pass
    cipher=tmp_path/'sealed.bin'
    with pytest.raises(CatalogueError):seal(db,cipher,key,legacy_path=legacy)
    cp=seal(db,cipher,key,legacy_path=legacy,allow_incomplete=True,expected_run_id='123.1')
    assert cp['complete_run'] is False
    with pytest.raises(CatalogueError):seal(db,tmp_path/'other.bin',key,legacy_path=legacy,allow_incomplete=True,expected_run_id='124.1')


def make_original_v1(path):
    import sqlite3,hashlib,uuid
    from src.catalogue import normalized_snapshot,compact
    from src.models import Job
    schema=Path('tests/fixtures/catalogue-v1-schema.sql').read_text()
    value=Job('Example::workday::1','Example','Engineer','US',None,None,'https://example.com/jobs/1','workday',NOW,NOW,'Synthetic source','unknown','normal',(),source_job_id='1')
    payload=compact(normalized_snapshot(value,{'name':'Example','enabled':True}));sha=hashlib.sha256(payload.encode()).hexdigest();uid=str(uuid.uuid4())
    with sqlite3.connect(path) as db:
        db.executescript(schema);db.execute('PRAGMA user_version=1')
        db.executemany('INSERT INTO meta VALUES(?,?)',[('catalogue_uuid',uid),('identity_version','1')])
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)',('stable-job','example',NOW.isoformat(),NOW.isoformat(),'open'))
        db.execute('INSERT INTO snapshots VALUES(?,?)',(sha,payload))
        for run in ['first','second']:
            db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(run,NOW.isoformat(),'fixture',None,NOW.isoformat()))
            db.execute('INSERT INTO scans VALUES(?,?,?,?,?,?,?)',(run,'source','example','complete',NOW.isoformat(),2,0))
            for _ in range(2):db.execute('INSERT INTO observations(run_id,source_id,source_record_id,job_id,snapshot_sha,observed_at) VALUES(?,?,?,?,?,?)',(run,'source','1','stable-job',sha,NOW.isoformat()))
        db.execute('INSERT INTO source_state VALUES(?,?,?,?,?)',('stable-job','source','1','open',NOW.isoformat()))
    return uid


def test_real_v1_layout_migration_keeps_duplicate_logical_history_and_adapter_context(tmp_path):
    path=tmp_path/'v1.sqlite';uid=make_original_v1(path)
    with Catalogue(path,migrate=True) as store:
        assert store.db.execute("SELECT value FROM meta WHERE key='catalogue_uuid'").fetchone()[0]==uid
        assert store.db.execute('SELECT count(*) FROM observations').fetchone()[0]==4
        rows=store.history();assert len(rows)==4 and {r['run_id'] for r in rows}=={'first','second'}
        assert all(r['snapshot']['adapter_posted_at']==NOW.isoformat() for r in rows)
        assert store.query()[0]['job_id']=='stable-job'


def test_late_migration_failure_rolls_back_original_bytes(tmp_path,monkeypatch):
    path=tmp_path/'v1.sqlite';make_original_v1(path);before=path.read_bytes()
    def fail(self):raise OSError('synthetic migration interruption')
    monkeypatch.setattr(Catalogue,'_backfill_history',fail)
    with pytest.raises(CatalogueError):Catalogue(path,migrate=True)
    assert path.read_bytes()==before
    assert (tmp_path/'v1.sqlite.v1-backup').exists()


def test_retention_removes_only_redundant_owned_copies_preserving_current_parent(bundle,tmp_path):
    from datetime import timedelta
    from src.catalogue_checkpoint import redundant_transport_ids
    db,legacy,key=bundle;cp=seal(db,tmp_path/'sealed.bin',key,legacy_path=legacy)
    cp.update(cache_roundtrip_verified=True,rollback_verified=True,parent_cipher_sha256='f'*64)
    def cache(n,cache_key):return {'id':n,'key':cache_key,'ref':'refs/heads/main','created_at':(NOW+timedelta(minutes=n)).isoformat()}
    prefix='jobbie-catalogue-v2-'+cp['catalogue_uuid']+'-'
    rows=[cache(n,prefix+f'{n}.1-'+f'{n:016x}') for n in range(1,9)]
    rows+=[cache(100,cp['cache_key']),{**cache(101,prefix+'old-parent-'+'f'*16),'created_at':(NOW-timedelta(days=3)).isoformat()},cache(200,'pip-unrelated'),
           {**cache(201,prefix+'201.1-'+'a'*16),'ref':'refs/pull/1/merge'}]
    deleted=redundant_transport_ids(cp,rows)
    assert set(deleted)=={1,2,3,4,5}
    assert 100 not in deleted and 101 not in deleted and 200 not in deleted and 201 not in deleted
    with pytest.raises(CatalogueError):redundant_transport_ids(cp,[r for r in rows if r['id']!=100])

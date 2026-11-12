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

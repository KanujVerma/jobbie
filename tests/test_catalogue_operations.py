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

"""Bounded authenticated SQLite transport. Never cache plaintext or reset custody."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
import uuid
import zlib
from datetime import datetime,timezone
from pathlib import Path

from src.catalogue import Catalogue,CatalogueError,SCHEMA_VERSION,MAX_DB_BYTES,compact

EPOCH='p2-c2-v2-20261112'
MAX_COMPRESSED_BYTES=16*1024*1024
MAX_CIPHER_BYTES=24*1024*1024
MAX_METADATA_BYTES=16384
CACHE_BUDGET_BYTES=8*1024**3  # Below the documented included10GiB; never opt into paid settings.
_FIELDS={'schema_version','epoch','catalogue_uuid','run_id','config_sha256','code_sha256',
         'db_sha256','legacy_file_sha256','parent_cipher_sha256','sealed_at'}


def file_sha(path):
    result=hashlib.sha256()
    with open(path,'rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def code_sha():
    root=Path(__file__).resolve().parent.parent
    names=['main.py','requirements.txt','requirements-catalogue.txt','.github/workflows/job-alerts.yml',
           *sorted(str(p.relative_to(root)) for p in (root/'src').rglob('*.py'))]
    return hashlib.sha256(compact({p:file_sha(root/p) for p in names}).encode()).hexdigest()


def _read(path,maximum):
    path=Path(path)
    if path.is_symlink():raise CatalogueError('checkpoint symlink rejected')
    with path.open('rb') as file:raw=file.read(maximum+1)
    if len(raw)>maximum:raise CatalogueError('checkpoint exceeds bound')
    return raw


def _write(path,raw):
    path=Path(path)
    if path.is_symlink():raise CatalogueError('checkpoint symlink rejected')
    fd,name=tempfile.mkstemp(prefix='.catalogue-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as file:file.write(raw);file.flush();os.fsync(file.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)  # Only this operation's temporary file.


def _cache_key(cp):
    return 'jobbie-catalogue-v2-'+cp['catalogue_uuid']+'-'+cp['run_id']+'-'+cp['cipher_sha256'][:16]


def validate_checkpoint(cp):
    if not isinstance(cp,dict) or set(cp)-(_FIELDS|{'cipher_sha256','cache_key','cache_roundtrip_verified','rollback_verified'}):raise CatalogueError('invalid checkpoint metadata')
    if not (_FIELDS|{'cipher_sha256','cache_key'})<=cp.keys():raise CatalogueError('incomplete checkpoint metadata')
    if type(cp['schema_version']) is not int or cp['schema_version']!=SCHEMA_VERSION or cp['epoch']!=EPOCH:raise CatalogueError('unsupported checkpoint epoch')
    try:uuid.UUID(cp['catalogue_uuid'])
    except (ValueError,TypeError,AttributeError) as error:raise CatalogueError('invalid checkpoint identity') from error
    if not isinstance(cp['run_id'],str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',cp['run_id']):raise CatalogueError('invalid checkpoint run')
    for field in ['config_sha256','code_sha256','db_sha256','legacy_file_sha256','cipher_sha256']:
        if not isinstance(cp[field],str) or not re.fullmatch(r'[0-9a-f]{64}',cp[field]):raise CatalogueError('invalid checkpoint digest')
    if cp['parent_cipher_sha256'] is not None and not re.fullmatch(r'[0-9a-f]{64}',cp['parent_cipher_sha256']):raise CatalogueError('invalid parent checkpoint')
    if cp['cache_key']!=_cache_key(cp):raise CatalogueError('checkpoint cache key mismatch')
    return cp


def read_checkpoint(path):
    try:return validate_checkpoint(json.loads(_read(path,MAX_METADATA_BYTES)))
    except (OSError,ValueError,TypeError) as error:raise CatalogueError('cannot read retained checkpoint') from error


def seal(db_path,cipher_path,key,*,legacy_path,parent=None):
    from cryptography.fernet import Fernet
    cipher_path=Path(cipher_path)
    if cipher_path.exists():raise CatalogueError('refusing to replace a retained sealed snapshot')
    if parent is not None:validate_checkpoint(parent)
    with Catalogue(db_path,readonly=True) as store:
        uid=store.db.execute("SELECT value FROM meta WHERE key='catalogue_uuid'").fetchone()[0]
        last=store.db.execute("SELECT * FROM shadow_runs ORDER BY rowid DESC LIMIT 1").fetchone()
        if last is None or last['status']=='running':raise CatalogueError('unfinished shadow run cannot publish')
        if parent and parent['catalogue_uuid']!=uid:raise CatalogueError('checkpoint lineage mismatch')
        if parent:
            restored=store.db.execute("SELECT value FROM meta WHERE key='restored_cipher_sha256'").fetchone()
            if not restored or restored[0]!=parent['cipher_sha256']:raise CatalogueError('retained database is not the exact parent checkpoint')
        fd,scratch=tempfile.mkstemp(suffix='.sqlite',dir=cipher_path.parent);os.close(fd)
        try:
            with sqlite3.connect(scratch) as target:store.db.backup(target)
            raw=_read(scratch,MAX_DB_BYTES);compressed=zlib.compress(raw,6)
            if len(compressed)>MAX_COMPRESSED_BYTES:raise CatalogueError('compressed catalogue exceeds transport bound')
            cp={'schema_version':SCHEMA_VERSION,'epoch':EPOCH,'catalogue_uuid':uid,'run_id':last['run_id'],
                'config_sha256':last['config_sha'],'code_sha256':code_sha(),'db_sha256':hashlib.sha256(raw).hexdigest(),
                'legacy_file_sha256':file_sha(legacy_path),'parent_cipher_sha256':parent['cipher_sha256'] if parent else None,
                'sealed_at':datetime.now(timezone.utc).isoformat()}
            token=Fernet(key).encrypt(compact(cp).encode()+b'\n'+compressed)
            if len(token)>MAX_CIPHER_BYTES:raise CatalogueError('encrypted catalogue exceeds transport bound')
            cp['cipher_sha256']=hashlib.sha256(token).hexdigest();cp['cache_key']=_cache_key(cp)
            validate_checkpoint(cp);_write(cipher_path,token);return cp
        finally:
            if os.path.exists(scratch):os.unlink(scratch)


def unseal(checkpoint,cipher_path,destination,key,*,remote=False):
    from cryptography.fernet import Fernet
    cp=validate_checkpoint(checkpoint);destination=Path(destination)
    if destination.exists() or destination.is_symlink():raise CatalogueError('refusing to replace retained catalogue')
    try:
        token=_read(cipher_path,MAX_CIPHER_BYTES)
        if hashlib.sha256(token).hexdigest()!=cp['cipher_sha256']:raise CatalogueError('ciphertext digest mismatch')
        envelope=Fernet(key).decrypt(token);header,compressed=envelope.split(b'\n',1)
        if len(header)>MAX_METADATA_BYTES or len(compressed)>MAX_COMPRESSED_BYTES:raise CatalogueError('invalid transport bound')
        metadata=json.loads(header)
        if metadata!={k:cp[k] for k in _FIELDS}:raise CatalogueError('authenticated checkpoint metadata mismatch')
        decoder=zlib.decompressobj();raw=decoder.decompress(compressed,MAX_DB_BYTES+1)
        if len(raw)>MAX_DB_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:raise CatalogueError('invalid/bounded compressed catalogue')
        if hashlib.sha256(raw).hexdigest()!=cp['db_sha256']:raise CatalogueError('database digest mismatch')
        fd,scratch=tempfile.mkstemp(suffix='.sqlite',dir=destination.parent)
        try:
            with os.fdopen(fd,'wb') as file:file.write(raw);file.flush();os.fsync(file.fileno())
            with Catalogue(scratch) as store:
                uid=store.db.execute("SELECT value FROM meta WHERE key='catalogue_uuid'").fetchone()[0]
                if uid!=cp['catalogue_uuid']:raise CatalogueError('database identity mismatch')
                with store.db:
                    store.db.execute("INSERT INTO meta VALUES('restored_cipher_sha256',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(cp['cipher_sha256'],))
                    store.db.execute('INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('custody:'+cp['run_id'],'remote_exact_digest_verified' if remote else 'local_cipher_digest_verified'))
            os.replace(scratch,destination)
        finally:
            if os.path.exists(scratch):os.unlink(scratch)
    except CatalogueError:raise
    except Exception as error:raise CatalogueError('cannot authenticate retained catalogue') from error
    return cp


def publish_checkpoint(cp,destination,cipher_path,*,legacy_path,cache_hit):
    validate_checkpoint(cp)
    if cache_hit is not True:raise CatalogueError('remote exact-cache roundtrip is required')
    if hashlib.sha256(_read(cipher_path,MAX_CIPHER_BYTES)).hexdigest()!=cp['cipher_sha256']:raise CatalogueError('remote ciphertext mismatch')
    if file_sha(legacy_path)!=cp['legacy_file_sha256']:raise CatalogueError('legacy ledger changed after seal')
    destination=Path(destination)
    if destination.exists():
        previous=read_checkpoint(destination)
        if cp['parent_cipher_sha256']!=previous['cipher_sha256']:raise CatalogueError('checkpoint parent changed')
    elif cp['parent_cipher_sha256'] is not None:raise CatalogueError('parent checkpoint missing')
    result={**cp,'cache_roundtrip_verified':True};_write(destination,(compact(result)+'\n').encode());return result


def cache_budget(active_bytes,new_bytes):
    return type(active_bytes) is int and active_bytes>=0 and type(new_bytes) is int and 0<new_bytes<=MAX_CIPHER_BYTES and active_bytes+new_bytes<CACHE_BUDGET_BYTES


def rollback_check(cp,cipher_path,key,legacy_path):
    before=file_sha(legacy_path)
    with tempfile.TemporaryDirectory(prefix='jobbie-rollback-') as directory:
        destination=Path(directory)/'retained.sqlite';unseal(cp,cipher_path,destination,key)
        with Catalogue(destination,readonly=True) as store:
            stats=store.stats();uid=store.db.execute("SELECT value FROM meta WHERE key='catalogue_uuid'").fetchone()[0]
    return {'cipher_roundtrip':True,'legacy_unchanged':before==file_sha(legacy_path),
            'delivery_authority':'legacy_json','catalogue_uuid':uid,'stats':stats,
            'legacy_sha256':before,'cache_custody_claimed':False}

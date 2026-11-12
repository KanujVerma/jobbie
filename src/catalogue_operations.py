"""Explicit shadow transport/verification CLI. No sends or automatic cutover."""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

from src.catalogue import Catalogue,CatalogueError,compact
from src.catalogue_checkpoint import (EPOCH,_read,_write,read_checkpoint,seal,unseal,publish_checkpoint,
    rollback_check,cache_budget,code_sha,MAX_METADATA_BYTES,MAX_CIPHER_BYTES,redundant_transport_ids,validate_checkpoint)
from src.catalogue_shadow import evidence_gate,digest,config_fingerprint


def add_shadow_parser(subparsers):
    parser=subparsers.add_parser('catalogue-shadow',help='Encrypted shadow custody/audit; legacy delivery authority')
    _arguments(parser)


def _arguments(parser):
    parser.add_argument('operation',choices=['plan','restore','seal','probe-prepare','publish','rollback','audit','prune-transport'])
    parser.add_argument('--directory',default='state/catalogue-shadow')
    parser.add_argument('--checkpoint',default='state/catalogue_shadow_checkpoint.json')
    parser.add_argument('--legacy',default='state/seen_jobs.json')
    parser.add_argument('--health',default='state/catalogue_shadow_health.json')
    parser.add_argument('--cache-hit',choices=['true','false'],default='false')
    parser.add_argument('--cache-usage')
    parser.add_argument('--allow-bootstrap',action='store_true')
    parser.add_argument('--allow-incomplete',action='store_true')
    parser.add_argument('--approval-comment-id',type=int)


def _output(**values):
    path=os.getenv('GITHUB_OUTPUT')
    if path:
        with open(path,'a') as file:
            for key,value in values.items():
                rendered=str(value).lower() if isinstance(value,bool) else str(value)
                if '\n' in rendered or '\r' in rendered:raise CatalogueError('unsafe action output')
                file.write(key+'='+rendered+'\n')


def _primary(path,params=None):
    # Fixed repository API paths only; response/job text is never an instruction.
    command=['gh','api','--method','GET',path]
    for key,value in (params or {}).items():command+=['-f',f'{key}={value}']
    result=subprocess.run(command,capture_output=True,timeout=30,check=True)
    if len(result.stdout)>16*1024*1024:raise CatalogueError('primary receipt exceeds bound')
    return json.loads(result.stdout)


def _audit(cp,cipher,key,approval_id):
    with tempfile.TemporaryDirectory(prefix='jobbie-audit-') as directory:
        destination=Path(directory)/'retained.sqlite';unseal(cp,cipher,destination,key)
        with Catalogue(destination,readonly=True) as store:
            rows=store._rows('SELECT r.*,s.result FROM runs r JOIN shadow_runs s ON s.run_id=r.run_id ORDER BY r.started_at')
            custody=dict(store.db.execute("SELECT key,value FROM meta WHERE key LIKE 'custody:%'"))
    first=min(datetime.fromisoformat(r['started_at']) for r in rows)
    receipts=[]
    for page in range(1,11):
        response=_primary('repos/KanujVerma/jobbie/actions/workflows/job-alerts.yml/runs',
            {'event':'schedule','branch':'main','created':'>='+(first-timedelta(hours=1)).isoformat(),'per_page':100,'page':page})
        batch=response.get('workflow_runs')
        if not isinstance(batch,list):raise CatalogueError('invalid primary schedule receipt')
        receipts.extend(batch)
        if len(batch)<100:break
    else:raise CatalogueError('bounded primary receipt window incomplete')
    # A completed publish step proves the latest public checkpoint's real
    # save/restore roundtrip, rather than a caller-provided fixture timestamp.
    run_number=cp['run_id'].split('.')[0]
    if not run_number.isdigit():jobs={'jobs':[]}
    else:jobs=_primary(f'repos/KanujVerma/jobbie/actions/runs/{run_number}/jobs',{'per_page':100})
    run_receipt=next((r for r in receipts if str(r.get('id'))==run_number),{})
    published=cp.get('cache_roundtrip_verified') is True and any(
        step.get('name')=='Publish verified catalogue checkpoint' and step.get('conclusion')=='success'
        for job in jobs.get('jobs',[]) if job.get('head_sha')==run_receipt.get('head_sha') and job.get('head_sha')
        for step in job.get('steps',[]))
    stored=[]
    for row in rows:
        report=json.loads(row['result'])
        stored.append({**row,'parity_ok':report.get('parity_ok') is True,
            'code_sha256':report.get('code_sha256'),'config_sha256':report.get('config_sha256'),
            'custody_verified':custody.get('custody:'+row['run_id'])=='remote_exact_digest_verified'
                or (row['run_id']==cp['run_id'] and published)})
    target={'catalogue_uuid':cp['catalogue_uuid'],'checkpoint_sha256':cp['cipher_sha256'],
            'config_sha256':cp['config_sha256'],'code_sha256':cp['code_sha256'],'last_run_id':cp['run_id']}
    approval=None
    if approval_id is not None:
        if approval_id<=0:raise CatalogueError('invalid owner approval reference')
        comment=_primary(f'repos/KanujVerma/jobbie/issues/comments/{approval_id}')
        if comment.get('user',{}).get('login')=='KanujVerma' and len(comment.get('body',''))<=MAX_METADATA_BYTES:
            body=json.loads(comment['body'])
            approval={**body,'verified_owner':'KanujVerma','approved_at':comment['created_at']}
    result=evidence_gate(stored,github_runs=receipts,owner_approval=approval,
        rollback_proof=cp.get('rollback_verified') is True,target=target)
    if cp['code_sha256']!=code_sha():
        result['gates'].append('BLOCKED_CODE_CHANGE');result['cutover_ready']=False
    from src.config import load_config
    if cp['config_sha256']!=config_fingerprint(load_config()):
        result['gates'].append('BLOCKED_CONFIG_CHANGE');result['cutover_ready']=False
    result.update(target=target,activation_performed=False,delivery_authority='legacy_json',
                  verified_by='primary_github_receipts_and_exact_encrypted_checkpoint')
    return result


def cmd_shadow(args):
    directory=Path(args.directory);checkpoint=Path(args.checkpoint);cipher=directory/'sealed.bin'
    database=directory/'jobs.sqlite';pending=directory/'pending.json';operation=args.operation
    try:
        if operation=='plan':
            if checkpoint.exists():
                cp=read_checkpoint(checkpoint);_output(restore=True,cache_key=cp['cache_key'],bootstrap=False)
            else:_output(restore=False,bootstrap=True)
            return 0
        if operation=='probe-prepare':
            if not cipher.is_file() or (directory/'probe-retained.bin').exists():raise CatalogueError('invalid owned probe state')
            cipher.rename(directory/'probe-retained.bin');return 0
        if operation=='prune-transport':
            cp=read_checkpoint(checkpoint)
            remote=_primary('repos/KanujVerma/jobbie/contents/state/catalogue_shadow_checkpoint.json',{'ref':'main'})
            content=remote.get('content','')
            if remote.get('encoding')!='base64' or len(content)>32768:raise CatalogueError('invalid published checkpoint receipt')
            published=validate_checkpoint(json.loads(base64.b64decode(content)))
            if published!=cp:raise CatalogueError('published checkpoint changed; retention skipped')
            copies=[]
            for page in range(1,11):
                response=_primary('repos/KanujVerma/jobbie/actions/caches',{'ref':'refs/heads/main',
                    'key':'jobbie-catalogue-v2-'+cp['catalogue_uuid']+'-','per_page':100,'page':page})
                batch=response.get('actions_caches')
                if not isinstance(batch,list):raise CatalogueError('invalid transport listing')
                copies.extend(batch)
                if len(batch)<100:break
            else:raise CatalogueError('bounded transport listing incomplete')
            ids=redundant_transport_ids(cp,copies)
            for identifier in ids:
                subprocess.run(['gh','api','--method','DELETE',f'repos/KanujVerma/jobbie/actions/caches/{identifier}'],
                    capture_output=True,timeout=30,check=True)
            print(compact({'redundant_transport_copies_removed':len(ids),'canonical_records_removed':0,
                           'current_checkpoint':cp['cipher_sha256']}))
            return 0
        key=os.getenv('JOBBIE_CATALOGUE_KEY','')
        if not key:raise CatalogueError('BLOCKED_SECRET')
        from cryptography.fernet import Fernet
        Fernet(key)  # Validate before creating any database.
        if directory.is_symlink():raise CatalogueError('unsafe private catalogue directory')
        if operation in {'restore','seal'}:directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        if operation=='restore':
            if checkpoint.exists():
                cp=read_checkpoint(checkpoint)
                if args.cache_hit!='true':raise CatalogueError('BLOCKED_CUSTODY')
                unseal(cp,cipher,database,key,remote=True)
                if (directory/'parent.bin').exists():raise CatalogueError('retained parent cipher already exists')
                cipher.rename(directory/'parent.bin')
            else:
                if not args.allow_bootstrap or database.exists() or cipher.exists():raise CatalogueError('initialization is not authorized or custody is ambiguous')
                with Catalogue(database,create=True) as store:
                    with store.db:store.db.execute('INSERT INTO meta VALUES(?,?)',('shadow_epoch',EPOCH))
            _output(mode='shadow');result={'mode':'shadow','delivery_authority':'legacy_json','status':'ready'}
        elif operation=='seal':
            parent=read_checkpoint(checkpoint) if checkpoint.exists() else None
            actual=(os.getenv('GITHUB_ACTIONS')=='true' and os.getenv('GITHUB_WORKFLOW')=='Job Alerts'
                and os.getenv('GITHUB_REPOSITORY','').casefold()=='kanujverma/jobbie' and os.getenv('GITHUB_REF')=='refs/heads/main')
            expected=os.getenv('GITHUB_RUN_ID','')+'.'+os.getenv('GITHUB_RUN_ATTEMPT','1') if actual else None
            cp=seal(database,cipher,key,legacy_path=args.legacy,parent=parent,
                allow_incomplete=getattr(args,'allow_incomplete',False),expected_run_id=expected)
            if not args.cache_usage:raise CatalogueError('primary cache usage receipt required')
            usage=json.loads(_read(args.cache_usage,MAX_METADATA_BYTES))
            if not cache_budget(usage.get('active_caches_size_in_bytes'),cipher.stat().st_size):raise CatalogueError('BLOCKED_STORAGE_BUDGET')
            proof=rollback_check(cp,cipher,key,args.legacy)
            if not proof['legacy_unchanged'] or not proof['cipher_roundtrip']:raise CatalogueError('BLOCKED_ROLLBACK')
            cp['rollback_verified']=True;_write(pending,(compact(cp)+'\n').encode())
            with Catalogue(database,readonly=True) as store:
                row=store.db.execute('SELECT result FROM shadow_runs ORDER BY rowid DESC LIMIT 1').fetchone()
                report=json.loads(row[0])
            result={'mode':'shadow','status':'sealed_pending_remote_roundtrip','checkpoint':cp,'report':report,'rollback':proof,
                    'operational_gates':['BLOCKED_72H_EVIDENCE','BLOCKED_APPROVAL']}
            _output(ready=True,cache_key=cp['cache_key'])
        elif operation=='publish':
            cp=read_checkpoint(pending)
            published=publish_checkpoint(cp,checkpoint,cipher,legacy_path=args.legacy,cache_hit=args.cache_hit=='true')
            result={'mode':'shadow','status':'published','checkpoint':published,'operational_gates':['BLOCKED_72H_EVIDENCE','BLOCKED_APPROVAL']}
            # Preserve last source/parity counts; publish is transport evidence.
            health=Path(args.health)
            if health.exists():result={**json.loads(_read(health,128*1024)),**result}
        elif operation=='rollback':
            cp=read_checkpoint(checkpoint);print(compact(rollback_check(cp,cipher,key,args.legacy)));return 0
        else:
            cp=read_checkpoint(checkpoint);print(json.dumps(_audit(cp,cipher,key,args.approval_comment_id),indent=2));return 0
        _write(Path(args.health),(compact(result)+'\n').encode());print(compact(result));return 0
    except Exception as error:
        _output(mode='off',ready=False)
        known={'BLOCKED_SECRET','BLOCKED_CUSTODY','BLOCKED_STORAGE_BUDGET','BLOCKED_ROLLBACK'}
        gate='BLOCKED_DEPENDENCY' if isinstance(error,ImportError) else str(error) if isinstance(error,CatalogueError) and str(error) in known else 'BLOCKED_CUSTODY'
        if operation not in {'audit','rollback'}:
            result={'mode':'off','status':'blocked','gates':[gate],'stage':operation,
                    'error_type':type(error).__name__,'delivery_authority':'legacy_json'}
            try:_write(Path(args.health),(compact(result)+'\n').encode())
            except Exception:pass
        print('Catalogue shadow operation blocked: '+gate+' '+type(error).__name__,file=sys.stderr)
        return 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();_arguments(parser);sys.exit(cmd_shadow(parser.parse_args()))

"""Auditable shadow decisions. No network, sender or cutover authority."""
from __future__ import annotations

import copy
import hashlib
import json
import zlib
from datetime import datetime,timezone
from pathlib import Path

from src.catalogue import Catalogue,CatalogueError,compact,stamp,employer_key
from src.job_identity import canonical_job_url
from src.storage import normalize_url


def digest(value):return hashlib.sha256(compact(value).encode()).hexdigest()


def legacy_snapshot(state):
    """Only public ledger authority; never copy descriptions/private future fields."""
    companies={}
    for name,company in state.get('companies',{}).items():
        rows={key:{field:value.get(field) for field in ['first_seen','last_seen','alerted','baseline_suppressed','stale_suppressed','cap_suppressed']}
              for key,value in company.get('seen_jobs',{}).items()}
        companies[name]={'seen_jobs':rows}
    return copy.deepcopy({'companies':companies,'alerted_urls':state.get('alerted_urls',{})})


def source_key(config):
    return config['name']+':'+config['adapter']+':'+digest(config.get('config',{}))[:16]


def config_fingerprint(config):
    manifest=config.defaults.get('public_feeds_manifest');manifest_sha=None
    if manifest:
        from src.catalogue_checkpoint import _read
        try:
            if not Path(manifest).is_file():raise CatalogueError('manifest is not a regular file')
            manifest_sha=hashlib.sha256(_read(manifest,1024*1024)).hexdigest()
        except Exception as error:manifest_sha='unreadable:'+type(error).__name__
    return digest({'defaults':config.defaults,'filters':config.filters,'companies':config.companies,'feed_manifest_sha256':manifest_sha})


def ack_ids(state):
    return {(name,key) for name,c in state.get('companies',{}).items()
            for key,value in c.get('seen_jobs',{}).items() if value.get('alerted') is True}


class Shadow:
    def __init__(self,store,run_id,when,state,*,filters,origin='local',head_sha=None,config_sha='unknown',owns_store=False):
        self.store=store;self.run_id=run_id;self.filters=copy.deepcopy(filters);self.owns_store=owns_store
        self.sources={};self.gates=set();self.initial=legacy_snapshot(state);self.initial_acks=ack_ids(self.initial)
        self.started_at=stamp(when);self.finished=False;self.ack_count=0;self.ack_mismatches=0
        from src.catalogue_checkpoint import code_sha
        self.code_sha=code_sha();self.config_sha=config_sha;self.expected_sources=None
        self.outcomes={key:0 for key in ['ack','failed','dedup','capped','skipped']}
        self.lead_count=0;self.feed_confirmations=set();self.feed_confirmation_needs_review=0
        self.row_indexes={};self.current_urls={};self.leads_by_key={};self.confirmed_employers={}
        store.start_run(run_id,when,origin=origin,head_sha=head_sha)
        with store.db:
            store.db.execute('INSERT INTO shadow_runs VALUES(?,?,?,?,?,?)',(run_id,config_sha,digest(self.initial),None,compact(self.report()),'running'))
        self._retain_legacy(self.initial,when)
    def configure_sources(self,keys,when):
        self.expected_sources=set(keys);at=stamp(when)
        with self.store.db:
            for row in self.store._rows("SELECT * FROM source_state WHERE status='open'"):
                if row['source_id'] not in self.expected_sources and row['observed_at']<=at:
                    self.store.db.execute("UPDATE source_state SET status='unknown',observed_at=? WHERE job_id=? AND source_id=? AND source_record_id=?",(at,row['job_id'],row['source_id'],row['source_record_id']))
                    self.store._status(row['job_id'],row['source_id'],'source_scope_inactive','Source scope is not currently enabled; employer closure unknown',at)
    def __enter__(self):return self
    def __exit__(self,*_):
        if self.owns_store:self.store.close()
    def _retain_legacy(self,state,when):
        payload=compact(legacy_snapshot(state));sha=hashlib.sha256(payload.encode()).hexdigest()
        if len(payload.encode())>8*1024*1024:raise CatalogueError('bounded legacy projection exceeds limit')
        with self.store.db:self.store.db.execute('INSERT OR IGNORE INTO legacy_history VALUES(?,?,?,?)',(sha,zlib.compress(payload.encode(),6),stamp(when),sha))
    def retained_legacy(self,sha):
        row=self.store.db.execute('SELECT payload FROM legacy_history WHERE sha=?',(sha,)).fetchone()
        if row is None:raise CatalogueError('legacy projection evidence missing')
        decoder=zlib.decompressobj();raw=decoder.decompress(row[0],8*1024*1024+1)
        if len(raw)>8*1024*1024 or not decoder.eof or decoder.unused_data or hashlib.sha256(raw).hexdigest()!=sha:
            raise CatalogueError('corrupt bounded legacy evidence')
        return json.loads(raw)
    def _save_source(self,key):
        with self.store.db:self.store.db.execute('INSERT INTO shadow_sources VALUES(?,?,?) ON CONFLICT(run_id,source_id) DO UPDATE SET result=excluded.result',(self.run_id,key,compact(self.sources[key])))
    def observe(self,config,jobs,*,status,observed_at):
        key=source_key(config)
        result=self.store.observe_scan(self.run_id,key,config,jobs,status=status,observed_at=observed_at)
        index={}
        for raw in self.store.scan_rows(self.run_id,key):
            row=dict(raw);row['data']=json.loads(row['payload'])
            index.setdefault((row['data']['id'],row['data']['canonical_url']),[]).append(row)
        self.row_indexes[key]=index
        urls={}
        for row in self.store.db.execute('''SELECT ss.job_id,json_extract(s.payload,'$.canonical_url') AS url FROM source_state ss JOIN jobs j ON j.job_id=ss.job_id
            JOIN observations o ON o.id=ss.latest_observation_id
            JOIN snapshots s ON s.sha=o.snapshot_sha WHERE j.employer=? AND ss.status='open' ''',(employer_key(config),)):
            urls.setdefault(row['url'],set()).add(row['job_id'])
        self.current_urls[employer_key(config)]=urls
        self.sources[key]={'company':config['name'],'scan_status':result['status'],'returned_count':len(jobs),'observed':result['observed'],
                           'rejected':result['rejected'],'identity_conflicts':result['conflicts'],
                           'candidate_mismatches':0,'filter_mismatches':0,'comparison_complete':False}
        if result['conflicts'] or result['rejected']:self.gates.add('BLOCKED_IDENTITIES')
        if result['status']!='complete':self.gates.add('BLOCKED_SOURCE_SCAN')
        self._save_source(key);return result
    def _row(self,config,job):
        url=canonical_job_url(job.url)
        rows=self.row_indexes.get(source_key(config),{}).get((job.id,url),[])
        identities={row['job_id'] for row in rows}
        if len(identities)!=1:raise CatalogueError('missing or ambiguous normalized observation')
        return rows[0]
    def replay_filter(self,config,fetched,matched):
        """Re-evaluate retained snapshots, independently of caller match booleans."""
        from src.filtering import apply_filter_pipeline
        actual={(j.id,canonical_job_url(j.url)) for j in matched};replayed=set()
        for job in fetched:
            row=self._row(config,job);data={**row['data'],'_observed_at':row['observed_at']}
            restored=self.store.job_from_snapshot(data)
            passed,_=apply_filter_pipeline(restored,self.filters,config.get('config',{}))
            if passed is not None:replayed.add((job.id,canonical_job_url(job.url)))
        mismatch=len(actual^replayed);key=source_key(config)
        self.sources[key]['filter_mismatches']=mismatch
        if mismatch:self.gates.add('BLOCKED_PARITY')
        self._save_source(key);return mismatch
    def leads(self,leads):
        self.store.observe_leads(self.run_id,leads);self.lead_count=len(leads)
        self.leads_by_key={(lead.source_id,lead.lead_id):lead for lead in leads}
    def confirm(self,lead,config,confirmation,*,now=None):
        current=self.current_urls.get(employer_key(config),{}).get(confirmation.canonical_url,set())
        if len(current)!=1:self._revoke(lead);return False
        rows=self.row_indexes.get(source_key(config),{}).get((confirmation.official_job_id,confirmation.canonical_url),[])
        records={row['source_record_id'] for row in rows}
        if len(records)!=1:self._revoke(lead);return False
        try:self.store.confirm_lead(lead.source_id,lead.lead_id,source_key(config),next(iter(records)),now or datetime.now(timezone.utc))
        except CatalogueError:self.feed_confirmation_needs_review+=1;return False
        self.feed_confirmations.add((lead.source_id,lead.lead_id));self.confirmed_employers[(lead.source_id,lead.lead_id)]=employer_key(config)
        return True
    def _revoke(self,lead):
        with self.store.db:self.store.db.execute('UPDATE leads SET official_job_id=NULL,confirmed_at=NULL WHERE source_id=? AND lead_id=?',(lead.source_id,lead.lead_id))
        self.feed_confirmations.discard((lead.source_id,lead.lead_id));self.feed_confirmation_needs_review+=1
    def project(self,config,matched,state,*,freshness_hours,now):
        """SQL identities + legacy ledger facts, independent candidate algorithm."""
        snapshot=legacy_snapshot(state);before=digest(snapshot);company=config['name']
        self.sources[source_key(config)]['legacy_projection_sha256']=before
        seen=snapshot['companies'].get(company,{}).get('seen_jobs',{})
        # Canonical ACK aliases are linked through stored observations, not titles.
        known_acks=ack_ids(snapshot);acked_identities=set()
        for cname,jid in known_acks:
            for row in self.store.db.execute("SELECT DISTINCT o.job_id FROM observations o JOIN snapshots s ON o.snapshot_sha=s.sha WHERE json_extract(s.payload,'$.company')=? AND json_extract(s.payload,'$.id')=?",(cname,jid)):
                acked_identities.add(row[0])
        canonical_urls={canonical_job_url(url) for url in snapshot['alerted_urls']}
        result=set()
        for job in matched:
            row=self._row(config,job);identity=row['job_id'];entry=seen.get(job.id)
            if identity in acked_identities or canonical_job_url(job.url) in canonical_urls:continue
            if entry:
                if entry.get('alerted') or entry.get('baseline_suppressed'):continue
                first=datetime.fromisoformat(entry['first_seen'])
                if (now-first).total_seconds()>freshness_hours*3600:continue
            result.add(identity)
        if digest(snapshot)!=before:raise CatalogueError('shadow mutated its private legacy copy')
        self._retain_legacy(snapshot,now);return result
    def compare(self,config,matched,legacy_candidates,projection,*,state=None):
        # Legacy raw candidate counts and final canonical groups are both visible.
        effective=[j for j in legacy_candidates if state is None or normalize_url(j.url) not in state.get('alerted_urls',{})]
        actual={self._row(config,j)['job_id'] for j in effective}
        mismatch=len(actual^set(projection));key=source_key(config)
        self.sources[key].update(legacy_candidates=len(legacy_candidates),legacy_effective_groups=len(actual),
            canonical_candidates=len(projection),candidate_mismatches=mismatch,
            only_legacy_candidate_ids=sorted(actual-set(projection))[:50],
            only_canonical_candidate_ids=sorted(set(projection)-actual)[:50],
            duplicate_candidate_records=len(effective)-len(actual),comparison_complete=True)
        if mismatch:self.gates.add('BLOCKED_PARITY')
        self._save_source(key);return self.sources[key]
    def delivery(self,config,job,outcome,when):
        if outcome not in {'ack','failed','dedup','capped','skipped'}:raise CatalogueError('invalid delivery evidence')
        row=self._row(config,job)
        with self.store.db:self.store.db.execute('INSERT INTO shadow_delivery(run_id,source_id,legacy_id,job_id,outcome,observed_at) VALUES(?,?,?,?,?,?)',
            (self.run_id,source_key(config),job.id,row['job_id'],outcome,stamp(when)))
        self.outcomes[outcome]+=1
    def finish(self,state,when,*,summary_acks=0):
        for pair in list(self.feed_confirmations):
            lead=self.leads_by_key[pair];employer=self.confirmed_employers[pair]
            if len(self.current_urls.get(employer,{}).get(canonical_job_url(lead.url),set()))!=1:self._revoke(lead)
        final=legacy_snapshot(state);new_acks=ack_ids(final)-self.initial_acks
        summary=set(summary_acks) if summary_acks else set()
        positive={(self.sources[row['source_id']]['company'],row['legacy_id']) for row in self.store.db.execute("SELECT source_id,legacy_id FROM shadow_delivery WHERE run_id=? AND outcome IN ('ack','dedup')",(self.run_id,))}
        failed={(self.sources[row['source_id']]['company'],row['legacy_id']) for row in self.store.db.execute("SELECT source_id,legacy_id FROM shadow_delivery WHERE run_id=? AND outcome='failed'",(self.run_id,))}
        missing=(positive|summary)-ack_ids(final);unexpected=new_acks-positive-summary
        self.summary_ack_count=len(summary)
        self.ack_count=len(new_acks);self.ack_mismatches=len(missing)+len((failed&new_acks)-summary)+len(unexpected)
        if self.ack_mismatches:self.gates.add('BLOCKED_ACK_PARITY')
        if not self.sources or any(not r['comparison_complete'] for r in self.sources.values()):self.gates.add('BLOCKED_PARITY')
        if self.expected_sources is not None and set(self.sources)!=self.expected_sources:self.gates.add('BLOCKED_SOURCE_ROSTER')
        self.finished=True;self._retain_legacy(final,when)
        with self.store.db:
            self.store.db.execute('UPDATE runs SET finished_at=? WHERE run_id=?',(stamp(when),self.run_id))
            self.store.db.execute('UPDATE shadow_runs SET after_sha=?,result=?,status=? WHERE run_id=?',
                (digest(final),compact(self.report()),'complete' if not self.gates else 'degraded',self.run_id))
        return self.report()
    def report(self):
        return {'run_id':self.run_id,'delivery_authority':'legacy_json','sources':copy.deepcopy(self.sources),
            'ack_count':self.ack_count,'ack_mismatches':self.ack_mismatches,'gates':sorted(self.gates),
            'notifier_ack_count':self.outcomes['ack'],'failed_send_count':self.outcomes['failed'],
            'deduplicated_ack_links':self.outcomes['dedup'],'cap_suppressed_count':self.outcomes['capped'],
            'summary_ack_count':getattr(self,'summary_ack_count',0),
            'feed_lead_count':self.lead_count,'feed_confirmed_count':len(self.feed_confirmations),
            'feed_confirmation_needs_review_count':self.feed_confirmation_needs_review,
            'code_sha256':self.code_sha,'config_sha256':self.config_sha,
            'parity_ok':self.finished and not self.gates,'cutover_approved':False}


def open_shadow(path,mode,run_id,when,state,*,filters,dry_run=False,origin='local',head_sha=None,config_sha='unknown'):
    if mode=='off':return None
    if mode!='shadow':raise CatalogueError('unsupported/unapproved catalogue delivery authority')
    if dry_run:
        if Path(path).exists():
            with Catalogue(path,readonly=True) as existing:store=Catalogue.memory(existing)
        else:store=Catalogue.memory()
    else:store=Catalogue(path)
    try:return Shadow(store,run_id,when,state,filters=filters,origin=origin,head_sha=head_sha,config_sha=config_sha,owns_store=True)
    except Exception:store.close();raise


def _date(value):
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError,TypeError,AttributeError):return None


def evidence_gate(stored,*,github_runs,owner_approval,rollback_proof,target=None):
    """Measure a contiguous healthy suffix of actual ordinary GitHub receipts."""
    candidates=[r for r in stored if _date(r.get('started_at'))]
    earliest=min((_date(r['started_at']) for r in candidates),default=None)
    receipts={str(r['id']):r for r in github_runs if r.get('event')=='schedule' and r.get('head_branch')=='main'
              and r.get('status')=='completed' and _date(r.get('updated_at'))
              and (earliest is None or _date(r['updated_at'])>=earliest)}
    records={};invalid=[]
    for row in candidates:
        raw=str(row.get('run_id',''));parts=raw.split('.');key=parts[0];receipt=receipts.get(key)
        if not receipt:continue
        start,finish=_date(row.get('started_at')),_date(row.get('finished_at'))
        official_start,official_finish=_date(receipt.get('run_started_at')),_date(receipt.get('updated_at'))
        valid=(row.get('origin')=='schedule' and row.get('head_sha')==receipt.get('head_sha') and row.get('parity_ok') is True
               and row.get('custody_verified') is True and receipt.get('conclusion')=='success'
               and receipt.get('run_attempt',1)==1 and (len(parts)==1 or parts[1]=='1')
               and all([start,finish,official_start,official_finish]))
        if valid:valid=0<=(start-official_start).total_seconds()<=1800 and 0<=(finish-start).total_seconds()<=1800 and finish<=official_finish
        if valid and target is not None:
            valid=all(row.get(k)==target.get(k) for k in ['config_sha256','code_sha256'])
        if valid:records[key]=row
        else:invalid.append(key)
    ordered=sorted(receipts,key=lambda k:_date(receipts[k].get('run_started_at')) or datetime.min.replace(tzinfo=timezone.utc))
    suffix=[]
    for key in reversed(ordered):
        if key not in records:break
        suffix.append(key)
    suffix.reverse()
    hours=0.
    if suffix:
        hours=(_date(records[suffix[-1]]['finished_at'])-_date(records[suffix[0]]['started_at'])).total_seconds()/3600
    missing=[key for key in ordered if key not in records]
    gates=[]
    if hours<72:gates.append('BLOCKED_72H_EVIDENCE')
    if not rollback_proof:gates.append('BLOCKED_ROLLBACK')
    required={'catalogue_uuid','checkpoint_sha256','config_sha256','last_run_id'}
    approved=(isinstance(target,dict) and required<=target.keys() and isinstance(owner_approval,dict)
        and owner_approval.get('verified_owner')=='KanujVerma' and owner_approval.get('mode')=='canonical'
        and all(owner_approval.get(k)==target[k] for k in required) and _date(owner_approval.get('approved_at')) is not None)
    if approved and suffix:approved=_date(owner_approval['approved_at'])>=_date(records[suffix[-1]]['finished_at'])
    if not approved:gates.append('BLOCKED_APPROVAL')
    return {'shadow_hours':hours,'verified_run_count':len(suffix),'missing_run_ids':missing,'invalid_run_ids':invalid,
            'window_first_run_id':suffix[0] if suffix else None,'window_last_run_id':suffix[-1] if suffix else None,
            'gates':gates,'cutover_ready':not gates}


class ShadowBridge:
    """Optional boundary: storage/projection failures cannot skip legacy delivery."""
    def __init__(self,config,state,when,*,dry_run=False):
        import os,uuid
        self.mode=os.getenv('JOBBIE_CATALOGUE_MODE','off');self.requested=self.mode!='off'
        self.monitor=None;self.failure=None;self.dry_run=dry_run;self.active=False
        try:self.config_sha=config_fingerprint(config)
        except Exception:self.config_sha='unknown'
        if not self.requested:return
        action=(os.getenv('GITHUB_ACTIONS')=='true' and os.getenv('GITHUB_REPOSITORY','').casefold()=='kanujverma/jobbie'
                and os.getenv('GITHUB_REF')=='refs/heads/main' and os.getenv('GITHUB_WORKFLOW')=='Job Alerts'
                and os.getenv('GITHUB_EVENT_NAME') in {'schedule','workflow_dispatch'})
        origin=os.getenv('GITHUB_EVENT_NAME','local') if action else 'local'
        run_id=(os.getenv('GITHUB_RUN_ID','')+'.'+os.getenv('GITHUB_RUN_ATTEMPT','1')) if action else 'local-'+uuid.uuid4().hex
        try:
            self.monitor=open_shadow(os.getenv('JOBBIE_CATALOGUE_DB','state/catalogue-shadow/jobs.sqlite'),self.mode,run_id,
                when,legacy_snapshot(state),filters=config.filters,dry_run=dry_run,origin=origin,
                head_sha=os.getenv('GITHUB_SHA') if action else None,config_sha=self.config_sha)
            self.active=self.monitor is not None
            if self.monitor is not None:self.monitor.configure_sources({source_key(c) for c in config.companies if c.get('enabled') is True},when)
        except Exception as error:self.failure=type(error).__name__
    def close(self):
        if self.monitor is not None:
            try:self.monitor.store.close()
            except Exception as error:self.failure=type(error).__name__
    def _call(self,name,*args,**kwargs):
        if not self.active:return None
        try:return getattr(self.monitor,name)(*args,**kwargs)
        except Exception as error:
            self.failure=type(error).__name__;self.active=False
            self.monitor.gates.add('BLOCKED_STORAGE')
            return None
    def observe(self,config,jobs,succeeded):
        metadata=self._metadata(config)
        return self._call('observe',metadata,jobs,status='complete' if succeeded else 'partial' if jobs else 'failed',observed_at=datetime.now(timezone.utc))
    @staticmethod
    def _metadata(config):
        metadata=copy.deepcopy(config)
        if metadata['name']=='Microsoft Research':
            metadata['aliases']=[*metadata.get('aliases',[]),'Microsoft']
            if metadata.get('cohort')=='original_2026_11_04' and metadata.get('network_priority') is True:
                metadata.setdefault('catalogue_employer_key','microsoft')
        return metadata
    def leads(self,leads):return self._call('leads',leads)
    def confirm(self,lead,config,confirmation):return self._call('confirm',lead,self._metadata(config),confirmation)
    def project(self,config,fetched,matched,state,freshness_hours,now):
        self._call('replay_filter',config,fetched,matched)
        return self._call('project',config,matched,legacy_snapshot(state),freshness_hours=freshness_hours,now=now)
    def compare(self,config,matched,candidates,projection,state):
        if projection is not None:self._call('compare',config,matched,candidates,projection,state=legacy_snapshot(state))
    def delivery(self,config,job,outcome,when):return self._call('delivery',config,job,outcome,when)
    def finish(self,state,when,summary_acks=0):
        if self.monitor is not None:
            try:self.monitor.finish(legacy_snapshot(state),when,summary_acks=summary_acks)
            except Exception as error:self.failure=type(error).__name__;self.active=False
        return self.report()
    def legacy_saved(self,saved):
        if self.monitor is not None and not self.dry_run:
            try:
                if not saved:self.monitor.gates.add('BLOCKED_LEGACY_PERSISTENCE')
                result=self.report();result['legacy_saved']=saved
                with self.monitor.store.db:self.monitor.store.db.execute('UPDATE shadow_runs SET result=?,status=? WHERE run_id=?',
                    (compact(result),'complete' if result.get('parity_ok') else 'degraded',self.monitor.run_id))
            except Exception as error:self.failure=type(error).__name__
    def report(self):
        result=self.monitor.report() if self.monitor is not None else {'delivery_authority':'legacy_json','sources':{},'parity_ok':False,'gates':[]}
        if self.failure:
            result['gates']=sorted(set(result['gates'])|{'BLOCKED_STORAGE'})
            result['error_type']=self.failure;result['parity_ok']=False
        result['mode']=self.mode;result['dry_run']=self.dry_run
        return result

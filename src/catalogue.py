"""Versioned local SQLite evidence store. Legacy JSON remains delivery authority.

No network, sender, source activation, implicit migration or cutover lives here.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sqlite3
import unicodedata
import uuid
from dataclasses import asdict, fields
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from src.job_identity import canonical_job_url
from src.models import Job, CompensationRange

SCHEMA_VERSION = 1
MAX_PAYLOAD = 512 * 1024
MAX_SCAN_ROWS = 50000
MAX_DB_BYTES = 256 * 1024 * 1024
_LEGACY_NATIVE_COMPOSITES = {
    'amazon_jobs','apple_jobs','workday','lever','smartrecruiters',
    'microsoft_research','eightfold','eightfold_pcsx','eightfold_playwright',
    'phenom_people','oracle_careers',
}


class CatalogueError(Exception):
    pass


def stamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise CatalogueError('an aware evidence timestamp is required')
    return value.astimezone(timezone.utc).isoformat()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def text(value, maximum=8192, *, nullable=True):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or len(value)>maximum or '\0' in value or any(0xD800<=ord(c)<=0xDFFF for c in value):
        raise CatalogueError('invalid bounded source text')
    return value


def employer_key(config):
    # Cross-company aliases must be explicit, reviewed configuration. No name guess.
    name=text(config.get('catalogue_employer_key',config.get('name')),256,nullable=False)
    return unicodedata.normalize('NFKC',name).casefold().strip()


def normalized_snapshot(job, config):
    """Whitelist public source facts; observation clock and policy verdict are separate."""
    url=canonical_job_url(job.url)
    if not url:
        raise CatalogueError('unsafe or missing official posting URL')
    native=job.source_job_id
    prefix=f'{job.company}::{job.source_platform}::'
    if native is None and job.source_platform in _LEGACY_NATIVE_COMPOSITES and job.id.startswith(prefix):
        native=job.id[len(prefix):] or None
    req=job.official_req_id
    if req is None and job.source_platform=='oracle_careers':
        req=job.source_job_id
    result={name:text(getattr(job,name),262144 if name=='raw_text' else 8192)
            for name in ('id','company','title','location','department','category','raw_text',
                         'source_platform','source_url','source_board','source_internal_job_id',
                         'posted_at_kind','employment_type','salary')}
    result.update(source_job_id=text(native,512),official_req_id=text(req,512),
                  url=job.url,canonical_url=url,
                  source_record_id=native or 'url:'+url,
                  employer_names=[text(n,256,nullable=False) for n in [config['name'],*config.get('aliases',[])]],
                  source_enabled=config.get('enabled') is True,
                  description_complete=job.description_complete,
                  network_priority=config.get('network_priority') is True,
                  cohort=config.get('cohort','discovered'),
                  referral_status=config.get('referral_status','unconfirmed' if config.get('network_priority') is True else 'unavailable'))
    if result['referral_status'] not in {'unconfirmed','unavailable'}:
        raise CatalogueError('unsupported referral claim in public source catalogue')
    result['adapter_posted_at']=stamp(job.posted_at) if job.posted_at is not None else None
    # Older adapters sometimes turn a relative/calendar date into UTC midnight.
    # Retain that normalized value without promoting its precision into a fact.
    exact=job.source_platform in {'greenhouse','ashby'} and job.posted_at_kind in {'first_published','last_published'}
    result['posted_at']=result['adapter_posted_at'] if exact else None
    result['posted_precision']='instant' if exact and job.posted_at else 'unknown'
    result['source_posted_date']=date.fromisoformat(job.source_posted_date).isoformat() if job.source_posted_date else None
    if result['source_posted_date']:
        result['posted_precision']='date'
    result['source_updated_at']=stamp(job.source_updated_at) if job.source_updated_at is not None else None
    result['compensation']=[{**asdict(c),'minimum':str(c.minimum) if c.minimum is not None else None,
                           'maximum':str(c.maximum) if c.maximum is not None else None} for c in job.compensation]
    result['role_type']=job.role_type;result['priority']=job.priority
    result['matched_keywords']=list(job.matched_keywords)
    if len(compact(result).encode())>MAX_PAYLOAD:
        raise CatalogueError('normalized source snapshot exceeds bound')
    return result


_SCHEMA='''
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE runs(run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,origin TEXT NOT NULL,head_sha TEXT,finished_at TEXT);
CREATE TABLE jobs(job_id TEXT PRIMARY KEY,employer TEXT NOT NULL,first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,status TEXT NOT NULL);
CREATE TABLE claims(employer TEXT NOT NULL,kind TEXT NOT NULL,value TEXT NOT NULL,job_id TEXT NOT NULL REFERENCES jobs,
 PRIMARY KEY(employer,kind,value,job_id));
CREATE INDEX claim_lookup ON claims(employer,kind,value);
CREATE TABLE snapshots(sha TEXT PRIMARY KEY,payload TEXT NOT NULL);
CREATE TABLE observations(id INTEGER PRIMARY KEY,run_id TEXT NOT NULL REFERENCES runs,source_id TEXT NOT NULL,source_record_id TEXT NOT NULL,
 job_id TEXT NOT NULL REFERENCES jobs,snapshot_sha TEXT NOT NULL REFERENCES snapshots,observed_at TEXT NOT NULL);
CREATE INDEX source_lookup ON observations(source_id,source_record_id);
CREATE INDEX job_observations ON observations(job_id,observed_at);
CREATE TABLE scans(run_id TEXT NOT NULL REFERENCES runs,source_id TEXT NOT NULL,employer TEXT NOT NULL,status TEXT NOT NULL,
 observed_at TEXT NOT NULL,returned_count INTEGER NOT NULL,rejected_count INTEGER NOT NULL,PRIMARY KEY(run_id,source_id));
CREATE INDEX scan_chronology ON scans(source_id,employer,status,observed_at);
CREATE TABLE source_state(job_id TEXT NOT NULL REFERENCES jobs,source_id TEXT NOT NULL,source_record_id TEXT NOT NULL,status TEXT NOT NULL,
 observed_at TEXT NOT NULL,PRIMARY KEY(job_id,source_id,source_record_id));
CREATE TABLE status_events(id INTEGER PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs,status TEXT NOT NULL,source_id TEXT NOT NULL,
 evidence_kind TEXT NOT NULL,evidence TEXT NOT NULL,observed_at TEXT NOT NULL);
CREATE TABLE conflicts(id INTEGER PRIMARY KEY,run_id TEXT NOT NULL,source_id TEXT NOT NULL,source_record_id TEXT,code TEXT NOT NULL,
 detail TEXT NOT NULL,observed_at TEXT NOT NULL);
CREATE TABLE classifications(snapshot_sha TEXT NOT NULL REFERENCES snapshots,policy TEXT NOT NULL,result TEXT NOT NULL,classified_at TEXT NOT NULL,
 PRIMARY KEY(snapshot_sha,policy));
CREATE TABLE leads(source_id TEXT NOT NULL,lead_id TEXT NOT NULL,first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,
 payload TEXT NOT NULL,official_job_id TEXT REFERENCES jobs,confirmed_at TEXT,PRIMARY KEY(source_id,lead_id));
CREATE TABLE lead_history(id INTEGER PRIMARY KEY,source_id TEXT NOT NULL,lead_id TEXT NOT NULL,run_id TEXT NOT NULL,
 payload TEXT NOT NULL,observed_at TEXT NOT NULL);
'''


class Catalogue:
    def __init__(self,path,*,create=False,readonly=False):
        self.path=Path(path).absolute();self.readonly=readonly;self.db=None
        if self.path.is_symlink() or not self.path.parent.is_dir():
            raise CatalogueError('unsafe or missing catalogue path')
        new=not self.path.exists()
        if not new and self.path.stat().st_size>MAX_DB_BYTES:
            raise CatalogueError('catalogue exceeds local storage cap; no pruning performed')
        if new and (readonly or not create):
            raise CatalogueError('catalogue missing; explicit initialization required')
        try:
            if new:
                fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
            self.db=sqlite3.connect(self.path.as_uri()+('?mode=ro' if readonly else '?mode=rw'),uri=True,timeout=5)
            self.db.row_factory=sqlite3.Row
            self.db.execute('PRAGMA foreign_keys=ON')
            if not readonly:
                self.db.execute('PRAGMA synchronous=FULL')
                page_size=self.db.execute('PRAGMA page_size').fetchone()[0]
                self.db.execute(f'PRAGMA max_page_count={MAX_DB_BYTES//page_size}')
            if new:
                self.db.executescript(_SCHEMA)
                self.db.execute('INSERT INTO meta VALUES(?,?)',('catalogue_uuid',str(uuid.uuid4())))
                self.db.execute('INSERT INTO meta VALUES(?,?)',('identity_version','1'))
                self.db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                self.db.commit()
            version=self.db.execute('PRAGMA user_version').fetchone()[0]
            if version!=SCHEMA_VERSION or self.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                raise CatalogueError('unsupported or corrupt catalogue; no reset performed')
            if self.db.execute('PRAGMA foreign_key_check').fetchone() is not None:
                raise CatalogueError('catalogue referential integrity failure')
            expected={'meta','runs','jobs','claims','snapshots','observations','scans','source_state',
                      'status_events','conflicts','classifications','leads','lead_history'}
            actual={r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if actual!=expected:
                raise CatalogueError('unsupported catalogue schema')
            metadata=dict(self.db.execute('SELECT key,value FROM meta'))
            uuid.UUID(metadata['catalogue_uuid'])
            if metadata.get('identity_version')!='1':raise CatalogueError('unsupported identity version')
        except (sqlite3.Error,OSError,CatalogueError,KeyError,ValueError) as error:
            if self.db is not None:self.db.close()
            raise CatalogueError('cannot open verified catalogue') from error

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
    def close(self):
        if self.db is not None:self.db.close()
    def _write(self):
        if self.readonly:raise CatalogueError('read-only catalogue')
    def _rows(self,sql,args=()):return [dict(r) for r in self.db.execute(sql,args)]
    def start_run(self,run_id,when,*,origin='local',head_sha=None):
        self._write();text(run_id,256,nullable=False)
        if origin not in {'fixture','local','schedule','workflow_dispatch'}:raise CatalogueError('invalid run origin')
        with self.db:
            old=self.db.execute('SELECT * FROM runs WHERE run_id=?',(run_id,)).fetchone()
            if old is None:self.db.execute('INSERT INTO runs VALUES(?,?,?,?,NULL)',(run_id,stamp(when),origin,head_sha))
            elif old['origin']!=origin or old['started_at']!=stamp(when):raise CatalogueError('run identity cannot be reused')

    def _claims(self,source_id,data):
        result=[('source:'+source_id,data['source_record_id']),('url',data['canonical_url'])]
        if data['source_job_id']:
            result.append(('provider:'+data['source_platform']+':'+(data['source_board'] or ''),data['source_job_id']))
        if data['official_req_id']:result.append(('requisition',data['official_req_id']))
        return result

    def _compatible(self,job_id,claims):
        old=self._rows("SELECT kind,value FROM claims WHERE job_id=? AND kind!='url'",(job_id,))
        incoming=dict(claims)
        old_req={row['value'] for row in old if row['kind']=='requisition'}
        if old_req and incoming.get('requisition'):
            return old_req=={incoming['requisition']}
        return all(row['kind'] not in incoming or incoming[row['kind']]==row['value'] for row in old)

    def _conflict(self,run,source,record,code,detail,when):
        self.db.execute('INSERT INTO conflicts(run_id,source_id,source_record_id,code,detail,observed_at) VALUES(?,?,?,?,?,?)',
                        (run,source,record,code,compact(detail),when))

    def _identity(self,run,source,employer,data,when):
        claims=self._claims(source,data);candidates=set();by_claim={}
        for kind,value in claims:
            found={r[0] for r in self.db.execute('SELECT job_id FROM claims WHERE employer=? AND kind=? AND value=?',(employer,kind,value))}
            by_claim[kind]=found;candidates.update(found)
        compatible={candidate for candidate in candidates if self._compatible(candidate,claims)}
        identity=None
        # Retain an existing source record under an ambiguous bridge. Never mint
        # another canonical identity on every retry or silently merge old rows.
        ordered=[claims[0],*[c for c in claims if c[0]=='requisition'],
                 *[c for c in claims if c[0].startswith('provider:')],claims[1]]
        for kind,_ in ordered:
            found=by_claim[kind]&compatible
            if len(found)==1:identity=next(iter(found));break
        if identity is None and len(compatible)==1:identity=next(iter(compatible))
        if identity is None:
            # Never silently merge two existing identities. Reconciliation is evidence-gated.
            identity=str(uuid.uuid4())
            self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?)',(identity,employer,when,when,'unknown'))
        if candidates-compatible or len(compatible)>1:
            self._conflict(run,source,data['source_record_id'],'IDENTITY_CONFLICT',
                           {'existing_job_ids':sorted(candidates),'retained_job_id':identity},when)
        for kind,value in claims:
            self.db.execute('INSERT OR IGNORE INTO claims VALUES(?,?,?,?)',(employer,kind,value,identity))
        self.db.execute('UPDATE jobs SET first_observed_at=min(first_observed_at,?),last_observed_at=max(last_observed_at,?) WHERE job_id=?',(when,when,identity))
        return identity

    def _status(self,identity,source,kind,evidence,when):
        old=self.db.execute('SELECT status FROM jobs WHERE job_id=?',(identity,)).fetchone()[0]
        states=[r[0] for r in self.db.execute('SELECT status FROM source_state WHERE job_id=?',(identity,))]
        if 'open' in states:new='reopened' if old in {'closed','reopened'} else 'open'
        elif states and all(s=='closed' for s in states):new='closed'
        else:new='unknown'
        if old!=new or kind in {'explicit_closed','complete_scan_absence'}:
            self.db.execute('UPDATE jobs SET status=? WHERE job_id=?',(new,identity))
            self.db.execute('INSERT INTO status_events(job_id,status,source_id,evidence_kind,evidence,observed_at) VALUES(?,?,?,?,?,?)',
                            (identity,new,source,kind,evidence,when))

    def observe_scan(self,run_id,source_id,config,jobs,*,status,observed_at):
        self._write();text(source_id,512,nullable=False)
        if status not in {'complete','partial','failed'} or len(jobs)>MAX_SCAN_ROWS:raise CatalogueError('invalid/bounded source scan')
        when=stamp(observed_at);employer=employer_key(config);rejected=0;observed=0;seen={};present=set()
        before=self.stats()['conflicts']
        with self.db:
            if self.db.execute('SELECT 1 FROM scans WHERE run_id=? AND source_id=?',(run_id,source_id)).fetchone():
                raise CatalogueError('source scan already recorded')
            for job in jobs:
                try:data=normalized_snapshot(job,config)
                except (CatalogueError,TypeError,ValueError):
                    rejected+=1;self._conflict(run_id,source_id,None,'REJECTED_NORMALIZED_ROW',{'ordinal':observed+rejected-1},when);continue
                payload=compact(data);sha=hashlib.sha256(payload.encode()).hexdigest();record=data['source_record_id']
                if record in seen and seen[record]!=sha:
                    self._conflict(run_id,source_id,record,'CONFLICTING_SOURCE_ROWS',{'snapshot_sha256':sha,'earlier_sha256':seen[record]},when)
                seen[record]=sha
                identity=self._identity(run_id,source_id,employer,data,when);present.add((identity,record))
                self.db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?)',(sha,payload))
                self.db.execute('INSERT INTO observations(run_id,source_id,source_record_id,job_id,snapshot_sha,observed_at) VALUES(?,?,?,?,?,?)',
                                (run_id,source_id,record,identity,sha,when))
                self.db.execute("INSERT INTO source_state VALUES(?,?,?,'open',?) ON CONFLICT(job_id,source_id,source_record_id) DO UPDATE SET status='open',observed_at=excluded.observed_at WHERE excluded.observed_at>=source_state.observed_at",(identity,source_id,record,when))
                self._status(identity,source_id,'listed','Official adapter returned normalized listing',when)
                # A newly imported historical record may not yet have a source
                # head, even though newer complete absences are already stored.
                absence=self.db.execute('''SELECT sc.observed_at,sc.run_id FROM scans sc
                    WHERE sc.source_id=? AND sc.employer=? AND sc.status='complete' AND sc.observed_at>=?
                    AND NOT EXISTS (SELECT 1 FROM observations o WHERE o.run_id=sc.run_id
                        AND o.source_id=sc.source_id AND o.job_id=? AND o.source_record_id=?)
                    ORDER BY sc.observed_at DESC LIMIT 1''',(source_id,employer,when,identity,record)).fetchone()
                if absence:
                    changed=self.db.execute("UPDATE source_state SET status='unknown',observed_at=? WHERE job_id=? AND source_id=? AND source_record_id=? AND status='open' AND observed_at<=?",(absence['observed_at'],identity,source_id,record,absence['observed_at'])).rowcount
                    if changed:
                        self._status(identity,source_id,'complete_scan_absence',
                                     'Not observed in complete scan '+absence['run_id']+'; closure unknown',absence['observed_at'])
                observed+=1
            conflicts=self.stats()['conflicts']-before
            effective='partial' if status=='complete' and (rejected or conflicts) else status
            if effective=='complete':
                for row in self._rows('SELECT ss.* FROM source_state ss JOIN jobs j ON ss.job_id=j.job_id WHERE ss.source_id=? AND j.employer=?',(source_id,employer)):
                    if (row['job_id'],row['source_record_id']) not in present and row['status']=='open' and row['observed_at']<=when:
                        self.db.execute("UPDATE source_state SET status='unknown',observed_at=? WHERE job_id=? AND source_id=? AND source_record_id=?",(when,row['job_id'],source_id,row['source_record_id']))
                        self._status(row['job_id'],source_id,'complete_scan_absence','Not observed in this complete scan; closure unknown',when)
            self.db.execute('INSERT INTO scans VALUES(?,?,?,?,?,?,?)',(run_id,source_id,employer,effective,when,len(jobs),rejected))
        return {'status':effective,'observed':observed,'rejected':rejected,'conflicts':conflicts}

    def record_closed(self,identity,source_id,record_id,when,*,evidence_url,evidence):
        self._write();when=stamp(when)
        if not canonical_job_url(evidence_url) or not text(evidence,2048,nullable=False):raise CatalogueError('explicit public closure evidence required')
        with self.db:
            changed=self.db.execute("UPDATE source_state SET status='closed',observed_at=? WHERE job_id=? AND source_id=? AND source_record_id=? AND observed_at<=?",(when,identity,source_id,record_id,when)).rowcount
            if changed!=1:raise CatalogueError('closure must reference an observed source record')
            self._status(identity,source_id,'explicit_closed',compact({'url':evidence_url,'evidence':evidence}),when)

    def stats(self):
        return {table:self.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                for table in ('jobs','snapshots','observations','conflicts','leads','runs')}
    def conflicts(self):return self._rows('SELECT * FROM conflicts ORDER BY id')
    def status_history(self,job_id=None):
        return self._rows('SELECT * FROM status_events'+(' WHERE job_id=?' if job_id else '')+' ORDER BY id',(job_id,) if job_id else ())
    def history(self,job_id=None,*,limit=5000):
        self._limit(limit)
        rows=self._rows('SELECT o.*,s.payload FROM observations o JOIN snapshots s ON o.snapshot_sha=s.sha'+
                        (' WHERE o.job_id=?' if job_id else '')+' ORDER BY o.id LIMIT ?',((job_id,) if job_id else ())+(limit,))
        for row in rows:
            row['snapshot']=json.loads(row.pop('payload'));row['snapshot']['_observed_at']=row['observed_at']
        return rows
    @staticmethod
    def _limit(limit):
        if type(limit) is not int or not 1<=limit<=5000:raise ValueError('limit must be 1..5000')
    def query(self,*,text=None,status=None,employer=None,policy=None,limit=1000,offset=0):
        self._limit(limit)
        if type(offset) is not int or offset<0:raise ValueError('invalid query offset')
        clauses=[];args=[]
        if employer is not None:clauses.append('j.employer=?');args.append(employer)
        if status is not None:
            if status not in {'unknown','open','closed','reopened'}:raise ValueError('invalid status')
            clauses.append('j.status=?');args.append(status)
        if text is not None:
            pattern='%'+text.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
            clauses.append("(json_extract(s.payload,'$.title') LIKE ? ESCAPE '\\' OR json_extract(s.payload,'$.location') LIKE ? ESCAPE '\\')");args.extend([pattern,pattern])
        rows=self._rows('SELECT j.*,o.source_id,o.source_record_id,o.snapshot_sha,o.observed_at,s.payload FROM jobs j '
            'JOIN observations o ON o.id=(SELECT id FROM observations WHERE job_id=j.job_id ORDER BY observed_at DESC,id DESC LIMIT 1) '
            'JOIN snapshots s ON o.snapshot_sha=s.sha'+(' WHERE '+' AND '.join(clauses) if clauses else '')+
            ' ORDER BY j.job_id LIMIT ? OFFSET ?',(*args,limit,offset))
        for row in rows:
            row['snapshot']=json.loads(row.pop('payload'));row['snapshot']['_observed_at']=row['observed_at']
            row['title']=row['snapshot']['title'];row['canonical_url']=row['snapshot']['canonical_url']
            row['sources']=self._rows('SELECT source_id,source_record_id,min(observed_at) AS first_observed_at,max(observed_at) AS last_observed_at FROM observations WHERE job_id=? GROUP BY source_id,source_record_id ORDER BY source_id,source_record_id',(row['job_id'],))
            row['network_priority']=bool(self.db.execute("SELECT 1 FROM observations o JOIN snapshots s ON s.sha=o.snapshot_sha WHERE o.job_id=? AND json_extract(s.payload,'$.network_priority')=1 LIMIT 1",(row['job_id'],)).fetchone())
            row['referral_status']='unconfirmed' if row['network_priority'] else 'unavailable'
            row['classification']=None
            if policy is not None:
                found=self.db.execute('SELECT result FROM classifications WHERE snapshot_sha=? AND policy=?',(row['snapshot_sha'],policy)).fetchone()
                row['classification']=json.loads(found[0]) if found else None
        return rows
    def export(self,format='jsonl',**query):
        rows=self.query(**query)
        if format=='jsonl':
            for row in rows:yield compact(row)+'\n'
        elif format=='csv':
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=['job_id','employer','title','canonical_url','status','first_observed_at','last_observed_at'])
            writer.writeheader();yield output.getvalue();output.seek(0);output.truncate()
            for row in rows:
                values={key:row.get(key) for key in writer.fieldnames}
                values={key:("'"+value if isinstance(value,str) and value[:1] in '=+-@\t\r' else value) for key,value in values.items()}
                writer.writerow(values);yield output.getvalue();output.seek(0);output.truncate()
        else:raise ValueError('supported export formats: jsonl,csv')
    def reclassify(self,policy,classifier,when):
        self._write();text(policy,160,nullable=False);count=0
        with self.db:
            for row in self.db.execute('SELECT sha,payload FROM snapshots ORDER BY sha'):
                data=json.loads(row['payload'])
                data['_observed_at']=self.db.execute('SELECT max(observed_at) FROM observations WHERE snapshot_sha=?',(row['sha'],)).fetchone()[0]
                result=classifier(data)
                if not isinstance(result,dict) or set(result)-{'status','reasons'} or result.get('status') not in {'eligible','needs_review','excluded'}:
                    raise CatalogueError('invalid public deterministic classification')
                reasons=result.get('reasons',[])
                if not isinstance(reasons,list) or len(reasons)>100 or any(not isinstance(r,str) or len(r)>1024 for r in reasons):raise CatalogueError('invalid bounded classification reasons')
                value=compact(result)
                old=self.db.execute('SELECT result FROM classifications WHERE snapshot_sha=? AND policy=?',(row['sha'],policy)).fetchone()
                if old and old[0]!=value:raise CatalogueError('policy version is immutable; use a new version')
                self.db.execute('INSERT OR IGNORE INTO classifications VALUES(?,?,?,?)',(row['sha'],policy,value,stamp(when)));count+=1
        return count
    @staticmethod
    def job_from_snapshot(data):
        kwargs={f.name:data[f.name] for f in fields(Job) if f.name in data}
        kwargs.update(url=data['url'],posted_at=datetime.fromisoformat(data['adapter_posted_at']) if data['adapter_posted_at'] else None,
                      detected_at=datetime.fromisoformat(data['_observed_at']),matched_keywords=tuple(data['matched_keywords']))
        kwargs['source_updated_at']=datetime.fromisoformat(data['source_updated_at']) if data['source_updated_at'] else None
        kwargs['compensation']=tuple(CompensationRange(**{**c,'minimum':Decimal(c['minimum']) if c['minimum'] is not None else None,
                                    'maximum':Decimal(c['maximum']) if c['maximum'] is not None else None}) for c in data['compensation'])
        return Job(**kwargs)
    def observe_leads(self,run_id,leads):
        self._write()
        with self.db:
            for lead in leads:
                payload=asdict(lead)
                for key,value in list(payload.items()):
                    if isinstance(value,datetime):payload[key]=stamp(value)
                payload['confirmation_status']='lead';payload.pop('employer_posted_at',None)
                value=compact(payload)
                if len(value.encode())>MAX_PAYLOAD:raise CatalogueError('lead exceeds bound')
                when=stamp(lead.observed_at)
                self.db.execute('INSERT INTO leads VALUES(?,?,?,?,?,NULL,NULL) ON CONFLICT(source_id,lead_id) DO UPDATE SET last_observed_at=excluded.last_observed_at,payload=excluded.payload,official_job_id=NULL,confirmed_at=NULL WHERE excluded.last_observed_at>=leads.last_observed_at',
                                (lead.source_id,lead.lead_id,when,when,value))
                self.db.execute('INSERT INTO lead_history(source_id,lead_id,run_id,payload,observed_at) VALUES(?,?,?,?,?)',(lead.source_id,lead.lead_id,run_id,value,when))
    def confirm_lead(self,source_id,lead_id,official_source,official_record,when):
        self._write();stamp(when)
        matches={r[0] for r in self.db.execute('SELECT DISTINCT job_id FROM observations WHERE source_id=? AND source_record_id=?',(official_source,official_record))}
        if len(matches)!=1:raise CatalogueError('confirmation requires one observed official identity')
        row=self.db.execute('SELECT payload FROM leads WHERE source_id=? AND lead_id=?',(source_id,lead_id)).fetchone()
        if row is None:raise CatalogueError('lead missing')
        lead=json.loads(row[0]);identity=next(iter(matches))
        official=self.db.execute('SELECT s.payload,o.observed_at FROM observations o JOIN snapshots s ON o.snapshot_sha=s.sha WHERE o.job_id=? AND o.source_id=? AND o.source_record_id=? ORDER BY o.observed_at DESC,o.id DESC LIMIT 1',(identity,official_source,official_record)).fetchone()
        data=json.loads(official[0])
        source_state=self.db.execute('SELECT status FROM source_state WHERE job_id=? AND source_id=? AND source_record_id=?',(identity,official_source,official_record)).fetchone()
        age=(when-datetime.fromisoformat(official['observed_at'])).total_seconds()
        if source_state['status']!='open' or not 0<=age<=3600:raise CatalogueError('confirmation requires a current official observation')
        def name(value):return ''.join(c for c in unicodedata.normalize('NFKC',value or '').casefold() if c.isalnum())
        if not data['source_enabled'] or not lead.get('employer') or name(lead['employer']) not in {name(n) for n in data['employer_names']} or canonical_job_url(lead['url'])!=data['canonical_url']:
            raise CatalogueError('lead does not match exact approved employer posting')
        claimed=lead.get('official_req_id')
        known=data['official_req_id'] or (data['source_job_id'] if data['source_platform'] in {'greenhouse','ashby','oracle_careers'} else None)
        if claimed and claimed!=known:raise CatalogueError('lead identifier conflicts with official posting')
        with self.db:
            changed=self.db.execute('UPDATE leads SET official_job_id=?,confirmed_at=? WHERE source_id=? AND lead_id=?',(identity,official['observed_at'],source_id,lead_id)).rowcount
            if changed!=1:raise CatalogueError('lead missing')
    def leads(self):return self._rows('SELECT * FROM leads ORDER BY source_id,lead_id')

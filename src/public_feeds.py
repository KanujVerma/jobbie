"""Bounded optional JSON leads. Rights/owner gates precede every network read."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml

from src.adapters.public_board import public_https_url
from src.http import HTTPClient
from src.job_identity import canonical_job_url

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 5000


@dataclass(frozen=True)
class FeedLead:
    lead_id: str
    source_id: str
    source_url: str
    source_record_id: str | None
    employer: str | None
    title: str | None
    location: str | None
    url: str
    observed_at: datetime
    source_blob_sha256: str
    feed_updated_at: datetime | None = None
    reported_posted_at: datetime | None = None
    reported_posted_date: str | None = None
    official_req_id: str | None = None
    confirmation_status: str = 'lead'
    employer_posted_at: None = None


@dataclass(frozen=True)
class LeadConfirmation:
    source_id: str
    lead_id: str
    official_job_id: str
    canonical_url: str
    source_company: str
    confirmed_at: datetime


def _time(value):
    if not isinstance(value,str):
        return None
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def _text(value, limit=512):
    if value is None or value=='':
        return None
    if not isinstance(value,str) or len(value)>limit or any(ord(c)<32 or 0xD800<=ord(c)<=0xDFFF for c in value):
        raise ValueError('invalid bounded feed text')
    return value.strip() or None


def load_manifest(path):
    with open(path,'rb') as file:
        raw=file.read(1024*1024+1)
    if len(raw)>1024*1024:
        raise ValueError('feed manifest exceeds bound')
    data=yaml.safe_load(raw)
    if not isinstance(data,dict) or data.get('schema_version')!=1 or not isinstance(data.get('feeds'),list) or len(data['feeds'])>10:
        raise ValueError('invalid feed manifest')
    ids=[row.get('id') for row in data['feeds'] if isinstance(row,dict)]
    if len(ids)!=len(data['feeds']) or len(set(ids))!=len(ids):
        raise ValueError('duplicate or invalid feed manifest IDs')
    return data['feeds']


def _config(source, now):
    endpoint=source.get('endpoint')
    p=urlsplit(endpoint) if isinstance(endpoint,str) else None
    if not public_https_url(endpoint) or not p or p.hostname!='raw.githubusercontent.com' or p.query or p.fragment or '%' in p.path:
        raise ValueError('feed endpoint must be a fixed public raw.githubusercontent.com JSON URL')
    parts=p.path.strip('/').split('/')
    if len(parts)<4 or not p.path.endswith('.json') or any(x in ('.','..','') for x in parts):
        raise ValueError('invalid public feed endpoint path')
    if source.get('format')!='json':
        raise ValueError('unsupported feed format')
    cadence=source.get('refresh_seconds',3600)
    if type(cadence) is not int or not 3600<=cadence<=86400*7:
        raise ValueError('feed refresh must be 1 hour..7 days')
    key=source.get('rows_key','jobs')
    if key is not None and (not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',key)):
        raise ValueError('feed rows_key must be a literal field')
    fields=source.get('field_map',{})
    allowed={'id','company','title','location','url','posted_at','official_req_id'}
    if not isinstance(fields,dict) or set(fields)-allowed or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',v) for v in fields.values()):
        raise ValueError('invalid flat feed field mapping')
    rights=source['rights'];approval=source['owner_approval']
    if not public_https_url(rights.get('url')) or not _text(rights.get('basis'),600):
        raise ValueError('feed data permission evidence is required')
    for value in [rights.get('checked_at'),approval.get('approved_at')]:
        stamp=_time(value)
        if stamp is None or stamp>now+timedelta(minutes=5):
            raise ValueError('feed permission/approval timestamp invalid')
    if not _text(approval.get('reference'),600):
        raise ValueError('exact source approval reference required')
    return endpoint,cadence,key,fields


def fetch_feed(source, state, *, http=None, now=None, allow_network=True):
    now=now or datetime.now(timezone.utc)
    if not isinstance(source,dict) or not isinstance(state,dict):
        return [],{'source_id':None,'status':'invalid_config','returned_count':None,'gates':[]}
    sid=source.get('id')
    report={'source_id':sid,'status':'disabled','returned_count':None,'duplicate_count':0,'invalid_count':0,'gates':[]}
    rights=source.get('rights') or {};approval=source.get('owner_approval')
    if not isinstance(rights,dict):
        report['status']='invalid_config';return [],report
    if rights.get('status')!='permitted':report['gates'].append('BLOCKED_SOURCE_RIGHTS')
    if not isinstance(approval,dict) or approval.get('endpoint')!=source.get('endpoint'):
        report['gates'].append('BLOCKED_APPROVAL')
    if source.get('enabled') is not True or report['gates']:
        return [],report
    try:
        if not isinstance(sid,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',sid):
            raise ValueError('invalid feed ID')
        endpoint,cadence,key,fields=_config(source,now)
        previous=state.get(sid,{})
        if not isinstance(previous,dict):raise ValueError('corrupt feed health')
        last=previous.get('last_attempt_at')
        if last is not None and _time(last) is None:raise ValueError('corrupt feed health timestamp')
        if last and (now-_time(last)).total_seconds()<cadence:
            report['status']='not_due';return [],report
    except (TypeError,ValueError):
        report['status']='invalid_config';return [],report
    if not allow_network:
        report['status']='network_not_allowed';return [],report
    own=http is None;client=http if http is not None else HTTPClient('jobbie-public-feed/1.0',timeout=15,max_retries=1)
    response=None
    state[sid]={**previous,'last_attempt_at':now.isoformat()}
    try:
        response=client.get(endpoint,allow_redirects=False,stream=True)
        if response.status_code!=200:
            raise requests.HTTPError('feed HTTP failure',response=response)
        chunks=[];size=0
        for chunk in response.iter_content(chunk_size=65536):
            size+=len(chunk)
            if size>MAX_BYTES:raise ValueError('feed response exceeds bound')
            chunks.append(chunk)
        raw=b''.join(chunks)
        def reject_constant(_):raise ValueError('non-finite feed JSON')
        payload=json.loads(raw,parse_constant=reject_constant)
        rows=payload.get(key) if key is not None and isinstance(payload,dict) else payload if key is None else None
        if not isinstance(rows,list) or len(rows)>MAX_ITEMS:raise ValueError('invalid/bounded feed rows')
        updated=_time(payload.get('updated_at')) if isinstance(payload,dict) else None
        digest=hashlib.sha256(raw).hexdigest();leads=[];seen={}
        for row in rows:
            if not isinstance(row,dict):raise ValueError('feed row must be an object')
            def field(name):return row.get(fields.get(name,name))
            url=public_https_url(field('url'))
            if not url:raise ValueError('feed lead URL is unsafe or missing')
            canonical=canonical_job_url(url)
            identifier=field('id')
            if identifier is not None:
                if isinstance(identifier,bool) or not isinstance(identifier,(str,int)):raise ValueError('invalid source ID')
                identifier=_text(str(identifier),128)
            identity=identifier or hashlib.sha256(canonical.encode()).hexdigest()
            req=_text(str(field('official_req_id')),128) if field('official_req_id') is not None else None
            title,location=_text(field('title')),_text(field('location'))
            posted=field('posted_at');calendar=None
            if isinstance(posted,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',posted):
                from datetime import date
                try:calendar=date.fromisoformat(posted).isoformat()
                except ValueError:pass
            instant=_time(posted)
            fingerprint=(canonical,_text(field('company'),160),req,title,location,instant,calendar)
            if identity in seen:
                if seen[identity]!=fingerprint:raise ValueError('conflicting feed source ID')
                report['duplicate_count']+=1;continue
            seen[identity]=fingerprint
            leads.append(FeedLead(lead_id=f'{sid}:{identity}',source_id=sid,source_url=endpoint,
                source_record_id=identifier,employer=fingerprint[1],title=title,
                location=location,url=url,observed_at=now,source_blob_sha256=digest,
                feed_updated_at=updated,reported_posted_at=instant,reported_posted_date=calendar,official_req_id=req))
        report.update(status='ok' if leads else 'empty',returned_count=len(leads),blob_sha256=digest,
                      observed_at=now.isoformat(),feed_updated_at=updated.isoformat() if updated else None)
        state[sid].update(last_success_at=now.isoformat(),blob_sha256=digest)
        return leads,report
    except Exception as error:
        status=getattr(getattr(error,'response',None),'status_code',None)
        report.update(status='failed',error_type=type(error).__name__,http_status=status if isinstance(status,int) else None)
        return [],report
    finally:
        if response is not None:response.close()
        if own:client.session.close()


def collect_feeds(manifest_path, state, *, http=None, now=None, allow_network=True):
    """Optional errors are reports, never a reason to skip original employers."""
    if not isinstance(state,dict):
        return [],[{'source_id':None,'status':'corrupt_health','returned_count':None,'gates':[]}]
    try:
        sources=load_manifest(manifest_path)
    except Exception as error:
        return [],[{'source_id':None,'status':'invalid_manifest','returned_count':None,
                    'error_type':type(error).__name__,'gates':[]}]
    leads=[];reports=[]
    for source in sources:
        try:
            found,report=fetch_feed(source,state,http=http,now=now,allow_network=allow_network)
        except Exception as error:
            found=[];report={'source_id':source.get('id'),'status':'failed','returned_count':None,
                             'error_type':type(error).__name__,'gates':[]}
        leads.extend(found);reports.append(report)
    return leads,reports


def confirm_lead(lead, official_jobs, company_config, *, now=None):
    if company_config.get('enabled') is not True or not lead.employer:
        return None
    import unicodedata
    def key(value):return ''.join(c for c in unicodedata.normalize('NFKC',value).casefold() if c.isalnum())
    names=[company_config['name'],*company_config.get('aliases',[])]
    if company_config['name']=='Microsoft Research':names.append('Microsoft')
    if key(lead.employer) not in {key(n) for n in names}:return None
    matches=[j for j in official_jobs if key(j.company) in {key(n) for n in names} and canonical_job_url(j.url)==canonical_job_url(lead.url)]
    if len({j.id for j in matches})!=1:return None
    job=matches[0]
    req=getattr(job,'official_req_id',None)
    if job.source_platform in {'greenhouse','ashby','oracle_careers'}:req=job.source_job_id
    if lead.official_req_id and req!=lead.official_req_id:return None
    return LeadConfirmation(lead.source_id,lead.lead_id,job.id,canonical_job_url(job.url),company_config['name'],now or datetime.now(timezone.utc))

"""Compact exact scan memberships over immutable normalized content records."""
import json
import zlib
from collections import OrderedDict

HISTORY_SCHEMA='''
CREATE TABLE observation_spans(observation_id INTEGER PRIMARY KEY REFERENCES observations,
 first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,adapter_posted_at TEXT);
CREATE TABLE scan_memberships(run_id TEXT NOT NULL,source_id TEXT NOT NULL,members BLOB NOT NULL,
 PRIMARY KEY(run_id,source_id),FOREIGN KEY(run_id,source_id) REFERENCES scans(run_id,source_id));
CREATE INDEX observation_content ON observations(source_id,source_record_id,job_id,snapshot_sha);
'''
HISTORY_COLUMNS='''
ALTER TABLE source_state ADD COLUMN latest_observation_id INTEGER REFERENCES observations;
ALTER TABLE source_state ADD COLUMN last_listing_at TEXT;
ALTER TABLE source_state ADD COLUMN adapter_posted_at TEXT;
'''
MAX_MEMBERS_BYTES=8*1024*1024


def pack_members(ids,context):
    raw=json.dumps({'ids':ids,'adapter':context},separators=(',',':')).encode()
    if len(raw)>MAX_MEMBERS_BYTES:raise ValueError('scan membership exceeds bound')
    return zlib.compress(raw,6)


class ObservationHistory:
    def _members(self,run,source):
        row=self.db.execute('SELECT members FROM scan_memberships WHERE run_id=? AND source_id=?',(run,source)).fetchone()
        if row is None:raise self.error_class('scan membership missing')
        decoder=zlib.decompressobj()
        try:raw=decoder.decompress(row[0],MAX_MEMBERS_BYTES+1)
        except (zlib.error,TypeError) as error:raise self.error_class('corrupt compressed scan membership') from error
        if len(raw)>MAX_MEMBERS_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise self.error_class('corrupt bounded scan membership')
        data=json.loads(raw)
        ids,context=data.get('ids'),data.get('adapter')
        if not isinstance(ids,list) or not isinstance(context,list) or len(ids)!=len(context) or len(ids)>50000:
            raise self.error_class('invalid scan membership shape')
        if any(type(i) is not int or i<=0 for i in ids) or any(v is not None and not isinstance(v,str) for v in context):
            raise self.error_class('invalid scan membership values')
        return ids,context

    def _physical_rows(self,ids):
        unique=sorted(set(ids));result={}
        for offset in range(0,len(unique),400):
            batch=unique[offset:offset+400]
            for row in self.db.execute('SELECT o.*,s.payload FROM observations o JOIN snapshots s ON s.sha=o.snapshot_sha WHERE o.id IN ('+','.join('?' for _ in batch)+')',batch):
                result[row['id']]=dict(row)
        if len(result)!=len(unique):raise self.error_class('scan references missing observations')
        return result

    def scan_rows(self,run,source,*,job_id=None):
        scan=self.db.execute('SELECT rowid AS scan_id,* FROM scans WHERE run_id=? AND source_id=?',(run,source)).fetchone()
        if scan is None:raise self.error_class('source scan missing')
        ids,context=self._members(run,source)
        selected=ids
        if job_id is not None:
            allowed={r[0] for r in self.db.execute('SELECT id FROM observations WHERE job_id=?',(job_id,))}
            selected=[i for i in ids if i in allowed]
        rows=self._physical_rows(selected);result=[]
        for ordinal,(identifier,adapter) in enumerate(zip(ids,context)):
            if identifier not in rows:continue
            row={**rows[identifier]};data=json.loads(row['payload'])
            if row['source_id']!=source:raise self.error_class('membership references another source')
            if data['posted_precision']!='instant':data['adapter_posted_at']=adapter
            row.update(id=f"{scan['scan_id']}:{ordinal}",physical_observation_id=identifier,
                       run_id=run,source_id=source,observed_at=scan['observed_at'])
            row['payload']=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False)
            result.append(row)
        return result

    def _scan_has(self,run,source,identity,record):
        if not hasattr(self,'_scan_key_cache'):self._scan_key_cache=OrderedDict()
        key=(run,source)
        if key not in self._scan_key_cache:
            ids,_=self._members(run,source)
            values={(row['job_id'],row['source_record_id']) for row in self._physical_rows(ids).values()}
            self._scan_key_cache[key]=values
            if len(self._scan_key_cache)>8:self._scan_key_cache.popitem(last=False)
        else:self._scan_key_cache.move_to_end(key)
        return (identity,record) in self._scan_key_cache[key]

    def _physical_observation(self,run,source,record,identity,sha,when,adapter):
        row=self.db.execute('SELECT id FROM observations WHERE source_id=? AND source_record_id=? AND job_id=? AND snapshot_sha=? ORDER BY id LIMIT 1',(source,record,identity,sha)).fetchone()
        if row is None:
            identifier=self.db.execute('INSERT INTO observations(run_id,source_id,source_record_id,job_id,snapshot_sha,observed_at) VALUES(?,?,?,?,?,?)',(run,source,record,identity,sha,when)).lastrowid
        else:identifier=row[0]
        self.db.execute('''INSERT INTO observation_spans VALUES(?,?,?,?) ON CONFLICT(observation_id) DO UPDATE SET
            first_observed_at=min(first_observed_at,excluded.first_observed_at),
            adapter_posted_at=CASE WHEN excluded.last_observed_at>=last_observed_at THEN excluded.adapter_posted_at ELSE adapter_posted_at END,
            last_observed_at=max(last_observed_at,excluded.last_observed_at)''',(identifier,when,when,adapter))
        self.db.execute('''INSERT INTO source_state(job_id,source_id,source_record_id,status,observed_at,latest_observation_id,last_listing_at,adapter_posted_at)
            VALUES(?,?,?,'open',?,?,?,?) ON CONFLICT(job_id,source_id,source_record_id) DO UPDATE SET
            status=CASE WHEN excluded.observed_at>=source_state.observed_at THEN 'open' ELSE source_state.status END,
            observed_at=max(source_state.observed_at,excluded.observed_at),
            latest_observation_id=CASE WHEN excluded.last_listing_at>=source_state.last_listing_at THEN excluded.latest_observation_id ELSE source_state.latest_observation_id END,
            adapter_posted_at=CASE WHEN excluded.last_listing_at>=source_state.last_listing_at THEN excluded.adapter_posted_at ELSE source_state.adapter_posted_at END,
            last_listing_at=max(source_state.last_listing_at,excluded.last_listing_at)''',(identity,source,record,when,identifier,when,adapter))
        return identifier

    def _backfill_history(self):
        # Preserve every old physical row and its original run. Logical memberships
        # reproduce the prior history exactly, including duplicate source rows.
        for row in self.db.execute('SELECT o.*,s.payload FROM observations o JOIN snapshots s ON s.sha=o.snapshot_sha'):
            data=json.loads(row['payload'])
            self.db.execute('INSERT INTO observation_spans VALUES(?,?,?,?)',(row['id'],row['observed_at'],row['observed_at'],data.get('adapter_posted_at')))
        for scan in self.db.execute('SELECT * FROM scans ORDER BY rowid'):
            rows=self.db.execute('SELECT o.id,s.payload FROM observations o JOIN snapshots s ON s.sha=o.snapshot_sha WHERE run_id=? AND source_id=? ORDER BY o.id',(scan['run_id'],scan['source_id'])).fetchall()
            self.db.execute('INSERT INTO scan_memberships VALUES(?,?,?)',(scan['run_id'],scan['source_id'],pack_members([r['id'] for r in rows],[json.loads(r['payload']).get('adapter_posted_at') for r in rows])))
        for source in self.db.execute('SELECT * FROM source_state'):
            row=self.db.execute('SELECT o.id,o.observed_at,s.payload FROM observations o JOIN snapshots s ON s.sha=o.snapshot_sha WHERE job_id=? AND source_id=? AND source_record_id=? ORDER BY observed_at DESC,o.id DESC LIMIT 1',(source['job_id'],source['source_id'],source['source_record_id'])).fetchone()
            if row is None:raise self.error_class('source state has no observation evidence')
            self.db.execute('UPDATE source_state SET latest_observation_id=?,last_listing_at=?,adapter_posted_at=? WHERE job_id=? AND source_id=? AND source_record_id=?',(row['id'],row['observed_at'],json.loads(row['payload']).get('adapter_posted_at'),source['job_id'],source['source_id'],source['source_record_id']))

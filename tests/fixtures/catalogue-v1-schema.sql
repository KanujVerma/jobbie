-- Original schema from merged C1 1614d804; no source data.

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
CREATE INDEX status_evidence_lookup ON status_events(job_id,source_id,evidence_kind,observed_at);
CREATE TABLE conflicts(id INTEGER PRIMARY KEY,run_id TEXT NOT NULL,source_id TEXT NOT NULL,source_record_id TEXT,code TEXT NOT NULL,
 detail TEXT NOT NULL,observed_at TEXT NOT NULL);
CREATE TABLE classifications(snapshot_sha TEXT NOT NULL REFERENCES snapshots,policy TEXT NOT NULL,result TEXT NOT NULL,classified_at TEXT NOT NULL,
 PRIMARY KEY(snapshot_sha,policy));
CREATE TABLE leads(source_id TEXT NOT NULL,lead_id TEXT NOT NULL,first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,
 payload TEXT NOT NULL,official_job_id TEXT REFERENCES jobs,confirmed_at TEXT,PRIMARY KEY(source_id,lead_id));
CREATE TABLE lead_history(id INTEGER PRIMARY KEY,source_id TEXT NOT NULL,lead_id TEXT NOT NULL,run_id TEXT NOT NULL,
 payload TEXT NOT NULL,observed_at TEXT NOT NULL);

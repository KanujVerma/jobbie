"""Retain every logical observation without copying unchanged row metadata each poll."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import pytest
from src.catalogue import Catalogue
from src.models import Job

NOW=datetime(2026,11,12,tzinfo=timezone.utc)
CFG={'name':'Example Labs','enabled':True}


def job(i='1',**kwargs):
    return Job(**{**dict(id=f'Example Labs::workday::{i}',company='Example Labs',title='Engineer',location='US',department=None,category=None,
        url=f'https://example.com/jobs/{i}',source_platform='workday',posted_at=None,detected_at=NOW,raw_text='Synthetic fixture',
        role_type='unknown',priority='normal',matched_keywords=(),source_job_id=i),**kwargs})


def scan(store,rows,number):
    when=NOW+timedelta(minutes=number*15);store.start_run(str(number),when,origin='fixture')
    return store.observe_scan(str(number),'source',CFG,rows,status='complete',observed_at=when)


def test_unchanged_content_reuses_physical_rows_but_keeps_every_run_and_duplicate(tmp_path):
    with Catalogue(tmp_path/'db.sqlite',create=True) as store:
        rows=[job(str(i)) for i in range(20)]+[job('0')]
        for number in range(4):scan(store,rows,number)
        assert store.db.execute('SELECT count(*) FROM observations').fetchone()[0]==20
        assert store.stats()['observations']==84
        history=store.history(limit=100)
        assert len(history)==84 and {r['run_id'] for r in history}=={'0','1','2','3'}
        assert sum(r['source_record_id']=='0' for r in history)==8
        assert store.query()[0]['last_observed_at']==(NOW+timedelta(minutes=45)).isoformat()


def test_unknown_precision_adapter_clock_is_context_not_new_description_snapshot(tmp_path):
    with Catalogue(tmp_path/'db.sqlite',create=True) as store:
        for number in range(3):scan(store,[job(posted_at=NOW+timedelta(minutes=number))],number)
        assert store.stats()['snapshots']==1
        values=[r['snapshot']['adapter_posted_at'] for r in store.history()]
        assert values==[(NOW+timedelta(minutes=i)).isoformat() for i in range(3)]
        assert all(r['snapshot']['posted_at'] is None for r in store.history())
        assert store.query()[0]['snapshot']['adapter_posted_at']==values[-1]


def test_logical_source_lookup_and_reclassification_use_latest_context(tmp_path):
    with Catalogue(tmp_path/'db.sqlite',create=True) as store:
        for number in range(3):scan(store,[job(posted_at=NOW+timedelta(minutes=number))],number)
        rows=store.scan_rows('2','source')
        assert len(rows)==1 and rows[0]['observed_at']==(NOW+timedelta(minutes=30)).isoformat()
        def classifier(data):
            restored=store.job_from_snapshot(data)
            assert restored.posted_at==NOW+timedelta(minutes=2)
            assert restored.detected_at==NOW+timedelta(minutes=30)
            return {'status':'needs_review','reasons':['UNKNOWN_SOURCE_PRECISION']}
        assert store.reclassify('context-proof',classifier,NOW)==1


def test_repeated_scan_storage_growth_is_bounded_by_membership_not_full_rows(tmp_path):
    path=tmp_path/'db.sqlite'
    with Catalogue(path,create=True) as store:
        rows=[job(str(i)) for i in range(100)]
        scan(store,rows,0);initial=path.stat().st_size
        for number in range(1,8):scan(store,rows,number)
        assert path.stat().st_size-initial<=128*1024
        assert store.stats()['observations']==800

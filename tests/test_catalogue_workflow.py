"""Release-critical workflow boundaries, not a duplicate YAML snapshot."""
from pathlib import Path
import yaml


def steps():return yaml.safe_load(Path('.github/workflows/job-alerts.yml').read_text())['jobs']['check']['steps']


def test_legacy_ack_commit_precedes_optional_transport_and_keeps_failure_commit():
    values=steps();names=[x.get('name') for x in values]
    commit=values[names.index('Commit state')]
    assert names.index('Commit state')<names.index('Seal bounded catalogue checkpoint')
    assert "steps.scan.outcome == 'failure'" in commit['if']
    assert 'git add state/seen_jobs.json' in commit['run']
    assert 'git add state/catalogue_shadow_health.json' in commit['run']
    assert values[names.index('Run job alerts')]['timeout-minutes']==14


def test_only_ciphertext_is_cached_and_checkpoint_requires_fresh_exact_restore():
    values=steps();names=[x.get('name') for x in values]
    for item in values:
        if 'catalogue' in item.get('name','').lower() and item.get('uses','').startswith('actions/cache'):
            assert item['with']['path']=='state/catalogue-shadow/sealed.bin'
            assert 'restore-keys' not in item['with']
            assert item['continue-on-error'] is True
    assert names.index('Prepare fresh catalogue cache probe')<names.index('Restore newly saved catalogue for verification')<names.index('Publish verified catalogue checkpoint')
    publish=values[names.index('Publish verified catalogue checkpoint')]
    assert 'catalogue_probe.outputs.cache-hit' in publish['env']['CACHE_HIT']
    run=values[names.index('Run job alerts')]
    assert 'JOBBIE_CATALOGUE_KEY' not in run['env']
    assert 'DISCORD_WEBHOOK_URL' in run['env']


def test_crypto_install_is_optional_and_budget_probe_is_readonly():
    values=steps();names=[x.get('name') for x in values]
    optional=values[names.index('Install optional catalogue transport')]
    assert optional['continue-on-error'] is True
    assert 'requirements-catalogue.txt' in optional['run']
    seal=values[names.index('Seal bounded catalogue checkpoint')]
    assert 'actions/cache/usage' in seal['run']
    assert 'storage-limit' not in seal['run']


def test_retention_waits_for_remote_custody_commit_and_has_no_record_deletion():
    values=steps();names=[x.get('name') for x in values]
    retention=values[names.index('Retain bounded redundant catalogue transports')]
    assert names.index('Commit catalogue custody metadata')<names.index('Retain bounded redundant catalogue transports')
    assert "catalogue_commit.outcome == 'success'" in retention['if']
    assert 'prune-transport' in retention['run']
    assert retention['continue-on-error'] is True

# P2 original-source reliability audit

Observed 2026-11-11. Baseline main `9779cd0` includes P2-UX1 merge e0346f49bd572179250fe08bed73131db0ba311a. No public job text is treated as agent instructions.

## Production snapshot

[Job Alerts 43032487797](https://github.com/KanujVerma/jobbie/actions/runs/43032487797), schedule, source da898dc817e4e8da23e14dfecede74d98657e981. Heartbeat: duration 484.02s; finish-to-next-start gap 28373.03s; 12/13 responding, 1 failed, 2 empty; 2 matched, 309 review, 9002 excluded, 0 job ACKs, 0 failed job sends. These counters do not count successful health/digest webhook sends. No P2-UX1 live delivery established. Previous scheduled [run 42968108020](https://github.com/KanujVerma/jobbie/actions/runs/42968108020) also completed, at e0346f4. Neither the cron expression nor successful Actions conclusion establishes a latency SLA.

| Original source | Fetch result | Fetched | Matched | Review | Excluded |
|---|---|---:|---:|---:|---:|
| Micron | response | 2884 | 0 | 13 | 2871 |
| Salesforce | response | 1574 | 0 | 16 | 1558 |
| CrowdStrike | response | 378 | 0 | 3 | 375 |
| Intel | response | 879 | 0 | 8 | 871 |
| Applied Materials | response | 2000 | 1 | 12 | 1987 |
| Western Digital | response | 334 | 0 | 1 | 333 |
| SanDisk | empty response | 0 | 0 | 0 | 0 |
| Plaid | HTTP 404 | 0 | 0 | 0 | 0 |
| Oracle | empty response | 0 | 0 | 0 | 0 |
| Microsoft Research | response | 149 | 0 | 3 | 146 |
| Microsoft | bounded recent window | 210 | 0 | 15 | 195 |
| Amazon | bounded configured queries | 505 | 1 | 178 | 326 |
| Apple | bounded configured searches | 400 | 0 | 60 | 340 |

Zero matches from a source may reflect freshness/location/qualification exclusion or missing evidence, not employer-wide absence. Candidate and reason counts were not in this old snapshot; they remain unknown. P2-R1 adds them for future runs. Employer-wide completeness/false-negative rates are NOT_MEASURED. Legacy source schemas may omit descriptions/requirements or cap coverage. The audit does not certify all relevant openings discovered.

## Reproduced defects and evidence

- Original adapters swallowed request failures, including 403/404/429; main counted normal generator termination as a healthy empty/partial scan. Focused pre-fix regression: 26 failed, 3 passed. BaseAdapter now records sanitized query failures; multi-query sources continue other queries and preserve partial observations. Main marks scans failed and does not report recovery from partial data.
- `load_state` persisted v1 migration even in dry-run. A byte-invariance regression failed before the fix; read-only callers now migrate only in memory. Malformed nested state fails closed instead of becoming fresh state.
- Failed Discord request exceptions and response bodies could enter logs. Logs now retain only exception type/HTTP code. Successful webhook responses log an acknowledgement without URL/payload. This is instrumentation, not a live send test.
- Empty SanDisk public API response independently returned HTTP 200 with totalFound=0; Oracle HCM independently returned HTTP 200/items=[]/count=0. These do not establish no jobs at the employer. No authenticated endpoint, session handshake, bypass or speculative scraping was attempted.
- Plaid's configured Lever endpoint is 404 in production. [Official careers page](https://plaid.com/careers/) still lists roles; [one official role](https://plaid.com/careers/openings/engineering/new-york-city-office/software-engineer-backend-2/) links to [Plaid's Ashby application](https://jobs.ashbyhq.com/plaid/7e10c0b5-a09a-4e07-aaa8-899a7f82a0c9/application). This establishes a source migration, not new-grad eligibility (sample requires 2-4 years). [Ashby public API documentation](https://developers.ashbyhq.com/docs/public-job-posting-api) and [Plaid robots](https://plaid.com/robots.txt) were read. Restoring this existing employer needs a separately tested source migration with dedup/baseline protection; no production config changed in P2-R1. Do not guess that old Lever IDs map to new Ashby IDs.

## Rollout and remaining gates

P2-R1 adds public metadata/counters and a read-only `python main.py health --format json|markdown` command. Actions publishes the snapshot, with its finish time/age, even after a failed step. An absent or stale snapshot cannot establish current health. Revert code/workflow to roll back; keep state and roster. No policy version, alert cap, backfill/rate-limit rule or existing alerted flag is reset.

Local final suite observed: `.venv/bin/pytest -q` -> 869 passed in 32.98s on Python 3.15.2; `.venv/bin/python main.py validate-config`, compileall and `git diff --check` passed. CI Python 3.12, review, merge and new runtime evidence must be recorded when observed. Plaid migration, unresolved SanDisk/Oracle coverage, cron delays and live delivery remain explicit follow-up work, not fixed by observability.

## Additional source-repair finding for P2-R2
The read-only dry-run sent Amazon's configured gated-category mapping as the literal query keys `category` and `require_early_career`, rather than its configured category string. Reproduction appears in the request log. This is a source-query defect, not a reason to relax new-grad eligibility or add roles. Repair it separately with request-shape and eligibility regression tests alongside other state-safe original-source repairs.

## Read-only dry-run receipt

Command: `DISCORD_WEBHOOK_URL="" .venv/bin/python main.py run --dry-run --verbose`. Exit 0; no sender constructed, no Discord sends, no state/config writes. The full scan was performed during P2-R1 authoring; final unit tests cover the added corrupt-state/logging guards.

```text
Micron: fetched=2891 matched=0 review=13 excluded=2878 candidates=0 alerted=0
Salesforce: fetched=1574 matched=0 review=15 excluded=1559 candidates=0 alerted=0
CrowdStrike: fetched=379 matched=0 review=3 excluded=376 candidates=0 alerted=0
Intel: fetched=879 matched=0 review=8 excluded=871 candidates=0 alerted=0
Applied Materials: fetched=2000 matched=1 review=12 excluded=1987 candidates=0 alerted=0
Western Digital: fetched=335 matched=0 review=1 excluded=334 candidates=0 alerted=0
SanDisk: fetched=0 matched=0 review=0 excluded=0 candidates=0 alerted=0
Plaid: fetched=0 matched=0 review=0 excluded=0 candidates=0 alerted=0
Oracle: fetched=0 matched=0 review=0 excluded=0 candidates=0 alerted=0
Microsoft Research: fetched=149 matched=0 review=3 excluded=146 candidates=0 alerted=0
Microsoft: fetched=206 matched=0 review=16 excluded=190 candidates=0 alerted=0
Amazon: fetched=508 matched=3 review=179 excluded=326 candidates=2 alerted=0
Apple: fetched=400 matched=0 review=67 excluded=333 candidates=0 alerted=0
duration=462.97s, gap=20481.78s, scheduler_gap=True, adapters=12/13 (zero=2), matched=4, review=317, excluded=9000, alerted=0
```

SHA-256 before and after matched exactly:

```json
{
  "exit_code": 0,
  "before": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3",
    ".github/workflows/job-alerts.yml": "062266ff3dd69e4497d456fc216588b69608b3a67522ea83960c1b70b728ba38"
  },
  "after": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3",
    ".github/workflows/job-alerts.yml": "062266ff3dd69e4497d456fc216588b69608b3a67522ea83960c1b70b728ba38"
  },
  "unchanged": true,
  "discord_webhook_env": "empty",
  "mode": "dry-run"
}
```

## Independent review correction S1 and final local checks

Sol round 1 on 4c3af988687b95e5f51ede5a7f3baf2a0eb08e3a found that malformed health timestamps/counters could crash after an earlier source sent, losing its unsaved ACK. Parent reproduced all six two-source cases before the fix (6 failed). State loading now validates these fields before any sender can be constructed. The same cases pass and preserve original file bytes. The docs README and UX status were also reconciled (S2).

Latest full `.venv/bin/pytest -q`: **875 passed in 32.59s**, Python 3.15.2. Config validation, compileall, diff-check and read-only health loading of the actual production snapshot passed. Final guarded-state dry-runs with empty webhook environment: SanDisk exit 0 (empty API response), Plaid exit 1 (sole selected source is 404). Both preserve configuration and seen-state hashes; no sender or sends. These targeted checks supplement the earlier full scan; neither proves live delivery. Candidate Python 3.12 CI and hosted review still pending.

```json
{
  "checks": [
    {
      "command": [
        ".venv/bin/python",
        "main.py",
        "run",
        "--company",
        "SanDisk",
        "--dry-run",
        "--verbose"
      ],
      "exit_code": 0
    },
    {
      "command": [
        ".venv/bin/python",
        "main.py",
        "run",
        "--company",
        "Plaid",
        "--dry-run",
        "--verbose"
      ],
      "exit_code": 1
    }
  ],
  "before": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "after": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "unchanged": true,
  "webhook_environment": "empty",
  "source_reads_only": true
}
```

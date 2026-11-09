# P1-E production verification evidence

This record documents the verified post-P1-E production execution of the `Job Alerts` scheduled workflow on `main`, resolving the outstanding operational release gate for Phase 1 (Issue #6).

## Ancestry verification
- P1-E squash merge commit: `9c9365ae5f3d936b20fc8a90c7ac22a5e0c6ff42`
- Production run source commit: `ffc8c09bd2ec0cbcb7dd48143204c26255324bcb`
- Direct ancestry verification:
  ```bash
  git merge-base --is-ancestor 9c9365ae5f3d936b20fc8a90c7ac22a5e0c6ff42 ffc8c09bd2ec0cbcb7dd48143204c26255324bcb
  # Exit code 0 (verified true)
  ```
- Post-run commit: `62e8fdb` (`state: 2026-11-09T21:09:41Z`)

## Workflow execution record
- **Workflow:** Job Alerts (`.github/workflows/job-alerts.yml`)
- **Run URL:** https://github.com/KanujVerma/jobbie/actions/runs/42698015121
- **Job ID:** 129434952835
- **Event:** `schedule`
- **Trigger/Start Time:** 2026-11-09T20:58:28Z
- **Completion Time:** 2026-11-09T21:09:41Z
- **Duration:** 11m 19s (heartbeat duration=666.83s)

## Observed counters and metrics
From the verified production execution log (`job 129434952835`):
- `adapters`: 12/13 succeeded
- `zero`: 2 adapters returned zero postings
- `matched`: 0
- `review`: 277 postings sent to review queue
- `excluded`: 8,844 postings classified as excluded
- `alerted`: 0 (no jobs matched candidate criteria; zero alerts sent to Discord)
- `duration`: 666.83s
- `gap`: 37,588.38s (626.5 minutes elapsed since previous run)
- `scheduler_gap`: True

## Operational observations and limitations
1. **Pipeline Execution Proof:** Proves end-to-end execution of the post-P1-E codebase in production GitHub Actions environment under live network conditions without crashing.
2. **Zero Matches vs Suitability:** Zero matches is proof of filter execution and safe non-delivery; it is NOT proof that no suitable jobs exist across all employers, nor does it guarantee matching accuracy. No synthetic alerts were injected or forced.
3. **Plaid Lever 404:** Plaid's public Lever endpoint returned `404 Client Error: Not Found for url: https://api.lever.co/v0/postings/plaid?mode=json`. This is an upstream source failure/migration, tracked as an ongoing operational limitation.
4. **Scheduler Drift:** Actions schedule drift resulted in a 626.5-minute gap between runs (nominal cadence is ~15 minutes). GitHub Actions cron delays remain an external platform characteristic.

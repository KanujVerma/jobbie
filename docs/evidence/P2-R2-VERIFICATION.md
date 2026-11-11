# P2-R2 verification and remaining source limits

Scope: existing Plaid and Amazon only; no roster expansion. Parent P2-R1 #30 merged at 614b3edc14e86d952579a0c57db0eb68669c08d9. Source-repair candidate is not merged or production-verified yet.

## Reproductions and regressions

Amazon production config stores gated categories as mappings. The old adapter encoded the mapping keys into category[] rather than category text. A request-shape regression failed before the fix; string and mapped category configurations retain the same deterministic eligibility pipeline.

Plaid's old Lever endpoint returns 404. [Plaid's own role](https://plaid.com/careers/openings/engineering/new-york-city-office/software-engineer-backend-2/) links to [its Ashby application](https://jobs.ashbyhq.com/plaid/7e10c0b5-a09a-4e07-aaa8-899a7f82a0c9/application). The provider ID is verified from that employer-controlled link, not guessed. [Ashby public Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api) documents the read-only listing endpoint. No login/session/paid service or alternate route is used.

The new source_revision guard records first-observed provider IDs before filtering with baseline_suppressed, leaving alerted=false and URL ACK history unchanged. Only a complete scan finishes the revision; partial/failed scans remain pending. Current source rows can be reviewed under the existing bounded digest, but no baseline posting becomes an individual or migration-backfill send. Later new IDs pass through existing eligibility/freshness/dedup/failed-send ACK. Old original IDs and sent flags remain.

Focused regression development: 7 source/query/baseline cases initially failed; after implementation 10 runtime/schema cases initially failed and then passed. A reporting regression caught a completed baseline still labeled pending; reporting now distinguishes this scan's baseline operation from a transition still pending after the scan. Final source-repair suite: 24 passed. Full suite: **900 passed in 35.71s**, Python 3.15.2; validate-config, compileall and diff-check passed. Production-snapshot/corrupt-state, 403/404/429 and failed-send cases remain in the full suite.

## Read-only source and dry-run receipts

These are public listing observations and local no-mutation proof, not delivered alert evidence. The direct API pipeline drop count precedes main's stale-posting eligibility reassessment; it must not be described as all jobs definitively ineligible.

```json
{
  "retrieved_at": "2026-11-11T20:04:30.546349+00:00",
  "source": "https://api.ashbyhq.com/posting-api/job-board/plaid?includeCompensation=true",
  "official_careers": "https://plaid.com/careers/",
  "ownership_evidence": "https://plaid.com/careers/openings/engineering/new-york-city-office/software-engineer-backend-2/",
  "official_apply_link": "https://jobs.ashbyhq.com/plaid/7e10c0b5-a09a-4e07-aaa8-899a7f82a0c9/application",
  "normalized_count": 143,
  "state_written": false,
  "discord_sent": false,
  "source_ids_unique": true,
  "sample_public_urls": [
    "https://jobs.ashbyhq.com/plaid/5d8abedc-018a-4b42-ae1f-0e70b34f2007/application",
    "https://jobs.ashbyhq.com/plaid/4cc6c985-40cc-472f-94cd-90807c698b50/application",
    "https://jobs.ashbyhq.com/plaid/4c51247f-8da5-4fa3-b331-7da94b76bdac/application"
  ],
  "pipeline_counts_before_stale_reassessment": {
    "dropped_before_stale_reassessment": 143
  }
}
```

Guarded main dry-run: fetched 143, matched 0, review 8, excluded 135, candidates 0, sent 0. The empty webhook environment prevents sender construction. Config and original seen-state bytes remain identical; the source transition is only in memory during dry-run.

```json
{
  "exit_code": 0,
  "before": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "after": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "unchanged": true,
  "discord_sent": false,
  "webhook_environment": "empty"
}
```

## Source limits carried forward

- [SanDisk official careers](https://www.sandisk.com/careers/jobs-at-sandisk) links to https://avature.sandisk.com/Careers. The tool read returned HTTP 406. No retry via another route, auth bypass or speculative scraper is permitted. Its old SmartRecruiters response was HTTP 200/zero, which does not prove no openings. Access/coverage for the replacement is blocked pending permitted verification.
- [Oracle official careers](https://www.oracle.com/careers/) links to its US search. Public HTML identifies data-sitenumber=CX_45001 and the official location ID. [Oracle's CE list documentation](https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-recruitingcejobrequisitions-get.html) defines finder/site/limit/offset. A single unauthenticated nonredirecting documented finder GET returned two rows and advertised TotalJobsCount=2113; root count=1/hasMore=false describe the search envelope, not completion of job pagination. The old unscoped request returned empty. A separate Oracle query/pagination/date/URL repair is needed; no invented no-openings or complete-coverage claim.
- GitHub cron remains best effort; no scheduler SLA or replacement is introduced. No P2-UX1 actual delivered-message proof is established here.

## Rollout/rollback

Only Plaid's provider/config changes in the original 15-source production file; its enabled/network/cohort/referral fields remain unchanged, with a new explicit source revision. First complete live scan seeds IDs silently. Revert code/config for rollback, preserving the same seen ledger and both providers' history. No state reset, manual seeding, forced backfill or fake delivery ACK.

Independent review, exact-head CI, authorized merge and a real ordinary post-merge scheduled observation remain required. The catalogue, feeds, new employers, private profile and applications are out of scope.

## Modernization onto merged intake

PR31's actual conflict with main after #32 was resolved by preserving the current intake docs and adding source contracts, while replaying the same source code. Stable functional patch ID before/after is d3c04a39c60a21e63ef209bb22872ee5b273f992 across main/source/config/health/storage/tests. Current seen state is byte-identical to main, including the ordinary Amazon ACKs. Historical900test/5d034f5 review receipts remain historical; combined current-head tests and fresh CI/review are separate gates.

PR31 modernization proof: combined full952tests passed36.35s (source repair plus merged intake), config/compileall/diff passed. Plaid targeted no-webhook dry-run exited0 with identical state/config hashes. Current state matches main exactly; no reset/seed/manual edits. Fresh full-head CI/hosted review remains required.

```json
{
  "old_functional_patch_id": "d3c04a39c60a21e63ef209bb22872ee5b273f992",
  "rebased_functional_patch_id": "d3c04a39c60a21e63ef209bb22872ee5b273f992",
  "identical": true
}
```

```json
{
  "command": [
    "/Users/kanuj/Documents/projects/jobbie/.venv/bin/python",
    "main.py",
    "run",
    "--company",
    "Plaid",
    "--dry-run",
    "--verbose"
  ],
  "exit_code": 0,
  "before": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "after": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "unchanged": true,
  "webhook_environment": "empty",
  "discord_sent": false
}
```

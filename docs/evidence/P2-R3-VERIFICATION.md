# P2-R3 Oracle verification (candidate, not merged)

Owner scope: repair the existing Oracle source, preserving 13 enabled original sources and 2 historical disabled. This candidate depends on P2-R2's silent source-revision baseline and must be rebased onto merged main before its PR.

## Primary-source reproduction

[Oracle careers](https://www.oracle.com/careers/) links to [its US search](https://careers.oracle.com/en/sites/jobsearch/jobs?location=United%20States&locationId=300000000149325). Public HTML exposes `data-sitenumber=CX_45001`. [Official CE GET collection documentation](https://docs.oracle.com/en/cloud/saas/human-resources/farws/op-recruitingcejobrequisitions-get.html) specifies the findReqs finder and siteNumber/limit/offset/locationId variables. No authentication, session handshake or browser was used.

The old unscoped endpoint returned HTTP 200 with count=0/items=[]. The documented scoped finder returned a search envelope with root count=1/hasMore=false, inner TotalJobsCount=2113 and requisitionList rows. The root count does not count jobs or govern their pagination. Real rows use ShortDescriptionStr, ExternalQualificationsStr, ExternalResponsibilitiesStr, date-only PostedDate and nullable employment/qualification fields.

The old parser ignored the Str fields, created a naive datetime from a date-only source and constructed /jobs/{Id}. For public requisition 347942 the old route redirected; [the verified site route](https://careers.oracle.com/en/sites/jobsearch/job/347942) returned HTTP 200 with the matching job title in og:title. Candidate URLs are constructed only from a validated official site root and numeric source requisition ID; arbitrary source ExternalURL values are not used.

## Implemented behavior and tests

Optional site-specific finder mode uses bounded GET responses, fixed API path, validated provider/site/location parameters, explicit page bounds and actual search-row pagination. Empty/malformed/incomplete/repeated pages and changed search totals remain distinct. Partial rows survive in main while health records failure and cannot finish the baseline. Legacy fixture/config mode remains compatible.

Dates with an actual timezone retain their timestamp. Date-only values remain a source calendar date with no exact posted_at; the card says time unknown. Missing/naive time stays unknown and uses the existing first-observation freshness fallback. This does not invent a posting clock time or timezone. Source calendar date persists in the review queue for later catalogue work.

Full supplied qualification/responsibility fields reach deterministic eligibility. Missing fields set description_complete=false and unknown employment remains unknown. A regression exposed the explicit qualification form 'Required: United States citizenship' being accepted; a narrow line-anchored required-clause alternative fixes it, with negative tests for optional/not-required citizenship. No candidate citizenship is inferred and no eligibility threshold is relaxed.

The initial six finder/date/description/link regressions failed before correction. A malformed-row regression also failed before typed normalization, then passes while keeping other rows and failing health. Fixtures cover 403/404/429, unsafe config/URLs, duplicates/page cap/changed totals, corrupt schema, qualifications completeness, non-full-time types and truthful date rendering. Final `.venv/bin/pytest -q`: 937 passed in 39.84s on Python 3.15.2; source/legacy Oracle tests 53 passed. Config validation, compileall and diff-check passed. No mocked test establishes delivered alerts.

## Full read-only source scan

At 2026-11-11T21:05Z, the corrected US finder read **2113 unique normalized rows across 22 pages**. Main reported fetched=2113, matched=0, review=19, excluded=2094, candidates=0, sent=0; fetch duration 77.07s. Missing qualification/employment facts and explicit exclusions explain the screen; this is not a claim that Oracle has no eligible openings. Employer-wide completeness/false-negative recall is NOT_MEASURED. No protected detail endpoint or prohibited scraping was attempted.

The empty webhook environment prevents sender construction; silent baseline exists only in memory in dry-run. State/config SHA-256s match before/after:

```json
{
  "retrieved_at": "2026-11-11T21:05:05.605123+00:00",
  "command": [
    ".venv/bin/python",
    "main.py",
    "run",
    "--company",
    "Oracle",
    "--dry-run",
    "--verbose"
  ],
  "exit_code": 0,
  "before": {
    "companies.yaml": "8afbe552edb59566e6bedf604510337bf5d1e3a6cc02c02f1b8161dd0ece12f0",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "after": {
    "companies.yaml": "8afbe552edb59566e6bedf604510337bf5d1e3a6cc02c02f1b8161dd0ece12f0",
    "state/seen_jobs.json": "2588081d4ca27f33ed6135ac541e6e8be275d32cbb803de8f22e1a200e2235e3"
  },
  "unchanged": true,
  "webhook_environment": "empty",
  "discord_sent": false
}
```

## Rollout/rollback and pending gates

Only the existing Oracle source gains verified site/location/careers config and source_revision; enabled/network/cohort/referral are unchanged. First complete ordinary corrected scan silently baselines IDs before filtering; no false ACKs, state reset or forced backfill. Bounded health/review summaries retain normal policy. Later new IDs follow the existing eligibility/dedup/ACK path.

Rollback config and code together, keeping all source/history/ACK state and restoring the old known empty-query limit. New fields are additive. P2-R2 merge, independent review, exact-head hosted review/CI, authorized merge and actual ordinary scheduled observation are pending. SanDisk access, cron delays, optional feed rights, intake, catalogue and live delivery remain separate gates. No Phase 2 completion claim.

## Local review correction S1
At eda6d416d5c147fa1538952e538cab0a124baf59 Sol found that partly overlapping pages could reach the raw row total with missing unique IDs. Parent reproduced [1,2]/[2,3] advertised total4, observed no error/incorrect baseline completion, and fixed duplicate-ID detection to retain useful unique partial rows while reporting failure. Baseline completion now remains pending; a later complete [1,2]/[3,4] scan silently includes ID4. Regression failed before fix; full suite 938 passed in35.08s. Fresh independent re-check pending.

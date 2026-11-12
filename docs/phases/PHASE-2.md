# Phase 2 executable contract — broaden job discovery without losing original cohort

STATUS: PARTIAL. P2-A #23 and P2-UX1 #29 are merged. Live P2-UX1 delivery is unverified. Owner instruction 2026-11-11 authorizes completing all feasible remaining Phase 2 across scoped PRs, without automatic roster/feed expansion. See STATUS and the delivery plan for actual evidence.

## P2-A: direct company ATS adapters
- Add reusable Greenhouse and Ashby read-only adapters under `src/adapters/` with fixture contracts for pagination/HTTP failures/rate limits/descriptions, salary structured fields and locations. Maintain existing BaseAdapter/Job compatibility or migrate through a tested normalization layer.
- Board discovery: explicit company IDs/board tokens validated against official employer career page. Add candidate startup boards only when public endpoints and terms permit. No job-board user login or bypassing blocks.
- Show direct employer link, source ID and fetch observation time. Synthetic fixture cannot establish a live opening. Tests against fixture and allowed live read-only smoke.
- Merge only if existing 13 continue working; run source-specific health checks.

## P2-R1/R2 and owner-directed P2-ACT
- P2-R1: audit original 13 fetch, eligibility reasons, errors, scheduler gaps and delivery; fix reproduced false-health and dry-run defects with regression proof. Preserve partial results while surfacing failures.
- P2-R2: repair independently verified original-source migrations with identity reconciliation and suppression of historical alerts. No replacement/new employer is implicitly approved. Missing ownership/permission or a risky cutover is an explicit blocker.
- P2-UX1 is merged (#29). Synthetic payloads and workflow success do not prove live delivery.
- [P2-ACT](PHASE-2-ACT.md) is now an owner-directed issue/CLI proposal workflow. Accept company name, optional careers URL, role/location, priority, and monitor versus startup-research. Verify aliases, official ATS ownership/ID, access permission, health and actual listings. Generate disabled reviewable config proposals; preserve original 13 plus 2 historical disabled. Discovered never means confirmed referral. Dot compatibility is a portable request, not a fabricated trigger.

## P2-B: licensed/allowed curated feeds
- Source candidates: New-Grad-Jobs public output; SimplifyJobs list, Jobright public GitHub list, Freehire API, other aggregators ONLY after per-source license/robots/terms/data rights are documented. Reuse publicly licensed scraper code only where license allows.
- For every feed record retain original source and employer apply URL; mark discovery-only until official employer listing reconfirmed. If data rights unclear, leave feature disabled and mark `blocked_source_rights`, never invent permission.
- Maintain separate feeder provenance and refresh cadence; track closed/stale jobs without claiming hiring intent. Implement backoff, failure isolation, per-source quotas and size caps.
- Count number of unique eligible US roles and percentage of employer-link confirmations using repeatable evaluation samples, not marketing claims.

## P2-C: canonical catalogue / dedup and phase rollout
- Persist ALL validated normalized postings before per-user filtering; preserve originals and source history. Compare stable req-ID and canonical URLs; remove tracking params, do not merge distinct requisitions with identical title/location.
- Use versioned `job_id` mapping and reclassification of older data; old webhook dedupe remains valid during dual-write. A Phase 1 source must not be skipped because new source failed.
- Evaluate Cloudflare D1 or equivalent $0-capability, but do not force paid architecture or embed secrets in public GitHub. If backend not funded/free, retain a bounded SQLite artifact with documented sync and move later.
- Emit source label `network_priority` vs `discovered`, source attribution and employer-verified link confidence. Stage a shadow-run at least 72h with duplicate/coverage counters and rollback before switching canonical source.
- Tests: 30+ cross-source identity cases, source outage/corrupt feed, tracking URLs, reopened role, timezone/freshness, no duplicate/network-flag loss. Live smoke verified with exact links.

**Phase 2 completion:** all feasible components implemented, merged, tested and rollback-ready; original alerts preserved. Company/feed expansion is opt-in. Unknown feed rights -> BLOCKED_SOURCE_RIGHTS with tested disabled capability. Missing activation/cutover approval -> BLOCKED_APPROVAL. Missing >=72h real shadow -> BLOCKED_72H_EVIDENCE. Do not label those operational gates satisfied from fixtures. Observe a real scheduled run after an explicitly authorized canonical cutover.
## P2-A historical implementation packet (COMPLETED; NOT NEXT)
1. Verify current `main`, CI, post-P1E scheduled scan and [Phase 1 tracker #6](https://github.com/KanujVerma/jobbie/issues/6). If missing live verification, record BLOCKED_LIVE rather than pretending it occurred.
2. Inspect `src/adapters/base.py`, `src/adapters/__init__.py`, `src/models.py`, `src/config.py`, `src/http.py`, `src/notifier.py`, `main.py` and adapter fixture idioms. Preserve the frozen `Job` constructor and current CLI.
3. Confirm official Greenhouse/Ashby public job posting API formats, pagination, response limits, allowed fetch frequency and exact direct apply URLs using official documentation at execution time. Do not invent board IDs or use unauthorized authenticated endpoints.
4. Implement reusable Greenhouse and Ashby adapters using `HTTPClient` and current adapter registry, plus timeout/429/error handling and explicit source attribution. Emit only source-backed fields; do not mark jobs employer-verified from mock fixtures. Keep missing salary, date, role type as unknown rather than making up data.
5. Add fixtures covering empty board, multi-page/multi-location results, 429/403/404, malformed JSON, missing descriptions, requirement split and compensation with correct base units; ensure supplier-specific URLs cannot expose tokens in logs.
6. Initially configure ZERO additional active companies without a documented verified board token, employer source and permission. Add a small explicit approved sample after real read-only smoke. Never give discovered companies network priority.
7. Run all existing tests plus adapter tests; compare before/after original 13 source throughput; keep state unchanged in dry run, avoid flooding Discord. Prove one *permitted* live read-only fetch.
8. Update `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/RELEASE_LOG.md` and adapter contract docs, then PR review. P2-B is blocked until P2-A merged and tested. P2-C requires source rights, canonical state dual-write and 72-hour shadow evidence.

This scope is about **adding read-only discovery adapters**, not a Cloudflare migration, LLM matching, automated application submission, or resume processing.

## P2-A implementation and release
P2-A is MERGED into `main` via PR #23 (`ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb`).
All 812 tests passed in main CI run #42720639467. The adapters are available but remain
disabled in production (examples in `examples/p2a-public-boards.yaml`). Original 15
configured / 13 enabled Network Priority production sources remain unchanged.


## P2-B candidate interface
See PUBLIC_FEEDS.md: feed-check plus an optional default-OFF manifest hook, bounded public JSON leads, provenance/health/dedup and exact confirmation using approved employer records. Current candidates are all OFF/BLOCKED_SOURCE_RIGHTS with no owner feed approval. Metadata/policy and synthetic tests are not dataset coverage. Missing rights does not block the independent catalogue; legacy JSON remains delivery authority.

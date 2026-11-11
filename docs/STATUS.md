# Jobbie canonical project status

Audited 2026-11-11. This is a snapshot. Verify current main, PRs and Actions before acting.

## Released code and live limits

Canonical repository: KanujVerma/jobbie, numeric ID 1339847701. Main inspected at `9779cd0` (state-only successor of `da898dc`), with P2-A #23 merged at `ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb` and P2-UX1 #29 merged at `e0346f49bd572179250fe08bed73131db0ba311a`. P2-UX1 post-merge [Tests run 42944213890](https://github.com/KanujVerma/jobbie/actions/runs/42944213890) succeeded. Synthetic cards are not delivered messages.

Production configuration remains 15 source entries: exactly 13 enabled original Network Priority sources and 2 historical disabled sources (Snowflake, Applied Digital). Greenhouse/Ashby example boards are disabled. No optional feeds, catalogue, private profile, AI or application executor is production enabled.

[Scheduled Job Alerts run 43032487797](https://github.com/KanujVerma/jobbie/actions/runs/43032487797), at `da898dc817e4e8da23e14dfecede74d98657e981`, completed successfully on 2026-11-11: 12/13 adapters responding, Plaid Lever HTTP 404, SanDisk and Oracle empty responses, 2 matched, 309 review, 9002 excluded, 0 job sends acknowledged and 0 failed job sends. The gap after the previous finish was 28373.03 seconds (472.9 minutes), versus a configured 15-minute target. A successful workflow is not source health, a no-openings claim, or evidence of P2-UX1 webhook delivery: **LIVE_DELIVERY_UNVERIFIED**.

## Active Phase 2 completion work: PARTIAL

The 2026-11-11 owner instruction replaces mandatory P2-ACT expansion with owner-directed company intake. No automatic 3-5-employer expansion. Company and feed activation are opt-in and never prerequisites to completing independent implementation. See [delivery plan](superpowers/plans/2026-11-11-phase-2-completion.md).

P2-R1 candidate fixes reproduced swallowed request errors in original adapters and v1 state writes during dry-run. Partial observations remain usable but the scan is failed, not healthy. Adds fetch timing, filter-reason/candidate/ACK counters, a read-only `health` command and an Actions summary; failed send logs omit webhook URLs/response bodies. Existing eligibility, dedup, alert caps, rate limiting and backfill remain authoritative. Exact test, dry-run and review evidence is recorded in the PR and [audit](evidence/P2-RELIABILITY.md). Candidate is not yet a merged or live-verified release.

Remaining scoped implementation: P2-ACT request/proposal workflow, P2-B disabled lawful-feed capability, P2-C SQLite catalogue with legacy delivery authority, shadow comparison and rollback. No production employer is approved by this task. Missing rights remain **BLOCKED_SOURCE_RIGHTS**; activation and cutover remain **BLOCKED_APPROVAL**; the required 72-hour shadow is **BLOCKED_72H_EVIDENCE** until actually observed.

## Next major phase

After Phase 2 implementation and its operational gates, execute P3-A signed, allowlisted Discord interactions, then private resume/profile storage, owner-confirmed evidence and deterministic matching. Resume tailoring and owner artifact approval remain Phase 4. Application submission remains Phase 5 and requires a separately approved exact packet. No dot API or trigger has been verified.

Historical release evidence: [P2-A](evidence/P2-A-VERIFICATION.md), [P1-E](evidence/P1-E-PRODUCTION-VERIFICATION.md), [RELEASE_LOG](RELEASE_LOG.md). Preserve the existing production state; never force backfill or reset it to generate proof.

P2-R1 review checkpoint: S1's malformed-health ACK-loss path reproduced (6 failing two-source cases), then fixed with pre-delivery validation; S2 stale onboarding rows corrected. Latest full local suite: 875 passed in 32.59s; config/compileall/health/diff checks passed. Final SanDisk/Plaid no-webhook dry-runs returned 0/1 respectively (empty/404) with unchanged state/config hashes. Sol round 2, candidate CI/hosted review and merge remain pending.

Sol-loop round 2 approved behavior at fbb13745f4f64a3ede9a6b169fcb086d78eb94b1, resolving S1/S2; independent suite 875 passed in 36.66s and reliability suite 49 passed. Hosted exact-head review, Python 3.12 CI and merge remain pending. See evidence/P2-R1-REVIEW.md.

Hosted review H1 (ef4d864) found that an all-failed/partial scan can save successful delivery ACKs locally but return 1, causing Actions to skip Commit state. Reproduced with a synthetic partial scan: one successful fake send, failed run result, ACK saved locally, missing workflow failure override. The regression failed before correction and now passes. Commit state now runs after an executed scan succeeds or fails, excluding cancellation/skipped scans; the workflow still reports the scan failure. No live failure or test send was induced. New exact-head CI/hosted review required before merge.

H1 correction verification: `.venv/bin/pytest -q` passed 876 tests in 33.01s; validate-config, compileall and diff-check passed. Updated workflow failure-path execution is covered by a synthetic partial-scan ACK regression plus configuration checks, not a forced live outage.

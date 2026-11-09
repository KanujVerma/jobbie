# Jobbie canonical project status

**Audited:** 2026-11-09 America/Chicago. This is a snapshot, not continuous telemetry. Verify GitHub HEAD, PRs and Actions before acting.

Canonical repository: **KanujVerma/jobbie**, ID 1339847701. Repository rename is complete. Current inspected main is `ecb553fa652750e32f5eb8ec775ae7da70285a86` (squash-merge of Phase 2A PR #23).

## Completed release: Phase 2A, PR #23
- **PR:** https://github.com/KanujVerma/jobbie/pull/23
- **Branch:** `feat/p2-a-public-job-boards` (merged and closed)
- **Status:** MERGED to main at `ecb553fa652750e32f5eb8ec775ae7da70285a86`.
- **Production Status:** MERGED, NOT PRODUCTION_ENABLED. New Greenhouse and Ashby public adapters are tested and available in codebase; sample boards in `examples/p2a-public-boards.yaml` remain disabled. Production `companies.yaml` is unchanged with the original 15 configured / 13 enabled sources.
- **Reviewed runtime source:** `5e56bc668a6615002b5ac0fbe8592b2a84987162`.
- **Full CI:** Pre-merge CI passed at https://github.com/KanujVerma/jobbie/actions/runs/42342377756 and https://github.com/KanujVerma/jobbie/actions/runs/42343188762 (812 passed). Post-merge main CI passed at https://github.com/KanujVerma/jobbie/actions/runs/42720639467 — **812 passed in 45s**, Python 3.12, config validation and documentation gate passed.
- **Live public reads:** Actions run https://github.com/KanujVerma/jobbie/actions/runs/42342377775 (19 Greenhouse + 73 Ashby) and re-verified locally on merge prep (20 Greenhouse + 76 Ashby). All classified excluded on these provider-owned smoke boards. These counts are source connectivity/normalization proof, NOT new-grad matches.
- **Side effects:** receipts verify identical `companies.yaml` and `state/seen_jobs.json` hashes before/after; no Discord sender was constructed or called; examples remain disabled.
- **Independent review:** Codex completed review of `5e56bc6` with `has_any_findings=false`, `has_unresolved_findings=false`. Receipt: https://github.com/KanujVerma/jobbie/pull/23#issuecomment-6702690334 .
- **Durable evidence:** [P2-A verification record](evidence/P2-A-VERIFICATION.md), [unaltered live JSON](evidence/P2-A-live-2026-11-07.json), and [P1-E production verification](evidence/P1-E-PRODUCTION-VERIFICATION.md).

## Implemented P2-A functionality
`GreenhouseAdapter` and `AshbyAdapter` use official public GET endpoints and the existing HTTPClient/registry. Shared validation bounds response size/job count/detail requests, prevents arbitrary endpoints/redirects and preserves unknown fields. Prospect/unlisted jobs are excluded. Posting IDs, descriptions, location options, explicit employment, published-versus-updated dates and salary units retain their source meaning. HTML inline formatting cannot disconnect years from an experience requirement. Structured non-full-time types and incomplete descriptions cannot become verified new-grad alerts just because of a title.

The normal filter, immutable Job model, notification-payload builder, review queue, config validator and dry-run pipeline are integrated. `scripts/verify_public_boards.py` produces metadata-only read receipts without calling the notification loop. No database, LLM, private documents, feed scraping or application submission was added.

## Existing production system and constraints
- The original Python GitHub Actions monitor remains unchanged in production configuration: 15 configured sources, original 13 enabled, 2 disabled.
- Original network priority: Micron, Salesforce, CrowdStrike, Intel, Applied Materials, Western Digital, SanDisk, Plaid, Oracle, Microsoft Research, Microsoft, Amazon, Apple. Network priority does not mean a referral has been submitted.
- Phase 1 A/B/C (#12–14), D1/D2/D3 (#15–17), E (#18) code is merged. P1-E source commit is `9c9365ae5f3d936b20fc8a90c7ac22a5e0c6ff42`.
- **Phase 1 issue #6 post-P1-E production verification is SATISFIED:** Scheduled `Job Alerts` run #42698015121 (job 129434952835) completed on 2026-11-09 at source commit `ffc8c09bd2ec0cbcb7dd48143204c26255324bcb`, which is a verified descendant of P1-E (`9c9365ae`). Heartbeat metrics: duration=666.83s, adapters=12/13 (zero=2), matched=0, review=277, excluded=8844, alerted=0. Zero matches proves filter execution and safe non-delivery; it is not proof that no suitable jobs exist.
- Known limitations tracked separately: GitHub's nominal 15-minute cron has observed multi-hour gaps (run 42698015121 had a 626.5-minute gap). Plaid's known Lever 404 is an upstream endpoint failure.
- Phases 2B/2C and 3–6 remain PLANNED. The two P2-A example boards are outside production config and disabled; no new ongoing job alerts are active.

## Next steps
Phase 2A is complete and merged. Per instructions, stop after Phase 2A. Do not start P2-B or P2-C. Any future activation of additional employers requires source-grounded verification, separate owner authorization, and isolated PRs.

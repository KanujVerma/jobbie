# Engineering release and verification log

**Docs-continuity hardening:** [PR #19](https://github.com/KanujVerma/jobbie/pull/19) implements the canonical handoff and per-functional-PR documentation gate. Codex review found that deleted handoff docs were initially accepted by changed-file inspection; fixed with head-tree existence checks and regression cases. Both PR #19 and its corrective PR #21 have now merged; verified CI and reviewer evidence is logged below. Neither PR changes live job alert behavior.

This is an **append-only summary of verified engineering milestones**, not a claim that every implemented feature is currently working live. Each entry has a code/CI/review layer distinct from user-facing live operational evidence. More detailed logs are in GitHub PRs, Actions and phase documents. Runtime state-only commits are NOT separate product releases.

## 2026-11-06: P1-E final corrective code
- [PR #18](https://github.com/KanujVerma/jobbie/pull/18) **merged**; squash source commit `9c9365ae5f3d936b20fc8a90c7ac22a5e0c6ff42`.
- Work: `src/experience.py` adds bachelor-relevant experience-path checks, protects mandatory vs preferred qualification clauses; `src/eligibility.py` abstains on 2–4-year stretch conditions and prevents using a lower unrelated master/PhD or tool skill number; `src/backfill.py` and `main.py` acknowledge only displayed, confirmed-delivered URLs in batches of 10. Original state format, source cohort and CLI preserved.
- Evidence: [CI run #42329594922](https://github.com/KanujVerma/jobbie/actions/runs/42329594922) **716 passing tests** on branch with reconciled live-state main. Codex reviewed identical source code at `69acbe23dc9aede2dd881eb52bc72a2b0972da47` and reported **no findings** (see PR #18 discussion). Final merge-state commit only adds latest `state/seen_jobs.json`, no source deltas from reviewed blob set.
- **Operational qualification:** No post-merge full production scan recorded during documentation authoring. Earlier Intel alerts were under older classifier and must not be portrayed as examples of genuine new-grad roles. Source merged and tested, live post-release check pending.

## 2026-11-05: Phase 1D quality hardening
- [PR #15](https://github.com/KanujVerma/jobbie/pull/15) `e1608cf6223d21ef7ebaf2ce565c0e96f0159970`: seniority/location and Workday-detail checks.
- [PR #16](https://github.com/KanujVerma/jobbie/pull/16) `c9acd1cffc8ce11cca27c3821b3b0d0d29249acd`: migration and notification safety, rerunnable backfill, failed Lever API source accounting.
- [PR #17](https://github.com/KanujVerma/jobbie/pull/17) `b920f706d20b94a45d02261ed97ec911d0d85094`: automated CI, release evidence. [CI #41953363672](https://github.com/KanujVerma/jobbie/actions/runs/41953363672) **654 tests passed**, Codex finished final review with no major issues.
- Live scheduled scans subsequently reported 2 and 1 confirmed-delivery Intel job alerts in state heartbeats; eligibility of those actual jobs was subsequently questioned and is not independently confirmed.

## 2026-11-04: Phase 1 original implementation
- [PR #12](https://github.com/KanujVerma/jobbie/pull/12) `476975d043600e9d467c4c7e46f4d4c2e1a60a65`: deterministic eligibility, adversarial fixtures.
- [PR #13](https://github.com/KanujVerma/jobbie/pull/13) `ebca5eadc1cdff463564e972bd7ea0c648f45e63`: original 13 network-priority labels, unconfirmed referral metadata.
- [PR #14](https://github.com/KanujVerma/jobbie/pull/14) `9f94b560cf1600d6e933a1c6c0535084c611d63c`: versioned state, basic backfill, dedup and diagnostics.
- [Manual Actions #41915003368](https://github.com/KanujVerma/jobbie/actions/runs/41915003368) succeeded with 0 eligible matches/0 new-grad alerts. That was **workflow execution proof**, not a successful product-match proof.

## 2026-11-04: canonical documentation foundation
- [PR #1](https://github.com/KanujVerma/jobbie/pull/1) `c3e9dd130da5aeecfbf857155c2afe4209cd2f51`: AGENTS, locked product/security/data contracts, six-phase plan, phase-by-phase /code objectives and PR template.
- Original repository later renamed from `job-alert` to `jobbie`. Verified current canonical name and same repo ID before this log; no second repository created.

## Future release log protocol
Every functional PR must append a concise entry naming its PR slot, actual commit/CI URLs and truthful stage: `IMPLEMENTED`, `TESTED`, `LIVE_VERIFIED`, `BLOCKED_LIVE`, or `RELEASED`. Never invent a final merge SHA before merge; use "pending actual squash" and update after merge. No secret values or private resume contents. Update `docs/STATUS.md` and `docs/HANDOFF.md` in the same PR; CI enforces three-file handoff continuity.

## 2026-11-06: handoff documentation and follow-up gate hardening
- [PR #19](https://github.com/KanujVerma/jobbie/pull/19) merged `7458d18299b1ab36b25a221990ef2fd6d265252c` with canonical current state, cold-agent handoff, release log, accurate README and initial CI doc guard. 725 tests passed on PR CI; subsequent Codex review found test HTML and git-renamed source paths bypassing the guard.
- [PR #21](https://github.com/KanujVerma/jobbie/pull/21) merged `dbb309a6b30bbf90cf4fa2d887052467d8760720` and actually changes `scripts/check_handoff_docs.py` + `tests/test_handoff_gate.py` to count HTML fixtures and include source deletion paths on rename (`--no-renames`). [CI #42331100940](https://github.com/KanujVerma/jobbie/actions/runs/42331100940) **727 passing**, Codex final review with no findings. This is documentation CI hardening, no new runtime job sources or code changes to the scanner.

## 2026-11-06: P2-A initial implementation checkpoint (historical)
- Branch `feat/p2-a-public-job-boards`, baseline `d98afe7367`; issue #20.
- Public Greenhouse/Ashby adapters; registry/config, optional immutable source metadata, typed employment exclusions, preserved pay units/date meaning, read-only smoke CLI and disabled example targets. No source code copied from external repos; existing HTTPClient/BaseAdapter reused against official APIs.
- Local initial full regression: **803 passed in 32.68s**, before the final two URL regressions and seven HTML review regressions. Remote checks were pending at this initial checkpoint; the later verified record below supersedes that pending state.
- No production employers enabled, Discord test messages or historical state edits. Temporary transfer workflows/files removed from final diff.

## 2026-11-07 UTC / 2026-11-06 Chicago: P2-A verified source checkpoint
- **Implementation PR #23:** https://github.com/KanujVerma/jobbie/pull/23 . Source `5e56bc668a6615002b5ac0fbe8592b2a84987162`; PR remains open for remaining operational/merge gates, not production-enabled.
- **CI #42342377756:** https://github.com/KanujVerma/jobbie/actions/runs/42342377756 . **812 passed in 32.95s** (727 baseline + 85 new), config valid, documentation continuity PASS, Python 3.12.16.
- **Live read-only #42342377775:** https://github.com/KanujVerma/jobbie/actions/runs/42342377775 . GET requests observed 19 Greenhouse and 73 Ashby postings; all were classifier-excluded on these smoke boards. Metadata receipt confirms unchanged config/state hashes, no Discord sends and production_enabled=false.
- **Independent Codex review:** https://github.com/KanujVerma/jobbie/pull/23#issuecomment-6702690334 . Completed with no findings on exact runtime source `5e56bc6` after fixing inline HTML splitting numeric tenure from experience. Added seven regression cases before re-review.
- **Durable proof:** [verification narrative](evidence/P2-A-VERIFICATION.md) and [raw receipt](evidence/P2-A-live-2026-11-07.json). Receipt source SHA `00111df...` is the synthetic PR merge checkout of 5e56bc6 into d98afe7, NOT a production merge.
- **Remaining:** Phase 1 issue #6 post-P1-E runtime check, final-head consistency, conditional merge/post-merge CI, separately authorized employer activation. Existing original 13 company config and history unchanged. Gemini should follow [exact completion runbook](agent-prompts/PHASE-2A-VERIFY.md), not reimplement source or start Phase 2B/C.

## 2026-11-09: Phase 1 post-P1-E production verification
- **Workflow:** Job Alerts (`.github/workflows/job-alerts.yml`), scheduled run https://github.com/KanujVerma/jobbie/actions/runs/42698015121 , job 129434952835.
- **Source:** commit `ffc8c09bd2ec0cbcb7dd48143204c26255324bcb`, verified direct descendant of P1-E squash `9c9365ae5f3d936b20fc8a90c7ac22a5e0c6ff42` via `git merge-base --is-ancestor`.
- **Observed telemetry:** Duration 666.83s, adapters 12/13, zero 2, matched 0, review 277, excluded 8844, alerted 0. Scheduler gap 626.5 minutes. Plaid Lever API returned HTTP 404 (tracked source limitation). State committed as `62e8fdb`.
- **Disposition:** Proves production execution of the post-P1-E pipeline without crash; resolves the outstanding operational prerequisite in issue #6. Zero matches is not proof that no suitable jobs exist. Durable evidence recorded in `docs/evidence/P1-E-PRODUCTION-VERIFICATION.md`.

## 2026-11-09: P2-A squash merge release
- **PR #23:** https://github.com/KanujVerma/jobbie/pull/23 on `feat/p2-a-public-job-boards`.
- **Merge Commit:** `ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb` (squash-merge to main).
- **Code invariance:** Runtime code in `src`, `tests`, and `.github/workflows` remains 100% byte-identical to independently reviewed source `5e56bc668a6615002b5ac0fbe8592b2a84987162`.
- **Pre-merge Verification:** Config validation PASS, compileall PASS, 812 tests PASS in 31.01s. Documentation continuity PASS. Local live read smoke observed 20 Greenhouse and 76 Ashby postings, all excluded, zero state/config mutation, `discord_sent=false`, `production_enabled=false`.
- **Post-merge Main CI:** https://github.com/KanujVerma/jobbie/actions/runs/42720639467 passed in 45s (812 tests).
- **Status:** MERGED, NOT PRODUCTION_ENABLED. Production companies remain the original 15 configured / 13 enabled sources; example boards in `examples/p2a-public-boards.yaml` remain disabled.


## 2026-11-10 owner-approved architecture and roadmap amendment (DOCUMENTATION ONLY)
- Scope: clearer source-grounded webhook notifications, owner-approved activation of verified public boards, private resume diff/PDF preview, separate one-job `Approve & Apply`, dot-first application handoff feasibility with local browser fallback, startup outreach and application results. Explicit per-job authorization supersedes older blanket "no autoapply" design; NO bulk or unapproved submissions.
- Planned PR sequence: `P2-UX1` first, `P2-ACT` next, `P2-B` feeds then `P2-C` catalogue; P3 private commands/ledger/evidence; P4 resume review/packet; P5 dot/manual+controlled browser executor; P6 outreach/reminders. See [PHASES.md](PHASES.md), [AUTO_APPLY.md](AUTO_APPLY.md), [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md).
- Actual runtime remains Phase 2A source release [PR #23](https://github.com/KanujVerma/jobbie/pull/23), merge `ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb`, post-merge docs [#24](https://github.com/KanujVerma/jobbie/pull/24) at `58b108c07e070725dbde181d4d0fb8c1b62d8917`. Previous full hashes in docs had mismatched suffixes; corrected here. Main later advanced through state-only commit(s), which do not represent new product features.
- No live source config, state, Discord webhook, dot, AI calls or browser apply behavior changed by this documentation update. The new executor plan is speculative until actual integration tests; status `SPECIFIED` only. First functional PR should add clear notification payload with synthetic tests and existing live alert compatibility.

## 2026-11-10: P2-UX1 presentation candidate
- Candidate base: `1d943c9b105d7309b04acf9c44ea3e641cc00c56`. Exact PR head, CI and review evidence must be obtained from GitHub; no merge or live send is asserted here.
- Before: card title prioritized tags and could label unknown roles verified. After: title and company first, separate network/referral, disclosed source-backed Ashby base pay, deterministic screen, conservative date provenance, and a source link. The review digest bounds and sanitizes untrusted content. [Four synthetic payloads](evidence/P2-UX1-synthetic-previews.json) are not live evidence.
- Privacy: no candidate profile, private contact, credentials or resume fields are added; hostile text is escaped and bounded. Delivery rate limiting, existing sender result and state dedup are retained. An unsafe individual URL displays unavailable but existing successful-send acknowledgement is unchanged; digest URLs over 200 UTF-16 units are omitted.
- Rollback: revert this presentation PR without resetting state. Live webhook and actual employer-link behavior remain unverified until an approved destination or natural alert provides independent evidence.
- Local candidate checks: `python main.py validate-config` returned `Config is valid.`; `python -m compileall -q src scripts` exited 0; `pytest -q` returned `824 passed in 32.07s` on Python 3.15.2. These are local uncommitted candidate checks, not Python 3.12 CI or live delivery evidence.
- No-webhook dry run on the candidate using `env -u DISCORD_WEBHOOK_URL python main.py run --dry-run --verbose`: exit 0, 449.00s, adapters 12/13, matched 2, review 312, excluded 8994, alerted 0. This tests source reads and dry-run behavior, not webhook delivery. The three protected files match their base Git blobs.
- Independent Sol review found a hidden review-digest eligibility blocker and an unknown verdict level overwritten by the legacy role label. Both were reproduced using `apply_filter_pipeline` and corrected; a focused re-review is required before shipping.
- After the two review fixes: `python main.py validate-config` returned `Config is valid.`, `python -m compileall -q src scripts` exited 0, and `pytest -q` returned `826 passed in 34.03s` on Python 3.15.2. Exact-head Python 3.12 CI and live delivery remain pending.
- Independent Sol re-review approved the changed behavior, resolved both findings, and independently ran 826 tests on Python 3.15.2. This does not substitute for hosted exact-head review or CI.

## 2026-11-11: Phase 2 completion audit and P2-R1 candidate
- Confirmed P2-UX1 #29 merged at e0346f49bd572179250fe08bed73131db0ba311a; post-merge Tests 42944213890 succeeded. Current owner scope supersedes UX-only and mandatory P2-ACT expansion.
- Production schedule 43032487797 on da898dc: 12/13 responding, Plaid 404, 2 matched/309 review/9002 excluded, 0 job ACKs/failures, 472.9-minute gap. No verified P2-UX1 live delivery.
- Candidate fixes reproduced legacy failure masking and dry-run v1 migration writes; adds partial-failure health, source/filter/candidate/ACK timing reports, Actions summary, corrupt-state guard and secret-safe webhook logs. Original roster/config/seen state remain unchanged. Initial focused reproduction: 26 failed/3 passed before fixes. Full final tests/review/CI/merge evidence belongs in the PR; not yet a released or live-verified claim. See evidence/P2-RELIABILITY.md.
- Rollback code/workflow only, retain state. Remaining independent PRs: original-source repair, owner intake, OFF feeds, SQLite catalogue/shadow/search/export. Missing approval/rights/72h remain explicit gates.

- P2-R1 local verification checkpoint: 869 tests passed in 32.98s (Python 3.15.2), config/compileall/diff-check passed. Full no-webhook dry-run exited 0; production config and seen-state SHA-256s unchanged. This proves read-only execution, not live delivery. PR CI/review/merge pending.

P2-R1 review checkpoint: S1's malformed-health ACK-loss path reproduced (6 failing two-source cases), then fixed with pre-delivery validation; S2 stale onboarding rows corrected. Latest full local suite: 875 passed in 32.59s; config/compileall/health/diff checks passed. Final SanDisk/Plaid no-webhook dry-runs returned 0/1 respectively (empty/404) with unchanged state/config hashes. Sol round 2, candidate CI/hosted review and merge remain pending.

Sol-loop round 2 approved behavior at fbb13745f4f64a3ede9a6b169fcb086d78eb94b1, resolving S1/S2; independent suite 875 passed in 36.66s and reliability suite 49 passed. Hosted exact-head review, Python 3.12 CI and merge remain pending. See evidence/P2-R1-REVIEW.md.

Hosted review H1 (ef4d864) found that an all-failed/partial scan can save successful delivery ACKs locally but return 1, causing Actions to skip Commit state. Reproduced with a synthetic partial scan: one successful fake send, failed run result, ACK saved locally, missing workflow failure override. The regression failed before correction and now passes. Commit state now runs after an executed scan succeeds or fails, excluding cancellation/skipped scans; the workflow still reports the scan failure. No live failure or test send was induced. New exact-head CI/hosted review required before merge.

H1 correction verification: `.venv/bin/pytest -q` passed 876 tests in 33.01s; validate-config, compileall and diff-check passed. Updated workflow failure-path execution is covered by a synthetic partial-scan ACK regression plus configuration checks, not a forced live outage.

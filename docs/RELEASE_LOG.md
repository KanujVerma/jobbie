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

## 2026-11-11: ordinary live ACKs and owner-intake candidate
- Scheduled43100310762 on merged R1 614b3ed acknowledged2individual Amazon payloads withHTTP204 and persisted state f3deaae;12/13sources,4matched/323review/8994excluded,430.4min gap. No test message/dispatch/reset. Scoped UX webhook issue25 closed; client visual rendering/independent employer eligibility not claimed.
- P2-ACT local candidate: issue/form/portableCLI/evidence/aliases and fixed-source health, always disabled proposals and separate research requests. Full928tests passed31.74s, intake52cases; config/compileall/diff pass. Verification-only source/CLI reads and Amazon no-webhook dry-run preserved state/config. No additional owner company request/approval or source activation. Review/CI/merge pending. Rollback removes intake code/form only.

P2-ACT local review approved b58076cf7dcd7153a860841023ac246fb5f8280a in one round, independently passing928tests in36.74s, config/diff checks. No findings. Own PR/exact-head CI/hosted review/merge are still pending; production activation is not approved. See evidence/P2-ACT-REVIEW.md.

P2-R2 local candidate checkpoint, NOT merged: dependent branch feat/p2-source-repairs based on P2-R1 ef4d864. Amazon mapping query regression reproduced/fixed; source_revision baseline preserves old ACKs and suppresses initial provider rows without claiming delivery; next new IDs use existing delivery. Plaid official Ashby API normalized 143 unique rows, with first-scan silence. Local full suite 894 passed in 37.31s; config/compileall/diff and no-mutation Plaid dry-run passed. Only Plaid adapter/config changes; original 13 enabled/unconfirmed sources and 2 disabled remain. This candidate is preserved locally while PR #30's hosted all-partial-run state-commit finding is fixed. No PR, independent review or production release for P2-R2 yet. Source rights research and live receipts are under /tmp/jobbie-p2-r2-* and /tmp/jobbie-p2-feed-rights-research.json; copy only summarized provenance into future PR docs. SanDisk official new ATS returned 406, no bypass; Oracle empty HCM cause unresolved. Next: finish PR #30, rebase this branch onto merged main, finish source-repair edge cases/docs/review/CI before its PR.

## 2026-11-11: P2-R1 merged (#30)
- Merge `614b3edc14e86d952579a0c57db0eb68669c08d9`, reviewed head 7a74936d22033c14abc2eac564c3db29edee09db. Exact-head Tests 43094232460 and public-read 43094232452 succeeded; hosted code review completed with both finding flags false. Merge tree equals reviewed tree. Local suite 876 passed in 33.01s. Post-merge Tests 43095321312 queued at observation. No current scheduled-run/live-webhook success claimed.
- Source failure visibility, read-only migration safety, pre-send corrupt-health rejection, secret-safe webhook logs and source health reports. Hosted H1 corrected Actions state persistence after failed/partial runs while preserving the failed result. Production roster/config/seen ledger unchanged. Rollback code/workflow while retaining state.

## 2026-11-11: P2-R2 candidate verification (unmerged)
Amazon request-shape fix and Plaid's source-verified Ashby migration are isolated from roster expansion. Silent source_revision baseline keeps alerted=false plus an explicit suppression reason, preserves original history and reports pending/completed truthfully. Local suite 900 passed in 35.71s, config/compileall/diff passed. Read-only source 143 unique rows; guarded dry-run 0 matched/8 review/135 excluded/0 sends and unchanged state/config hashes. Independent review, exact-head CI/hosted review, merge and real schedule remain pending. See evidence/P2-R2-VERIFICATION.md; rollback reverts code/config together without state reset.

P2-R2 local Sol review approved implementation e09dc61b7e377d336b11a91c905781daf8c2d6f4 in one round, independently passing 900 tests in 33.27s. No findings. PR/hosted review/CI/merge and actual production observation remain pending; no live delivered-message claim. See evidence/P2-R2-REVIEW.md.

## 2026-11-11: P2-ACT merged and PR31 conflict resolution
- Intake #32 merged f46625845577f158da31974d927aa5748d0c3642 after exact-head checks/hosted review; post-merge Tests43114825827 passed. No company activated; new-source approval remains separate.
- PR31 MODERNIZE: main's intake changes caused a real conflict. Rebase preserves production state and source runtime behavior; functional patch ID unchanged from5d034f5. Documentation retains both source baseline and intake invariants. Current combined tests/CI/review evidence is recorded next; no old approval is promoted into a fresh-head CI pass.

PR31 modernization proof: combined full952tests passed36.35s (source repair plus merged intake), config/compileall/diff passed. Plaid targeted no-webhook dry-run exited0 with identical state/config hashes. Current state matches main exactly; no reset/seed/manual edits. Fresh full-head CI/hosted review remains required.

## 2026-11-11: P2-R3 Oracle candidate (not merged)
Documented site-scoped finder replaces the erroneous empty unscoped query; inner pagination, requirement fields, official route and date precision are normalized. Live read-only scan: 2113 unique US-search rows/22 pages, 0 matched/19 review/2094 excluded/0 sends, unchanged state/config hashes. Full local suite 937 passed in 39.84s; config/compileall/diff passed. Narrow required-clause citizenship regression and optional negatives verified. Parent P2-R2 and own reviews/CI/merge/live schedule remain gates; no additional employer or fake ACK.

P2-R3 local review S1 correction: overlapping pages [1,2]/[2,3] with advertised total4 previously completed a three-ID baseline. Parent reproduced the failing regression, then records DUPLICATE_REQUISITION while retaining unique partial rows; completion remains pending and a later complete scan silently includes the previously omitted ID. Full suite 938 passed in 35.08s; final focused re-check also covers the completed retry. Fresh local re-review pending.

New real operational evidence: scheduled Job Alerts 43100310762 on merged R1 614b3ed ran 21:07:18-21:14:55Z. Two individual Amazon candidates received HTTP204 ACKs at21:14:30Z, and state commit f3deaae persisted them. This establishes ordinary webhook acceptance, not visual-client or employer-eligibility verification. R2/R3 remain unmerged and unobserved in production.

P2-R3 Sol round2 approved b7112bcf4b30d277050a1556858f4e049093a62c with S1 resolved and no new findings. Independent full938tests passed in35.35s, source38passed; config/diff passed. The source branch is published for GitHub handoff while parentPR31 CI remains queued. It is not a production release or own PR/CI/hosted-review pass. Rebase onto merged parent before filing the scoped Oracle PR.

## 2026-11-11: P2-R2 merged; Oracle integration candidate
PR31 merged9317c73b1971d6c7bb19dcb22a6be76876ad7369 after exact-head81524a6 CI/hosted review; post-merge Tests43116984772 passed, merge tree equals reviewed tree. Ordinary Plaid production baseline PENDING_LIVE: no qualifying post-merge schedule exists at check. Oracle rebased onto this parent, functional patch unchanged from its local approval; own PR/CI/review/live gates pending.

Oracle integration verification: rebase onto merged9317c73 retains functional patch76c6409fe877a5fac07570fb78aa05916a71fc1e. Combined full990tests passed36.78s; config/compileall/diff pass, current main seen-state retained unchanged. Local Oracle behavior was independently approved atb7112bc with938tests before base integration; own current-head hosted review/CI/merge remain required.

Hosted H1 correction: the explicit citizenship matcher rejected a clause that also accepts permanent residency. Parent reproduced4failing alternative clauses, then checks the immediate continuation for an accepted residency/green-card alternative while retaining any separate mandatory citizenship clause. Five focused cases now pass. No personal status is inferred. Fresh exact-head hosted review/CI required; prior local review remains scoped to its earlier head.

Oracle H1 verification: full995tests passed38.93s;5focused clauses, config/compileall/diff passed. A separate mandatory clause still excludes correctly. This does not repeat live source/client rendering or approve production cutover.

P2-B local candidate: bounded OFF JSON leads, provenance/health/source dedup and exact approved-employer URL/ID confirmation. All3candidate feeds remain disabled with BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL; no feed dataset fetched. At base9317c73, full990tests passed37.30s, focused38 including generated URL invariants. Config/compileall/diff and no-mutation OFF feed-check/Plaid dry-run passed. Rebase onto newly merged Oracle #33, then repeat combined checks/current-head review/CI. No catalogue/72h/cutover claim.

Oracle PR33 merged4eb83f454e2671e8e06d7cb10f4b079ab98fcf90 after current-head e976032 checks/clean hosted review. Oracle/Plaid first ordinary production baselines remain PENDING_LIVE until a qualifying schedule. P2-B is integrated onto this merged parent; all3feeds remain OFF/rightsblocked, with no data-source activation. See PUBLIC_FEEDS.md and evidence/P2-B-VERIFICATION.md.

P2-B review corrections: supported source posting-ID confirmation and order-independent duplicate posting-date conflicts, reproduced before fixed. Fresh head checks/hosted review required; no feed/company enabled.

P2-B hosted correction: index official posting URLs once per employer when leads exist, preserving ID ambiguity/permission gates and protecting original delivery timing. Reproduced4000before/120after normalizations in normal-poller fixture. Fresh CI/review required.

## P2-C1 local catalogue candidate
SQLite source snapshots/identity and lifecycle evidence, versioned reclassification, query/history/JSONL/CSV CLI. No normal-run hook, source activation, state reset or delivery/cutover change. C2 pre-filter persistent shadow/parity/rollback and actual72h evidence still required. See CATALOGUE.md; release gates pending.

B actual release: PR34 merged f3a61f4ab2d5165474ffddf63ac0e052b4a75fdb; exact-head CI/hosted review and postmerge43128988343 passed. C1 candidate rebased onto this merge, full1105passed44.19s/64focused, permitted Plaid source capture143normalized rows/0identity conflicts and no-mutation CLI/dry-run proof. C1 review/CI/merge and C2 shadow gates remain pending.

C1 review correction: historical unseen listings respect already retained newer complete absence evidence, preserving source history and current status regardless of ingestion order. Reproduced before fixed; fresh checks/review/CI required.

C1 hosted correction: exclude synthetic Ashby URL fallback/unknown composite IDs from native recovery; later real posting ID links via URL without conflicts. Initial H1 run1failed/1108passed; no legacy state change or activation. New head review/CI required.


Evidence correction: a654434 prematurely recorded the H1 test run as passing. Actual full result was1failed/1108passed: the weak URL source-record claim still blocked reconciliation. The source/provider compatibility correction and fresh result supersede that failed attempt; no merge/approval is claimed for a654434.

C1 final H1 correction: weak URL claims excluded from native incompatibility;69focused/full1110passed37.69s. Earlier a654434 failure remains explicitly recorded. Live/no-mutation proof repeated; new exact-head release gates required.

C1 hosted ambiguity/lifecycle correction: no retry identity inflation, matching URL alias closure/reopen, unrelated/moved URL safety and registered native alias compatibility.75focused/full1116passed40.54s; live/no-mutation check passes. Fresh exact-head gates pending.

C1 H4 correction: historical alias ingestion respects later explicit closure without spurious old reopen; genuine newer reopen remains.77focused/full1118passed39.68s. Exact-head gates pending; no production cutover. C2 draft checkpoint published independently, not released.

## Ordinary repaired-source verification2026-11-12
Run43140198821, state d4724df: Plaid143/Oracle2113silent complete baselines with0new job ACKs, all257prior seen ACK flags/10URL entries retained.13successful responses/1empty SanDisk;600.08s/301.43minute gap. No manual seed/reset/dispatch. Source baselines VERIFIED_LIVE; catalogue shadow/cutover not deployed. C1 refreshes current-head gates after retaining this new production state.

C1 rebased onto actual ordinary state d4724df, preserving baseline/ACK history exactly. Full1118tests pass; permitted local source/CLI/dry-run byte proof repeated on new state. New head CI/hosted review required.

C2 WIP checkpoint only: pre-filter shadow comparison/ACK/memory dry-run and encrypted checkpoint helpers/CLI, optional crypto boundary and feed rights claims.30focused/1137fulltests passed42.13s on C1 ce304905 base. Not deployed or ready for PR: efficient logical scan membership, persistent workflow, primary receipt audit and final gates remain required. No activation/cutover/source-state reset.

C1 PR35 merged1614d804 after exact0be562f CI/clean hosted review; postmerge43148218676 passed. C2 local candidate now has efficient exact logical history, shadow comparisons/ACK receipts, encrypted bounded roundtrip custody workflow and optional-dependency isolation. Full1163passed40.76s before own rebase. No key/deployment/72h/cutover success claim. Capacity before/after fixtures committed separately from live source evidence.

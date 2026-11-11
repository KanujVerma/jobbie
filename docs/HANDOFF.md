# Jobbie agent handoff

Read STATUS.md, AGENTS.md, DECISIONS.md, PHASES.md, the exact phase spec, CONTRACTS.md, SECURITY.md, OPERATIONS.md and EVALS.md. GitHub plus committed files is sufficient context. Never require private resumes for Phase 2.

## Current scope and verified starting point

Owner instruction 2026-11-11: full-send ALL remaining Phase 2 across scoped PRs, with independent reviews and exact-head CI before authorized merges. Main inspected at `9779cd0`; P2-A #23 and P2-UX1 #29 are merged. The old instructions to stop at UX or require a mandatory expansion cohort are superseded. The [durable implementation plan](superpowers/plans/2026-11-11-phase-2-completion.md) gives files, tests, migrations and rollback.

Original production roster is 13 enabled Network Priority sources, referral unconfirmed, plus 2 historical disabled. No specific additional employer/feed or production catalogue activation is authorized. Company requests default discovered and never imply referral. Startup research must remain separate from monitoring/live openings. Dot-compatible means a portable request document, not an invented API or automatic trigger.

## Production evidence and active candidate

Scheduled [run 43032487797](https://github.com/KanujVerma/jobbie/actions/runs/43032487797) on da898dc: 12/13 responding, Plaid Lever 404, Oracle/SanDisk empty API responses, 2 matched, 309 review, 9002 excluded, 0 job ACKs, 0 job send failures, 472.9-minute finish-to-next-start gap. P2-UX1 delivered-message proof remains unestablished. See [audit](evidence/P2-RELIABILITY.md). Do not call empty adapters proof of no openings or workflow success proof of delivery.

P2-R1 is an unmerged candidate at authoring: source query errors remain visible while preserving partial observations, dry-run v1 migration no longer writes, health/report counters and Actions summary are additive, failed webhook logs redact sensitive data. Next: finish verification, Sol-loop and hosted exact-head review, CI, merge, record actual evidence. No source activation/state edits occur in P2-R1. Rollback code while retaining production state.

Then implement P2-ACT owner intake/proposals, P2-B bounded OFF feeds with rights evidence, P2-C SQLite pre-filter catalogue and search/export. Complete independent work despite rights/approval/shadow blockers. Canonical cutover requires >=72h real dual-write comparison, identity/alert reconciliation, proven rollback, explicit approval and an observed scheduled run after cutover. Existing state stays delivery authority until then.

## Verification and handoff discipline

Use the existing virtual environment (`.venv/bin/python`, `.venv/bin/pytest` locally; CI uses Python 3.12). Run full pytest, validate-config, compileall, docs continuity, safe read-only source checks and a dry-run with an empty webhook environment. Preserve before/after state/config hashes. No unapproved test send, reset, forced backfill, expensive infrastructure or private data in logs/commits. Every functional PR updates STATUS/HANDOFF/RELEASE_LOG and impacted specs. Record actual PR/head/merge/review/CI/run evidence, not agent activity as progress.

After Phase 2 gates, next exact major goal is P3-A signed allowlisted Discord interactions, followed by private profile/resume upload/evidence and matching. Phase 4 tailors resumes; Phase 5 alone executes a single separately approved application. No application or outreach sends are in the current task.

## P2-R1 verification checkpoint (2026-11-11)
Branch feat/p2-reliability, base 9779cd08b3c0a7e40fb3fda6cd53bae1e5a0d908. Local `.venv/bin/pytest -q`: 869 passed in 32.98s; validate-config/compileall/diff-check passed. Full no-webhook dry-run exited 0 with unchanged companies.yaml/seen-state/workflow hashes; see the audit receipt. All candidate work is unmerged until PR CI/review/merge evidence is recorded. Next concrete action: Sol-loop review of the base-to-working-tree diff, then hosted Codex review/CI and authorized merge. Continue P2-R2 and other scoped components afterward.

P2-R1 review checkpoint: S1's malformed-health ACK-loss path reproduced (6 failing two-source cases), then fixed with pre-delivery validation; S2 stale onboarding rows corrected. Latest full local suite: 875 passed in 32.59s; config/compileall/health/diff checks passed. Final SanDisk/Plaid no-webhook dry-runs returned 0/1 respectively (empty/404) with unchanged state/config hashes. Sol round 2, candidate CI/hosted review and merge remain pending.

Sol-loop round 2 approved behavior at fbb13745f4f64a3ede9a6b169fcb086d78eb94b1, resolving S1/S2; independent suite 875 passed in 36.66s and reliability suite 49 passed. Hosted exact-head review, Python 3.12 CI and merge remain pending. See evidence/P2-R1-REVIEW.md.

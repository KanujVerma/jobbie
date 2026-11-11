# Jobbie incremental delivery roadmap — current 2026-11-10 owner plan

**Evidence:** Phase 1 and Phase 2A were implemented/merged; P2-A Greenhouse/Ashby API reads verified but no additional employer boards are production enabled. See [STATUS.md](STATUS.md) for actual main HEAD. ALL future slots listed here are **PLANNED**, not implementation claims. PR slot IDs are stable design labels, not GitHub numeric PRs.

## Delivery principle
One small user-usable release at a time. Each functionality PR must keep earlier job polling/alerts available, pass full regression tests, receive independent review and update STATUS/HANDOFF/RELEASE_LOG. No huge one-shot implementation, no pseudo-buttons, no mass applications, no silent paid provider use.

| Order | PR slot / phase | User-visible completion | Dependencies |
|---|---|---|---|
| Shipped | Phase 1 + hardening (#12–18) | New-grad filtering and original 13 Network Priority stars | Existing bot |
| Shipped code | P2-A (#23, docs #24) | Official Greenhouse and Ashby read-only adapters available, **not activated** | Phase 1 |
| **Next** | **P2-UX1 — Alert card v2** | Readable source-grounded Discord webhook cards; existing job links work | P2-A merged |
| After UX | P2-ACT — Controlled board activation | 3–5 individually verified + owner-approved discovered employers monitored when available | P2-UX1; source rights |
| Then | P2-B — permitted new-grad feeds | Broader leads, verified employer originals, source provenance, no unauthorized scraping | P2-ACT |
| Then | P2-C — canonical catalogue | Global identity, dedup/history, safe state dual-write + 72h shadow, future private search substrate | P2-B |
| 3A | P3-A — Signed Discord interactions | Real private buttons/commands, allowlist, durable task status | P2-C |
| 3B | P3-B — Private store + basic app ledger | Saved jobs, owner-only docs/versioned uploads, append-only application event/attempt records | P3-A |
| 3C | P3-C — Candidate evidence | Owner-confirmed facts and explicitly approved GitHub project evidence, no private leaks | P3-B |
| 3D | P3-D — Ranking/search | Deterministic fit explanations; AI only where verified and budgeted | P3-C |
| 4A | P4-A — Resume quality bench | Role/company evidence selection, 24-case benchmark, provider privacy/quality | P3-D |
| 4B | P4-B — Fact-preserving tailored drafts | Structured edit ops, unsupported-claim rejection, source traceability | P4-A |
| 4C | P4-C — PDF/DOCX rendering | Immutable previewable one-page PDF/DOCX with hashes and parse/layout tests | P4-B |
| 4D | P4-D — Private edit approval + packet draft | Authenticated before/after review with why; `Approve resume` and `Prepare application packet` (UNSENT, unapproved for submission) | P4-C |
| 5A | P5-A — Dot feasibility pilot | One approved single-job manual dot handoff, actual outcome and supported-trigger investigation | P4-D |
| 5B | P5-B — App executor protocol | Authenticated one-job packet, approval digest, idempotent attempts, receipts, pause/rollback | P5-A |
| 5C | P5-C — Browser fallback | Optional local scoped Playwright/Stagehand for employer forms if dot can't act | P5-B; site permissions |
| 5D | P5-D — Approved submission rollout | Owner-approved real application with authoritative confirmation and audit, fail closed on uncertainties | P5B/C as needed |
| 6A | P6-A — Startup discovery | Verified employer roles vs proactive outreach targets; product/project match evidence | P5 gate |
| 6B | P6-B — Contact + approved outreach | Public business contacts and individually approved email, no LinkedIn auto-DM | P6-A |
| 6C | P6-C — Follow-ups and feedback | Application reminders, recruiter/response statuses, outcome-informed ranking, privacy/export | P6-B |

**Optional operational mini-PR:** P2-OPS1 may assess more reliable $0-compatible scheduling once actual source activation makes timely delivery important; do not treat the existing `*/15` GitHub cron as a delivery SLA. Do not sneak this into P2-UX1.

## Release boundaries
- P2-UX1 is PRESENTATION-ONLY. Do not enable a new employer, add an account, alter persistent state or create a fake button.
- P2-ACT enables only owner-approved boards with verified employer provenance, ensuring original 13 never lose Network Priority.
- Phase 3 moves basic application records early because later approval/execution must reference immutable job/resume IDs. Auto-submit remains impossible here.
- Phase 4 never submits an application. It only signs `Approve resume` and optionally `Prepare application packet` as an UNSENT DRAFT. Phase 5 introduces per-job `Approve & Apply` authorization (job/URL/answer/resume hash/nonce) alongside a tested executor.
- Phase 5 starts with a dot manual-handoff test. A supported direct dot API is UNKNOWN; no claimed automated trigger until verified. If unavailable, keep manual handoff or a separately approved local browser runner. No vendor ToS evasion or hidden paid runtime.
- Phase 6 rehouses previously planned Phase 5 startup outreach and Phase 6 reminders/feedback. Old phase documents and goal prompts must follow this new plan.

## Generic PR acceptance
1. Exact latest main/head, safe branch and no loss of bot-generated `state/seen_jobs.json`.
2. Scoped implementation, synthetic/adversarial fixtures and full `pytest` with documented actual counts.
3. Source/data/license/ToS checks, negative consent/privacy/replay tests where relevant.
4. Full PR docs: `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/RELEASE_LOG.md`, and affected architecture/security/contracts and phase files.
5. Actual code review/CI logs and accurate `IMPLEMENTED / TESTED / LIVE_VERIFIED / MERGED / PRODUCTION_ENABLED` states.
6. Proven rollback. A mock alert or automated form fixture is NOT proof of a real delivered alert or submitted employer application.
7. Blocked secret/provider/consent means `BLOCKED_LIVE` or `BLOCKED_APPROVAL`. Do not forge success.

## First executable goal
**[P2-UX1 issue #25](https://github.com/KanujVerma/jobbie/issues/25), [contract](phases/PHASE-2-UX.md), and [ready-to-paste /goal](agent-prompts/PHASE-2-UX-GOAL.md).** Next is [P2-ACT issue #26](https://github.com/KanujVerma/jobbie/issues/26) / [contract](phases/PHASE-2-ACT.md), with [second /goal](agent-prompts/PHASE-2-ACT-GOAL.md). The historical `docs/agent-prompts/PHASE-2-CODE.md` is not the next instruction unless explicitly redirected to the new slots.

## Subsequent phase specs
- [P2-B/C](phases/PHASE-2.md)
- [Phase 3](phases/PHASE-3.md)
- [Phase 4](phases/PHASE-4.md)
- [Phase 5](phases/PHASE-5.md) and [AUTO_APPLY.md](AUTO_APPLY.md)
- [Phase 6](phases/PHASE-6.md)
- [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md) and [RESUME_TAILORING.md](RESUME_TAILORING.md)

# Jobbie incremental delivery roadmap — current 2026-11-11 owner plan

**Evidence:** Phase 1 and Phase 2A were implemented/merged; P2-A Greenhouse/Ashby API reads verified but no additional employer boards are production enabled. See [STATUS.md](STATUS.md) for actual main HEAD. P2-UX1 #29 is merged; live delivery remains unverified. Other future slots are **PLANNED**, not implementation claims. PR slot IDs are stable design labels, not GitHub numeric PRs.

## Delivery principle
One small user-usable release at a time. Each functionality PR must keep earlier job polling/alerts available, pass full regression tests, receive independent review and update STATUS/HANDOFF/RELEASE_LOG. No huge one-shot implementation, no pseudo-buttons, no mass applications, no silent paid provider use.

| Order | PR slot / phase | User-visible completion | Dependencies |
|---|---|---|---|
| Shipped | Phase 1 + hardening (#12–18) | New-grad filtering and original 13 Network Priority stars | Existing bot |
| Shipped code | P2-A (#23, docs #24) | Official Greenhouse and Ashby read-only adapters available, **not activated** | Phase 1 |
| Shipped code | P2-UX1 (#29) | Source-grounded webhook cards; live delivery unverified | P2-A merged |
| Active | P2-R1/P2-R2 reliability | Failure/empty distinction, dry-run safety, actionable health, state-safe original-source repairs | P2-UX1 merged |
| Then | P2-ACT owner-directed intake | Issue form, tested portable CLI requests and disabled reviewed proposals for monitor/startup-research | P2-R1; activation separately approved |
| Then | P2-B optional public feeds | Reusable OFF capability, rights/provenance/official-link checks; activate only if permitted and owner-approved | P2-A; expansion optional |
| Then | P2-C canonical catalogue | SQLite pre-filter identity/history/search/export; legacy delivery authority through >=72h shadow and approved cutover | Existing normalized adapters; feed activation optional |
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
- P2-ACT is owner-directed intake, replacing mandatory expansion. Proposals are disabled; only a separately approved exact company can be enabled. Preserve 13 original flags and 2 historical disabled entries. Missing approvals/rights never block independent implementation. No company is requested by this roadmap itself.
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

## Current executable work
Follow the [remaining Phase 2 goal](agent-prompts/PHASE-2-CODE.md) and [delivery plan](superpowers/plans/2026-11-11-phase-2-completion.md). Complete scoped reliability, owner intake, optional feeds and catalogue PRs sequentially. Never collapse them into one PR. Phase 2 stays PARTIAL/BLOCKED while live-delivery, source health, approval, rights or >=72h/cutover evidence remains missing. No forced production changes to manufacture a pass.

## Subsequent phase specs
- [P2-B/C](phases/PHASE-2.md)
- [Phase 3](phases/PHASE-3.md)
- [Phase 4](phases/PHASE-4.md)
- [Phase 5](phases/PHASE-5.md) and [AUTO_APPLY.md](AUTO_APPLY.md)
- [Phase 6](phases/PHASE-6.md)
- [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md) and [RESUME_TAILORING.md](RESUME_TAILORING.md)

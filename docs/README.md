# Jobbie technical and product documentation

**Start here if joining cold:** [Agent handoff](HANDOFF.md) -> [Current audited status](STATUS.md) -> [Agent rules](../AGENTS.md) -> [Roadmap](PHASES.md) -> [active remaining Phase2 contract](phases/PHASE-2.md). Phase 1 and P2-A release evidence is recorded in STATUS. The auto-apply design is PLANNED, not deployed. GitHub source HEAD and Actions evidence override old snapshots.

## Sources of truth
- [STATUS.md](STATUS.md): CURRENT code release, CI evidence, live operation confidence, blockers and next implementation.
- [HANDOFF.md](HANDOFF.md): exact fresh-agent onboarding, reading order, commands, code map, next PR and completion packet.
- [RELEASE_LOG.md](RELEASE_LOG.md): chronological PR/commit/CI/review record and remaining live checks.
- [MAINTENANCE.md](MAINTENANCE.md): documentation update requirements, CI checks and conflict resolution.
- [IMPLEMENTED_ARCHITECTURE.md](IMPLEMENTED_ARCHITECTURE.md): running implementation and module map.
- [ARCHITECTURE.md](ARCHITECTURE.md): FUTURE evolutionary architecture and provider boundaries; not already deployed.
- [PRODUCT.md](PRODUCT.md): audience, three recruiting paths, 13 original priority sources, UX requirements.
- [DECISIONS.md](DECISIONS.md): locked policy, architecture choices and defaults.
- [CONTRACTS.md](CONTRACTS.md): eligibility, canonical IDs, candidate evidence, document/outreach models.
- [SECURITY.md](SECURITY.md): privacy and outbound authorization.
- [EVALS.md](EVALS.md): test matrices and release gates.
- [OPERATIONS.md](OPERATIONS.md): dry run, Actions, state safety, monitoring and rollback.
- [OPEN_SOURCE.md](OPEN_SOURCE.md): permitted reusable code, candidate feeds and license checks.
- [RESUME_TAILORING.md](RESUME_TAILORING.md): planned natural, evidence-locked tailored resume quality pipeline.
- [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md): notification presentation contract; P2-UX1 #29 merged, ordinary webhook ACK observed.
- [AUTO_APPLY.md](AUTO_APPLY.md): approved single-job packet, dot feasibility and fallback executor design (NOT deployed).
- [RENAME.md](RENAME.md): verified repository rename and local-remote migration checklist.
- [CURRENT_STATE.md](CURRENT_STATE.md): **historical 2026-11-04 baseline only**; do not treat as current implementation.

## Releases / detailed execution entry points
| Order | User value / actual status | Contract | Agent prompt |
|---|---|---|---|
| 1, P2-A | New-grad filtering and public ATS adapters merged; 13 original sources only active | [P1](phases/PHASE-1.md), [P2](phases/PHASE-2.md) | Historical P1/P2 prompts |
| P2-UX1 (#29 merged) | Source-grounded cards; ordinary HTTP204 ACKs verified | [P2-UX1](phases/PHASE-2-UX.md) | Historical UX goal |
| P2-R1/R2/R3 merged | Source-failure health, read-only state safety and original-source repairs | [Phase 2](phases/PHASE-2.md) | [Remaining Phase 2 goal](agent-prompts/PHASE-2-CODE.md) |
| P2-ACT #32 merged | Tested form/CLI for monitor/startup-research and OFF proposals; [onboarding](COMPANY_INTAKE.md) | [P2-ACT](phases/PHASE-2-ACT.md) | [Intake goal](agent-prompts/PHASE-2-ACT-GOAL.md) |
| P2-B #34/C1 #35 merged; C2 #36 merged/live gates pending | OFF feeds, canonical store and persistent shadow | [Phase 2](phases/PHASE-2.md) | [P2 overview](agent-prompts/PHASE-2-CODE.md) |
| P3 | Real private commands/profile/evidence/basic app ledger | [Phase 3](phases/PHASE-3.md) | [P3](agent-prompts/PHASE-3-CODE.md) |
| P4 | Grounded tailored resume, diff/preview, private approval packet | [Phase 4](phases/PHASE-4.md) | [P4](agent-prompts/PHASE-4-CODE.md) |
| P5 | Owner-approved dot/browser application execution | [Phase 5](phases/PHASE-5.md) | [P5](agent-prompts/PHASE-5-CODE.md) |
| P6 | Startup outreach, reminders and learning | [Phase 6](phases/PHASE-6.md) | [P6](agent-prompts/PHASE-6-CODE.md) |
**Archive:** older `docs/superpowers/` development plans are historical, not the release contract. For requests to implement a phase, read active phase docs and live GitHub first. Never start a later phase because an old conversation said it is ready.

## Exact update cadence
Every functional PR changes [STATUS](STATUS.md), [HANDOFF](HANDOFF.md) and [RELEASE_LOG](RELEASE_LOG.md); a pull-request CI check enforces that these files were touched. Scheduled production state-only commits are exempt. The guard does NOT prove truth: reviewer must still compare documentation to code, CI and live logs.

[COMPANY_INTAKE.md](COMPANY_INTAKE.md) is the current owner request, source-evidence and disabled-proposal workflow. It preserves the original roster and has no automatic activation/dot trigger.

[PUBLIC_FEEDS.md](PUBLIC_FEEDS.md) documents the optional OFF lead path and actual source-rights blockers. No current third-party feed dataset is ingested.

[CATALOGUE.md](CATALOGUE.md) describes the merged C1 source store/query and C2 persistent shadow/parity implementation, including actual operational gates. A local SQLite helper is not production cutover or real72h evidence.

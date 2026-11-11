# FUTURE ARCHITECTURE (PLANNED / EVOLUTIONARY)

> For actual deployed modules, first read [IMPLEMENTED_ARCHITECTURE.md](IMPLEMENTED_ARCHITECTURE.md) and [STATUS.md](STATUS.md). Design targets below are not proof of deployed providers, databases, private features or production verification.

# System architecture, boundaries and evolutionary path

## Non-negotiable delivery strategy
We are *evolving* the existing Python monitor, not replacing it with an unrelated monolith. Phase 1 must work using only GitHub Actions, Python adapters, committed public seen state and existing Discord webhook. Future subsystems are add-ons behind isolated failure boundaries; if AI, Discord commands, private store or new startup source fails, original-company alerts still run.

## Phase 1 (implemented architecture stays intact)
`companies.yaml` -> adapter registry -> `BaseAdapter.fetch()` -> normalized frozen `Job` -> deterministic new-grad eligibility -> per-company seen state -> `Notifier` -> Discord webhook.
Actions performs best-effort scheduled job, serializes concurrent runs and commits public dedup state. A monitor observes run age vs configured target and warns about scheduler gaps; no promise of guaranteed 15-minute latency.

Recommended module changes in Phase 1:
- `src/eligibility.py`: pure deterministic classifier with explicit `eligible` / `needs_review` / `excluded`, precise evidence, never side effects.
- `src/network.py`: company cohort metadata, referral status validation, stable monitored_source keys and view labels.
- `src/filtering.py`: orchestrate eligibility/freshness/location without mistaking plain mention of "intern" for internship job.
- `src/notifier.py`: public network-priority label with separate location priority; keep webhook rate limits.
- `src/storage.py`: separate policy-version/backfill markers and dedupe, preserving v2 legacy state. Do not make non-reversible in-place rewrites of historic records.
- `main.py`: safe migration/preview entry point, bounded backfill and diagnostics; retain old CLI flags or provide a tested deprecation path.
Paths are intended contracts, not a claim these files exist yet.

## Phase 2: ingestion + catalogue
Add Greenhouse, Ashby and specifically authorized public/curated feeds; every source adapter produces normalized source-backed jobs. Persist *all* validated scraped postings before personal filtering to enable rescoring. Canonical job ID prefers employer requisition ID + canonical employer domain; else normalized canonical URL. Preserve per-source IDs, first observed, last verified, employer reported posted_at, active/unknown/closed evidence. ATS direct listing takes presentation precedence, but source history remains. Never merge distinct requisitions only because their title matches.

Catalogue likely moves to a small database (evaluate D1 free limits) after dual-write parity. Do not delete or reset `state/seen_jobs.json` until reconciliation and rollback are demonstrated. Each source can fail independently with bounded retries/backoff.

## P2-UX1/P2-ACT (upcoming small bridge releases)
Redesign only the existing Discord embed formatter first, with synthetic snapshot tests and no changes to state/delivery semantics. Then source-verify and owner-approve a small Greenhouse/Ashby employer shortlist in a separate config PR. P2-B feeds/P2-C catalogue follow; preserve original 13.

## Phase 3: personal services
Discord application command endpoint (HTTP interactions) -> signature verification, timestamp replay protection, allowlisted USER ID, minimal immediate response -> durable work queue -> Python task worker. Cloudflare Worker/D1/private R2 are proposed, not mandatory without free-tier feasibility check. Command inputs and PDFs live in private storage; public repository may contain ONLY redacted test fixtures. No message-content scanning. Generated result links must be authorized, short-lived and scoped.

Phase 3 also introduces a minimal private `JobSnapshot`, `Application` and append-only `ApplicationAttempt` ledger (saved is not applied). No external submission capability yet; it is the stable substrate for future approval/receipt tracking.

Candidate facts have `fact_id`, exact source (resume version, approved repo commit/path, owner confirmation), visibility, verification state and confidence. Fact extraction is proposal, not automatic promotion. Model queries receive only minimal approved facts, not blanket private repositories.

## Phase 4: resume tailoring
Approved `CandidateFact` + specific `JobSnapshot` + role/company context -> evidence selection -> LLM proposes structured edit operations only -> deterministic preservation + grounding validator -> user diff/approval -> RenderCV PDF / DOCX -> reparse and layout gate -> immutable artifact + owner review. A **separate per-job application packet approval** binds job/requisition/official URL, answer set and artifact hash; it does not submit anything until Phase 5. Original immutable. Unapproved/unsupported claims => fail closed and request correction. See `RESUME_TAILORING.md`.

## Phase 5: approval-driven dot/browser application executor
`ApplicationPacket` verified private job snapshot + approved resume SHA-256 + candidate answer version + explicit one-job owner submission approval (hash/nonce/expiry) -> `ApplicationExecutor` adapter. First pilot is manually delegated to a dot in ChatGPT; a direct API trigger remains UNVERIFIED until supported official product docs + real test. Browser runner fallback may use local Playwright/Stagehand behind the same interface when employer site permissions allow. Unknown legal/EEO questions/MFA -> `needs_input` and human takeover. Submitted only with authoritative employer receipt. Indeterminate timeout -> reconcile, never blind retry. No mass apply; fail closed.
Do not couple Jobbie scraping to private executor availability. Preserve free hosting target, scope auth and site restrictions.

## Phase 6: startup sourcing/outreach plus recruiting lifecycle
Source-backed `Company` + `HiringSignal` (confirmed active role vs outreach target) -> source-permitted verified business contact -> approved exact draft -> authenticated email provider with single-message approval, idempotent receipt, no LinkedIn auto send. Expand the Phase 3 application ledger with reminders, follow-ups, recruiter stage changes and feedback. Do not infer applied from opening a URL or artificially change employer outcomes.
## Bounded provider interfaces (future)
- `JobSource.fetch(cursor) -> SourceFetchResult`: entries + fetch status + observed_at + errors, no fabricated missing data.
- `Eligibility.classify(job, candidate_policy) -> EligibilityVerdict`: tri-state + reason codes + source spans.
- `Matcher.rank(job, candidate_version) -> MatchScore`: weighted rubric + known/unknown dimensions + matched fact_ids.
- `AIProvider.generate(schema, bounded_context) -> ValidatedJsonOrError`: model/version, latency, tokens, cost/usage, no silent paid fallback.
- `DocumentRenderer.render(structured_resume) -> ArtifactSet`: PDF/DOCX + page count + parse/layout checks.
- `ApplicationPacket.approve(job_id, resume_sha256, answer_version, owner_id) -> ApprovalReceipt`: exact single-job digest+expiry+nonce; requires authenticated owner action.
- `ApplicationExecutor.execute(approved_packet) -> AttemptResult`: manual dot handoff at first, optional verified direct trigger/local runner; return confirmed receipt/needs_input/failed/indeterminate, never guess.
- `OutreachTransport.send(approved_message_id) -> SendReceiptOrIndeterminate`: Phase 6 message approval, idempotency and audit, never assume success on timeout.

Do not implement these interfaces in Phase 1 unless necessary to meet that phase's acceptance test. These names define semantics and a future boundary, not a mandate to build infrastructure early.

## Failure isolation and upgrade mechanics
- Job scraping is independent of AI inference, resume rendering and send service.
- Unverified company/job fields use `unknown` and carry source/time, never made-up defaults.
- Stored job identities and candidate versions are immutable; derived match scores can be regenerated with rubric/model versions.
- External actions require exact authenticated approval and idempotency. Retry on ambiguous send status requires provider reconciliation, not blind resubmission.
- Every phase deploys feature flags, shadow comparison where applicable, graceful rollback and an incident/recovery procedure.
- Planned private providers need account-level quota + pricing verification before activation. $0 recurring is a hard operational constraint; metered services must have safety limits and an alternative when quota is exhausted.

## Ownership of source of truth
Original company cohort: `docs/PRODUCT.md` + Phase 1 config metadata.
Live job facts: source snapshot/provenance.
Candidate claims: confirmed fact/evidence ledger.
Resume output: approved version + edit ledger.
Outreach: approved exact draft + recipient + provider receipt.
Release status: CI, test evidence, actual operational verification; never README assertion alone.

# As-built architecture vs intended future system

**As-built code release audited 2026-11-10:** P2-A `ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb` (merge #23), followed by docs #24. Later `main` commits may be state-only. P2-A adds Greenhouse/Ashby public read-only adapters but no employer board is production enabled. Future architecture in `docs/ARCHITECTURE.md` describes targets, not implemented capabilities.

## As-built synchronous cycle
`GitHub Actions job-alerts.yml` (best-effort cron / manual dispatch)
→ `main.py run`
→ `companies.yaml` 13 enabled monitored source entries
→ `src/adapters/__init__.py` and per-platform `BaseAdapter.fetch`
→ immutable `src.models.Job`
→ `src.filtering.apply_filter_pipeline` (normal 48-hour freshness; special migration 7 days)
→ `src.eligibility.classify_eligibility` + `src.experience.assess_experience_requirements` (tri-state)
→ `src.storage.classify_jobs` (per-source seen IDs and cross-source URL history)
→ `src.notifier.Notifier` (Discord webhook, only confirmed-delivery ACK)
→ bounded versioned `state/seen_jobs.json` commit to `main`.

Ambiguous early-career jobs go into a review queue/daily digest, not an "eligible" alert. `src.backfill.deliver_backfill_batch` sends only up to 10 represented direct links per scan and acknowledges exactly those after confirmed delivery; further unalerted candidates remain pending. `src.health.compute_run_diagnostics` records failed vs empty sources and scheduling gaps.

No long-running server, webhook receiver, Cloudflare database/Worker, AI SDK, private document upload, recruiter mail OAuth or application tracker exists in the running architecture at this audited release.

## Important actual semantics and constraints
- `network_priority` is a config-driven *original source* badge, not a confirmed referral. Original 13 source names are locked in `docs/PRODUCT.md`.
- `Job.priority` means location preference and must not be reused as network importance.
- Workday may retrieve details for promising postings; Microsoft PCSX uses summary fields (full detail can require additional requests). Never treat missing descriptions as confirmed experience requirements.
- Employment/seniority parsing is heuristic and conservative. Even when classifier says eligible, real ATS full requirements and employer cohorts need verification before applications.
- `state/seen_jobs.json` public state must never contain personal resumes, family contacts or private API tokens.
- `.github/workflows/job-alerts.yml` can be 4–8 hours late despite */15 schedule; health logs do not fix the scheduler.

## Phase 2A implemented vs later Phase 2 delta (planned)
P2-A Greenhouse/Ashby public read-only adapters, safe provider normalizers, optional immutable Job source fields, integration tests and read-only verification workflow are merged and CI-tested. No new employer boards have been activated; production remains the original 13 enabled source entries. P2-UX1 notification layout, P2-ACT controlled owner-approved boards, P2-B permitted feeds and P2-C catalogue are NOT implemented yet.
P2-A: read-only official Greenhouse and Ashby job-board adapters with pagination, description/role/compensation sources and backoff. Existing employers unaffected.
P2-B: vetted and authorized public feeds, permission and original-employer source verification.
P2-C: canonical catalogue storing validated jobs *before* personal filtering, provenance, global dedup and status history, 72-hour shadow migration. Proposed Cloudflare D1 may be replaced with a fully free local/Actions-compatible catalogue; validate actual quota and no paid fallback.

## Target Phases 3–6 (NOT implemented)
3. Authenticated Discord interactions/private candidate and resume store, verified GitHub evidence, explainable matching, plus early private Application/Attempt ledger.
4. Structured, source-backed natural resume tailoring, exact before/after review and full PDF/DOCX, owner Approve resume separate from Approve & Apply packet.
5. Dot-first MANUAL owner delegation feasibility, then exact one-job consent-bound application execution/receipts and optional policy-compliant local browser fallback. **No verified direct dot API**, no mass applications.
6. Startup sourcing/verified contacts and exact approval outbound email, plus recruiter/application reminders and feedback. No automatic LinkedIn DMs.

## Failure isolation and rollback
Legacy company polling must remain runnable even if later data feed, AI, private storage or outreach services fail. Feature flags and migrations must preserve original job history. On a state commit conflict, preserve both branches' relevant data and do NOT force push or delete state. Source-rights restrictions apply to all sources and feeds.

## Provider boundary (future only)
Source adapters -> normalized record -> hard eligibility -> ranking -> evidence-backed LLM interpretation -> human approval for documents/outbound actions -> tracking. No single model may declare that an email was sent, job is open, candidate has a credential, or applicant is hired without independently verified evidence.

## P2-A branch addition (not yet production-enabled)
`GreenhouseAdapter` and `AshbyAdapter` -> shared `public_board` validation/GET
normalization -> optional immutable Job source facts -> existing tri-state
eligibility, storage, notifier. No new database/service. Explicit source employment
and incomplete-description flags prevent false full-time alerts; review queue
retains these facts. `scripts/verify_public_boards.py` runs the same adapters
read-only with metadata-only receipts, not `main.do_run` or any webhook.

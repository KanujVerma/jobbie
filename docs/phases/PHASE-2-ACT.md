# P2-ACT owner-directed company intake

Owner amendment 2026-11-11 replaces the historical mandatory 3-5-company expansion. Status: implemented and merged in #32 at f46625845577f158da31974d927aa5748d0c3642; production employer activation remains separately gated. See COMPANY_INTAKE.md and STATUS.md for actual tests/review/CI. Issue #26 tracks this workflow.

Accept a versioned portable request containing company name, optional official careers URL, aliases, requested roles/locations, priority and intent `monitor` or `startup-research`. A GitHub issue form and tested CLI/agent workflow must share the same semantics. A user may manually give this request to dot; no API, automatic trigger or session transfer is assumed.

Before generating a config proposal, verify canonical employer/aliases, official careers-to-ATS ownership, exact provider ID, access/data permission, response health and current listed jobs. Unknown evidence stays needs_review. Reject unsafe URLs and alias/provider collisions. Research targets are not live job monitors or current hiring claims.

Proposals are disabled and reviewable, with source URLs/retrieval time/evidence and role/location intent. New employers are `cohort: discovered`, `network_priority: false`, `referral_status: unavailable`. Never modify production config automatically. Enable an exact employer only after explicit owner approval in a separate reviewed activation PR with state-safe initial-volume, dedup and rollback proof. Preserve 13 original enabled sources and 2 historical disabled sources.

Tests: request schema, missing optional URL, aliases and collisions, official provider/ID mismatch, missing rights/health/listings, 403/404/429, hostile URLs, startup-research separation, unconfirmed referrals and unchanged production config/state. Full pytest/config, no-mutation dry-run, independent review and exact-head CI. Update STATUS/HANDOFF/RELEASE_LOG and onboarding documentation.

Missing owner requests or approval never authorizes inventing a shortlist and does not block independent P2-B/C implementation. Record BLOCKED_APPROVAL only for activation. Existing P2-A adapters stay available and examples stay disabled.

## Merged implementation interface
`python main.py company-request` accepts direct fields or the GitHub form Markdown and emits version1 JSON. `company-proposal --request FILE --evidence FILE` validates supplied manual evidence; `--live-check` measures the fixed public ATS only after explicit ownership=verified and permission=permitted. Unknowns never become a config proposal. Successful output stays enabled=false/discovered/networkfalse/referralunavailable and BLOCKED_APPROVAL. Verified aliases persist in the proposal. A positive process exit is not activation authority.

[Onboarding and exact commands](../COMPANY_INTAKE.md), [fictional fixtures](../../examples/company-intake/request.synthetic.json), and [verification](../evidence/P2-ACT-VERIFICATION.md) define the merged implementation. Role/location preferences are preserved and shown through literal listing checks, not hard global filters or profile-fit claims. Startup-research remains a request with unknown opening status and no monitor/network check. No dot integration or automatic issue trigger.

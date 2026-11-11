# Jobbie product specification — owner-approved 2026-11-10 direction

**Current deployed code:** GitHub Actions + Python webhook-only job alerts for original 13 company sources; P2-A Greenhouse/Ashby adapters are merged but no additional employer boards are active. Read [STATUS.md](STATUS.md) first. **Everything below about Discord buttons, AI resume previews, dots or application submission is PLANNED** until release evidence says otherwise.

## Mission
A personal, single-user Discord-first job-search system for relevant US full-time new-grad engineering roles. Three recruiting paths remain:
1. traditional new-grad/early-career openings with direct employer applications;
2. relevant startup openings;
3. proactively contacting verified startup founders/engineering leads when no posting exists.

New owner-approved long-term workflow: **source-backed discovery -> clear actionable alert -> verified profile match -> natural role-specific resume -> private edit/PDF review -> owner approves ONE exact application -> dot or controlled browser executor submits where permitted -> capture employer receipt -> track follow-ups/outcomes**.

**Approve resume alone != approve job application.** A per-job `Approve & Apply` action is separate, authenticated, revocable and bound to exact employer/requisition/URL, answer version and PDF hash.

## Candidate preferences (locked, unchanged)
- UW–Madison BS Computer Science, December 2026 graduation; January 2027 onward preferred start (verify specific cohort windows).
- US permanent resident authorized to work without sponsorship; not US citizen. Citizenship-only/clearance requirements not automatically eligible. Keep personal immigration details private.
- SWE/general, SWE I, backend, full-stack, product engineering, applied AI, forward-deployed AI, AI agent/retrieval/evaluation, select junior ML/data/platform and clearly labeled stretch startup engineering.
- Full-time US roles; internships/co-ops excluded. Salary ≥$100,000 USD annual BASE preferred, not a hard filter; undisclosed compensation not rejected, bonus/equity separate.
- SF Bay Area top; other CA, NYC, Chicago, Texas and Florida also prioritized; other US positions searchable, remote must be US-eligible.
- Free-first hosting and inference; no silent paid fallback or assumed dot entitlements.

## Network cohort (exact 13 original ENABLED sources)
`Micron`, `Salesforce`, `CrowdStrike`, `Intel`, `Applied Materials`, `Western Digital`, `SanDisk`, `Plaid`, `Oracle`, `Microsoft Research`, `Microsoft`, `Amazon`, `Apple`.

All are permanently `network_priority=true` for source grouping unless owner changes them. Actual referral status defaults `unconfirmed`; DO NOT claim a confirmed referral/contact. Disabled historical configurations `Snowflake` and `Applied Digital` do not gain network priority. Microsoft & Microsoft Research are separate source entries for one employer.

New discovered companies get `network_priority=false` / `referral_status=unavailable` unless explicitly owner-approved. For an original company with an unconfirmed potential referral, let owner choose `hold for referral` or `apply directly`. Do not block job discovery while waiting on a referral.

## UX and actual incremental release order
1. **P2-UX1: clear notification cards** on existing webhook: job-title-first, actual company/location, eligibility screen reason (not a hiring probability), verified base salary or undisclosed, network/referral, truthful posted vs first-seen date, and direct employer URL. NO AI skill match or inert buttons. [Details](NOTIFICATIONS_V2.md).
2. **P2-ACT (amended 2026-11-11):** owner-directed issue/CLI requests for monitor or startup-research, with verified aliases/ATS ownership/rights/health and disabled reviewed proposals. Expansion is optional; activate only exact owner-approved employers. Original 13 and 2 historical disabled entries persist. No implied referral or invented dot API.
3. **P2-B:** allowed/verified new-grad feeds and employer link resolution. **P2-C:** canonical catalogue/dedupe/shadow migration and optional measured scheduler improvement.
4. **Phase 3:** signed Discord interactions and private owner profile/storage, fact/GitHub evidence, job matching, and basic application ledger. `/jobs find`, `/jobs top`, `/resume upload`, `/github repos`, `/applications`, `/settings`; public webhook alerts continue if this service is down. Buttons can now perform actual actions.
5. **Phase 4:** evidence-preserving role/company resume tailoring, private before/after edit review, full PDF/DOCX preview, owner `Approve resume`, and optional **unsent `Prepare application packet` draft**. Actual `Approve & Apply` button and submission authority only appear in Phase 5.
6. **Phase 5:** dot-first application execution feasibility and one-job delegation. No asserted direct dot trigger until official supported integration is proven. Use explicit owner manual dot handoff first; then replaceable authenticated executor, optional local Stagehand/Playwright fallback, consent per role, definitive receipts.
7. **Phase 6:** startup/company research, permitted business contacts, separately owner-approved outbound outreach, reminders, application outcome feedback.

## Approval and privacy
- No mass auto-apply, unauthenticated job-board scraping, bot evasion, guessed screening answers, invented career metrics, false US citizenship or clearance, or automated LinkedIn sending contrary to platform restrictions.
- User may approve a single job's exact packet and authorize final submission; the executor can fill/submit THAT role where site policy and safety permit. New legal/EEO/signature/verification questions require owner response.
- Private resume, referrals, personal contacts, account credentials and private GitHub code never in PUBLIC GitHub, PRs or Discord alert embeds. Approved private repositories are explicitly allowlisted read-only; reading is not permission to disclose.
- Dot programmatic inbound handoff is **unverified**. Treat manual delegation and cloud session login/takeover as possible constraints. Never invent an API or claim automatic background execution before testing.
- A job marked `applied` requires authoritative employer confirmation, not merely opening a form or pressing Submit.
- Match/explanations and resume changes trace to employer source and verified candidate facts. No model-only eligibility/authorization.

## Success and release gates
- Every mini-release independently improves a working system, with passing regression suite, code review, rollback, source provenance and observed live evidence when available. Documentation alone is not a shipped feature.
- Job discovery: source rights, coverage/false-positive audits, no duplicate floods, correct 13-star flags and accurate salary/date semantics.
- Resume editing: zero accepted invented facts, naturalness/source review, correct diff/PDF/DOCX, no unapproved artifact sent.
- Application execution: zero unauthorized submissions, one-job approval digest, no blind retries on uncertain results, verified submitted receipt, documented fallback if dot unsupported.
- Preserve $0 recurring budget and original webhook pipeline if private services fail.

See [PHASES.md](PHASES.md) for scoped PRs, [AUTO_APPLY.md](AUTO_APPLY.md) for executor protocol, [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md) for card spec, and [RESUME_TAILORING.md](RESUME_TAILORING.md) for grounded revisions.

# Jobbie notifications v2 — approved product contract

**Status:** PLANNED, not implemented. First next coding PR: `P2-UX1`. No interactive Discord app exists yet; v2 initially uses the existing outbound webhook and plain employer links. See [phase scope](phases/PHASE-2-UX.md).

## Design goal
An alert should tell the owner within seconds: *what is the job; is it worth considering; is there a potential referral; what was verified; what is unknown; what do I do next?* Avoid duplicative metadata and inflated "verified" statements. Do NOT display an unsupported fit score, hiring probability, employer salary, or personalized skill evidence before Phase 3.

## One compact full-time job card
Recommended employer-verified source field hierarchy:

1. **Embed title:** actual JOB TITLE, then COMPANY. Never title the card "New Grad · Company" while burying the job title below. Suggested `Software Engineer I — Example Corp`.
2. **One-line summary:** strongest known LOCATION(s), actual employment type and early-career level. Remote/hybrid/onsite only if explicitly given; otherwise omit or "work arrangement unknown".
3. **Network/referral line:** `NETWORK PRIORITY ★` for the *original 13 source entries*; show `Referral: Unconfirmed` rather than claiming it is available. Non-original sources show `Discovered` without a star. Referral submitted/confirmed appears ONLY after owner-confirmed private status.
4. **Compensation:** verified **BASE** salary with currency, period and meaningful range if the source provides it; show "Not disclosed" otherwise. Do not annualize hours without known hours, mix bonus/equity into base, or infer company salary.
5. **Eligibility screen:** `Pass` or `Needs review` with 1–2 source-grounded reasons and any blocker/unknown. This is the deterministic Jobbie screen, **not** confirmation of hiring eligibility. Avoid the current "Full-Time ... (Verified)" label when full-time/year data is missing.
6. **Freshness:** label `Employer posted` only for an actual employer-posted timestamp; `First published` / `Last published` where the platform explicitly says so; otherwise `First observed by Jobbie`. Never treat source updated_at as posted date or display "posted today" from detected_at.
7. **Action:** one primary direct employer apply URL. If the user can only reach an aggregator, mark `Employer link unverified` and don't label the job application-ready. Source/board/req ID in small footer or expanded details.
8. **Future only:** `Why you match`, `Evidence`, `Potential gaps`, `Preview tailored resume`, `Approve & Apply` appear once private verified candidate profile + signed Discord interactions + resume approval and packet store are implemented. Until then show honest absence, not inert action buttons.

### Example (ILLUSTRATIVE, not a real listing)
`Software Engineer I — Example Company`
`★ NETWORK PRIORITY · Full-time · Entry-level`
`San Francisco, CA · Work arrangement unknown`
`Base: Not disclosed · Referral: Unconfirmed`
`Eligibility screen: Pass (early-career title; source explicitly full-time)`
`First observed: Nov 10, 2026, 5:30 PM CT`
`View official posting: https://example.com/jobs/123`
`Footer: Example Company careers · Job ID 123`

## Message types and notification rate
- `eligible` + original network -> one individual high-signal alert (existing dedupe and Discord token bucket).
- `eligible` + newly discovered -> one individual alert; don't add "referral available" without confirmation.
- `needs_review` -> bounded daily review digest with reason, not a confidently eligible alert. Sort plausible early-career roles ahead of known senior/non-US roles; don't fabricate a match score.
- `excluded` -> no alert.
- Backfill/report -> compact digest; preserve actual counts and no acknowledgement of jobs omitted from a sent batch.
- Later approval requests and executor states -> distinct PRIVATE notifications rather than public embeds; do not leak resumes or immigration details in channels.

## Exact implementation rules
- Phase P2-UX1 changes only presentation/helper code and tests. No source expansion, data schema migration, networking changes, Discord application bot, interactive fake controls, AI, candidate profile, or automatic applying.
- Keep `Notifier.send_job_alert(Job) -> bool` and current `build_job_embed(Job) -> dict` interface compatible. Preserve existing webhook ACK and rate limits.
- Render only values backed by existing Job fields and eligibility verdict. Unknown ≠ missing but implicitly verified.
- Format 1–2 clear eligibility reason codes/source-grounded explanations if possible. Never dump raw employer description or confidential candidate data.
- Escape/neutralize mentions/Markdown, truncate untrusted titles, sanitize URLs, enforce Discord embed title ≤256, description ≤4096, 25 fields max, each name ≤256/value ≤1024, overall embed ≤6000 chars. No raw @everyone ping. Prefer 5–7 short fields, not 12 lines of duplicative metadata.
- Timezone: use explicit configured timezone when available; default `America/Chicago` for owner-facing presentation (implementation choice; unit-test DST); store absolute UTC unchanged. Do not reinterpret date-only posted fields as exact timestamps.
- Salary: distinguish `CompensationRange` and old string `salary`; avoid choosing one contradicted by a stronger source. If only hourly, display $/hour, do not invent annual base.
- If a Job has `employment_type=unknown` or missing description, do not present it as a verified full-time opening. P2-A source-data semantics must remain intact.
- The direct employer job URL remains discoverable/clickable. Future signed Discord app may replace it with buttons without changing source identity.

## Release gates P2-UX1
- Before/after sample cards for original network, discovered, known base range, unknown salary, explicit internship (no new-grad alert), unknown date, multiple locations, employer updated time, needs_review digest, untrusted long Unicode/mentions, and both Greenhouse/Ashby.
- Snapshot/assert field ordering, text meaning, URL, source/req ID, total length and text escaping. No field missing that would hide unknowns; no false "verified" claims.
- Entire existing pytest passes; config valid, integration contract preserved, no change to `companies.yaml` or `state/seen_jobs.json` (including no forced backfill). Live webhook test only with approved destination; otherwise show a local payload preview and mark `BLOCKED_LIVE`, not "sent".
- After merging, old alerts still function when AI/private services are absent. Update `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/RELEASE_LOG.md` in that functional PR.

## Later interactive UI (explicitly NOT P2-UX1)
In Phase 3, signed Discord commands/components may provide `View job`, `Why match`, `Save`, `Tailor resume`. In Phase 4, private browser preview shows exact edits/why, accept/edit/reject. Phase 5 introduces `Approve & Apply` for one immutable packet and executor. Never put fake clickable controls in webhook-only notifications.

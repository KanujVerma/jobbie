# Verification matrix and release gates

No fabricated benchmark numbers, simulated "live" claims or implicit passing thresholds. Store exact fixtures, test commands, GitHub run URLs, git SHA, timestamp and evaluation owner in each release PR.

## Evidence levels
- `SPECIFIED`: docs only.
- `IMPLEMENTED`: code exists at exact SHA.
- `UNIT_TESTED`: relevant deterministic tests pass at that SHA.
- `INTEGRATION_TESTED`: local or CI integration behavior verified against representative systems/data.
- `LIVE_VERIFIED`: authorized real Discord/source/provider test observed, with link/log and environment.
- `RELEASED`: all required gates complete and deployed; fallback still viable.
A green synthetic fixture never promotes anything to `LIVE_VERIFIED`.

## Phase 1 critical fixture matrix
At least 25 deterministic table-driven cases with expected status/reason:
(1) explicit full-time New Grad 2026, (2) 2027 cohort allowing December 2026, (3) 2027 cohort unspecified, (4) SWE I 0-2 yrs, (5) Junior Backend 0-2 yrs, (6) general SWE unknown years, (7) SWE II ambiguous, (8) SWE 3 years, (9) senior 5 years, (10) staff, (11) explicit intern title, (12) co-op, (13) internship mention in generic team description but full-time SWE I, (14) "sales analytics" nontech, (15) SWE working on sales features, (16) PhD preferred, (17) PhD required, (18) master's preferred, (19) masters degree required, (20) US citizen REQUIRED, (21) sponsorship unavailable but candidate does not need it, (22) San Jose CA and Toronto mixed, (23) Toronto-only, (24) generic Remote with no US scope, (25) US remote explicitly, (26) missing posted date, (27) SF $100k, (28) undisclosed salary, (29) same MS req via Microsoft Research, (30) identical title with different official req IDs.
Qualify 100% of clear disqualifiers excluded and 100% of clearly eligible fixtures included. All ambiguous statuses `needs_review`. Never infer citizenship.

## Phase 1 acceptance
- All `pytest` green (or exact pre-existing failures explained, not silently ignored); `validate-config` green; dry-run state SHA before/after equal.
- 13 original flags true, 2 disabled not flagged, added test source not flagged, no assertion of actual referral.
- Bounded migration summary, idempotent rerun, no duplicate alert storm, no private data in source/log.
- Real source read-only fetch with correct job URL; a real authorized webhook smoke plus Actions run evidence before LIVE_VERIFIED. Scheduling gaps measured; user told observed latency.
- Shadow compare classified jobs against baseline and sampled manual labels. Record precision/recall; do not invent improvement numbers.

## Phase 2 acceptance
P2-A and P2-UX1 code are merged. UX live delivery remains unverified. P2-R1/R2: test original-source 403/404/429/partial versus empty reporting, eligibility reasons/candidates and failed-send ACK, corrupt state, no-mutation v1 dry-run and state-safe source migration. Observe actual scheduled run counters; cron is best effort. P2-ACT: tested owner request/proposal workflow, aliases/official ATS/rights/health checks, hostile URL/collision handling and unchanged original 13 plus 2 historical disabled. New companies remain discovered; no referral or invented dot trigger. Expansion is opt-in. P2-B: reusable OFF feeds with provenance/rights gates and official employer confirmation before alerts; absent rights stays BLOCKED_SOURCE_RIGHTS. P2-C: >=30 cross-source identity/closure/reopen/adversarial cases, pre-filter storage, reclassification/search/export, legacy parity and >=72h real shadow/rollback before approved cutover. Observe a scheduled run after cutover. Missing approval/rights/72h never becomes simulated success or blocks independent implementation.

## Phase 3 acceptance
Valid and invalid signed Discord requests, replay, unauthorized owner access and privacy tests. At least 40 manually labeled job matches with per-class confusion, missing-info handling; confirmed vs proposed candidate facts; private repo read-only and scope enforcement; no public storage leak.

## Phase 4 acceptance
See `RESUME_TAILORING.md`: 24 frozen jobs, zero accepted invented numbers/ownership/title/dates; 12 owner-reviewed samples with >=10 rated improved and at least as natural; all generated PDF/DOCX pass text, link, page and preserved-field checks. A single severe hallucination fails release.

## Phase 5 acceptance — explicit single-job automation
- Dot feasibility: owner-authorized manual handoff on a verified employer application, privately transferred document and actual outcome; do not report supported direct dot API unless technically confirmed by a real test.
- Executor: wrong recipient/domain/job, altered resume/answer version, expired/replayed nonce, unauthorized user, missing legal/EEO answer, MFA/captcha, uncertain submit, duplicate retry, inconsistent provider receipt; all fail closed or `needs_input`.
- No fabricated application submission. First **actual** owner-approved external application and authoritative confirmation ID/page/receipt required before `LIVE_VERIFIED`; if blocked, report precise state rather than fake success.
- Privacy scan and budget/ToS checks. Document latency, correctly filled fields, manual takeovers and failures without claiming inflated interview success.

## Phase 6 acceptance — startup outreach and reminders
At least 20 sourced company facts, zero guessed business contacts, no unsolicited or LinkedIn automated sends, exact owner-approved email and provider receipt if sending enabled; deduplicated application/reminder events, reliable privacy/export/retention, optional Gmail read classification only with consent, user-confirmed statuses. Original 13 and Phase 5 approval/receipt ledger preserved.


## Cost/reliability/privacy gates (each phase)
- $0 recurring: explicitly record provider tier/limits, observed usage, API rate/429 handling, disabled paid fallback. Cannot guarantee free if usage charges may be incurred; requires spend cap or not deployed.
- No secrets/private documents/family contact data published to GitHub or Discord public channels.
- Source and recipient provenance, retry/backoff, no duplicate external send and a rollback procedure.
- Regression across previously released phases.
- Do not claim uptime/SLA. Record actual delay distribution, missing checks, source errors and fallback behavior.

## Mandatory PR evidence template
`Base SHA:`, `Head SHA:`, `Files changed:`, `Reproduced behavior:`, `Tests (command / result):`, `Coverage (fixtures / live):`, `External source URLs/time:`, `Privacy review:`, `Known unknowns:`, `Rollout / rollback:`, `Codex review status / resolved findings:`, `Release gate status:`.

No PR merges solely because an LLM or README says tests passed.

P2-ACT candidate gates: form/CLI normalized JSON/digest parity; optional URL; aliases/canonical/provider collisions across enabled/historical entries; original roster/referrals unchanged; explicit ownership/permission provenance and unknowns before fixed-ATS read; unsafe/private-shaped input; real GH/Ashby fixture normalization; 403/404/429/empty/incomplete distinction; research mode without monitor/hiring inference; literal role/location evidence; bounded document reads, no sender or state/config writes. A verification-only provider probe is not an owner employer request or production approval. Hosted form rendering remains unassessed until available after merge.

P2-R2 source transition gates: first complete scan silent without false ACK; partial failure stays pending; duplicate IDs count once; successful empty baseline; pre-filter recording of excluded rows; later new IDs follow existing delivery; failed sends remain unacknowledged/retryable; old ACK/URL history and original roster/referrals preserved; corrupt transition metadata/config fails closed. Roll back code+source config together and preserve ledger. Baseline snapshots and provider connectivity are not live alert delivery proof.

P2-R3 verification: real site/finder provenance and root-versus-inner pagination; original empty response reproduced; partial/error versus explicit zero; repeated/capped/changed/malformed search; unsafe config/URLs; numeric stable IDs and truthful official route; complete versus missing qualifications/employment, non-full-time/seniority/citizenship exclusions; date-only/aware/naive precision; review-state date retention; no-mutation dry-run and source baseline. Unknown requirements and zero eligible counts do not establish no eligible employer openings.

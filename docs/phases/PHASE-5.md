# Phase 5 executable contract — dot-first, owner-approved job application

**PLANNED and NOT INTEGRATED.** Depends on Phases 3 and 4 and their private evidence, packet and review UI. **NOT the old startup-outreach plan** (now Phase 6). Normative [AUTO_APPLY.md](../AUTO_APPLY.md), [SECURITY.md](../SECURITY.md), [CONTRACTS.md](../CONTRACTS.md).

## P5-A: proof-driven dot pilot (first)
- Research the CURRENT actual eligibility, supported dot cloud-computer/browser behavior, ways to hand it a private file, and whether ANY supported authenticated inbound programmatic trigger exists. Do not invent dot API access or assume it can be called from Discord.
- Start with **manual delegation** of one owner-approved private application packet to user's dot in ChatGPT. Confirm secure file access, sign-in, form execution scope, owner takeover, actual status report. No browser-account automation without site permission.
- Record a redacted outcome with source/job ID, blockers and authorized proof. If no direct trigger, label integration `manual_handoff` and proceed with that truthful capability; do not block all application execution waiting on undocumented API.

## P5-B: application executor contract
- Versioned immutable `ApplicationPacket` with exact job/requisition, allowed destination, candidate/answers version, approved resume checksum, one-time nonce/digest/expiry and explicit owner `Approve & Apply`.
- Separate `ApplicationAttempt` states; `needs_input` on unknown questions, `indeterminate` after uncertain send, `submitted_confirmed` ONLY with employer receipt. Replay/duplicate prevention, correct resume upload, domain/policy checks, redacted audit.
- No unlimited cross-role approval, no fabricated screening answers, no unapproved final submission. An owner action for a specific job can authorize routine final click where platform permits; new legally consequential choices must pause.

## P5-C: optional scoped browser fallback
- Evaluate self-hosted/local Playwright + Stagehand/Browser Use vs dot. Prefer deterministic employer ATS form selectors and prompts over full autonomous free-roaming agents.
- Free-first; user approves allowed sites/tools and local/cloud security before use. No prohibited LinkedIn automation, bot evasion, CAPTCHA solving, or paid fallback without consent.
- Mock and owner-authorized live tests across different ATS types, per-field accuracy and resumes; pause for sign-in/MFA/EEO and evidence gaps.

## P5-D: single-job real submission gate
- Owner authorizes one actual target job and exact resume packet; executor completes form or stops with clear reason. Confirm employer receipt or `indeterminate`, never claim success from clicking Submit.
- Gate from [AUTO_APPLY.md](../AUTO_APPLY.md): zero unauthorized sends, zero invented protected answers, zero blind duplicate retries. Audit captured privately; do not leak resume/contact info or job account cookies to public GitHub.
- Only expand number of attempts after measured failures, site-policy compliance and explicit owner controls.

**No mass autoapply; no unbounded application agent; no guaranteed dot trigger.** If feasibility fails, keep manual dot delegation or authenticated local runner as documented fallback. Original job alerts continue if executor offline.

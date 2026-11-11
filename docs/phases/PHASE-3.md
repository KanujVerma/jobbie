# Phase 3 executable contract — authenticated search, private profile and application ledger

**PLANNED.** Depends on P2-C released. No auto-application or model-driven external action in this phase. Four sequential PRs P3-A–P3-D; keep legacy webhook alerts working if this private subsystem fails.

## P3-A: authenticated Discord interactions
- Verify official Discord Ed25519 signature and timestamp/replay controls before executing commands. Single owner's allowlisted Discord ID; private ephemeral replies and rate limiting.
- `/jobs find`, `/jobs top`, `/profile show`, `/github repos`, `/resume upload`, `/applications`, `/settings`, `/health`. Real buttons/commands: job source link, save, explain, request tailoring (only when Phase 4 live). No inert "Approve & Apply" before Phase 5.
- Defer tasks within Discord deadline, use durable queue for long analysis; sign all private URLs and reject cross-user/expired requests. No full channel scanning.

## P3-B: durable private profile/storage and basic app ledger
- Owner-scoped private DB + private blob store for uploaded resumes, temporary PDFs, validated candidate answer drafts and job metadata. No raw resumes/citizenship details in public GitHub state or Discord embeds.
- Add immutable `JobSnapshot`, `ResumeVersion`, `Application` and `ApplicationAttempt` scaffolds with append-only events; `saved` is not `applied`. Versioning and owner-confirmed status changes only.
- Content-type/size checks, parser isolation, expiry/deletion, encrypted/scoped fetch links. Credential and auth integration are not assumed available; show exact setup blockers.

## P3-C: verified facts / GitHub evidence
- Parse owner uploaded Epic/HCL/Tesla resumes; proposed facts require confirmation when new/ambiguous. No invented accomplishments, job titles, metrics, graduation dates.
- Public project evidence candidates (Clinical Notes synthetic demo, RegimeRadar real/demo distinction, Relay incomplete native, Drift no live capital). Attribution to user's actual code/PR, not simply README. Private repos allowlisted per repo, read-only, not automatically published or sent to model.
- Fact revocation invalidates derived match/resume recommendations. Keep source URLs/path/SHA and privacy scope.

## P3-D: transparent ranking, command search
- Hard eligibility tri-state remains authoritative. Starting weights role 30, verified skills 25, geography 15, salary 10, freshness 10, company 10; not a hiring probability. Unknown compensation is not zero.
- Explain `why match` / `what's missing` with candidate fact IDs and exact job source; avoid AI confabulation. Optional free-budgeted AI only for ambiguous explanations with privacy review; deterministic fallback works.
- Add actual saved-job statuses and feedback; nothing creates an employer submission or outbound email.

### Phase 3 release gates
Authorized and unauthorized commands tested on signed interactions; file upload/deletion and private data isolation tested; 40 source-grounded ranking fixtures; app record idempotency, no false applied status; \$0 provider limits; old 13 network webhook not broken. Owner-facing live command only if account settings permit; otherwise exact BLOCKED_LIVE.

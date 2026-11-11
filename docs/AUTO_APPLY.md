# Approval-driven application automation — planned design

**Status:** PRODUCT REQUIREMENT APPROVED; NOT IMPLEMENTED or connected to a dot. This doc intentionally distinguishes verified platform capabilities, potential integrations and unproven product hypotheses. Previous "no auto-apply" prohibition is superseded ONLY for explicitly authorized per-job execution by decision J-026; mass or unapproved applications remain prohibited.

## The owner's intended workflow
Jobbie finds a relevant full-time role -> ranks against confirmed experience -> generates job/company-specific resume revisions -> user inspects exact before/after and fact/source rationale in an authenticated private page -> user accepts/edits/rejects changes -> PDF/DOCX render verified -> user separately chooses `Approve & Apply` for a specific JOB and exact RESUME version -> job application executor completes allowed form steps -> returns authoritative receipt or asks for owner input -> status stored and digest updated.

**Approving a resume alone is NOT approval to submit an application.** Approval must explicitly bind candidate profile/answers, employer and requisition, exact destination and final resume checksum. Do not assume pressing "Open job" is an application.

## Why dot-first; what remains UNVERIFIED
OpenAI dots (where available) can use a cloud computer and supported websites to perform tasks with consent. The owner prefers reusing their dot instead of buying/managing another browser host. However, **no verified general-purpose programmatic Discord/Jobbie-to-dot API or event trigger has been established** in this project. Thus:
- `Executor mode A (first pilot):` Jobbie exports an owner-scoped encrypted/short-lived application packet; user manually delegates it to a dot in ChatGPT. Dot submits only within its own permissions and approval prompts. The workflow is considered MANUAL HANDOFF until a supported trigger is proven.
- `Executor mode B (if proven):` a documented/authorized dot handoff via an actually available plugin/event mechanism. Test real account entitlements, data permissions, file transfer, response/reconciliation, state and cost before implementing. **Do not fabricate an API, promise automatic launch, or claim browser sessions are shared with a user's local browser.**
- `Executor mode C (fallback):` owned/local browser runner with deterministic Playwright actions and constrained AI (e.g. Stagehand) for unfamiliar fields. Use only when provider site policies and user consent permit. Free/open-source SDK ≠ free cloud browsers/inference. No hidden paid account.

A dot's own browser/session/auth and device policy may demand user login, MFA/CAPTCHA, or takeover; never bypass safeguards. Even with prior approval, the executor may need another confirmation required by the platform.

## Bounded application packet (private, immutable)
`ApplicationPacket` fields (initial contract, version 1):
- `packet_id`, `schema_version`, `created_at`, `expires_at`;
- `job_snapshot_id`, `official_company_domain`, `official_req_id` nullable, `apply_url` exactly matched official destination (https), `source_verified_at`;
- `candidate_profile_version` and approved individual answer IDs; protected factual fields (education, citizenship/work auth, experience, salary expectation, dates, location) only if confirmed;
- `resume_artifact_id`, approved rendered PDF checksum (`sha256`), DOCX checksum optionally, owner approval timestamp; no silent new version;
- optional cover letter and answers with approved exact text/hash, bounded supporting facts and source refs; privacy and least-privilege restrictions;
- `submission_authorized` explicit separate owner action, `approval_digest` SHA256 over canonical packet, `approved_by` authenticated owner ID, `approved_at`, `approval_expiry`, `one_time_nonce`;
- `attempt_id`, `idempotency_key` and executor routing mode; append-only audit log and result receipts.
No plain passwords, OAuth refresh tokens, private repository source code or family referral contact details inside exportable packets. Secret/auth handling belongs in secure provider mechanisms.

## Privacy and approvals
1. Signed-in/allowlisted owner reviews the exact posting and the final PDF/DOCX preview. Change after approval -> invalidates hash and requires reapproval.
2. `Approve resume` only signs document content; `Approve & Apply` signs the *single job-specific* packet and authorizes submission for that destination. No bulk/blanket application approval, mass submissions or "autoapply while asleep" default.
3. Prioritize referral path for original 13: if referral is possible but not yet confirmed, allow owner to choose `hold for referral` or `apply directly`; the bot never claims that referral exists or always requires it.
4. Executor fills only grounded user-confirmed answers. No invented years/metrics, US citizenship/clearance, source code deployment, previous employer or demographic facts.
5. For unfamiliar legal disclosures, required demographic/EEO/self-identification choices, privacy/terms attestations, salary/relocation commitments, accessibility requests, signatures, security questions or verification challenges: ask the owner. Optional EEO choices never guessed.
6. Original employer ATS workflow first; avoid forbidden scraping/automation on LinkedIn or others. No CAPTCHA bypass, anti-bot evasion, credential theft or browser profile exfiltration.
7. Exact validated employer URL and redirected domains are checked before uploading personal data. No malicious form instructions or prompt injection may change approval scope.
8. If the application form or questions diverge materially from approved packet -> `needs_input`; the existing approval is NOT a blank check to answer new questions.

## Attempt/result state machine
**Candidate application stage** (owner tracking): `discovered -> saved -> ready_to_apply -> applied -> assessment -> interview -> offer` or `rejected/withdrawn/closed`. These are NOT inferred from the browser opening a URL.
**Executor attempt state** (separate record):
`created -> approved -> delegated -> in_progress -> needs_input | submitted_confirmed | failed | indeterminate | cancelled`.
- `submitted_confirmed` requires employer confirmation page, employer application ID, authorized provider receipt or confirmation email. Record source/hash/timestamp; a click on Submit is NOT sufficient.
- `indeterminate` after timeout/redirect uncertainty; inspect employer dashboard/email before retrying. Never blindly repeat submission.
- `failed` should indicate known non-submission. `needs_input` says exactly what owner must answer; no guessed workaround.
- Unknown/ambiguous results stay unknown; don't fake real submissions or acceptance.
- Same company+requisition+owner should have a unique active attempt. Dedupe/reconcile across discovered sources.
- On expiry/revocation, approvals cannot be reused or upgraded to different jobs; audit is append-only with correction events.

## Tooling to evaluate, not blindly install
All star/license observations are from GitHub on 2026-11-10 and subject to version verification:
- `browserbase/stagehand` (MIT, ~26k stars) — candidate for deterministic/AI-assisted form act/observe, custom fallback.
- `browser-use/browser-use` (MIT, ~120k) — agent browser for unfamiliar workflows; higher autonomy/risk, needs strict scoped approval.
- `microsoft/playwright-mcp` (Apache-2.0, ~39k) — explicit browser tools/accessibility selectors, deterministic paths.
- `vercel-labs/agent-browser` (Apache-2.0, ~49k) — agent-friendly browser CLI.
- `feder-cr/Jobs_Applier_AI_Agent` (MIT, ~32k) — job-form and tracking workflow reference ONLY, not permission to mass apply or bypass restrictions.
- `Skyvern-AI/skyvern` (AGPL-3.0, ~23k) — capable but heavier / obligations; evaluate license implications before code reuse.
Source code licenses do not authorize employer data collection or website automation. Star counts are adoption signals, NOT validated success or safety.

## Stage gates and metrics
### Gate 5A: Dot feasibility *without promising direct automation* ([future tracker #27](https://github.com/KanujVerma/jobbie/issues/27))
- One owner-selected ordinary employer ATS job, verified official job URL, no sensitive data leaked in ChatGPT public output; owner explicitly agrees to the test.
- Build packet and a manual dot prompt that cites exact approved resume version and source; verify dot can access the document securely, sign in / request takeover, fill allowed fields, return result.
- Identify whether dot permits a supported inbound programmatic action on THIS account, with official documentation and real authorized end-to-end test. If unavailable, record `unsupported` and preserve one-step manual handoff.
- Track outcome/steps/failure, including unknown/blocked; no fake auto-dispatch or submission.

### Gate 5B: Executor orchestrator
- Auth/approval anti-replay, expiration, one-time nonce, hashed immutable packet, URL/domain binding, no unauthorized sensitive data, idempotent attempt, record reconciled receipt. Simulated malicious forms/redirects and timeout tests.
- Cannot send without exact per-job approval; no unapproved file edits or fabricated screening answers.

### Gate 5C: Fallback browser runner
- Restrict to authorized employer pages and owner-approved sites; avoid platform ToS violations.
- Use bounded context/AI, deterministic field mapping where possible; mandatory owner takeover for unknown answers/MFA; no arbitrary open-ended application loops or unbounded paid inference.
- Compare known mock ATS fixtures with real approved test runs; capture field accuracy, resume checksum and receipt confidence.

### Gate 5D: First owner-approved actual submission
- One explicit approved real application (NOT synthetic) can be completed end-to-end and an authoritative confirmation recorded, or record precisely which step blocked.
- Zero unauthorized submissions; no blind duplicates after uncertain status; zero invented screening claims; redacted audit evidence and no public resume PII in GitHub.

## Human-visible interaction (future)
Private authenticated review UI: original resume vs tailored bullet change; reason tied to JD/evidence; accept/reject/edit; full PDF preview; `Approve resume`; separate `Approve & Apply` control with destination/answer confirmation. Discord buttons only after signed interaction endpoint and user identity checks exist. No inert webhook-only buttons.

## Budget and scope boundaries
The free-first constraint includes no automatic paid browser hosting or LLM credits, no undocumented dot access guarantees. If dot unsupported, keep manual dot prompt or local runner rather than silently spending. Job discovery and alerts must keep working if AI/dot/runner offline.

Current status: NO private packet storage, no dot integration, no browser executor, no automated submissions have been implemented.

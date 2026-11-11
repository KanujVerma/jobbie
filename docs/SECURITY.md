# Security/privacy and outbound authorization gates

No claims of "zero risk", "fully secure", or "GDPR/HIPAA compliant" from unit tests. Security status must be supported by tested boundaries and recorded deployment settings.

## Threat model
Adversarial job descriptions/README content may contain prompt-injection instructions. Discord interactions and attached PDFs may be malformed or spoofed. A mistaken company contact/email could cause unauthorized messages. Public GitHub Actions logs, artifacts, commits, issues and PR comments are PUBLIC. API providers may retain inputs and charge against quotas. GitHub private repo read permission is not outward disclosure permission.

## Phase 1 (public legacy bot)
- Continue using `DISCORD_WEBHOOK_URL` GitHub Actions secret; never print its value. `.env` remains ignored. Error output must redact tokens/headers.
- Never commit private candidate data to `state/seen_jobs.json`; network flag/status can be public but real referral names cannot.
- Sanitize untrusted job posting strings before Discord embeds; disable `@everyone`/role/user mentions; enforce field, title and total length limits, escape markdown where necessary, URL allowlist http(s).
- Scrape only publicly and legitimately accessible endpoints, respect rate limits and robots/terms; no login automation, anti-bot bypass or proxy rotation to evade restrictions.
- Require dry-run to be side-effect-free; verify state remains byte-identical and no webhook traffic during dry run.
- Detect stale/failed sources and scheduler gaps without leaking private state.

## Phase 3+ private candidate processing
- Private data must not enter public repository, workflow logs, issue bodies, screenshots, fixture files or default telemetry. Use synthetic redacted fixtures.
- Discord HTTP signature verify via official Ed25519 public key; reject invalid timestamp/replay, owner Discord ID allowlist, guild/DM scope as intended; ephemeral responses for private data. Rate-limit commands, confirm owner for any irreversible state changes.
- PDFs/DOCX: size/MIME/magic validation, compressed-content limits, parser isolation/timeouts, no arbitrary code execution/macros, virus-scan capability evaluated. Never trust filename or document text as commands. User deletion should remove private raw and derived artifacts subject to retention policy and provider limitations.
- Short-lived scoped download tokens/signed URLs, no guessable file identifiers, strict access checks before serving, transport encryption, server-side encryption where provided, minimal key scopes.
- GitHub private repos: explicit repository names allowlisted; read-only permissions; private content not sent to external providers or outreach unless separately approved. Store evidence metadata only when sufficient.
- Candidate facts: explicit owner confirmations, protected fact classes (work auth, employer, dates, education, metrics), provenance ledger with corrections/revocations.

## AI use
- Prompt injection from jobs, company websites, and project docs remains untrusted context. System/tool instructions are code, not retrieved text.
- Redact personal details and use only necessary source excerpts; verify provider data handling and rate limits before use. No automatic paid fallback.
- All AI-generated resume/outreach claims must be validated against approved facts and grounded company/job snapshots. Human final approval mandatory.

## Outbound email (Phase 6)
- Email sender requires authenticated owner approval bound to exact recipient, subject, body SHA256, draft version, expiry and one-use nonce.
- Message edit invalidates previous approval. Send provider receipt is authoritative for sent status. Timeout -> indeterminate, reconcile before any retry. No implied approval from "draft" or "save".
- Never invent email addresses, impersonate referrals, bypass LinkedIn automation restrictions or send bulk unsolicited outreach. Honor opt-out/bounce feedback.

## Owner-approved application automation (Phase 5)
- Only authenticated owner may issue `Approve & Apply` for exact job/requisition, verified HTTPS employer destination, exact resume checksum and answer set version; resume approval alone is not enough. Approval nonce one use; expiry/revocation and no broadened job scope.
- Private packet/URI can be delegated to the user's dot MANUALLY first; direct Discord/Jobbie-to-dot API cannot be assumed. Approved local browser fallback is restricted to specific allowed employer ATS origin(s). Credentials/MFA belong in authorized browser/provider sessions, never exported to GitHub or embedded in packet.
- No bot evasion, CAPTCHA bypass, account credential exfiltration, mass apply, or platform-prohibited browser automation. Always honor site challenges, rate limits and human takeover.
- Never invent experience, US citizenship, security clearance, demographic/EEO selection, signatures, legal consent, protected screening answers or salary commitments. Missing/unfamiliar choices pause as `needs_input`.
- Final submission occurs only within exact per-job owner authority and permitted site functionality; require employer-side authoritative confirmation. `indeterminate` after timeout/unknown state, reconcile before retry to avoid duplicate applications.
- Approval and resume hashes, employer URL, response receipt and state transitions are append-only and PRIVATE. No public screenshots containing personally identifying data, receipts, cookies or application confirmation codes.

## Emergency response and deletion

1. Disable outgoing send/command feature flag; rotate affected token at its provider; do not put secrets in incident notes.
2. Review scope of leakage, audit immutable action logs and revoke signed URLs/access. For compromised Discord webhook rotate URL and GitHub Actions secret.
3. Restore from last verified backup/version; preserve evidence of data/schema changes and audit.
4. For confirmed privacy leak, notify owner with actual facts and remediation steps; never claim deletion from third parties without evidence.

## Mandatory negative tests
Unauthorized Discord user; forged signature; replayed nonce; PDF with misleading content; prompt injection in job description; malicious mention; long Unicode Discord field; GitHub private file accidentally selected as public proof; double-click send; changed recipient after approval; backend 429 / timeout; revoked candidate fact used in resume draft; changed job URL/resume hash after application approval; double Submit; unsupported dot trigger; unknown EEO/legal question; employer confirmation missing; uncertain submission retry. Preserve approved packet privacy and fail closed. Fail closed, preserve old alerts.

## P2-R1 observed logging and state safeguards
Failed webhook requests log only exception type or HTTP status, omitting response bodies and secret-bearing exception URLs. Successful requests log HTTP ACK without payload. Read-only health reports omit raw error strings. Dry-run and health cannot persist v1 migrations. Corrupt ledger containers/timestamps fail closed before alerting. These tests do not establish successful live delivery or complete security coverage.

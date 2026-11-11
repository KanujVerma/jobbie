# Phase 6 executable contract — startup outreach and recruiting follow-up

**PLANNED.** Depends on Phase 5 release for application handoff architecture, although some startup discovery research can be implemented as an isolated earlier research fixture if specifically approved. Previously separate Phases 5 (outreach) and 6 (tracking) are combined without dropping their requirements.

## P6-A: startups and evidence-backed hiring signals
- Source startup companies around SF Bay Area primarily and also NYC/Miami/other FL/CA/TX/Chicago from verified company sites, official job APIs and permitted sources. Distinguish `confirmed_open_job` from `outreach_target_without_posting`. Company product/stage/location and signals need dated source.
- Rank against approved PUBLIC candidate facts and projects. No fake traction/hiring/current headcount, no scraping protected LinkedIn/Jobright data.
- Test 20 company fact samples with source evidence and disabled sources when rights unknown.

## P6-B: verified contacts and separately approved email
- Public verified business contacts or owner-supplied contacts only; don't guess email patterns. Generate concise natural company-specific draft grounded in 1–2 authorized PUBLIC project facts.
- Owner approves exact recipient/subject/body/nonce/hash before an authenticated OAuth sender can send. No unsolicited mass outreach, unapproved LinkedIn DM automation, hidden free trial promise or fabricated referral.
- Provider message ID/receipt, idempotency on retry, `indeterminate` if timeout, bounce/opt-out handling; block on missing OAuth and require single owner-approved live send for release.

## P6-C: full application lifecycle + reminders and feedback
- Add digest, follow-up reminders, recruiter events, saved/applied/assessment/interview/offer/reject/revise/withdraw/closed while preserving early Phase 3 immutable application ledger and Phase 5 confirmed attempt receipts.
- Schedule safely and reflect real cron delays; do not invent deadlines, current opening status or mark applied from viewing a URL.
- Feedback improves ranking against manually labeled job relevance and outcomes; no black-box claim of hiring probability. Optional consented Gmail read-only classification marks ambiguous status `needs_review` until confirmed.
- Export/delete private data, retention and access audit. Never leak family referral contacts, resume versions or OAuth tokens.

### Release gates
20 source-backed company fact samples; no guessed business contacts; one owner-approved real outreach email if enabled; correct record/message idempotence; at least one real deduped reminder; original job alerts and personal resume pipeline unaffected by outage.

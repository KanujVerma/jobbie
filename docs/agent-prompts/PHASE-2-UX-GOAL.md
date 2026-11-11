# Copy/paste first /goal: Phase 2-UX1 (notification card redesign)

/goal

Repository: KanujVerma/jobbie
Scope: **ONLY P2-UX1**, a one-PR presentation update to the EXISTING Discord webhook alerts. No other phase.

READ FIRST: AGENTS.md, docs/HANDOFF.md, docs/STATUS.md, docs/PRODUCT.md, docs/DECISIONS.md, docs/CONTRACTS.md, docs/NOTIFICATIONS_V2.md, docs/phases/PHASE-2-UX.md, docs/EVALS.md, docs/SECURITY.md, docs/OPERATIONS.md. Inspect latest main HEAD, src/notifier.py, src/models.py, src/eligibility.py, source adapters and tests before editing. Confirm P2-A #23/#24 merged; current 13 original Network Priority sources retained.

IMPLEMENT:
1. Replace cluttered embed layout with one job-title-first card: company/location, clearly labeled full-time/early-career attributes, original-source star or DISCOVERED, accurate UNCONFIRMED referral, verified BASE compensation with currency/period or "Not disclosed", deterministic eligibility screen with reasons/unknowns, truthful posted/first-observed date, and obvious official employer job URL. Source metadata in footer, not noisy tags.
2. Preserve original Notifier.send_job_alert(Job) -> bool and send_summary contract, webhook rate limit, delivery ACK/dedup, and old/Greenhouse/Ashby data models. Do not infer "verified" eligibility, a remote policy, salary, timestamp, match score or candidate experience from missing fields.
3. Add precise snapshot/adversarial tests for original 13/2 disabled, discovered, known/unknown/hourly compensation, date provenance and DST, multi-location, needs_review, missing description, unsafe URLs, mentions/long Unicode, Discord limits, legacy compatibility. Produce synthetic JSON previews (clearly not live).
4. DO NOT add interactive fake buttons; resume preview/approval and dot auto-apply require later authenticated private systems. Do not add/enable source boards or touch companies.yaml, state/seen_jobs.json, job-alerts.yml, AI/private storage or external accounts.
5. Run python main.py validate-config; python -m compileall -q src scripts; pytest -q. Inspect literal results, source SHA, GitHub CI. Request independent review and fix findings. Update docs/STATUS.md, docs/HANDOFF.md, docs/RELEASE_LOG.md in this PR; document before/after output, security, rollback and remaining limitations. Merge only if clean, otherwise leave reviewable PR and exact blocker.

STOP after P2-UX1. Do not begin P2-ACT, P2-B/C, Phase 3 or auto-apply. Final report: PR, SHA, test/review/run links, what changed, what remains unknown and next exact activation gate.

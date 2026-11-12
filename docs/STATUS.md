# Jobbie canonical project status

Verified2026-11-12UTC. Snapshot only; inspect current GitHub HEAD and Actions before acting.

## Released components

| Scope | Merged PR / full merge SHA | Evidence and remaining limits |
| --- | --- | --- |
| Public ATS | #23 / ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb | Existing adapter contracts retained. |
| Discord layout | #29 / e0346f49bd572179250fe08bed73131db0ba311a | Ordinary run43100310762 accepted2individual HTTP204 job sends; human receipt/client rendering unverified. |
| Reliability | #30 /614b3edc14e86d952579a0c57db0eb68669c08d9 | Exact-head CI and hosted review clean; pre-send corrupt-state guards and partial-run ACK persistence. |
| Owner intake | #32 /f46625845577f158da31974d927aa5748d0c3642 | Exact-head CI/review clean; postmerge43114825827 passed. Disabled proposals only; no employer activated. |
| Plaid/Amazon | #31 /9317c73b1971d6c7bb19dcb22a6be76876ad7369 | Exact-head81524a6 CI/review clean; postmerge43116984772 passed. Plaid first complete silent baseline PENDING_LIVE. |
| Oracle | #33 /4eb83f454e2671e8e06d7cb10f4b079ab98fcf90 | Exact-head e976032 CI/review clean; postmerge43125554558 passed. Full995tests before merge. First ordinary corrected baseline PENDING_LIVE. |

Production retains exactly13 enabled original Network Priority sources with unconfirmed referrals, plus Snowflake/Applied Digital disabled. No employer/feed/profile/application is activated. Legacy seen/URL state, eligibility, dedup, backfill, rate limits and ACKs remain authoritative. Never reset/seed state or force a send to manufacture proof.

## Actual production evidence

Latest ordinary [Job Alerts43100310762](https://github.com/KanujVerma/jobbie/actions/runs/43100310762) ran R1 on2026-11-11:12/13responding, Plaid404, Oracle/SanDisk empty;4matched/323review/8994excluded,2individual Amazon HTTP204 ACKs,0failed job sends. State commit f3deaae743dd5e0c889cf5a2dfda5c42281452ba persisted ACKs. This establishes webhook acceptance, not human receipt/client rendering or independently verified employer eligibility. Issue25 closed with these limits. [Receipt](evidence/P2-UX1-LIVE-ACK-2026-11-11.md). Observed gap430.4minutes; cron remains best effort.

No ordinary schedule after #31/#33 qualifies at this checkpoint. Plaid/Oracle source revisions stay pending until a complete ordinary scan silently baselines old roles without fake ACKs. Partial/failing scans must remain pending. SanDisk replacement ATS returned406: access BLOCKED, no bypass or no-openings claim.

## Current candidate and remaining Phase2

P2-B implements bounded OFF JSON leads, source provenance/health/dedup and exact official-employer URL/ID confirmation. Three evaluated feeds remain OFF with BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL. No feed dataset was fetched; actual feed coverage/confirmation/freshness NOT_MEASURED. See [guide](PUBLIC_FEEDS.md), [rights](evidence/P2-B-SOURCE-RIGHTS.json) and [verification](evidence/P2-B-VERIFICATION.md). Candidate current-head independent review, CI, hosted review and merge remain gates.

P2-C remains to implement: SQLite pre-filter normalized catalogue, identities/provenance/dates/unknowns, history/dedup/reclassification/query/export, crash-safe shadow and reconciliation/rollback. Actual >=72h shadow has not started. Keep legacy delivery authority until parity/rollback proof and exact owner cutover approval. Missing evidence/approval stays BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL, while independent code proceeds.

Phase2 is PARTIAL, not complete. Next major goal is P3-A signed allowlisted private Discord interactions, profile/resume upload with evidence, and deterministic matching. Tailoring is Phase4; exact one-job approved application execution is Phase5. No dot API/trigger is verified.

P2-B local Sol review found2reproduced defects (supported posting-ID confirmation and conflicting duplicate posting dates); parent fixed both with6focused cases. See evidence/P2-B-REVIEW.md; fresh full checks and hosted exact-head independent review remain release gates.

P2-B corrected candidate: full1039passed37.12s, focused44passed; repeated config/OFF CLI/Plaid no-webhook check preserved bytes. No feed activated.

P2-B hosted H1 reproduced quadratic confirmation work; fixed by one employer URL/company index. The actual poller regression drops4000normalizations to120for100postings/20leads, preserving ambiguity/source-ID checks. Fresh current-head CI/hosted review required; no source activated.

P2-C1 local implementation in progress: SQLite normalized source snapshots/identities/history/status evidence, immutable reclassification and bounded query/export CLI. Production polling still uses legacy JSON only. C2 shadow capture/persistence/parity/rollback and >=72h actual evidence remain required. See CATALOGUE.md and the2026-11-12catalogue plan. No canonical cutover or new employer/feed is approved.

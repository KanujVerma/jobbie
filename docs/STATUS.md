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
| Optional feeds | #34 /f3a61f4ab2d5165474ffddf63ac0e052b4a75fdb | Full1041tests; exact-head2ef45e1 CI/review and postmerge43128988343 passed. All3feeds remain OFF/rightsblocked. |

Production retains exactly13 enabled original Network Priority sources with unconfirmed referrals, plus Snowflake/Applied Digital disabled. No employer/feed/profile/application is activated. Legacy seen/URL state, eligibility, dedup, backfill, rate limits and ACKs remain authoritative. Never reset/seed state or force a send to manufacture proof.

## Actual production evidence

Latest ordinary [Job Alerts43100310762](https://github.com/KanujVerma/jobbie/actions/runs/43100310762) ran R1 on2026-11-11:12/13responding, Plaid404, Oracle/SanDisk empty;4matched/323review/8994excluded,2individual Amazon HTTP204 ACKs,0failed job sends. State commit f3deaae743dd5e0c889cf5a2dfda5c42281452ba persisted ACKs. This establishes webhook acceptance, not human receipt/client rendering or independently verified employer eligibility. Issue25 closed with these limits. [Receipt](evidence/P2-UX1-LIVE-ACK-2026-11-11.md). Observed gap430.4minutes; cron remains best effort.

No ordinary schedule after #31/#33 qualifies at this checkpoint. Plaid/Oracle source revisions stay pending until a complete ordinary scan silently baselines old roles without fake ACKs. Partial/failing scans must remain pending. SanDisk replacement ATS returned406: access BLOCKED, no bypass or no-openings claim.

## Catalogue candidate and remaining Phase2

P2-C1 is implemented locally on feat/p2-c-catalogue, rebased onto B merge f3a61f4. SQLite retains normalized source snapshots, stable provider/requisition/URL identities, source/observation history, explicit unknown/closed/reopen evidence, immutable policy reclassification and bounded query/history/JSONL/CSV export. No normal-poller hook or SQLite delivery authority yet. Full1105tests passed44.19s,64catalogue cases; config/diff/docs checks pass. Independent review, own PR/current-head CI/hosted review/merge remain gates. [Guide](CATALOGUE.md), [proof](evidence/P2-C1-VERIFICATION.md).

Approved Plaid local capture stored143pre-filter rows/143jobs/143snapshots,0rejected/identityconflicts. Deterministic eligibility alone:4eligible/8review/131excluded; those4are not alert candidates or proof of freshness. Normal no-webhook dry-run had0candidates/alerts and preserved config/seen bytes. Read-only catalogue query/export preserved DB bytes. Local source proof is not a scheduled production shadow run.

P2-C2 remains required: automatic pre-filter capture, crash-safe persistent encrypted shadow, independent identity/candidate/ACK reconciliation, rollback proof and actual>=72h ordinary scheduled comparison. Window not started. Legacy JSON/URL state stays authoritative until parity/rollback proof and exact owner cutover approval, followed by an ordinary scheduled run. BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL remain explicit while implementation continues.

All3evaluated optional feeds remain OFF/BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL. No feed dataset fetched; actual feed coverage/confirmation/freshness NOT_MEASURED. [Guide](PUBLIC_FEEDS.md), [pinned rights](evidence/P2-B-SOURCE-RIGHTS.json). Owner intake [COMPANY_INTAKE.md](COMPANY_INTAKE.md) produces disabled discovered/networkfalse/referralunavailable proposals; no employer activated.

Phase2 is PARTIAL, not complete. Exact next major goal: P3-A signed allowlisted private Discord interactions, private profile/resume upload with evidence and deterministic matching. Tailoring Phase4; exact one-job approved application execution Phase5. No dot API/trigger is verified.

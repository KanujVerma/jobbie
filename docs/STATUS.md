# Jobbie canonical project status

Snapshot refreshed after ordinary run43140198821 on2026-11-12UTC. Inspect current GitHub HEAD/Actions before acting.

## Released components

| Scope | Merged PR / full merge SHA | Evidence and remaining limits |
| --- | --- | --- |
| Public ATS | #23 / ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb | Existing adapter contracts retained. |
| Discord layout | #29 / e0346f49bd572179250fe08bed73131db0ba311a | Ordinary run43100310762 accepted2individual HTTP204 job sends; human receipt/client rendering unverified. |
| Reliability | #30 /614b3edc14e86d952579a0c57db0eb68669c08d9 | Exact-head CI and hosted review clean; pre-send corrupt-state guards and partial-run ACK persistence. |
| Owner intake | #32 /f46625845577f158da31974d927aa5748d0c3642 | Exact-head CI/review clean; postmerge43114825827 passed. Disabled proposals only; no employer activated. |
| Plaid/Amazon | #31 /9317c73b1971d6c7bb19dcb22a6be76876ad7369 | Exact-head81524a6 CI/review clean; postmerge43116984772 passed. Plaid silent baseline VERIFIED_LIVE in43140198821. |
| Oracle | #33 /4eb83f454e2671e8e06d7cb10f4b079ab98fcf90 | Exact-head e976032 CI/review clean; postmerge43125554558 passed. Full995tests before merge. Oracle silent baseline VERIFIED_LIVE in43140198821. |
| Optional feeds | #34 /f3a61f4ab2d5165474ffddf63ac0e052b4a75fdb | Full1041tests; exact-head2ef45e1 CI/review and postmerge43128988343 passed. All3feeds remain OFF/rightsblocked. |

Production retains exactly13 enabled original Network Priority sources with unconfirmed referrals, plus Snowflake/Applied Digital disabled. No employer/feed/profile/application is activated. Legacy seen/URL state, eligibility, dedup, backfill, rate limits and ACKs remain authoritative. Never reset/seed state or force a send to manufacture proof.

## Actual production evidence

[Run43140198821](https://github.com/KanujVerma/jobbie/actions/runs/43140198821) on f3a61f4 automatically scanned13sources successfully,1empty(SanDisk). Plaid143and Oracle2113completed their first silent provider baselines:0new individual job ACKs, delivery_acknowledged=false, all2256new baseline records suppressed/alerted=false. State d4724df3e3f70b17762f123c32216a1a671e8bfb retained all257legacy seen ACK flags/10URL entries with0lost. [Receipt](evidence/P2-R2-R3-LIVE-2026-11-12.md). No dispatch/seed/reset/forced backfill/test send.

11569fetched,2matched/356review/11211excluded,0new job ACKs/0job send failures;600.08s duration,301.43minute scheduler gap. Successful responses do not establish13healthy employer catalogues or no openings. SanDisk replacement406remains BLOCKED_SOURCE_ACCESS; no bypass. Cron is best effort. Prior run43100310762 separately established2individual Amazon HTTP204ACKs and persisted them; human receipt/client rendering remains unverified.

## Catalogue implementation and remaining Phase2

P2-C1 local store/query PR35 is under final gates. Source code from reviewed9add133 is unchanged while rebasing onto the real production state d4724df; repeat combined full checks/new-head CI/hosted review before merge.77focused/full1118tests passed39.68s before this state-only rebase. SQLite identities/snapshots/history/unknown closure/reopen, versioned reclassification and bounded query/export are implemented. Local/hosted findings and one failed intermediate attempt are truthfully retained in evidence/P2-C1-REVIEW.md. No failed or stale head is merge evidence.

C2 draft feat/p2-c-shadow is public for handoff, no PR/key/deployment yet. Shadow hooks/filter-candidate-ACK comparisons, optional lead rights/provenance, memory-only dry-run, encrypted checkpoint/rollback helpers/CLI and optional crypto dependency are implemented locally. An intermediate base passed30focused/1137fulltests; after C1 integration107focused passed. These are local/code facts, not production evidence. Synthetic capacity testing requires compact logical scan membership/timestamp context before safe deployment; workflow/audit/remaining full gates are unfinished. [Plan](superpowers/plans/2026-11-12-p2-c-catalogue.md), [guide](CATALOGUE.md).

All3optional feeds remain OFF/BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL;0datasets fetched, actual feed coverage/freshness NOT_MEASURED. Intake proposals stay disabled/discovered/networkfalse/referralunavailable; no new employer activated. Preserve13enabled original Network Priority sources/unconfirmed referrals and2historicaldisabled; legacy seen/URL delivery authority remains.

Actual>=72h catalogue shadow has not started. Production cutover needs exact owner approval, parity/reconciliation and rollback proof, then a real scheduled run. BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL remain; complete independent code meanwhile. Phase2 PARTIAL, not complete. Exact next goal: P3-A signed allowlisted private Discord interactions, profile/resume upload/evidence and deterministic matching. Tailoring Phase4, exact one-job approved application execution Phase5. No verified dot API/trigger.

C1 production-state rebase verification: unchanged source implementation, full1118passed on the current d4724dfstate base. Repeated permitted Plaid local capture/CLI/no-webhook dry-run preserved config and new production state SHA256e1967067a69c86c5e39b8ac49e3c206aeb2193b17387aea4bf1dfa6885c7cdd6. Fresh current-head CI/hosted review still required.

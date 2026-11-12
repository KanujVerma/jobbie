# Jobbie canonical project status

Audited2026-11-11. Snapshot only; verify live GitHub HEAD, PRs and Actions before acting.

## Merged and operationally observed

Main includes P2-A #23, P2-UX1 #29, P2-R1 #30 and owner intake #32 (merge614b3edc14e86d952579a0c57db0eb68669c08d9). R1's exact reviewed head7a74936d22033c14abc2eac564c3db29edee09db passed both checks and completed hosted review without findings. Its all-partial-run state-commit finding was fixed before merge; the merge tree matched the reviewed tree.

Ordinary [Job Alerts43100310762](https://github.com/KanujVerma/jobbie/actions/runs/43100310762) ran merged R1 on2026-11-11: 12/13 responding, Plaid404, Oracle/SanDisk empty, 4matched/323review/8994excluded, 2individual Amazon HTTP204 ACKs and0failed job sends. State commit f3deaae743dd5e0c889cf5a2dfda5c42281452ba persisted the ACKs. This establishes P2-UX1 webhook acceptance; issue25 is closed. Human receipt, Discord-client rendering and independent employer eligibility are not established. [Live receipt](evidence/P2-UX1-LIVE-ACK-2026-11-11.md). The gap after previous finish was430.4minutes; cron remains best effort.

Production still has exactly13 enabled original Network Priority sources, referral unconfirmed, plus Snowflake/Applied Digital disabled. No new employer/feed/catalogue/private profile/application service is enabled. State is preserved; never reset it or force backfill to manufacture proof.

## Source repair candidates

[P2-R2 PR31](https://github.com/KanujVerma/jobbie/pull/31) merged9317c73b1971d6c7bb19dcb22a6be76876ad7369 after exact-head CI/clean hosted review on81524a6. Post-merge Tests43116984772 passed; merge/reviewed trees match. No ordinary schedule after that merge qualifies yet: Plaid production baseline is PENDING_LIVE. Do not seed state or force a send.

P2-R3 Oracle candidate is published on [its source branch](https://github.com/KanujVerma/jobbie/tree/feat/p2-oracle-source), latest published5a167754a12ceddf0f0012fa1d577a4a7ac4e209. Local re-check approved b7112bcf4b30d277050a1556858f4e049093a62c, independent938tests. Documented finder restored2113 US-search rows in a no-webhook scan; overlapping pages fail baseline completion. Parent merge, own rebase/PR/CI/hosted review/merge and real schedule remain gates. SanDisk replacement ATS returned406; no bypass or no-openings claim.

## Merged owner-directed intake

[P2-ACT PR32](https://github.com/KanujVerma/jobbie/pull/32) merged f46625845577f158da31974d927aa5748d0c3642 after both exact-head checks and clean hosted review on8e6a7e2be9974d45b810d9cceda7f1220d4920fe. Post-merge Tests43114825827 passed. Local/independent928tests covered52intakecases. Issue26 is closed for the intake scope. [Guide](COMPANY_INTAKE.md), [evidence](evidence/P2-ACT-VERIFICATION.md). No employer was activated; proposals stay OFF and require separate exact owner approval.

## Remaining full Phase2

Implement P2-B reusable OFF public feeds with source/data rights and official employer confirmation, then P2-C SQLite pre-filter catalogue, identity/provenance/history, dedup/reclassification/search/export, shadow comparison and rollback. Cached upstream policy research identifies missing data rights; the feed capability is still to implement. Catalogue is still to implement; >=72h real shadow has not started and cutover is unapproved. Missing rights/approval/72h evidence stay BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL/BLOCKED_72H_EVIDENCE while independent work continues.

Next major goal after Phase2 gates is P3-A signed allowlisted Discord interactions, private profile/resume upload/evidence and deterministic matching. Tailoring is Phase4; exact one-job approved application execution is Phase5. No dot API/trigger has been verified.

P2-ACT local review approved b58076cf7dcd7153a860841023ac246fb5f8280a in one round, independently passing928tests in36.74s, config/diff checks. No findings. Own PR/exact-head CI/hosted review/merge are still pending; production activation is not approved. See evidence/P2-ACT-REVIEW.md.

## PR31 modernization checkpoint
Main's merged intake changes overlap PR31's docs/main orchestration, so the source branch was rebased onto f466258 to resolve the actual conflict. Current production seen state is retained exactly. The old reviewed source head5d034f5 remains historical evidence; source functional patch ID is unchanged (d3c04a39c60a21e63ef209bb22872ee5b273f992), while documentation preserves both intake and source-rollout contracts. Fresh current-head CI/hosted review are required; old queued runs do not qualify a new head.

PR31 modernization proof: combined full952tests passed36.35s (source repair plus merged intake), config/compileall/diff passed. Plaid targeted no-webhook dry-run exited0 with identical state/config hashes. Current state matches main exactly; no reset/seed/manual edits. Fresh full-head CI/hosted review remains required.

P2-R3 is rebased onto merged parent9317c73 without changing its approved functional patch (76c6409fe877a5fac07570fb78aa05916a71fc1e). Current own PR/CI/hosted review remain required. The first corrected Oracle production baseline will also require an ordinary post-merge run. SanDisk replacement access remains blocked406, no bypass.

Oracle integration verification: rebase onto merged9317c73 retains functional patch76c6409fe877a5fac07570fb78aa05916a71fc1e. Combined full990tests passed36.78s; config/compileall/diff pass, current main seen-state retained unchanged. Local Oracle behavior was independently approved atb7112bc with938tests before base integration; own current-head hosted review/CI/merge remain required.

Hosted H1 correction: the explicit citizenship matcher rejected a clause that also accepts permanent residency. Parent reproduced4failing alternative clauses, then checks the immediate continuation for an accepted residency/green-card alternative while retaining any separate mandatory citizenship clause. Five focused cases now pass. No personal status is inferred. Fresh exact-head hosted review/CI required; prior local review remains scoped to its earlier head.

Oracle H1 verification: full995tests passed38.93s;5focused clauses, config/compileall/diff passed. A separate mandatory clause still excludes correctly. This does not repeat live source/client rendering or approve production cutover.

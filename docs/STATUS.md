# Jobbie canonical project status

Audited2026-11-11. Snapshot only; verify live GitHub HEAD, PRs and Actions before acting.

## Merged and operationally observed

Main includes P2-A #23, P2-UX1 #29 and P2-R1 #30 (merge614b3edc14e86d952579a0c57db0eb68669c08d9). R1's exact reviewed head7a74936d22033c14abc2eac564c3db29edee09db passed both checks and completed hosted review without findings. Its all-partial-run state-commit finding was fixed before merge; the merge tree matched the reviewed tree.

Ordinary [Job Alerts43100310762](https://github.com/KanujVerma/jobbie/actions/runs/43100310762) ran merged R1 on2026-11-11: 12/13 responding, Plaid404, Oracle/SanDisk empty, 4matched/323review/8994excluded, 2individual Amazon HTTP204 ACKs and0failed job sends. State commit f3deaae743dd5e0c889cf5a2dfda5c42281452ba persisted the ACKs. This establishes P2-UX1 webhook acceptance; issue25 is closed. Human receipt, Discord-client rendering and independent employer eligibility are not established. [Live receipt](evidence/P2-UX1-LIVE-ACK-2026-11-11.md). The gap after previous finish was430.4minutes; cron remains best effort.

Production still has exactly13 enabled original Network Priority sources, referral unconfirmed, plus Snowflake/Applied Digital disabled. No new employer/feed/catalogue/private profile/application service is enabled. State is preserved; never reset it or force backfill to manufacture proof.

## Source repair candidates

[P2-R2 PR31](https://github.com/KanujVerma/jobbie/pull/31), head5d034f57ceebec206f3ca5b3279c41e398f29a7b: Plaid/Amazon repairs and silent provider baseline, local/independent900tests and clean hosted review. Exact-head Tests43098516268/public-read43098516215 remain queued at last observation, with zero jobs. R1 post-merge Tests43095321312 also queued. Existing handles are preserved; no merge without actual checks.

P2-R3 Oracle candidate is published on [its source branch](https://github.com/KanujVerma/jobbie/tree/feat/p2-oracle-source), latest published5a167754a12ceddf0f0012fa1d577a4a7ac4e209. Local re-check approved b7112bcf4b30d277050a1556858f4e049093a62c, independent938tests. Documented finder restored2113 US-search rows in a no-webhook scan; overlapping pages fail baseline completion. Parent merge, own rebase/PR/CI/hosted review/merge and real schedule remain gates. SanDisk replacement ATS returned406; no bypass or no-openings claim.

## Active P2-ACT candidate

Owner-directed issue form, portable request CLI, source-evidence/alias/collision checks and disabled proposals are implemented locally in feat/p2-owner-intake. Local full928tests passed in31.74s; intake52cases. Live verification-only provider reads and a complete Greenhouse CLI OFF-proposal probe passed with unchanged production hashes; this is not an owner company request or activation. [Intake guide](COMPANY_INTAKE.md), [verification](evidence/P2-ACT-VERIFICATION.md). Independent review, exact-head CI/hosted review and merge remain pending. No requested company inherits a confirmed referral or original Network Priority.

## Remaining full Phase2

Implement P2-B reusable OFF public feeds with source/data rights and official employer confirmation, then P2-C SQLite pre-filter catalogue, identity/provenance/history, dedup/reclassification/search/export, shadow comparison and rollback. Cached upstream policy research identifies missing data rights; the feed capability is still to implement. Catalogue is still to implement; >=72h real shadow has not started and cutover is unapproved. Missing rights/approval/72h evidence stay BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL/BLOCKED_72H_EVIDENCE while independent work continues.

Next major goal after Phase2 gates is P3-A signed allowlisted Discord interactions, private profile/resume upload/evidence and deterministic matching. Tailoring is Phase4; exact one-job approved application execution is Phase5. No dot API/trigger has been verified.

P2-ACT local review approved b58076cf7dcd7153a860841023ac246fb5f8280a in one round, independently passing928tests in36.74s, config/diff checks. No findings. Own PR/exact-head CI/hosted review/merge are still pending; production activation is not approved. See evidence/P2-ACT-REVIEW.md.

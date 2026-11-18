# Phase2 acceptance ledger

Verify current GitHub and Actions before acting. C2 [#36](https://github.com/KanujVerma/jobbie/pull/36) is merged and has live encrypted custody receipts. The 72-hour window and exact cutover approval are open. [Scheduled shadow status](STATUS.md#scheduled-catalogue-shadow-through-2026-11-17-utc)

## First ordinary run after PR #38

[Run 44286689134](https://github.com/KanujVerma/jobbie/actions/runs/44286689134), attempt 1, checked out `998e929117cd7b87695d1f913e4559a3ac8d6f23` on `main`, a descendant of the PR #38 squash commit `c073060348b20f767f3b7ea42ccce6767ef0b46b`. It started November 18 at 10:34:29 UTC, 8h 08m 34s after the [last pre-fix scan](https://github.com/KanujVerma/jobbie/actions/runs/44223196999) and before the 14:25:55 UTC cutoff. [Issue #7 receipt](https://github.com/KanujVerma/jobbie/issues/7#issuecomment-6981493023)

- **Coverage and retries.** Eight of 13 sources completed, including SanDisk's empty result. Micron, Salesforce, CrowdStrike and Applied Materials exhausted bounded retries and received terminal HTTP 429 at offset zero. Intel returned 60 rows and remained partial after a terminal 429 at offset 60. Logs show 1s, 2s and 4s retry delays. The run supplies no header-specific retry evidence. [Run logs](https://github.com/KanujVerma/jobbie/actions/runs/44286689134/job/134741055017)
- **Shadow parity.** There were 3,897 observed rows, zero identity rejects, zero identity conflicts and zero filter, candidate or ACK mismatches. Coverage gaps kept parity false under `BLOCKED_SOURCE_SCAN`. Applied Materials returned no rows in this run, so its previously documented rejection remains a separate historical result. [Published shadow health](https://github.com/KanujVerma/jobbie/blob/fa3b29ea3f7cecd9b3cd729e8ef3440a9e31b69a/state/catalogue_shadow_health.json)
- **Legacy delivery.** Zero new job alert ACKs. All 235 historical job ACK flags and 11 URL ACK keys survived with zero loss. The legacy state file matches the SHA-256 recorded in the published checkpoint. [Legacy state commit](https://github.com/KanujVerma/jobbie/commit/fdc7802bdb34defd0e4846a052adff6b389344c5)
- **Encrypted custody.** The workflow restored the exact parent, saved and restored the new encrypted checkpoint, and published verified custody. The catalogue UUID and config fingerprint stayed consistent, and the new parent digest matches the prior checkpoint. The published record confirms cache round-trip and rollback verification. [Parent checkpoint](https://github.com/KanujVerma/jobbie/blob/998e929117cd7b87695d1f913e4559a3ac8d6f23/state/catalogue_shadow_checkpoint.json) · [Published checkpoint](https://github.com/KanujVerma/jobbie/blob/fa3b29ea3f7cecd9b3cd729e8ef3440a9e31b69a/state/catalogue_shadow_checkpoint.json)

The scheduler met the 12-hour test on this interval. `BLOCKED_72H_EVIDENCE` and `BLOCKED_APPROVAL` remain open. Legacy JSON remains authoritative. [PR #38 release receipt](https://github.com/KanujVerma/jobbie/pull/38#issuecomment-6967392364)

| Requirement | Current proof | Status / remaining gate |
| --- | --- | --- |
| Existing direct ATS/Discord layout retained | Merged #23/#29, subsequent full suites; ordinary43100310762 accepted2individual HTTP204job sends | Implemented/merged; human receipt/client rendering unverified |
| Original13source reliability/failed-send ACK/corrupt state/dry-run | #30/#31/#33; regression suites and ordinary43140198821 | Verified scoped behavior; source coverage is within configured queries |
| Plaid first complete ordinary silent baseline |143rows, revision complete, delivery_acknowledged=false,0new job ACKs; state d4724df | VERIFIED_LIVE |
| Oracle finder/site/location/pagination/partial semantics | #33; real2113-row complete ordinary baseline,0new job ACKs | VERIFIED_LIVE |
| No state reset/fake ACK/backfill flood | Ordinary state retained all257seen ACK flags/10URL entries;2256baseline records alerted=false | Verified first repaired scan; preserve ongoing legacy authority |
| SanDisk source completeness | Current empty response; official replacement406 | BLOCKED_SOURCE_ACCESS; do not bypass or infer no openings |
| Scheduling/delivery health | Actual600.08s run/301.43minute gap, health reports and preserved partial-run state commits | Best-effort cron. First post-#38 interval was 8h 08m 34s |
| Owner company intake/issue/portable CLI/agent workflow | #32, COMPANY_INTAKE.md, tests/manual-evidence/fixed-probe receipts | Merged; all proposals OFF/discovered/networkfalse/referralunavailable |
| Roster/referrals/opt-in expansion | companies.yaml unchanged13enabled original Network Priority +2historicaldisabled | Preserved; exact new employer approval absent |
| Generic optional feed infrastructure | #34 + candidate C2 provenance persistence; source/rights gates/bounds/errors/ID/date collisions/official confirmation tests | Merged OFF capability; no actual feed coverage |
| Real feed rights/activation | Pinned P2-B-SOURCE-RIGHTS.json; New-Grad-Jobs excludes job data, others lack confirmed data rights | BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL; all3OFF,0datasets fetched |
| Normalized catalogue before filtering | C1 #35 + C2 normal-run hook and compact logical history; [first scheduled shadow](https://github.com/KanujVerma/jobbie/actions/runs/43197320954) | Live in shadow; Workday coverage remains degraded on the latest observed run |
| Stable IDs/URLs/original sources/date precision/unknown lifecycle/reopens | C1 identity/history tests + C2 compact history/context/migration regressions | Implemented/tested locally; no title-only merging |
| Cross-source dedup/reclassification/query/export | C1 CLI/API and C2 canonical projection; exact source/employer facts, policy versioning | Implemented; preserve conflicts/unknowns, never infer referral |
| Crash-safe shadow/custody/parity/rollback | C2 transactions, v1 backup, bounded Fernet roundtrip and ACK-before-transport workflow; [first post-#38 receipt](https://github.com/KanujVerma/jobbie/actions/runs/44286689134) | Encrypted parent and fresh checkpoint restore and publication verified. Parity degraded under `BLOCKED_SOURCE_SCAN` |
| Verified $0 storage/private source data | Standard-library SQLite/public domain, optional Apache/BSD crypto, included cache usage guard; ciphertext only | Policy/read-only usage checked; custom paid-limit read402unverified, no change/bypass |
| >=72h actual shadow comparison | Public logs show about 26 hours at most across consecutive healthy runs through 2026-11-17 UTC; the authenticated audit checks the retained receipts and current code/config | BLOCKED_72H_EVIDENCE |
| Exact production cutover approval | Read-only owner-bound audit; no actuation/sender/authority switch | BLOCKED_APPROVAL; legacy JSON remains authority |
| Ordinary run after approved cutover | No cutover performed | BLOCKED_APPROVAL/PENDING_LIVE after any later authorization |
| Per-PR tests/docs/CI/independent review/rollback | STATUS/HANDOFF/RELEASE_LOG + exact-head proof/review ledgers | C2 exactfe8f7f7 CI/hosted clean; no failed/stale head counts |
| Privacy/no extra sends/paid services/applications | Whitelisted public-source data/private encrypted storage; no private profile/resume/application code; dry-run/missing-dependency regressions | Preserved within implemented scope; no test dispatch/send |
| Roadmap/handoff | PHASES/specs/prompts/current docs/issue7; source commits/evidence linked | Keep current through C2 release and final audit |

Next exact major goal after the Phase2 gates: P3-A signed allowlisted private Discord interactions, private profile/resume upload with evidence, and deterministic matching. Tailoring is Phase4; exact one-job approved applications Phase5. No verified dot API/trigger or application authorization exists here.

# Implemented architecture and operational proof

Snapshot2026-11-12UTC. Verify current main/PRs/Actions before acting. #23ATS, #29Discord layout, #30reliability, #32owner intake, #31Plaid/Amazon, #33Oracle, #34OFFfeeds and #35catalogue core are merged. STATUS/RELEASE_LOG have exact SHAs/CI. C2 #36 merged830dcd13d05433b286e7b810385807481e9cc744 after exact-head CI/hosted review; its workflow is active and secret provisioned. First ordinary shadow verification and72h are separate pending facts.

## Legacy delivery authority

GitHub Actions best-effort schedule -> main.py run ->13enabled source entries -> BaseAdapter.fetch -> immutable Job -> deterministic freshness/location/tri-state eligibility -> legacy seen/URL classification -> bounded Notifier -> atomic seen JSON save/state commit. Unknown early-career records go to review/digest; represented-link backfill ACKs only after successful delivery. No internship/private profile/application feature is added here.

Original Network Priority is source configuration, not a referral. Role/location preference is separate. Workday details can be incomplete; Oracle finder supplies date-only/unknown employment/description facts. Do not turn missing source facts into qualifications or timestamps. Exactly13original enabled sources plus2historicaldisabled remain; no new employer/feed is enabled. Source failures/partial/empty distinguish responding within configured scope from verified employer coverage.

## Implemented modules

| Boundary | Implemented code | Authority / limits |
| --- | --- | --- |
| Public employer ingestion | src/adapters/*, public_board.py, HTTPClient | Official/fixed approved sources, bounded retries/errors; no protected scraping/login |
| Eligibility | filtering.py, eligibility.py, experience.py | Deterministic tri-state, source unknowns preserved; no hiring outcome/application authority |
| Legacy ledger/delivery | storage.py, source_migration.py, backfill.py, notifier.py, health.py | JSON/URL ACK authority, quiet revisions, limits/dedup, no reset |
| Owner intake | company_intake.py, CLI/form, COMPANY_INTAKE.md | Portable monitor/startup-research requests, manual evidence/fixed probes, OFF proposals; no dot API/activation |
| Optional leads | public_feeds.py, job_identity.py, PUBLIC_FEEDS.md | OFF rights/owner gates, bounded JSON/provenance/health, exact current official link;0production feeds |
| Catalogue C1 | catalogue.py, catalogue_cli.py, CATALOGUE.md | SQLite normalized identities/history/reclassification/search/export; no send authority |
| C2 #36 merged shadow | catalogue_history.py, catalogue_shadow.py, catalogue_checkpoint.py, catalogue_operations.py, workflow | Pre-filter compact logical observations/context, independent parity, encrypted custody/rollback; actual ordinary evidence/72h/approved cutover still required |

No Cloudflare service/database, AI provider, long-running private interaction server, resume upload, recruiter OAuth or application executor is deployed. Future provider boundaries in ARCHITECTURE are design, not capabilities.

## Actual production and rollback

Ordinary43140198821 on f3a61f4 retained real state d4724df: Plaid143/Oracle2113complete silent baselines,0new job ACKs, all257legacy seen ACK flags/10URL entries retained.13successful responses/1empty SanDisk,11569fetched/2matched/356review/11211excluded,600.08s/301.43minute gap. See evidence/P2-R2-R3-LIVE-2026-11-12.*. No manual seed/dispatch/backfill. SanDisk replacement406 remains access blocked; empty is not no openings. Earlier43100310762 separately accepted2individual HTTP204job sends; human receipt/rendering unverified.

C2 preserves original JSON authority and isolates optional crypto/custody failures. Its workflow commits ACKs before optional transport and publishes a new checkpoint only after a fresh exact-key ciphertext restore/digest check. Latest DB snapshots retain all append-only canonical history; only redundant task-owned encrypted transport copies may expire. Roll back by disabling optional shadow stages/mode, retaining both ledgers/keys; never reset history or bypass lost custody. These mechanics have local/fixture proof; deployed scheduled comparison and>=72h are not established by those tests.

## Next boundaries

Complete C2 release and ordinary verification, then record real72h/approval gates truthfully. Exact owner approval/parity/rollback is required before any canonical delivery cutover, followed by an ordinary scheduled run. Phase2 remains PARTIAL meanwhile.

Next major goal: P3-A signed allowlisted private Discord interactions, profile/resume upload/evidence and deterministic matching. P4grounded tailoring/owner resume approval is separate from P5one-exact-job approved application execution. Dot-first execution remains a manual feasibility path, no verified direct dot API. P6startup sourcing/outreach requires source permission and exact-message approval; no automatic LinkedIn sending. No model-only claim establishes a credential, open role, send or application outcome.

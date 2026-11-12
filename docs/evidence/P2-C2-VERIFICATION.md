# C2 verification tiers

C2 is a candidate until its own review/CI/merge and ordinary scheduled shadow run are observed. No local/synthetic capacity result counts as a real72hwindow or cutover.

## Real permitted original13read, no mutation

Corrected full normal polling with JOBBIE_CATALOGUE_MODE=shadow and --dry-run --verbose completed527.29s. All13configured source entries,11582normalized observations/jobs/snapshots,0rejections/identity conflicts/filter mismatches/candidate mismatches/ACK mismatches. Source returned data includes configured scope, not every global employer role; SanDisk returned empty and replacement406access remains blocked. No third-party feed dataset read, no sender/webhook environment,0agent sends. Legacy config/state/input-DB bytes unchanged. Source capture code digest c7aba85ad50aba3ce98a4bb1601f2a0fafd97ce77ce4bead958d4cea34cc7e41. Later changes are transport capacity/retention, tested separately; do not promote this into an exact later-head operational claim.

Memory-only normalized SQLite measured52674560rawbytes/10207883compressedbytes. It was never persisted to production state or publicly exposed. Receipt P2-C2-LIVE-READ-2026-11-12.json. Config SHA2568afbe552edb59566e6bedf604510337bf5d1e3a6cc02c02f1b8161dd0ece12f0, production seen e1967067a69c86c5e39b8ac49e3c206aeb2193b17387aea4bf1dfa6885c7cdd6 preserved. No new baseline seed/backfill/reset; existing2256silent baseline facts preserved.

## Failed predecessor and reproduced correction

The first full legacy dry-run completed528.39s/exit0/no mutation but its shadow rejected1Micron row and stopped later shadow capture; P2-C2-LIVE-FAILED-2026-11-12.json remains a FAILED shadow receipt. The later permitted Micron-only diagnostic2902rows/0rejects did not reproduce that invalid row/cause. Do not call the initial failure success.

The isolation defect was reproduced with a rejected hostile-URL row plus a second valid source. Corrected code keeps rejection/identity gates, captures later valid sources and records legacy delivery receipts with null canonical ID when unmappable, not a fabricated job. Two regressions and full1168passed43.52s proved the correction before the second successful live read. Validation was not weakened to accept the original unknown bad row.

## Synthetic storage and rollback mechanics

Original1000unchanged-row capacity fixture grew3899392→4251648→4620288bytes across3scans. Compact source content/memberships/spans measured4268032→4268032→4276224bytes while preserving1000physical/3000logical observations, duplicates and actual per-observation context. No historical rows deleted. Separate288-run ledger-volume simulation reached21.5MBraw/14.5MBcompressed without source descriptions, showing the original16MiBtransport cap could not fit that projected cadence plus measured initial source data. This is SYNTHETIC capacity, not actual elapsed evidence. Transport caps64MiBcompressed/96MiBcipher and guarded redundant-copy retention address the measured bound while every latest database retains all history.

Real C1 v1 schema fixture migration retains UUID/stable job ID/all duplicate observations/adapter context and a private verified backup. Late migration failure preserves original bytes. Off/on/failed-send/summary ACK tests preserve legacy behavior; normal shadow dry-run is memory-only; missing crypto, missing/corrupt DB/cipher/wrong keys/digests/foreign memberships do not reset state or skip original delivery. Cache save is not trusted until a fresh exact-key restore/digest. Retention fixture plan preserves current/parent/four newest owned copies and all unrelated/fork caches; no live cache deletion executed in development.

## Release and operational gates

Full suite/current-head config/docs/diff/actionlint checks and independent/hosted review/CI must be recorded at the final candidate head. actionlint1.7.12 via its official Go module passed the workflow before the later bounded-retention step; repeat at final head. CATALOGUE_SHADOW_KEY was privately generated with0600recovery permissions and provisioned as a repository secret2026-11-12T04:07:35Z; value never printed/committed/cached. Current main does not consume it before C2 merges. Not deployment evidence.

Actual>=72h, primary-receipt identity/candidate/ACK reconciliation, exact cutover approval and an ordinary post-cutover run remain unsatisfied. Keep BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL, Phase2 PARTIAL. First ordinary shadow run must be independently inspected after authorized merge; no manual dispatch/test send to manufacture proof.

Final local candidate checks after rejection isolation, original-v1 migration fixtures and transport retention: full1170passed38.85s; config validation, diff/docs continuity and actionlint1.7.12passed. The successful original13read above covers unchanged ingestion logic; later transport-only capacity/retention changes are unit/workflow-validated separately. No real72h/cutover/deployment claim. Independent/current-head hosted review/CI remain required.

Hosted H1 corrected head: audit recent-window regression4passed; full1171passed45.02s, config/diff passed. Change is audit retrieval only, no ingestion/alert/source configuration change. Fresh exact-head CI/hosted review required; prior local approval remains pinned to its reviewed code.

# SQLite catalogue and legacy-authority shadow

C1 #35 is merged at1614d804001edbf1d1fe10f33d661b6331c8961a. C2 implements automatic pre-filter capture, compact history, independent filter/candidate/ACK comparisons and encrypted checkpoint custody. C2 is a release candidate until its own review/CI/merge and real ordinary run are observed. Legacy seen/URL JSON remains the only delivery authority; no command sends alerts or automatically switches authority.

## Source facts and identity

Every fetched approved employer row reaches the catalogue before user eligibility/location/freshness and provider-baseline suppression. Invalid normalized rows are rejected with evidence and a partial catalogue scan; failures do not become empty success. Public fields are whitelisted; source descriptions stay in private local SQLite/encrypted cache, never public Git. Job.official_req_id is distinct from provider posting/internal IDs. Missing salary, posted dates, employment and descriptions stay unknown.

Identity version1 uses explicit employer keys, provider/board IDs, actual requisitions where supplied and conservative URLs. Never title/location/legacy-hash-only joins. Decode legacy composite native IDs only for known provider formats; Ashby URL fallbacks stay URL evidence. Different known reqs/IDs at the same URL remain distinct with conflicts. Ambiguous retries reuse an unresolved identity, not a newly minted job every scan. An explicit reviewed catalogue_employer_key can group aliases. The original Microsoft Research source is explicitly grouped with its verified Microsoft parent; both original source entries/labels remain. No other company is guessed or activated.

Queries retain all official sources and original Network Priority attribution; referrals remain unconfirmed/unavailable. Optional feeds are stored separately as LEADS with source/blob/time/permission-configuration claims. A fresh official employer/URL/ID match links a lead; conflicting current requisitions leave it unconfirmed. No lead URL is fetched and no lead sends/ACKs itself. All3production feed candidates remain OFF/rightsblocked.

## Exact logical history without repeated payload growth

Schema2 keeps immutable content records and exact compressed per-run membership, including duplicate rows and their order. Unchanged normalized source content reuses physical rows; logical history/stats still include every run/source/observation. observation_spans records first/last observation and latest normalization context. source_state points to the latest positive content/context separately from lifecycle evidence time. No prior records are pruned/reset.

Exact source posted/updated times and date-only values stay source facts. Legacy unknown-precision adapter timestamps can change with relative-date parsing: preserve each original value in observation context rather than making another identical description snapshot. Query/replay/history restore that value for existing policy behavior while posted_at remains unknown. Observation clocks never become source posting dates. Reclassification creates immutable snapshot+policy results and cannot change source facts/legacy ACKs.

A returned role is listed evidence. Complete configured-scope absence means unknown, not closed; failed/partial scans cannot close roles. Explicit closure requires actual observed URL/evidence. URL/native aliases cannot mask closure or manufacture historical reopen; newer positive evidence still prevails. Different current URLs remain distinct. Config scopes no longer monitored become unknown rather than retaining an unsupported current-open assertion. Completeness is within configured source scope, not proof of every employer opening.

Explicit v1 migration verifies source schema/integrity/UUID, retains a private .v1-backup, adds memberships/spans/latest pointers and preserves every old row. Read-only commands never initialize/reset missing/corrupt/unknown layouts. SQLite is standard-library/public-domain, no hosted bill. Local cap256MiB and bounded exports fail closed without deleting history. See synthetic capacity evidence; it does not prove actual72h operation.

## Query and export

```sh
python main.py catalogue init --db state/jobs.sqlite
python main.py catalogue migrate --db state/jobs.sqlite
python main.py catalogue query --db state/jobs.sqlite --text software --status open --limit 100
python main.py catalogue history --db state/jobs.sqlite --job-id UUID
python main.py catalogue export --db state/jobs.sqlite --format jsonl --limit 1000 --offset 0
python main.py catalogue export --db state/jobs.sqlite --format csv
python main.py catalogue reclassify --db state/jobs.sqlite --policy-version EXPLICIT_NEW_VERSION
```

Query/history/export opens existing stores read-only; literal SQL parameters escape search wildcards and bounds are1..5000. CSV escapes formula prefixes; JSONL retains provenance/unknowns. Reclassification runs existing deterministic eligibility, never sends or authorizes freshness/backfill. Keep exports private and review rights before sharing source text. This is not a private profile/resume service.

## Normal shadow and rollback

CLI polling defaults OFF unless JOBBIE_CATALOGUE_MODE=shadow and an existing verified schema2 DB is selected by JOBBIE_CATALOGUE_DB. --dry-run copies into memory and never writes either production ledger. Shadow exceptions cannot skip original fetches/sends/ACK persistence. Failed individual sends are not ACKs; an exact successful backfill summary receipt is separate from an individual send. Legacy raw candidates, canonical groups, actual notifier ACKs, deduplicated ACK links, cap suppression and mismatches are reported separately.

The workflow restores the exact retained encrypted checkpoint, runs normal polling with shadow, then commits legacy ACK state before optional transport. No catalogue lookup authorizes an alert. Optional crypto is installed separately with failure isolation; legacy CLI/polling does not require cryptography. The source scan retains its14minute cap; overall35minute backstop includes bounded optional transport. Cron remains best effort.

Set JOBBIE_CATALOGUE_MODE=off (or remove the optional workflow stages) for rollback; original seen/URL history stays authoritative and both ledgers are retained. No reset, seeding, forced backfill or test send. Private decrypt/SQLite roundtrip and off/on sender/failed-ACK tests establish rollback mechanics, not an actual production authority cutover.

## Encrypted checkpoint protocol

Only sealed.bin is cached, using authenticated Fernet encryption; keys never enter cache/public Git. Exact cache-key hit, digest, epoch, UUID, schema, parent lineage and bounds are required. Missing/wrong/evicted/corrupt custody blocks shadow; never silently reinitialize when a checkpoint exists. Initial bootstrap is allowed only when no checkpoint/DB/cipher exists and the explicit bootstrap gate is set.

Ciphertext is bounded96MiB, compressed payload64MiB and raw DB256MiB. The runtime usage guard stops below8GiB against the documented included10GiB cache allowance; no paid settings/overage. Custom cache-limit read was402and remains unverified, not bypassed. Only included-budget usage reads are used. A save action may report success without storing: rename the local sealed file, perform a fresh exact-key cache restore and verify digest/legacy file hash before publishing the new public reference. A second small state commit publishes only checkpoint/health metadata, never source text.

Interrupted runs can be retained explicitly as incomplete/degraded snapshots, never72h success. The current workflow run ID must match captured data. Cache/transport failures keep the prior checkpoint and preserve already committed legacy ACKs. First bootstrap/missing secrets/dependencies and health failures are visible in state/catalogue_shadow_health.json/Actions summary. Local files and keys are private; source/ledger metadata only is public.

Operational CLI: python main.py catalogue-shadow plan|restore|seal|probe-prepare|publish|rollback|audit. These are explicit local/GitHub workflow tools, not a dot API/trigger. Restore/seal/publish need JOBBIE_CATALOGUE_KEY. No operation dispatches a scan or sends Discord. prune-transport removes only redundant owned encrypted cache copies after publication; it never removes canonical records.

## Live evidence and cutover gate

Audit reads the fixed repository's primary GitHub scheduled-run/job receipts and exact authenticated checkpoint. It verifies head/event/main/attempt/times/healthy custody/parity and measures a contiguous healthy suffix for the same code/config; old failures remain visible and a later genuine72h window can qualify. Fixtures/local clocks, shorter windows, incomplete/failed/manual reruns cannot qualify. A changed code/config requires new evidence. Owner approval must name the exact UUID/checkpoint/config/last run via a real owner GitHub comment; no approval is generated by the agent.

Production cutover still needs exact owner approval, parity/identity/ACK reconciliation and rollback proof, followed by an ordinary scheduled run. Audit is read-only and never activates authority. Currently no cutover approval or real72h catalogue window exists. Keep BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL, complete remaining implementation and observe ordinary schedules without forcing sends.

Legacy projection evidence is also losslessly compressed and content-addressed; a source comparison records its exact ledger hash plus bounded canonical mismatch ID samples. This prevents unchanged2256-row baseline ledgers from dominating storage. Projections retain first/last seen, ACK/suppression facts with provenance, without pretending old full descriptions were observed before the catalogue existed.


Transport retention keeps current, parent and at least four newest history-complete encrypted copies. It runs only after custody metadata commits, re-reads main's published checkpoint, and scopes cache IDs to this catalogue UUID/main branch. Every retained snapshot includes all append-only job/observation/ledger history. Old redundant cache archives, unlike canonical records, may expire; unrelated dependency/browser/fork caches are untouched. This bounds cache usage while preserving rollback copies. The listing/delete API needs Actions write permission; failure remains isolated and budget guard prevents paid growth. A synthetic288-run ledger-volume check exceeded the original16MiB compressed allowance once combined with actual initial source data; the64/96MiB transport caps and duplicate-copy retention address that capacity defect without pruning history. Not real72h evidence.

Primary audit retrieval uses a recent96hevidence window, independent of how many years of history the database retains. The query's10-page bound cannot be exhausted merely by old retained runs at the configured15minute cadence. Actual recent missing/degraded runs still break the qualifying suffix; old fixture history never becomes elapsed production proof.

# SQLite public-source catalogue

P2-C1 is a local storage/query capability. Automatic pre-filter shadow capture, persistent scheduled-run comparison, >=72h evidence and approved cutover follow in P2-C2. Legacy seen/URL state and alert/ACK authority remain unchanged; a SQLite row never authorizes a send.

## Store and identity

Python standard-library SQLite has no hosted service charge; SQLite is public domain ([primary license](https://www.sqlite.org/copyright.html), checked2026-11-12). No paid infrastructure/account is introduced. Source text stays in an ignored private local SQLite file, never committed as public repository data. The operational encrypted checkpoint path is a later scoped release. Current local cap256MiB fails closed without pruning/resetting history.

Create only with an explicit local path. Read/query commands open an existing database read-only and do not create a missing/corrupt database. Schema/version/integrity/foreign keys and catalogue UUID are checked; unknown versions require a reviewed migration, not a reset. Transactions retain all validated rows in a scan or roll back together on a late storage failure. Rejected normalized rows and identity conflicts retain bounded error evidence and make the scan partial.

Every adapter row is normalized before any user eligibility/location/freshness filtering by the future shadow integration. Current storage API accepts whole normalized scans; it never calls a network provider. Payloads whitelist public job facts, excluding policy verdicts/private candidate fields. Content-addressed snapshots exclude observation clocks; repeated observations retain source/run/time without duplicating unchanged descriptions. All conflicting source-row versions remain auditable.

Identity version1 uses explicit employer keys, native provider/board IDs, actual employer requisition IDs where supplied, and conservative canonical URLs. No title/location-only join. Legacy composite IDs are decoded only when their exact company/provider prefix matches; legacy title-derived hashes remain opaque and cannot establish a provider identity. Different known requisitions or incompatible provider IDs at the same URL remain separate with IDENTITY_CONFLICT. Ambiguous existing identities are retained for reconciliation, never silently collapsed. Cross-company employer aliases need an explicit reviewed catalogue_employer_key, not a name guess. Source ID history and Greenhouse internal job IDs remain distinct from employer requisitions.

Original Network Priority metadata comes from approved company config, not adapter defaults or a feed claim. Query aggregates original-source attribution without promoting referrals; unconfirmed/unavailable stay explicit. All per-source observations/provenance remain available even when an official requisition or exact URL links records across sources.

## Dates, lifecycle and classifications

Source exact posted/updated times, source calendar dates, legacy adapter timestamp values and first/last observed are separate. Greenhouse first_published and Ashby last_published timestamps retain their stated meanings; Oracle date-only remains date-only. Older adapters can normalize relative/calendar dates to midnight: adapter_posted_at is retained with unknown precision, never promoted to a fabricated exact posting timestamp. Missing facts stay null. Observations do not become posting dates.

A returned source row is positive listed evidence, even when a scan is partial. A complete scan's absence means unknown/not observed, not proven closed. Failed/partial scans cannot close or erase roles. Explicit source closure requires an observed identity plus public URL and evidence; a second open source keeps the canonical role open. Later positive evidence after closed records a reopen event. Evidence is append-only, including a closure from one source when another source remains open. Out-of-order scans retain history without regressing newer source status.

Classification results are separate immutable snapshot+policy records. Reclassification cannot rewrite source snapshots, old verdicts or legacy seen/ACK state. A changed result under the same policy version fails the entire transaction: use a new explicit version. The CLI runs existing deterministic eligibility only, not source activation, freshness/delivery authorization or private candidate matching.

## Query/export interface

```sh
python main.py catalogue init --db state/jobs.sqlite
python main.py catalogue stats --db state/jobs.sqlite
python main.py catalogue query --db state/jobs.sqlite --text software --status open --limit 100
python main.py catalogue history --db state/jobs.sqlite --job-id UUID
python main.py catalogue export --db state/jobs.sqlite --format jsonl --limit 1000 --offset 0
python main.py catalogue export --db state/jobs.sqlite --format csv
python main.py catalogue reclassify --db state/jobs.sqlite --policy-version EXPLICIT_NEW_VERSION
```

No command polls sources, constructs a sender or edits legacy JSON. Query is parameterized, literal text (percent/underscore escaped), deterministic and bounded1..5000rows with offset. History is bounded. JSONL includes source facts/provenance/classifications and unknowns; CSV is a compact projection and escapes spreadsheet formula prefixes. Exports can contain employer source descriptions, so retain them privately and review data rights before sharing. Do not commit them. There is no Phase3 private profile/resume service yet.

Optional feed lead/history storage is separate from official jobs. Lead observations do not create official job identities. A confirmation must link one actual current open official source observation with matching approved employer/alias, canonical URL and compatible reported ID; title resemblance is insufficient. Closed/stale records cannot confirm a new lead. Confirmation records the official observation time; changed lead facts clear the link until rechecked. All production feed candidates remain OFF/rightsblocked.

## Rollout, rollback and remaining gates

C1 does not change production config or normal polling. Revert the CLI/helpers/models addition to roll back; ignored local databases remain retained and original state/alerts continue. Do not delete either ledger. C2 must add crash-safe pre-filter dual-write, encrypted bounded persistent custody, actual-run parity/identity/ACK reports and rollback proof. Only then can a >=72h ordinary scheduled shadow window start. Synthetic tests/local scans do not satisfy it. Canonical cutover requires exact owner approval and parity/rollback evidence, followed by an ordinary scheduled run. Until then BLOCKED_72H_EVIDENCE/BLOCKED_APPROVAL; Phase2 remains PARTIAL.

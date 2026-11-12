# Optional public feeds remain unverified leads

P2-B provides a reusable bounded JSON lead reader, provenance and health reports, source dedup and confirmation against already fetched approved employer jobs. It never discovers/logs into employers, follows lead URLs, enables a company, sends or acknowledges a lead. Current candidate feeds in public-feeds.yaml are OFF with BLOCKED_SOURCE_RIGHTS and BLOCKED_APPROVAL; no third-party dataset has been ingested or claimed as coverage.

## Rights and source evaluation

Pinned current heads, timestamps, code-license metadata and policy-document hashes are in [the rights record](evidence/P2-B-SOURCE-RIGHTS.json). Code licenses and job-data permission are separate.

- New-Grad-Jobs has an MIT code license, but its own copyright policy excludes employer/platform job data and explains that attribution is not permission. Its repository describes roughly30-minute updates; that is a publisher claim, not measured Jobbie coverage or an employer posting timestamp. Data ingestion remains blocked.
- Simplify's evaluated repository has no confirmed reusable dataset license. Repository updates/README dates are not employer posted dates. No dataset ingestion permission is established.
- Jobright's evaluated public list has no confirmed reusable dataset license. Aggregator URLs are leads, not employer requisitions, and no authenticated site/proprietary implementation is accessed.

The checked primary policies are linked at immutable commits. No upstream scraper code or job-description dataset is copied. A future source needs documented job-data access/reuse permission, terms/rate review and exact owner approval, not merely a public GitHub page or MIT badge. Unknown/prohibited rights keep it OFF. CLI network permission does not override those gates.

## Inspect without activation

```sh
python main.py feed-check --manifest public-feeds.yaml
python main.py feed-check --manifest public-feeds.yaml --allow-network
```

Both commands produce no lead reads for the current OFF/unapproved manifest. Output counts remain unknown, not fabricated zero coverage. `--allow-network` permits a read only when a source is enabled, data permission says permitted and exact owner approval matches its endpoint.

The generic reader accepts flat JSON arrays or a literal rows_key, with an optional literal field_map. Fields are id/company/title/location/url/posted_at/official_req_id. Mapping never evaluates expressions. Supported network endpoints are fixed public raw.githubusercontent.com JSON files; no credentials, arbitrary/custom hosts, query secrets or redirected requests. A new endpoint/provider needs a reviewed extension, not a guessed API or scrape bypass.

Source configuration includes a stable id, enabled boolean, endpoint, format=json, rows_key(defaultjobs or null for a root array), refresh_seconds(1hour..7days), rights(status/url/basis/checked_at) and owner_approval(exact endpoint/reference/approved_at). Field maps are flat key names only. Current unverified candidates deliberately have no guessed endpoint/profile. No source is approved by an example or fixture.

## Provenance and health

Every lead retains source/record ID, source URL, retrieval time and raw-response SHA256. Feed-updated time and feed-reported posted dates remain distinct from employer time. Date-only/naive/missing values never become fabricated UTC posting timestamps; employer_posted_at remains unknown until an official source supplies it.

Reads are bounded to2MiB/5000records and bounded text/URLs, with existing timeout/retry policy, source refresh intervals and isolated failures. Explicit empty responses differ from HTTP/schema/size/identity conflicts. Duplicate identical source IDs collapse once; conflicting records with the same ID fail the feed instead of silently replacing facts. Disabled/missing rights/approval makes no network call. Manual feed-check is read-only and does not persist cadence metadata; configured polling retains optional health in memory/state under its normal save policy.

The normal source poller only consults a manifest when defaults.public_feeds_manifest is explicitly configured; production does not configure it. Feed errors, malformed manifests or optional health failures are reports and do not skip original employer fetches/alerts. Existing state containers and delivery authority are retained. No feed failure can manufacture an empty employer response or successful ACK.

## Confirm before using an employer job

Leads remain `confirmation_status=lead`. Confirmation reuses normalized jobs fetched from an enabled approved employer source. It requires a matching company/verified alias and exact canonical posting URL, a single official identity and no conflicting reported requisition ID. A title/location resemblance or aggregator redirect is insufficient. The module does not fetch a lead URL or add a company to resolve it.

Known posting/application variants are normalized only for supported ATS patterns. Query job IDs, path case, distinct requisition values and repeated-key semantics survive normalization. Tracking parameters are removable, but generic ref/source query values remain meaningful. Distinct jobs are never merged by title alone. Feed confirmation is a link to an actual source job, not candidate eligibility, a hiring outcome or referral proof; the original employer job still follows the existing filter/dedup/rate/ACK path.

The poller reports lead and unique confirmation counts when explicitly configured. It does not create extra alerts from leads. New employers still require the owner-intake and separate exact source activation workflow; disabled historical sources are not reactivated through feeds.

## Rollback and remaining limits

Revert the optional hook/CLI/helper and remove any explicit manifest configuration. Original company configuration, seen/URL ACK authority and prior alerts remain unchanged. No state reset, forced backfill, source activation, paid service, protected scrape or application is needed.

Actual feed coverage, employer-confirmation percentage and upstream freshness are NOT_MEASURED because no source has approved data rights/activation. Synthetic fixture tests prove capability, not live feed coverage. The catalogue will retain lead/source history separately from verified employer listings; it does not promote a feed record into an official opening.

Confirmation's optional `official_req_id` claim is compared to the supported adapter's published posting identifier (Greenhouse/Ashby `source_job_id`, Oracle requisition ID). Greenhouse internal employer job IDs and posting IDs are distinct; this comparison confirms the exact source posting, not an independently established employer requisition number. Contradictory normalized posting dates/instants on the same feed record ID fail the feed in either row order; timezone-equivalent instants are duplicates.

Normal polling builds a canonical URL/company index once per employer fetch when optional leads exist. Confirmation work scales with postings plus leads, with no repeated full-board scan per lead; ambiguity and conflicting source-ID checks are retained. OFF feeds add no index work.

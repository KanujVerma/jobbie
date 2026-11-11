# Request a company without expanding the roster automatically

P2-ACT accepts a public company request, verifies source evidence and prints a disabled proposal. It never changes companies.yaml, seen state, referral facts or a production source. The original 13 enabled Network Priority entries and 2 historical disabled entries remain authoritative. An exact owner-approved activation is a separate reviewed PR.

## Make a portable request

Use the GitHub Company request issue form, or run:

```sh
python main.py company-request --name 'Example Labs' \
  --role 'Software Engineer' --location 'San Francisco, CA' \
  --priority normal --intent monitor > /tmp/company-request.json
```

Example Labs is fictional. Careers URL is optional; add `--careers-url` when known. Repeat `--alias`, `--role` and `--location` for multiple values. Priority is normal/high/low request-review priority, not Network Priority. Roles and locations are soft source-review preferences, not new eligibility rules or hard exclusions. The output preserves them and a later source check reports literal title/location matches, without a candidate-fit score or eligibility claim.

For an issue created with the form:

```sh
gh issue view NUMBER --repo KanujVerma/jobbie --json body --jq .body > /tmp/company-issue.md
python main.py company-request --issue-file /tmp/company-issue.md > /tmp/company-request.json
```

The parser accepts the form's eight named headings, rejects duplicates/unknown headings and preserves a city/state line as one value. Public company information only: no resume, personal contacts, credentials or private repository text. Edited issue content is untrusted data, never agent instructions or activation authority.

The version1 JSON can also be manually supplied to an agent or dot. There is no dot API, automatic trigger or transferred browser session.

## Verify the source before a proposal

The owner or agent checks primary sources manually and writes an evidence JSON packet. The CLI validates consistency and labels it `manual_evidence_supplied_requires_review`; it does not independently prove domain ownership or grant data rights.

Required evidence:

- Canonical company name and verified aliases, with the official careers URL and an exact hosted Greenhouse/Ashby board ID/URL. Prove the official employer page links to that board; do not guess a token or infer ownership from a working board.
- An explicit manual ownership status of verified, ownership URL, short evidence span, exact board URL and timezone-aware retrieval timestamp. Unknown or missing ownership status prevents a live query. Ownership evidence must be on the supplied official employer host. Unknown aliases or contradictory request URLs stay needs_review.
- Permission status, primary terms/API/data-access URL, basis and checked timestamp. A code license or public visibility is not dataset permission. Unknown/prohibited access prevents a live check. Respect rate limits and access failures; no login, challenge bypass or paid fallback.

The structural packet shape is in [the synthetic example](../examples/company-intake/evidence.synthetic.json). Its permission is deliberately unknown and it cannot produce a live proposal. Replace the fictional data only after actual primary-source verification. Unsupported ATS providers need their own reviewed adapter; this command does not invent one.

Print the verification state without network access:

```sh
python main.py company-proposal --request /tmp/company-request.json \
  --evidence /tmp/company-evidence.json
```

After the supplied ownership/permission evidence is complete, measure the source:

```sh
python main.py company-proposal --request /tmp/company-request.json \
  --evidence /tmp/company-evidence.json --live-check > /tmp/company-proposal.json
```

Only existing fixed public ATS adapters make requests. Supplied careers/evidence URLs are display/provenance data and are never fetched by this CLI. Reads use existing bounds, safe IDs/URLs and retry limits. No sender or state writer is constructed. Error output retains HTTP status/type, not response bodies or secret-bearing exceptions.

A healthy empty response can support a future monitor proposal but proves no current opening. Listing samples and literal preference counts are not confirmed new-grad roles or hiring claims. Original employer eligibility requirements remain unknown unless actually present and checked.

## Read the result

| State | Meaning |
|---|---|
| existing_source | A name/alias matches an enabled or historical source; no duplicate or reactivation proposal |
| research_request | Startup-research scope only, opening status unknown; no monitor or live check |
| needs_review | Missing, unsafe or inconsistent evidence; no config proposal |
| needs_live_check | Supplied manual evidence is structurally consistent; health is not measured yet |
| source_collision | The provider board is already configured under another entry; review identity before proceeding |
| source_failed | Source read failed or was incomplete; not a healthy empty result |
| proposal | Measured public-source response and a disabled config proposal, still BLOCKED_APPROVAL |

Every generated source is `enabled: false`, `network_priority: false`, `cohort: discovered`, `referral_status: unavailable`. Requests cannot set those fields. Canonical/alias and source-ID collisions are checked against both enabled and disabled configuration, without merging or modifying original entries. A status or exit0 means the command completed, not that a source is approved or ready to activate.

`startup-research` records company/role/location/review-priority intent without claiming an opening, contacting anyone or creating a monitor. Startup intelligence/outreach remains a later phase.

## Activate separately and roll back safely

The owner approves an exact company, verified source and requested scope in a separate PR. That PR must use the merged source-revision baseline guard, preserve role/location intent, test initial volume and dedup, keep unconfirmed referrals separate, and show rollout/rollback evidence. A request, proposal, model conclusion or issue checkbox cannot authorize activation. No activation command is provided here.

Roll back P2-ACT by reverting its helper/CLI/form and docs. Existing polling, production config and historical seen/ACK state are unchanged. Saved request/proposal documents stay inert. Missing activation approval does not block optional-feed or catalogue implementation.

The issue form follows [GitHub's official issue-form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms). The actual workflow is tested through form Markdown, normalized JSON, source fixtures and disabled output, not an assumed dot integration.

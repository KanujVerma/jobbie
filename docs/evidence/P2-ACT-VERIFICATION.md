# P2-ACT owner intake verification (candidate)

Base f3deaae743dd5e0c889cf5a2dfda5c42281452ba, isolated feat/p2-owner-intake. This is a local candidate, not a merged/production-enabled release. No new employer is requested or approved by its verification probes.

## Implemented contract and regressions

Version1 portable requests and GitHub-form Markdown parse into the same schema. Optional careers URL, role/location lists, priority and monitor/startup-research intent survive normalization and stable request hashing. Unsupported authority fields, unsafe URLs, control characters, duplicate/unknown form headings and oversized documents are rejected. Canonical names/verified aliases and provider-board collisions are checked against enabled and historical sources. Verified aliases persist in disabled proposals for later collision checks.

Manual primary-source ownership and permission evidence are explicitly typed. Ownership must be marked verified by the supplying owner/agent and permission permitted before any live read. The result still says manual_evidence_supplied_requires_review; the CLI does not prove ownership, legal rights or owner approval. Unknown/prohibited/mismatched evidence produces no config or network query. Only fixed Greenhouse/Ashby public adapters fetch listings; supplied employer/evidence URLs are never fetched by the CLI.

The request/issue/CLI round trips, both actual public parsers against synthetic fixtures, 403/404/429/empty/incomplete outcomes, nested private-material rejection, unchanged production hashes and no sender construction are tested. Startup research never creates a monitor or assumes an opening. Role/location screening is literal source-review context, not profile matching or eligibility.

Initial absent-module tests failed; CLI/private-evidence cases failed before their fixes; wrapped HTTP diagnostics, issue-form schema, alias persistence and unknown-ownership gate each failed before correction. Final focused intake suite52passed. Full suite **928 passed in31.74s**, Python3.15.2; config, compileall and diff-check passed. Baseline was876passed before this feature.

## Live read-only proof, limited to verification

The existing provider-owned P2-A manifest returned19 Greenhouse and75 Ashby normalized listings with unchanged config/seen hashes, GET-only, no credentials/POST/webhook. Original metadata receipt: [public read](P2-ACT-public-read-2026-11-11.json). Its source_sha is the unchanged shared reader/library base during authoring, not a claim that the entire uncommitted intake feature was at that SHA. Unit/CLI tests cover the new paths and exact-head CI remains required.

A complete current CLI probe used only Greenhouse's already-approved provider smoke scope. [Official careers HTML](https://www.greenhouse.com/careers/opportunities) embeds the Greenhouse board script with for=greenhouse; [official Job Board API](https://developers.greenhouse.io/job-board.html) documents public unauthenticated GETs. Public HTML SHA256: ab86e8b5eb0a0799572a4de0ea6a2f06b2aa4af4ae126c208fe53cccf4727e33. This establishes provider identity for the probe, not a new owner monitoring request or production/data-redistribution approval. The probe generated an OFF proposal, kept BLOCKED_APPROVAL, measured19 rows and preserved state/config. It made no send.

```json
{
  "scope": "VERIFICATION_ONLY_NOT_OWNER_REQUESTED_OR_PRODUCTION_APPROVED",
  "command": [
    "/Users/kanuj/Documents/projects/jobbie/.venv/bin/python",
    "main.py",
    "company-proposal",
    "--request",
    "/tmp/jobbie-p2-act-greenhouse-request.json",
    "--evidence",
    "/tmp/jobbie-p2-act-greenhouse-evidence.json",
    "--live-check"
  ],
  "exit_code": 0,
  "before": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "after": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "unchanged": true,
  "discord_sent": false,
  "output": {
    "schema_version": 1,
    "request": {
      "schema_version": 1,
      "name": "Greenhouse",
      "careers_url": "https://www.greenhouse.com/careers/opportunities",
      "aliases": [],
      "roles": [],
      "locations": [],
      "priority": "normal",
      "intent": "monitor"
    },
    "request_digest": "07fc556dc2a47f94289464f35ccfc42691cb3ad26d9385d84c83b5b070e16eb3",
    "state": "proposal",
    "approval_status": "BLOCKED_APPROVAL",
    "config_proposal": {
      "name": "Greenhouse",
      "aliases": [],
      "adapter": "greenhouse",
      "enabled": false,
      "network_priority": false,
      "cohort": "discovered",
      "referral_status": "unavailable",
      "config": {
        "board_token": "greenhouse",
        "board_url": "https://job-boards.greenhouse.io/greenhouse",
        "employer_careers_url": "https://www.greenhouse.com/careers/opportunities"
      }
    },
    "ownership_check": "manual_evidence_supplied_requires_review",
    "health": {
      "status": "nonempty",
      "returned_count": 19,
      "checked_at": "2026-11-11T22:19:08.272232+00:00",
      "scope": "configured public board only"
    },
    "gates": [
      "BLOCKED_APPROVAL",
      "ACTIVATION_REQUIRES_REVIEWED_SCOPE_BASELINE_AND_ROLLBACK"
    ],
    "source_evidence": {
      "schema_version": 1,
      "company_name": "Greenhouse",
      "verified_aliases": [],
      "provider": "greenhouse",
      "board_id": "greenhouse",
      "board_url": "https://job-boards.greenhouse.io/greenhouse",
      "employer_careers_url": "https://www.greenhouse.com/careers/opportunities",
      "ownership": {
        "status": "verified",
        "url": "https://www.greenhouse.com/careers/opportunities",
        "span": "Official careers HTML embeds boards.greenhouse.io/embed/job_board/js?for=greenhouse.",
        "board_url": "https://job-boards.greenhouse.io/greenhouse",
        "retrieved_at": "2026-11-11T22:19:07.824175+00:00"
      },
      "permission": {
        "status": "permitted",
        "basis": "Documented unauthenticated public GETs and the existing provider-owned P2-A read-only smoke scope; production monitoring/redistribution is not authorized by this probe.",
        "url": "https://developers.greenhouse.io/job-board.html",
        "checked_at": "2026-11-11T22:19:07.824175+00:00"
      }
    },
    "preference_screen": {
      "method": "literal title/location preference check, not eligibility or candidate fit",
      "literal_match_count": 19,
      "unknown_location_count": 0,
      "samples": [
        {
          "source_job_id": "8126988",
          "title": "Commercial Counsel",
          "location": "Eastern Timezone",
          "url": "https://job-boards.greenhouse.io/greenhouse/jobs/8126988?gh_jid=8126988"
        },
        {
          "source_job_id": "8279752",
          "title": "Enterprise Account Executive",
          "location": "London, United Kingdom",
          "url": "https://job-boards.greenhouse.io/greenhouse/jobs/8279752?gh_jid=8279752"
        },
        {
          "source_job_id": "8234044",
          "title": "Enterprise Sales Development Representative",
          "location": "Anywhere in the United States",
          "url": "https://job-boards.greenhouse.io/greenhouse/jobs/8234044?gh_jid=8234044"
        }
      ]
    }
  }
}
```

An earlier authoring-only Ashby probe supplied incomplete fresh ownership evidence; it is not used as final ownership/proposal proof. The final contract blocks unknown or missing ownership status. Ashby parser/network connectivity is separately covered by fixtures and the read-only shared manifest receipt.

## No-mutation polling regression

Normal no-webhook Amazon dry-run: exit0, fetched510, matched3/review183/excluded324, candidates0, sent0. Config/seen hashes are identical; current persisted ordinary ACKs suppress prior deliveries.

```json
{
  "command": [
    "/Users/kanuj/Documents/projects/jobbie/.venv/bin/python",
    "main.py",
    "run",
    "--company",
    "Amazon",
    "--dry-run",
    "--verbose"
  ],
  "exit_code": 0,
  "before": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "after": {
    "companies.yaml": "077cf59d2e2a5a6eb9889ad79b54b96d0e97183f28d33ac84ddb39bea8c971d4",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "unchanged": true,
  "webhook_environment": "empty",
  "discord_sent": false
}
```

## Rollback and remaining gates

No production config, state, policy, adapter, scheduler or sender path changes. Exactly13 original enabled/unconfirmed sources and2historical disabled remain. Every generated source is disabled/discovered/networkfalse/referralunavailable; startup research has no monitor config. Rollback reverts helper/CLI/form and retains all existing state. Activation requires an exact separately reviewed owner grant and source baseline/volume/scope/rollback proof. No activation command or dot API/trigger exists.

Independent review, exact-head CI/hosted review and merge remain pending. Hosted issue-form rendering is not claimed before merge; its official schema and generated Markdown parser round trip are tested. Missing activation approval does not block optional feeds/catalogue. Full Phase2 remains partial.

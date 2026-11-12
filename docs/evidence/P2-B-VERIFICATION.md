# P2-B disabled capability verification

All current candidate feeds remain OFF/BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL. No third-party feed dataset was fetched, no new employer enabled, no sender/ACK path added. Generic JSON fixtures exercise the gated infrastructure and exact confirmation against already fetched approved employer jobs.

Focused tests38passed, including100generated examples each for URL idempotence and meaningful requisition-query preservation. Cases cover off/rights/approval/endpoint gates, bounded wire/shape, 403/404/429/redirect/error isolation, source IDs/collisions, timestamps/unknowns, refresh health, literal field maps and official company/URL/req confirmation. Known supported ATS URL variants normalize without collapsing distinct query IDs/path case. Incomplete optional metadata does not reset health or block original delivery. Fixture cases are not live feed coverage.

At pre-Oracle base9317c73, full990passed37.30s; current parent integration results are recorded separately after checking. Config/compileall/diff passed. Hypothesis6.170.15 is a dev-only MPL-2.0 dependency, no code vendoring/modification or runtime service.

Permitted live checks inspect upstream repository/legal metadata only; current policy hashes match previously read primary files. Pinned evidence is in P2-B-SOURCE-RIGHTS.json. Data ingestion/confirmation coverage and update freshness remain NOT_MEASURED. New-Grad-Jobs excludes job data from MIT; other candidates have no confirmed reusable data license.

No-mutation CLI/normal-poll checks both exited0: feed-check --allow-network retained all3OFF/no leads; normal Plaid dry-run fetched143/matched0/review8/excluded135/candidates0/alerted0. No webhook environment or sender traffic, no state/config changes:

```json
{
  "checks": [
    {
      "command": [
        "/Users/kanuj/Documents/projects/jobbie/.venv/bin/python",
        "main.py",
        "feed-check",
        "--manifest",
        "public-feeds.yaml",
        "--allow-network"
      ],
      "exit_code": 0
    },
    {
      "command": [
        "/Users/kanuj/Documents/projects/jobbie/.venv/bin/python",
        "main.py",
        "run",
        "--company",
        "Plaid",
        "--dry-run",
        "--verbose"
      ],
      "exit_code": 0
    }
  ],
  "before": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "after": {
    "companies.yaml": "8a44adcc21b5be919bd6d875d3a16ae9de9abdd8222a939cfe7fbc18e1f7d943",
    "state/seen_jobs.json": "12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe"
  },
  "unchanged": true,
  "discord_sent": false,
  "third_party_feeds_fetched": false
}
```

Production does not configure defaults.public_feeds_manifest; the new hook is OFF. Any future exact owner-approved, permitted source is still a lead until its official enabled-employer record matches. The hook reuses official reads, never follows a lead URL or adds an employer. Optional errors remain reports while original polling/ACK works. Existing legacy state/dedup/rate/backfill remains authoritative.

Rollback removes the optional hook/CLI/manifest and keeps original state. No data migration/reset or cutover. Current-head independent/hosted review, CI and merge remain gates. This ships tested disabled capability, not fabricated feed coverage or completion of full Phase2.

Integrated onto merged Oracle4eb83f454e2671e8e06d7cb10f4b079ab98fcf90: full1033tests passed35.59s using PYTHONDONTWRITEBYTECODE=1 /Users/kanuj/Documents/projects/jobbie/.venv/bin/python -m pytest -p no:cacheprovider -q. Postmerge main Tests43125554558 passed. Current config validation, OFF feed-check --allow-network and Plaid no-webhook dry-run all exited0; config SHA2568afbe552edb59566e6bedf604510337bf5d1e3a6cc02c02f1b8161dd0ece12f0 and seen-state12bed813017dbd685b085e9b4fceceb79dadd158ef77df7be6071028343cbbbe were byte-identical before/after. No ordinary post-R2/R3 schedule qualifies at this checkpoint. Production baselines PENDING_LIVE; no forced send or state seed.

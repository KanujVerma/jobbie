# P2-ACT executable PR — first additional source-verified employers

**Status:** PLANNED. [Tracking issue #26](https://github.com/KanujVerma/jobbie/issues/26). Start only after [P2-UX1](PHASE-2-UX.md) has merged and passed regression gates. P2-A existing Greenhouse/Ashby adapters have already merged, but NO new employer was enabled in `companies.yaml`.

## Why a separate PR?
Alert presentation can be deployed and reverted without touching scraping or historical dedup. Activating employers changes production coverage, fresh-state and potential Discord volume. Do not conflate test-board connectivity with a relevant new-grad opportunity.

## Step-by-step implementation
1. Verify available new-grad openings and actual **official employer** public Greenhouse/Ashby board URLs for a SHORTLIST of 3–5 companies in target regions (SF Bay prioritized; other CA, NYC, Chicago, TX, FL). Verify board token/name from employer careers domain. Source URLs and retrieval times required. Start with fewer if only fewer can be verified.
2. A company without an active eligible role may still be a legitimate future monitor if board and rate/permission are verified; label status honestly. Do not invent a current job or hiring demand.
3. Before modifying production config, present the explicit shortlist and source evidence to the owner for approval (the owner has not authorized specific new employers by name in this plan). If no approval, publish a source-verified activation proposal and mark `BLOCKED_APPROVAL`, not active.
4. Once approved, add only approved boards to `companies.yaml` with `enabled:true`, `network_priority:false`, `cohort:discovered` and `referral_status:unavailable`, retaining the 13 original source entries, 2 historical disabled, and exact config semantics.
5. Run controlled read-only dry-run for ONLY new boards, verify source returned data, no state writes, no Discord sends; classify actual title, employment, locations, salary and freshness with no fabricated metadata. Record false positive/negative samples.
6. Add source-specific adapter/config tests, before/after source counts, source health detection for 404 vs zero, dedup where employer appears in old source, rate/batch caps and a safe first-run summary or suppression if existing state would flood.
7. Activate through reviewed PR with a flag and rollback, then observe one authorized real scheduled run with recorded counts and no duplicate storm. If source permission uncertain, do not activate.
8. Update STATUS/HANDOFF/RELEASE_LOG, tests/review, sourced evidence and limitations.

## Scope boundaries
Do not implement P2B feeds, P2C canonical catalogue, private profile, AI, resume review or auto-apply in this activation PR. Do not mark future discovered companies as referral priorities without explicit owner override. Preserve public state and stored job IDs; never delete/reset to force new alerts.

## Success
Three to five source-verified monitored employers where available and approved, transparently `DISCOVERED`, reliable public ATS links and independently measured alerts/digest; original 13 unchanged. If evidence or consent missing, safe blocker is an acceptable engineering outcome, not silently fabricated activation.

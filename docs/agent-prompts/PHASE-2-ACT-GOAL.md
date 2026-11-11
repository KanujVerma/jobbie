# Future /goal: P2-ACT (only AFTER P2-UX1 is released)

/goal

Repository: KanujVerma/jobbie
Execute ONLY P2-ACT, controlled new employer board activation. Require P2-UX1 merged before coding. Read AGENTS.md, docs/HANDOFF.md, docs/STATUS.md, docs/DECISIONS.md, docs/phases/PHASE-2-ACT.md, docs/PHASES.md, docs/CONTRACTS.md, docs/SECURITY.md, docs/OPERATIONS.md and actual companies.yaml, adapters/Greenhouse/Ashby tests/source docs.

FIRST research 3–5 actual employers in preferred US locations with official public Greenhouse/Ashby boards. Cite official employer board domain, verified board ID, actual data rights/access, time checked and a small sample showing whether new-grad/full-time eligible openings exist. Do not infer current hiring from a board existing.

BEFORE setting enabled:true, present EXACT shortlist and source links to owner and require explicit approval. If approval unavailable, leave boards disabled in a reviewable PR and mark BLOCKED_APPROVAL, not activated. Keep original 13 source stars/referral_status and 2 disabled historical entries unchanged. New employers are DISCOVERED, no implied referral.

After owner approval, enable ONLY exact approved boards with safe default config. Run targeted read-only dry-run, full pytest + config validation, production state invariance, dedup, source 403/404/429 handling, and a controlled first-run alert plan with no spam. Update STATUS/HANDOFF/RELEASE_LOG; request independent review, merge if gates pass, and observe actual scheduled run. Never reset/force backfill or send unapproved test webhook.

Do not implement P2-B/C, AI, private resume, application executor, dot integration or automatic submissions. Final report: PR, verified boards/links/approval, test/run/review evidence, enabled vs disabled, rollback, blockers.

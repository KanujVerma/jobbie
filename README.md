# jobbie

**Personal, Discord-first new-grad job search assistant.** Canonical repository: [KanujVerma/jobbie](https://github.com/KanujVerma/jobbie).

> **Current truth:** [docs/STATUS.md](docs/STATUS.md) · **Agent resume:** [docs/HANDOFF.md](docs/HANDOFF.md) · **Full spec:** [docs/PRODUCT.md](docs/PRODUCT.md) · **Roadmap:** [docs/PHASES.md](docs/PHASES.md). This README describes the CURRENT Python bot. Later phases are planned, not already working.

## Working functionality
- Python 3.12 job monitors for 15 configured employer sources, 13 enabled and 2 disabled; scheduled by best-effort GitHub Actions plus manual dispatch.
- Tri-state role filter (`eligible`, `needs_review`, `excluded`) focused on full-time US entry/new-grad roles; internships/co-ops excluded from normal alerts. Degree/experience interpretation remains rule-based, not a guarantee of suitability.
- Original-company `NETWORK PRIORITY` star displayed on eligible jobs. A network connection is NOT a confirmed referral; every original source defaults to `referral_status: unconfirmed`.
- Discord outbound webhooks, company/source health records, bounded review digest, versioned seen-job history, canonical URL deduplication, and safe limited backfill.
- Automated regression tests on PRs and main via `.github/workflows/test.yml`.
- **P1-E corrected** bachelor's degree/tenure pathways and safe resumable backfill (PR #18); its post-merge scheduled workflow was verified [Actions #42698015121](https://github.com/KanujVerma/jobbie/actions/runs/42698015121). That run had 0 eligible matches, so it proves pipeline execution, not job relevance or Discord alert delivery.

## Original 13 network-priority monitored sources (verified against `companies.yaml`)
Micron; Salesforce; CrowdStrike; Intel; Applied Materials; Western Digital; SanDisk; Plaid; Oracle; Microsoft Research; Microsoft; Amazon; Apple.

Two disabled historical configurations: Snowflake and Applied Digital. Microsoft and Microsoft Research are separate *source entries*, not two unrelated employers. Do not automatically tag discovered companies as having referrals.

## Getting started (local)
```bash
git clone https://github.com/KanujVerma/jobbie.git
cd jobbie
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py validate-config
pytest -q
python main.py run --company Microsoft --dry-run --verbose
```

The dry run is read-only for the persisted state and does not send webhooks. Do not run a real alert scan with a new/empty state unless backfill and delivery are explicitly reviewed.

Actual alerts require the existing `DISCORD_WEBHOOK_URL` secret configured in GitHub Actions. **Never expose webhook credentials** in public issues, commits or logs. `python main.py test-discord` sends a REAL message; use only with an owner-approved test destination.

## Actual deployment and cadence
- Monitor: `.github/workflows/job-alerts.yml` uses a scheduled 15-minute cron expression and `workflow_dispatch`.
- **This does not mean it runs every 15 minutes.** Observed gaps have reached many hours. No near-real-time or SLA claim is justified.
- Production job history: `state/seen_jobs.json`. **Never delete or reset it to force new alerts**; that risks lost history or spam. Follow [Operations](docs/OPERATIONS.md) for safe migration, rollback and diagnostic procedures.
- Diagnostics distinguish a failed fetch (e.g. Plaid Lever 404) from a genuinely empty source. Source outages should not stop other company checks.
- The app currently sends **webhooks only**. It does NOT yet receive Discord commands or resume uploads, tailor resumes, run a dot/computer-use executor, submit employer applications, send founder emails, or manage private application records.

## Roadmap (ordered, one usable release at a time)
1. **Phase 1 + hardening:** new-grad filtering, 13 source stars, release tests and safe backfill. Implemented; last corrective code merged at [PR #18](https://github.com/KanujVerma/jobbie/pull/18), subsequent production validation tracked in STATUS.
2. **Phase 2A released (code only):** public Greenhouse/Ashby adapters merged in [PR #23](https://github.com/KanujVerma/jobbie/pull/23); additional boards NOT enabled. **Next: [P2-UX1 informative alerts](docs/phases/PHASE-2-UX.md), [first /goal](docs/agent-prompts/PHASE-2-UX-GOAL.md)**, then [P2-ACT owner-approved boards](docs/phases/PHASE-2-ACT.md), permitted feeds P2-B and canonical catalogue P2-C.
3. **Phase 3 (planned):** signed Discord commands, owner-private resumes/evidence, ranking and basic application ledger.
4. **Phase 4 (planned):** natural evidence-preserving tailoring, before/after + why, full PDF/DOCX preview and exact one-job approval packet.
5. **Phase 5 (planned):** dot-first MANUAL application delegation/feasibility, then consent-bound single-job executor and optional local browser fallback. No verified automatic dot trigger yet.
6. **Phase 6 (planned):** startup discovery/approved outreach plus application follow-ups/feedback. [Full plan](docs/PHASES.md) · [Safety & auto-apply design](docs/AUTO_APPLY.md).

Existing public/third-party source access, license and data-rights constraints remain in force. No LinkedIn automation, unsupported resume claims, unpaid job applications or unapproved paid API activity.

## Handoff to any new coding agent
**Do not ask for this conversation.** Start at [AGENTS.md](AGENTS.md), then [docs/HANDOFF.md](docs/HANDOFF.md), [docs/STATUS.md](docs/STATUS.md), and the referenced phase contract. Verify live GitHub HEAD, issues, CI and run logs. Every functional PR must update [STATUS](docs/STATUS.md), [HANDOFF](docs/HANDOFF.md) and [RELEASE_LOG](docs/RELEASE_LOG.md) together; CI enforces this on pull requests.

The current product, future architecture, contracts, evaluation, privacy, open-source reuse and rollback instructions are linked from [docs/README.md](docs/README.md).

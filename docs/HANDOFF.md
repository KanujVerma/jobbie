# Agent restart handoff: complete context without chat history

Read this file and [STATUS.md](STATUS.md) before changing Jobbie. Then read [AGENTS.md](../AGENTS.md), [DECISIONS.md](DECISIONS.md), [PRODUCT.md](PRODUCT.md), [PHASES.md](PHASES.md), the active phase, [CONTRACTS.md](CONTRACTS.md), [SECURITY.md](SECURITY.md), [OPERATIONS.md](OPERATIONS.md), [EVALS.md](EVALS.md) and [OPEN_SOURCE.md](OPEN_SOURCE.md). Current runtime and future architecture are intentionally separate in IMPLEMENTED_ARCHITECTURE.md and ARCHITECTURE.md.

## Current state: Phase 2A release completed and merged
- Repository: `KanujVerma/jobbie`; branch `main`.
- Phase 2A PR #23 has been **merged to main** via squash commit `ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb`.
- Main post-merge CI https://github.com/KanujVerma/jobbie/actions/runs/42720639467 passed: **812 tests passed in 45s**, config valid, documentation continuity PASS.
- Production status: **MERGED, NOT PRODUCTION_ENABLED**. The 2 public board example entries remain in `examples/p2a-public-boards.yaml` and disabled. `companies.yaml` maintains the original 15 configured / 13 enabled sources. No new active alerts, no database, no LLMs.
- Real read-only smoke verified with zero state/config mutations and `discord_sent=false`.
- Phase 1 issue #6 post-P1-E live gate is SATISFIED via scheduled run 42698015121 at descendant commit `ffc8c09bd2ec0cbcb7dd48143204c26255324bcb`.
- The owner subsequently approved the NEXT scoped implementation, **P2-UX1 notification layout**. Start only that [contract](phases/PHASE-2-UX.md) and [first goal](agent-prompts/PHASE-2-UX-GOAL.md). Do NOT start P2-ACT/P2-B/C/Phase 3 at the same time.

## Takeover procedure
1. Query GitHub repo metadata, current main HEAD, PRs and open issues. Check whether Phase 2A is merged before assuming it is open.
2. Fetch origin, inspect working tree; never discard local work.
3. Inspect `git diff origin/main...HEAD -- companies.yaml state/seen_jobs.json .github/workflows/job-alerts.yml`. The implementation must not alter these production files.
4. Run `python main.py validate-config`, `python -m compileall -q src scripts`, `pytest -q`, and `python scripts/check_handoff_docs.py --base origin/main --head HEAD` on the actual checkout using Python 3.12 and requirements-dev.txt.
5. All functional PRs must update STATUS.md, HANDOFF.md, and RELEASE_LOG.md together.

## As-built code map
| Area | Files | Invariant |
|---|---|---|
| Legacy poll orchestration | main.py, companies.yaml, src/config.py | 13 enabled original companies; dry-run no state writes/webhooks |
| Employer fetch | src/adapters/*.py | BaseAdapter + shared HTTPClient; failures are not fabricated empty success |
| New public boards | greenhouse.py, ashby.py, public_board.py | GET-only fixed endpoints; listed jobs, safe IDs/URLs, bounded reads |
| Source facts | src/models.py | frozen Job, optional fields preserve old constructors; explicit salary units |
| Eligibility | filtering.py, eligibility.py, experience.py | tri-state; required qualifications and source employment override title guesses |
| Delivery | notifier.py, storage.py, backfill.py | accurate date labels, canonical URL dedup, acknowledge only delivered visible links |
| Health | src/health.py | actual failed/empty distinction and scheduler gap evidence |
| P2-A tests | tests/test_public_board_adapters.py, test_public_board_html.py | 85 new cases plus existing 727-suite baseline (812 total) |
| Read-only live check | scripts/verify_public_boards.py, examples/p2a-public-boards.yaml | no production config enabling, no Notifier calls, hashes before/after |

## Locked product constraints
Personal single user; Dec 2026 UW–Madison BS CS; January 2027 target start; full-time US new-grad/SWE/related technical roles; internships excluded. $100k annual base is preferred, not a hard cutoff. SF Bay Area first, other CA/NYC/Chicago/TX/FL prioritized. US authorized without sponsorship; permanent residence is not citizenship. Original 13 network sources retain a separate UNCONFIRMED referral status. Do not add unrelated titles just to increase match counts.

Private resumes, family contacts, credentials and private GitHub code never go in public commits/logs. Private repository reading requires explicit allowlist approval; reading is not outward-disclosure approval. No mass/unapproved auto-apply; future Phase 5 may submit a SINGLE owner-authorized exact job packet after separate `Approve & Apply`. No assumed dot API, unauthorized Jobright/LinkedIn scraping, unsolicited founder emails, or unapproved paid inference. Later phases use approved evidence for matching/tailoring and exact owner approval for outbound messages.

## Approved future plan: one PR at a time
1. **First [P2-UX1 issue #25](https://github.com/KanujVerma/jobbie/issues/25):** compact, informative truthful webhook alerts without changing source/state. [Exact scope](phases/PHASE-2-UX.md) and [first /goal](agent-prompts/PHASE-2-UX-GOAL.md).
2. **Second [P2-ACT issue #26](https://github.com/KanujVerma/jobbie/issues/26):** source-check and owner-approve a small shortlist, then enable additional Greenhouse/Ashby boards with `discovered` status; original 13 remain star-marked.
3. P2-B allowed feeds; P2-C catalogue/global dedup/shadow cutover.
4. P3 private authenticated Discord commands/profile/evidence and basic application ledger.
5. P4 role/company resume tailoring with before/after reasons, PDF/DOCX preview, owner `Approve resume` and optional UNSENT `Prepare application packet`; P5 alone adds the live `Approve & Apply` control and submission permission.
6. P5 prove dot manual delegation before assuming programmatic trigger, then secure one-job executor/receipt, local fallback only if needed and allowed.
7. P6 startup sourcing/outreach and follow-up optimization.

The actual AUTOAPPLY executor is not implemented. A dot's inbound programmatic trigger, account access, hosting cost and site automation rules are unresolved feasibility questions; do not invent an API or auto-submit without exact approval. See [AUTO_APPLY.md](AUTO_APPLY.md), [NOTIFICATIONS_V2.md](NOTIFICATIONS_V2.md), [PHASES.md](PHASES.md).

Every functional PR updates STATUS/HANDOFF/RELEASE_LOG, plus impacted architecture/contracts/security/phase docs. CI checks missing/deleted/empty/symlinked handoff files, HTML fixtures and renamed source paths. Reviewer still checks truth: record exact source SHA, tests, reviewer SHA, actual live evidence, rollback and next slot. No private chat history needed.

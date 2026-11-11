# P2-UX1 executable PR — make existing Discord alerts informative

**Status:** PLANNED. [Tracking issue #25](https://github.com/KanujVerma/jobbie/issues/25). This is the next smallest user-visible coding milestone after P2-A merged in [PR #23](https://github.com/KanujVerma/jobbie/pull/23) and its documentation PR #24. It is one REVIEWABLE PR, not a broad Phase 2 rewrite or a promise of personal matching. Normative specification: [NOTIFICATIONS_V2.md](../NOTIFICATIONS_V2.md).

## Scope
- Present job title prominently, followed by actual company/location and known full-time/early-career attributes.
- Make original-13 `NETWORK PRIORITY` clearly distinct from new `DISCOVERED` companies, and display referral `unconfirmed` accurately.
- Include verified base salary with unit/currency if provided; otherwise say "Not disclosed". Never treat total comp/equity as base.
- Show concise deterministic eligibility-screen result/reasons, unknowns where relevant, and truthful timestamp labels (employer posted vs first published vs first observed).
- Direct employer application URL remains obvious, not a hidden tag. Source metadata in small footer, not the primary focus.
- Review digest uses `needs_review` label; no pretending unknown full-time or graduation eligibility has been verified.
- Use existing webhook transport only. Future application buttons, resume previews and fit scores belong to Phases 3–5 and MUST NOT be mocked as working actions.

## Implementation instructions
1. Read `AGENTS.md`, `STATUS.md`, `HANDOFF.md`, `PRODUCT.md`, `CONTRACTS.md`, `NOTIFICATIONS_V2.md` and current `src/notifier.py`, `src/models.py`, `src/eligibility.py`, `src/config.py` plus notifier/network/Greenhouse/Ashby tests. Confirm latest `main` and no conflicting feature PR.
2. Implement compact embed construction in `src/notifier.py` (or small presentation helper), preserving `Notifier.send_job_alert(Job) -> bool`, `Notifier.send_summary()`, webhook rate limit, dedup and existing state.
3. Map optional source facts defensively; source employment is not necessarily full-time when missing; source `updated_at` cannot appear as posted date.
4. Preserve privacy; only source-backed job fields in public channel. No candidate work authorization, private resume details or family contact info in embeds.
5. Add tests under `tests/`, using synthetic Job fixtures. Test exactly 13 starred source entries, 2 disabled, discovered none, Microsoft duplicate source label, base vs bonus/equity and hourly/unknown salary, time zone, source date/first seen distinction, eligible/review statuses, long/hostile Unicode and mentions, broken URLs and Discord byte/char limits. Preserve old notifier ACK behavior.
6. Create a static **synthetic payload preview** under `docs/evidence/` (safe JSON/redacted, NO webhook) showing 4 examples. Label as a render fixture not real listing/real notification.
7. Run `python main.py validate-config`, `python -m compileall -q src scripts` and complete `pytest -q`. Document exact count/SHA/run URL. Confirm no changes to `companies.yaml`, `state/seen_jobs.json`, `job-alerts.yml`, no new source activation or backfill resets. Compare current vs new embed.
8. Update `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/RELEASE_LOG.md` in same PR and documentation if behavior changes. Request independent review and fix findings; merge only with CI and reviewer gate. If no authorized test webhook, document `LIVE_DELIVERY_UNVERIFIED`, not fake a delivered job.
9. Keep the new generation compatible with public webhook; a release is actionable if actual jobs can still link to employer. Test independently of AI and private services.

## Explicitly out of scope
- No candidate profile/AI fit %, saved application state, authenticated Discord interactions, buttons to tailor/resume preview/apply, automatic submissions or background dot tasks.
- No new Greenhouse/Ashby employers and no changes to planned feed/data catalogue. See [P2-ACT](PHASE-2-ACT.md) for activation.
- No provider billable calls, no claim of guaranteed 15-minute cron or fixes to Plaid's 404.

## Acceptance & rollback
A synthetic layout preview and exact embed tests show source-grounded concise fields with no misclassification/mention leak. Full tests pass; config and state untouched; reviewer completed with no unresolved serious findings; old job alerts remain functional. Rollback is revert of presentation-only PR; delivery/state unchanged. Separate production smoke only with approved destination or real naturally eligible job, never force one.

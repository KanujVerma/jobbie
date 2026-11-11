# Phase 4 executable contract — natural resume tailoring, preview, approval packet

**PLANNED.** Requires Phase 3 released. Normative [RESUME_TAILORING.md](../RESUME_TAILORING.md), [AUTO_APPLY.md](../AUTO_APPLY.md) for approval boundaries, and [EVALS.md](../EVALS.md). Four sequential PRs.

## P4-A: frozen evidence and model benchmark
- Use only confirmed CandidateFacts, approved repository ownership, original/source resume, job JD snapshot and employer sources. Benchmark 24 real role descriptions (six each SWE/backend, AI/FDE, startup/product, ML/data); read source/license constraints.
- Start with Groq GPT-OSS 120B only as candidate free option; compare permitted challengers using blind user naturalness, authenticity, specificity, latency, data policy and free quotas. No unapproved paid spend. Freeze profiles/requirements for reproducibility.

## P4-B: structured edits and independent fact validator
- Model proposes `replace bullet`, `reorder experience/project`, `remove irrelevant`, `reorder skills`, `rewrite concise summary` with exact before/after source span, verified fact IDs and targeted job requirement IDs.
- Reject changes to title/date/employer/ownership and unsupported skills/metrics, invented ROI/production performance, synthetic-to-live upgrades, false citizenship. Natural one-idea-per-bullet voice, no em dashes, no ATS keyword stuffing.

## P4-C: reproducible PDF/DOCX
- Render from one canonical structured resume via pinned RenderCV or equivalent PDF and python-docx DOCX; one-page engineering default, selectable text, correct reading order and link behavior. Source/target job artifact ID, SHA-256, render version and immutable original; verify no clipped content and PDF-DOCX parity.
- Private short-lived preview/download URLs; don't leak resumes via Discord public channel.

## P4-D: actual preview and separate approval
- Authenticated review page linked from signed Discord command: original vs new bullet-by-bullet diff, clear JD-based *why*, what was removed, accept/reject/edit, undo, full-page PDF preview, downloadable PDF/DOCX. Revalidate after edits.
- `Approve resume` signs exact document hash without submitting an application.
- Separate `Approve & Apply` requires a single verified job/requisition/official URL, confirmed candidate answer set and approved resume hash, one-time nonce/expiry. In this phase it may create a **private queued packet** only; NO executor/browser submit until Phase 5 is validated. Never display a fake fully functional auto-apply button.
- Store exact immutable resume version attached to application record, no substitution later.

### Release gates
Zero accepted severe factual hallucinations across 24 test jobs, 12 owner-reviewed samples with ≥10 improved-and-at-least-as-natural, all PDF/DOCX parse/layout/links correct, hostile-upload and unauthorized-link tests, stale approval invalidation. One real approved preview/download where possible. No automatic employer submission.

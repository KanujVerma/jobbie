# P2-R3 local review ledger

Base5d034f57ceebec206f3ca5b3279c41e398f29a7b. Round1 at eda6d416d5c147fa1538952e538cab0a124baf59: CHANGES. Selected codex/gpt-6.1-sol reasoningEffort high, no fallback, usage unavailable. Independent full937tests and focused53 passed, config/diff passed; no live source or CI check was repeated.

S1 should: partial overlap skipped duplicate IDs but counted them toward page completion, allowing incomplete silent baseline. Agreed; reproduced failing regression, then record DUPLICATE_REQUISITION for every duplicate while keeping unique partial results. Tests ensure revision remains pending and later complete retry includes the omitted old ID without alerting. Full parent suite938passed. No declined findings. Round2 APPROVE at b7112bcf4b30d277050a1556858f4e049093a62c. S1 resolved, no new findings. Independent full suite938 passed in35.35s, source suite38 passed; config/diff passed. Public source/live/CI were not repeated. This record is documentation only. Parent PR31 CI and own CI/hosted review/merge remain separate gates.

Oracle integration verification: rebase onto merged9317c73 retains functional patch76c6409fe877a5fac07570fb78aa05916a71fc1e. Combined full990tests passed36.78s; config/compileall/diff pass, current main seen-state retained unchanged. Local Oracle behavior was independently approved atb7112bc with938tests before base integration; own current-head hosted review/CI/merge remain required.

Hosted H1 correction: the explicit citizenship matcher rejected a clause that also accepts permanent residency. Parent reproduced4failing alternative clauses, then checks the immediate continuation for an accepted residency/green-card alternative while retaining any separate mandatory citizenship clause. Five focused cases now pass. No personal status is inferred. Fresh exact-head hosted review/CI required; prior local review remains scoped to its earlier head.

Oracle H1 verification: full995tests passed38.93s;5focused clauses, config/compileall/diff passed. A separate mandatory clause still excludes correctly. This does not repeat live source/client rendering or approve production cutover.

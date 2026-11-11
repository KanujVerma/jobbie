# P2-R3 local review ledger

Base5d034f57ceebec206f3ca5b3279c41e398f29a7b. Round1 at eda6d416d5c147fa1538952e538cab0a124baf59: CHANGES. Selected codex/gpt-6.1-sol reasoningEffort high, no fallback, usage unavailable. Independent full937tests and focused53 passed, config/diff passed; no live source or CI check was repeated.

S1 should: partial overlap skipped duplicate IDs but counted them toward page completion, allowing incomplete silent baseline. Agreed; reproduced failing regression, then record DUPLICATE_REQUISITION for every duplicate while keeping unique partial results. Tests ensure revision remains pending and later complete retry includes the omitted old ID without alerting. Full parent suite938passed. No declined findings. Round2 re-check pending. Parent PR31 CI and own CI/hosted review/merge remain separate gates.

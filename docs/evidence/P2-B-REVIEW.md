# P2-B independent review ledger

Round1: codex/gpt-6.1-sol, reasoningEffort high, serviceTier default, pinned d03dbdef3b3958771abe80daa99552901a411024 against4eb83f454e2671e8e06d7cb10f4b079ab98fcf90. Verdict CHANGES; full1033passed33.64s plus config/diff/docs/syntax/OFF CLI checks. Usage unavailable. Clean pinned worktree retained.

- S1 P2: supported Greenhouse/Ashby source IDs were not consulted for optional lead posting-ID confirmation. Parent reproduced2failing matching-ID cases and fixed the explicit supported adapter mapping. Positive/conflicting cases now cover all3supported adapters. This is a posting-ID comparison, not a claim that Greenhouse posting ID equals internal employer requisition ID.
- S2 P2: same feed source ID with contradictory posting dates retained the first row. Parent reproduced2failures for reversed orders, added normalized date/instant facts to collision comparison; both fail closed now. Equivalent timezone instants still deduplicate.

Parent repaired the small findings directly and verified6focused cases. No second delegate was started for these small fixes. Fresh full tests and exact-head hosted independent review/CI remain required; the earlier local reviewer verdict is not restated as approval of a different head.

Hosted H1 on8a797f0: repeated normalization cost O(leads*postings) could delay original employer alerts. Parent reproduced4000URL normalizations for20nonmatching leads/100postings. A reusable official URL/company index is now built once per employer only when leads exist; the same poller regression requires <=130calls and observed120. Exact source-ID ambiguity/conflict checks remain. Two focused regressions include conflicting official posting IDs at the same URL. No feed activation or timeout increase.

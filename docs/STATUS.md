# Jobbie canonical project status

Phase 2 remains **PARTIAL**. Verify current GitHub main and Actions before acting. [Requirement audit](PHASE-2-ACCEPTANCE.md).

## Isolated Phase 3 stack

P3-A adds a separate signed Discord endpoint and worker. The enabled manifest contains health, settings, and deferred task status. Additional commands and controls enter the manifest as their private backends arrive. Live Discord registration, HTTPS hosting, and keys are `BLOCKED_LIVE` pending owner setup and approval. [Phase 3 contract](phases/PHASE-3.md)


P3-B adds owner-scoped encrypted profiles, resumes, job snapshots, saved-job and application ledgers, and isolated upload processing. Discord profile and application views and deferred resume upload use these backends. Owner-hosted storage and Discord activation remain `BLOCKED_LIVE`.


P3-C adds private candidate proposals with versioned source spans, explicit decisions and deletion or revocation invalidation. GitHub evidence requires a per-repository approval and pinned commit. Owner repository access and Discord registration remain `BLOCKED_LIVE`.

## Scheduled catalogue shadow through 2026-11-17 UTC

The first ordinary C2 run bootstrapped and published encrypted custody. Across 21 ordinary runs through [44164832540](https://github.com/KanujVerma/jobbie/actions/runs/44164832540), 21 verified a fresh exact-key cache restore, 7 reported healthy parity, and 14 were degraded. The longest consecutive healthy stretch in the public logs was about 26 hours, and the last healthy run was [43767315174](https://github.com/KanujVerma/jobbie/actions/runs/43767315174). These are public run counters. The authenticated 72-hour audit remains open.

The latest run restored the parent checkpoint and published its successor under the same catalogue UUID. It fetched 3,856 rows and recorded zero job alert ACKs. Eight of 13 adapters responded successfully, including an empty SanDisk response. Workday returned HTTP 429 for Micron, Salesforce, CrowdStrike and Intel, and stopped Applied Materials after 80 rows. Parity was false with `BLOCKED_SOURCE_SCAN`. [Run and logs](https://github.com/KanujVerma/jobbie/actions/runs/44164832540)

[Run 43790517896](https://github.com/KanujVerma/jobbie/actions/runs/43790517896) also recorded two Applied Materials catalogue rejects. A separate local dry run reproduced one rejection in the same source: the adapter yielded a row without an official posting URL while reporting success. The exact historical rows and the original 429 headers were unavailable in the public logs. See [release evidence](RELEASE_LOG.md#p2-c2-scheduled-shadow-reliability).

## Merged components

| Scope | PR / merge commit | Proof |
| --- | --- | --- |
| Direct ATS | #23 ecb553fa98cf5a7ccd0cd4d2212b72ea457a3aeb | Adapter fixtures/permitted source checks |
| Discord layout | #29 e0346f49bd572179250fe08bed73131db0ba311a | Ordinary43100310762 accepted2individual HTTP204job sends; human receipt/rendering unverified |
| Reliability | #30 614b3edc14e86d952579a0c57db0eb68669c08d9 | Corrupt-state/pre-send/dry-run/partial ACK safety, exact CI/reviews |
| Owner intake | #32 f46625845577f158da31974d927aa5748d0c3642 | Portable issue/CLI/manual evidence, disabled proposals,928local/independent tests |
| Plaid/Amazon | #31 9317c73b1971d6c7bb19dcb22a6be76876ad7369 | Exact-head gates; first repaired ordinary baseline verified below |
| Oracle | #33 4eb83f454e2671e8e06d7cb10f4b079ab98fcf90 | Correct finder/site/location/inner pagination/dates; first ordinary baseline verified below |
| Optional feeds OFF | #34 f3a61f4ab2d5165474ffddf63ac0e052b4a75fdb |1041tests, exact2ef45e1 CI/hosted review, postmerge43128988343 |
| Catalogue core | #35 1614d804001edbf1d1fe10f33d661b6331c8961a |1118tests; exact0be562f test43147233493/public-read43147233507 and hosted clean; postmerge43148218676 |

All13original enabled Network Priority source entries/unconfirmed referrals and2historicaldisabled remain. No employer/feed/private profile/application is activated. Legacy JSON/URL delivery authority is preserved.

## Actual source production evidence

[Ordinary43140198821](https://github.com/KanujVerma/jobbie/actions/runs/43140198821), head f3a61f4, state d4724df3e3f70b17762f123c32216a1a671e8bfb:13successful responses/1empty SanDisk;11569fetched,2matched/356review/11211excluded;0new job ACKs/0job send failures.600.08s duration/301.43minute gap. Plaid143/Oracle2113complete silent baselines, delivery_acknowledged=false and all2256baseline entries alerted=false. All257prior legacy seen ACK flags/10URL ACK entries retained,0lost. These flags are ledger assertions, not257repeated HTTP deliveries. [Receipt](evidence/P2-R2-R3-LIVE-2026-11-12.md).

Source baseline gates VERIFIED_LIVE. No manual dispatch, seed/reset, forced backfill or test send. Complete responses are within configured scope and do not prove no openings. SanDisk replacement406 remains BLOCKED_SOURCE_ACCESS; current empty response is not a no-openings result. Cron remains best effort. Earlier43100310762 remains the separate2individual HTTP204job proof; human client receipt/rendering unverified.

## Persistent shadow code release

C2 implements pre-filter shadow capture, compact exact logical observation history/context, independent filter/canonical-candidate/ACK comparisons, immutable reclassification/query/export, explicit v1 backup migration, bounded encrypted checkpoint/rollback tools and optional transport workflow. Original ACK state commits before optional cache transport; publication requires a fresh exact-key restore/digest. Missing crypto/custody/storage leaves original alerts independent. No automatic cutover.

Final C2 full1171passed45.02s after hosted audit-window correction; exact-head CI/hosted review and postmerge checks passed. Permitted original13memory-only no-webhook verification passed11582rows/0mismatches; it is not production shadow. Synthetic1000rows×3scans retained3000logical/1000physical with8KiB repeat growth, not actual72h proof. C2 review/CI/merge/key preparation are complete; actual ordinary shadow observation/72h/approved cutover remain gates. [Guide](CATALOGUE.md), [plan](superpowers/plans/2026-11-12-p2-c-catalogue.md).

All3evaluated feeds remain OFF/BLOCKED_SOURCE_RIGHTS/BLOCKED_APPROVAL;0datasets fetched and real coverage/freshness NOT_MEASURED. [Rights](evidence/P2-B-SOURCE-RIGHTS.json), [feed guide](PUBLIC_FEEDS.md). Owner onboarding is [COMPANY_INTAKE.md](COMPANY_INTAKE.md); requested monitors default discovered/networkfalse/referralunavailable and stay disabled until separate exact approval.

Cutover requires a qualifying 72-hour window, parity/identity/ACK reconciliation, rollback proof and exact owner approval, followed by an ordinary scheduled run. `BLOCKED_72H_EVIDENCE` and `BLOCKED_APPROVAL` remain. The next major phase begins with P3-A signed, allowlisted Discord interactions after P2-C releases.

### Historical C2 development and merge evidence

C2 rejection-isolation correction passes full1168tests43.52s; first failed live shadow receipt remains preserved, never a passing claim. Corrected original13memory-only read is still in progress. Optional repository secret CATALOGUE_SHADOW_KEY was provisioned2026-11-12T04:07:35Z from a new private owner-only recovery file; value withheld. Current main does not consume it, so this is preparation, not shadow deployment or cutover.

Corrected local original13shadow read passed527.29s:11582stored rows,0rejects/identity/filter/candidate/ACK mismatches,0sends/feeds, config/state/input-DB hashes unchanged. Normalized memory DB52.7MBraw/10.2MBcompressed. Failed predecessor remains explicitly failed. Later transport caps/guarded duplicate-copy retention are separate tested changes, not a real72hwindow. See evidence/P2-C2-VERIFICATION.md and live read receipt.

C2 final local checks: full1170passed38.85s, config/diff/docs/actionlint passed. Real original13no-mutation shadow read passed with0mismatches. Candidate is pinned for independent review, not merged/deployed; real72h and cutover approval remain blocked.

C2 local Sol approved pinned55785e8 in one round, independently1170passed41.53s/config/diff/docs/clean-state checks; no findings. Own PR/current-head CI/hosted review/merge and actual ordinary shadow still required. See evidence/P2-C2-REVIEW.md; not72h/cutover approval.

C2 hosted H1 reproduced/fixed: primary audit window is now recent96h independently of retained history, avoiding the1000-receipt permanent failure. Old records retained; fixture still cannot satisfy real72h. Fresh head full checks/CI/hosted review required.

C2 audit correction full1171passed45.02s/config/diff, no ingestion/source/alert change. Fresh exact-head CI/review pending.

## C2 release2026-11-12

PR36 merged830dcd13d05433b286e7b810385807481e9cc744 after exactfe8f7f73e42c928e99d96025ff906d43169a1a6d test43155934557/public-read43155934550 and completed hosted review with both finding flags false. The merged/reviewed trees match. Postmerge Tests43156415856 passed.1171local tests include the hosted audit-window regression; local Sol independently approved earlier source with1170tests. The key and workflow were ready at merge. The scheduled evidence above supersedes the merge-time live status.

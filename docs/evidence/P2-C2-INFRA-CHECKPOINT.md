# C2 infrastructure research, not deployment evidence

SQLite is standard-library/public-domain software, no hosted spend. Optional cryptography50.0.2 installed successfully; package metadata declares Apache-2.0 OR BSD-3-Clause. Fernet authenticates encrypted bounded snapshots; keys must never enter cache or public Git. No actual production key has been generated/deployed yet at this checkpoint.

Primary references checked2026-11-12UTC:
- https://www.sqlite.org/copyright.html
- https://cryptography.io/en/stable/fernet/
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- https://docs.github.com/en/rest/actions/cache
- https://github.com/actions/cache

Primary billing policy: public standard runners free; cache allowance10GiB/repository separate from artifacts. Anyone able to read a repository may access cache data, so cache only authenticated ciphertext. Standalone cache save can succeed with a warning and no saved object: require a fresh exact-key restore/digest check before publishing a new checkpoint. No paid limits/overage/billing changes.

Observed read-only usage:155096679bytes/3caches. Custom cache-limit GET returned402 requiring a payment method; no retry, alternative route, purchase or setting change. The included-policy allowance is verified; the repository custom limit is NOT_MEASURED. Planned runtime guard stops before8GiB with bounded ciphertext, leaving original polling independent. Missing/evicted/incorrect custody must block shadow rather than reseed it.

Synthetic capacity record P2-C2-CAPACITY-BEFORE.json demonstrates the current per-row repeated layout needs compaction before a72hwindow at illustrative10kpostings/15minute polling. It is not production scale/coverage/72hevidence. No upstream datasets, third-party scraper code, private profiles or secrets are imported. Workflow/receipt audit and safe deployment remain unfinished; this is a development checkpoint only.

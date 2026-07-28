# Effectiveness Contract

Use this file before accepting any CI/CD speedup. A fast pipeline that no longer detects defects, proves provenance, or isolates trust boundaries is a failure.

## Non-negotiables

| Area | Must preserve |
|---|---|
| Tests | Same required test set or a risk-approved selected set with periodic full validation. |
| Types/build | Same compile/type/link gates unless the work is graph-provably unaffected. |
| Security | Secrets, dependency, SAST, container, provenance, and policy controls remain in an appropriate tier. |
| Cache | Trusted outputs cannot be influenced by untrusted writes. |
| Artifact | Deploy/promote the exact digest that passed validation; no rebuild drift. |
| Run identity | Green status applies to the exact head SHA and intended workflow/event. |
| Flakiness | Retries do not erase failure evidence or ownership. |
| Rollback | A previous validated artifact remains deployable. |

## Reject these shortcuts

- Deleting or marking required checks optional because they are slow.
- Broad `continue-on-error`, empty catches, weakened assertions, or reduced thresholds.
- Retrying until green without recording the initial failure.
- Running security scans on a subset while reporting them as full scans.
- Letting PR builds write to a shared remote cache consumed by protected branches.
- Using `latest` mutable images or unpinned third-party actions in trusted paths.
- Rebuilding an artifact separately for staging and production.
- Path/affected filtering without verified history, merge base, graph completeness, and fallback.
- Accepting a rerun that started before the relevant commit landed.

## Safe ways to reduce validation cost

1. **Split, don't skip:** shard the same suite so every test runs once.
2. **Select, then defend:** use affected/test-impact selection plus scheduled or merge-queue full runs.
3. **Tier security:** block high-confidence/high-severity findings on PRs; run deep scans scheduled or before release.
4. **Cache correctly:** key by complete inputs and separate trust scopes.
5. **Parallelize gates:** run independent checks concurrently while keeping the same aggregate gate.
6. **Move cadence, not existence:** heavy non-PR-critical checks can run on merge queue, nightly, or release, with documented coverage.

## Decision rule

If you cannot explain why the optimized pipeline would still catch the same defect classes, stop. Revert the optimization or add a defensive full-validation path.

## Sources

- SLSA levels: https://slsa.dev/spec/v1.0/levels (accessed 2026-07-28)
- in-toto attestations: https://github.com/in-toto/attestation/blob/main/spec/README.md (accessed 2026-07-28)
- DORA metrics: https://dora.dev/guides/dora-metrics/ (accessed 2026-07-28)

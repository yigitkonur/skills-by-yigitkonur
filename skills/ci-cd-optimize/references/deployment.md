# Deployment Acceleration

Use this file when build/deploy stages are slow, repeated, unsafe, or hard to verify.

## Build once, deploy many

The artifact that passed validation is the artifact deployed everywhere:

1. Build and test once.
2. Store by immutable digest.
3. Promote the digest to staging.
4. Verify health and provenance.
5. Promote the same digest to production.

Do not rebuild per environment. Rebuilds introduce dependency, base-image, cache, and timestamp drift.

### The artifact must be self-contained

Splitting build from deploy only works if the artifact carries everything the deploy step needs. Framework build outputs frequently contain **symlinks or relative references into the build workspace** — `node_modules`, a framework cache directory, or a traced-dependency tree. Archiving only the visible output directory produces a package that unpacks fine and then fails at deploy with a missing-file error naming a path nobody deliberately excluded. This hides from every check on the build machine, where the referenced files still exist; it appears only on the clean runner that consumes the artifact. Verify by unpacking into an empty directory on a *different* runner and running the real deploy command; "works when the deploy job also checks out and installs" means the artifact is not self-contained and you are shipping a rebuild in disguise.

## Safe speed levers

| Bottleneck | Safe optimization |
|---|---|
| Rebuild per environment | Promote immutable digest. |
| Manual traffic switch | Automated metric-gated canary/blue-green. |
| Timed pauses with no signal | Analysis based on error rate, latency, saturation, business checks. |
| Deployment races | Concurrency/resource group with queueing, not cancellation. |
| Slow preview setup | Change-based previews with deterministic teardown. |
| Rollback uncertainty | Retain prior artifact/ReplicaSet and test rollback. |

## Migration sequencing

- Additive/backward-compatible migrations can precede application rollout.
- Destructive changes need expand-and-contract: add new shape, migrate consumers, remove old shape only after old consumers are gone.
- Deployment rollback cannot undo data loss.
- Migration jobs need clear failure handling and must not run concurrently against shared state.

## Verification

Before claiming a deployment is done, verify:

- run head SHA is the intended commit,
- artifact digest equals the validated artifact,
- provenance/SBOM/signature checks pass where required,
- readiness/startup probes pass,
- canary/analysis metrics are inside budget,
- rollback artifact remains available.

Size a self-verifying deploy's convergence budget to **propagation, not to the deploy call**. Edge and CDN-backed platforms serve the previous revision for tens of seconds after the deploy returns 200; a budget tuned to how long the deploy command takes produces a false red on a deploy that actually succeeded — worse than no check, because it trains everyone to ignore the signal. Set the budget above observed propagation p95, poll with a strict equality check against the expected revision (retry HTTP/malformed-body errors, never treat them as success), and emit both expected and observed revision in the failure line. Distinguish a deploy/migration-step failure (roll back) from a revision-assertion failure that usually means propagation outran the budget (re-query before rolling back).

## TypeScript status probe sketch

```ts
type RolloutStatus = { phase: "Healthy" | "Progressing" | "Degraded"; message?: string };

export async function waitForHealthy(getStatus: () => Promise<RolloutStatus>, timeoutMs = 300_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const status = await getStatus();
    if (status.phase === "Healthy") return;
    if (status.phase === "Degraded") throw new Error(status.message ?? "Rollout degraded");
    await new Promise((resolve) => setTimeout(resolve, 5_000));
  }
  throw new Error("Timed out waiting for rollout health");
}
```

## Sources

- Immutable artifacts: https://beyond.minimumcd.org/docs/migrate-to-cd/pipeline/immutable-artifacts/ (accessed 2026-07-28)
- Argo Rollouts analysis/canary/blue-green: https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ ; https://argo-rollouts.readthedocs.io/en/stable/features/canary/ ; https://argo-rollouts.readthedocs.io/en/stable/features/bluegreen/ (accessed 2026-07-28)
- Argo CD sync waves/hooks: https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/ (accessed 2026-07-28)
- Kubernetes probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ (accessed 2026-07-28)

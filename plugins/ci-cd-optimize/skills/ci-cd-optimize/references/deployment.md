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

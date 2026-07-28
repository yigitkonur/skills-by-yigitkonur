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

Framework build outputs often contain symlinks or relative references into
the build workspace (`node_modules`, framework cache directories,
traced-dependency trees). Archiving only the visible output directory
yields a package that unpacks cleanly and fails at deploy with a
missing-file error — invisible on the build machine, where the referenced
files still exist. Verify by unpacking the artifact into an empty directory
on a different runner and running the real deploy command against it. If it
only "works when the deploy job also checks out and installs", that is a
rebuild in disguise, not a promoted artifact: dereference links when
archiving or explicitly include the referenced trees.

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
- rollback artifact remains available,
- the deployment reached a terminal verdict by observation rather than by an assumed timeout.

A deployment timeout is **unknown**, not automatically failed over or safe to
rebuild. Investigate the exact rollout state first; rebuilds per environment
reintroduce artifact drift and are not an acceptable "verification" fallback.

### Size the convergence budget to propagation, not the deploy call

Edge/CDN platforms commonly serve the previous revision for tens of seconds
after the deploy call returns success. A revision-poll budget tuned to the
deploy command's duration produces false reds on good deploys — worse than
no check, because it trains people to ignore the signal and can trigger a
needless rollback.

- Set the budget well above observed propagation p95 (a couple of minutes
  is unremarkable), with short per-request timeouts.
- Poll with a strict equality check on the expected revision; retry HTTP
  errors and malformed bodies — never count them as success.
- On failure, distinguish a deploy/migration failure (bad ship — roll back)
  from an assertion-only failure (propagation outran the budget — re-query
  before rolling back).
- Emit both the expected and the observed revision in the failure message.

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

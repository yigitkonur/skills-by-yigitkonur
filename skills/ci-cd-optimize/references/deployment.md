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

### Size the convergence budget to propagation, not to the deploy call

A self-verifying deploy — deploy, then poll a `/version`-style endpoint until it reports the pushed revision — is the cheapest guard against a silently stale release. It has one classic defect: **the polling budget is tuned to how long the deploy command takes, not to how long the platform takes to converge.**

Edge and CDN-backed platforms (Cloudflare Workers, Vercel, Fastly, multi-region rollouts) commonly serve the previous revision for tens of seconds after the deploy call returns 200. A 30-second budget produces a **false red on a deploy that actually succeeded** — which is worse than no check, because it trains everyone to ignore the signal and can trigger an unnecessary rollback.

Rules:

- Set the budget well above observed propagation p95 (a 2-minute budget is unremarkable for edge platforms), and keep the per-request timeout short so a hung request does not consume it.
- Poll with a **strict equality** check against the expected revision. Retry HTTP errors and malformed bodies; never treat them as success.
- When the assertion fails, distinguish the two cases before acting: a failure in the deploy/migration step is a real bad ship (roll back); a failure only in the revision assertion usually means propagation outran the budget — re-query the endpoint before rolling back anything.
- Emit the expected and observed revision in the failure message. "Did not converge" without both values is unactionable.

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

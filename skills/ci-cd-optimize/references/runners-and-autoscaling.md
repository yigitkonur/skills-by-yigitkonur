# Runners and Autoscaling

Use this file when queue time, runner capacity, runner isolation, or fleet cost
is the bottleneck.

Read `measurement.md` first if queue and execution have not yet been separated.
Read `capacity-and-contention.md` next when the suspected fix is “add more jobs”
or “increase parallelism” — that file decides whether the fleet has enough slots
for the change to pay off at all.

## Decision order

1. **Trust:** does the job run untrusted code?
2. **Isolation:** does state need to disappear after one job?
3. **Hardware:** CPU, RAM, disk, GPU, macOS, architecture.
4. **Locality:** proximity to registry, cache, artifacts, source, and private network.
5. **Elasticity:** how quickly must capacity react to queue depth?
6. **Cost:** per-minute hosted versus owned fleet plus operations.

## Trust boundaries

- Untrusted public PRs belong on vendor-isolated hosted runners or equivalent
  one-job sandboxes.
- Persistent self-hosted runners can retain malicious processes, files,
  credentials, and network access.
- Do not share runner groups across trust levels.
- Prefer OIDC and short-lived credentials over stored cloud secrets.

## Ephemeral versus warm

| Model | Best for | Cost/latency behavior |
|---|---|---|
| Ephemeral scale-to-zero | untrusted or spiky work | lowest idle cost, cold-start queue time |
| Warm minimum | PR/deploy latency-critical work | higher idle cost, low queue p95 |
| Persistent runner | trusted specialized hardware/locality | highest state/poisoning risk |

Keep orchestration/upload capacity warm separately from scale-to-zero workers.

## Queue time varies by class — measure it, do not assume

A larger instance class is not automatically faster end-to-end. Scarcity, pool
warmth, and time-of-day decide whether the bigger class is provisioned sooner or
later than the small one, and the answer differs per fleet and per hour.

What generalizes is the method:

1. Record `started_at - created_at` per job, grouped by runner label.
2. Report median and p95 per class.
3. Compare the queue penalty of the larger class against the execution gain it buys.
4. Confirm the job is actually CPU- or memory-bound first — per-core idle ratios
   and peak versus average utilization, not just duration.

Size up only when utilization proves the job is compute-bound **and** the class's
measured queue penalty is smaller than the execution gain. When a job is
queue-bound, a bigger runner makes it slower.

## Downsizing is often the real win

“Start large, then step down” sounds prudent but silently overpays if the
step-down half never gets measured. Peak memory far below allocation, CPU average
well under 100%, and wall-clock flat across sizes is the signature of a job that
should shrink.

Treat a downsizing experiment as first-class, not as a consolation prize.

## Autoscaling signals

Scale from queued/assigned jobs, job startup latency, and wait percentiles. CPU
utilization alone misses jobs waiting for a runner. Keep the runner
manager/controller on persistent on-demand infrastructure.

Corollary: fanning many concurrent jobs onto one scarce large label can exhaust
that pool and serialize your own pipeline. Several runs of *your own* repository
queueing simultaneously on the same large label is capacity starvation, not slow
CI — reduce job count, spread across labels, or collocate work before buying
more hardware.

## Spot capacity

Use spot/preemptible runners only for short, idempotent, retryable, or
checkpointed jobs. Keep an on-demand fallback and never run the
controller/manager on spot. Do not use spot for deployment gates where
interruption is costly.

## Architecture and OS

- ARM64 Linux can reduce cost when toolchain and actions support it; benchmark
  compatibility first.
- macOS is scarce and expensive. Move lint/typecheck/cross-platform tests to
  Linux and reserve macOS for Xcode, signing, simulator, and Apple-specific
  validation.
- Pin runner images and Xcode versions; avoid `-latest` for reproducible timing.

## Kubernetes fleets

- Use pod-per-job isolation.
- Avoid privileged containers.
- Set security contexts and least-privilege service accounts.
- Use bin packing that lets the cluster autoscaler remove cold nodes.
- Isolate namespaces for multi-tenant workloads.

## Cross-links

- `capacity-and-contention.md` — when the queue ceiling, not runner speed, is the issue.
- `measurement.md` — how to prove a bigger/smaller class changed execution rather than queue.
- `network-and-artifacts.md` — when registry or artifact locality dominates more than CPU/RAM.
- `deployment.md` — runner choices for rollout and release paths.
- `swift-xcode.md` — macOS-specific constraints and where to optimize instead.

## Sources

- GitHub secure use: https://docs.github.com/en/actions/reference/security/secure-use (accessed 2026-07-28)
- GitHub Actions Runner Controller: https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/deploy-runner-scale-sets (accessed 2026-07-28)
- GitHub limits: https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitLab runner autoscaling: https://docs.gitlab.com/runner/runner_autoscale/ (accessed 2026-07-28)
- GitLab Kubernetes executor: https://docs.gitlab.com/runner/executors/kubernetes/ (accessed 2026-07-28)
- Buildkite Elastic CI Stack: https://buildkite.com/docs/agent/self-hosted/aws/elastic-ci-stack (accessed 2026-07-28)
- Kubernetes bin packing: https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/ (accessed 2026-07-28)

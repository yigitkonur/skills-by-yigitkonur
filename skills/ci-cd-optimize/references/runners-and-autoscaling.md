# Runners and Autoscaling

Use this file when queue time, runner capacity, runner isolation, or fleet cost is the bottleneck.

## Decision order

1. **Trust:** does the job run untrusted code?
2. **Isolation:** does state need to disappear after one job?
3. **Hardware:** CPU, RAM, disk, GPU, macOS, architecture.
4. **Locality:** proximity to registry, cache, artifacts, source, and private network.
5. **Elasticity:** how quickly must capacity react to queue depth?
6. **Cost:** per-minute hosted versus owned fleet plus operations.

## Trust boundaries

- Untrusted public PRs belong on vendor-isolated hosted runners or equivalent one-job sandboxes.
- Persistent self-hosted runners can retain malicious processes, files, credentials, and network access.
- Do not share runner groups across trust levels.
- Prefer OIDC and short-lived credentials over stored cloud secrets.

## Ephemeral versus warm

| Model | Best for | Cost/latency behavior |
|---|---|---|
| Ephemeral scale-to-zero | untrusted or spiky work | lowest idle cost, cold-start queue time |
| Warm minimum | PR/deploy latency-critical work | higher idle cost, low queue p95 |
| Persistent runner | trusted specialized hardware/locality | highest state/poisoning risk |

Keep orchestration/upload capacity warm separately from scale-to-zero workers.

## Queue time varies by runner class — measure it, do not assume

A larger instance class is not automatically faster end-to-end. Scarcity, pool warmth, and
time-of-day decide whether the bigger class is provisioned sooner or later than the small one,
and the answer differs per fleet and per hour.

Two real observations from the *same* provider illustrate the spread:

- One window: the 16-vCPU class was provisioned immediately while smaller classes waited.
- Another window: 16-vCPU jobs waited ~6-7× longer than 2-vCPU jobs (medians over tens of
  launches), and a job that executed in ~60s spent nearly twice that waiting for its runner.

Neither generalizes. What generalizes is the method:

1. Record `started_at - created_at` per job, grouped by runner label.
2. Report median and p95 per class (averages hide exactly the skew you are looking for).
3. Compare the queue penalty of the larger class against the execution gain it buys.
4. Confirm the job is actually CPU- or memory-bound first — per-core idle ratios and peak versus
   average utilization, not job duration.

Size up only when utilization proves the job is compute-bound *and* the class's measured queue
penalty is smaller than the execution gain. When a job is queue-bound, a bigger runner makes it
slower.

Corollary: fanning many concurrent jobs onto one scarce large label can exhaust that pool and
serialize your own pipeline. Several of your runs queueing simultaneously on the same big label
is capacity starvation, not slow CI — reduce job count, spread across labels, or collocate work.

## Autoscaling signals

Scale from queued/assigned jobs, job startup latency, and wait percentiles. CPU utilization alone misses jobs waiting for an available runner. Keep the runner manager/controller on persistent on-demand infrastructure.

## Spot capacity

Use spot/preemptible runners only for short, idempotent, retryable, or checkpointed jobs. Keep an on-demand fallback and never run the controller/manager on spot. Do not use spot for deployment gates where interruption is costly.

## Architecture and OS

- ARM64 Linux can reduce cost when toolchain and actions support it; benchmark compatibility.
- macOS is scarce and expensive. Move lint/typecheck/cross-platform tests to Linux and reserve macOS for Xcode, signing, simulator, and Apple-specific validation.
- Pin runner images and Xcode versions; avoid `-latest` for reproducible timing.

## Kubernetes fleets

- Use pod-per-job isolation.
- Avoid privileged containers.
- Set security contexts and least-privilege service accounts.
- Use bin packing that lets the cluster autoscaler remove cold nodes.
- Isolate namespaces for multi-tenant workloads.

## When provisioning becomes the bottleneck

Past a certain point, fan-out stops paying. If per-job provisioning is 20–40 s and several jobs do 10–30 s of work, the pipeline is mostly waiting for VMs. Symptoms, straight from per-job start offsets:

- a job whose queue time exceeds its duration (e.g. queue 133 s, work 24 s),
- total job work falling while wall-clock stays flat,
- max queue time rising as job count rises.

The lever is **fewer, better-packed jobs**, not a bigger runner — CPU is idle while the VM is being created. Merge jobs that already share setup: same runner class, same dependency install, same service containers, same gating condition. Two DB jobs each booting an identical Postgres container are one job.

Before merging, check what the separation was buying:

- **Rerun granularity.** A merged job means rerunning both halves. Fine when both are short.
- **Failure attribution.** Keep step names distinct so the failing half is obvious.
- **Isolation.** This is the one that bites. Jobs that ran in separate VMs may share state once merged — a database, a fixed port, a temp path, a global config. Merging two suites against one Postgres service can fail with "already exists" errors because the first suite created the schema the second one migrates. Give each consumer its own database/namespace, or keep them apart.

Verify the merge with the same before/after evidence as any other change; a consolidation that trades 30 s of queue for a 40 s serial chain is a regression.

## Sources

- GitHub secure use: https://docs.github.com/en/actions/reference/security/secure-use (accessed 2026-07-28)
- GitHub Actions Runner Controller: https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/deploy-runner-scale-sets (accessed 2026-07-28)
- GitHub limits: https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitLab runner autoscaling: https://docs.gitlab.com/runner/runner_autoscale/ (accessed 2026-07-28)
- GitLab Kubernetes executor: https://docs.gitlab.com/runner/executors/kubernetes/ (accessed 2026-07-28)
- Buildkite Elastic CI Stack: https://buildkite.com/docs/agent/self-hosted/aws/elastic-ci-stack (accessed 2026-07-28)
- Kubernetes bin packing: https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/ (accessed 2026-07-28)

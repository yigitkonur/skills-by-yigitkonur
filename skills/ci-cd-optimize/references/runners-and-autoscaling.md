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

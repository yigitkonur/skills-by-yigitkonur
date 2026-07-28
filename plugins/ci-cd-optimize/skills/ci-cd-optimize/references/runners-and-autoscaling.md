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

Use spot/preemptible runners only for short, idempotent, retryable, or
checkpointed jobs. Keep an on-demand fallback and never run the
controller/manager on spot. Do not use spot for deployment gates where an
interruption is costly.

## Capacity and contention before topology work

Parallelizing a pipeline above its effective runner ceiling often makes it look
busier and run no faster. A useful approximation is:

```text
wall-clock ≈ queue + ceil(job_count / effective_concurrency) × (per-job setup + execution)
```

That model is coarse — jobs are not really uniform — but it tells you when the
next job split is likely to re-pay setup rather than buy wall-clock.

A practical routing heuristic is **queue share**:

```text
queue share = Σ queue time / (Σ queue time + Σ execution time)
```

Measured over a representative window:

| Queue share | Read it as | Usually do this next |
|---|---|---|
| <15% | Work dominates | Normal optimization: caching, sharding, DAG shape |
| 15–35% | Mixed | Improve execution, but stop adding jobs |
| >35% | Capacity dominates | Reduce job count or raise the ceiling |

Above roughly a third, adding more jobs is often the wrong move even when the
DAG looks cleaner.

## Detect the effective ceiling empirically

Do not assume the documented plan limit equals the concurrency you actually get.
Org-wide contention, runner-class scarcity, and autoscaler warm-up often bite
first. Look for jobs created together whose `started_at` values cluster into
waves separated by about one job duration. That means the ceiling is below the
job count, even if the provider docs advertise something larger.

## Compare execution when pool state differs

If runner contention is uneven, compare **execution** for in-job changes and use
wall-clock only when the queue regime is comparable. A bigger runner can make a
CPU-bound step faster while still making the total workflow slower if its queue
is materially worse. That is not a contradiction; it is why queue and execution
must be reported separately.

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

## Sources

- GitHub secure use: https://docs.github.com/en/actions/reference/security/secure-use (accessed 2026-07-28)
- GitHub Actions Runner Controller: https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/deploy-runner-scale-sets (accessed 2026-07-28)
- GitHub limits: https://docs.github.com/en/actions/reference/limits (accessed 2026-07-28)
- GitLab runner autoscaling: https://docs.gitlab.com/runner/runner_autoscale/ (accessed 2026-07-28)
- GitLab Kubernetes executor: https://docs.gitlab.com/runner/executors/kubernetes/ (accessed 2026-07-28)
- Buildkite Elastic CI Stack: https://buildkite.com/docs/agent/self-hosted/aws/elastic-ci-stack (accessed 2026-07-28)
- Kubernetes bin packing: https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/ (accessed 2026-07-28)

# Buildkite

Use this file for Buildkite dynamic pipelines, queues, autoscaling, concurrency, and hosted/self-hosted agent decisions.

## Mental model

Buildkite Pipelines orchestrates; agents execute. Optimize both:

- orchestration: dynamic fan-out, dependencies, concurrency, priority,
- execution: queue topology, cache, images, test splitting, autoscaling.

## Dynamic pipelines

Generate only the work justified by repository evidence:

```yaml
steps:
  - label: ":typescript: compute pipeline"
    command: npx tsx .buildkite/generate-pipeline.ts | buildkite-agent pipeline upload
    agents:
      queue: default
```

Guardrails:

- Generator runs with `set -euo pipefail` or equivalent failure propagation.
- Assign stable keys to avoid duplicate jobs on retry.
- Treat generated steps as code; untrusted forks must not inject arbitrary pipeline steps or secrets.
- Keep a tiny always-on `default` queue for upload/bootstrap jobs so fan-out does not wait behind expensive workers.

## Queue topology

Use queues as workload and security boundaries:

| Queue | Purpose | Capacity |
|---|---|---|
| `default` | bootstrap/upload/orchestration | one or two tiny always-on agents |
| `linux-medium` | normal TypeScript builds/tests | autoscaled from scheduled-job depth |
| `deploy` | serialized deployment credentials/state | minimal trusted agents |
| `macos` | scarce Xcode work | explicitly budgeted |

Agent priority and warm caches matter. Agents that recently completed jobs successfully are attractive for cache locality.

## Concurrency groups

```yaml
- label: deploy production
  command: ./deploy.sh production
  concurrency: 1
  concurrency_group: deploy/production
  concurrency_method: ordered
```

Use ordered groups for serialized deployments. Use eager groups for shared test services where any ready job may take the next slot.

## Cache versus artifacts

- Cache: warm, lossy accelerator for package stores and build caches; tolerate misses.
- Artifacts: deterministic durable handoff for `dist/`, reports, and release candidates.

Do not persist an entire workspace when a targeted artifact will do.

## Autoscaling signals

Scale from scheduled-job depth and wait-time percentiles, not CPU utilization alone. Sustained waiting depth plus busy agents means undersized; idle agents plus zero waiting means oversized. Keep orchestration capacity separate from scale-to-zero workers.

## Sources

- Dynamic pipelines: https://buildkite.com/docs/pipelines/configure/dynamic-pipelines (accessed 2026-07-28)
- Queues: https://buildkite.com/docs/agent/queues (accessed 2026-07-28)
- Agent management: https://buildkite.com/docs/pipelines/best-practices/agent-management (accessed 2026-07-28)
- Concurrency: https://buildkite.com/docs/pipelines/configure/workflows/controlling-concurrency (accessed 2026-07-28)
- Caching: https://buildkite.com/docs/pipelines/best-practices/caching (accessed 2026-07-28)
- Queue metrics: https://buildkite.com/docs/pipelines/insights/queue-metrics (accessed 2026-07-28)

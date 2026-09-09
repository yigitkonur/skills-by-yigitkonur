# Device & Runtime Context Capture

How to attach operating system, memory metrics, runtime versions, and container metadata to Sentry reports.

## Standard Context Blocks

Sentry events support standard context blocks under `.contexts`:

| Block | Fields Captured |
|---|---|
| `os` | Name, version, build, kernel version |
| `runtime` | Name (node, python, go), version |
| `device` | Family, model, memory_size, free_memory, battery_level, orientation |
| `app` | app_name, app_version, app_build, app_start_time |
| `cloud_resource` | cloud.provider (aws, gcp, vercel), cloud.region |

## Manual Context Enrichment in Node.js

```typescript
import * as Sentry from '@sentry/node';
import os from 'node:os';

export function enrichDeviceContext(scope: Sentry.Scope) {
  scope.setContext('device_resources', {
    freeMemoryMB: Math.round(os.freemem() / 1024 / 1024),
    totalMemoryMB: Math.round(os.totalmem() / 1024 / 1024),
    cpuCount: os.cpus().length,
    loadAvg: os.loadavg(),
  });

  scope.setContext('process_runtime', {
    pid: process.pid,
    nodeVersion: process.version,
    uptimeSeconds: Math.round(process.uptime()),
    memoryUsageMB: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
  });
}
```

When an exception occurs during high-load conditions, these contexts immediately reveal whether memory exhaustion (OOM) or CPU saturation caused the crash.

# CI/CD & Cloud Container Optimization

## Overview

Running TypeScript verification inside containerized CI environments (GitHub Actions, Cloudflare Workers Builds, GitLab CI, Daytona sandboxes) requires understanding memory limits, process spawning, and environment variables.

## Key Invariants for CI Containers

### 1. `NODE_OPTIONS` Sanitation
When running inside CI containers with constrained RAM (e.g. 3.5 GB on Cloudflare or 7 GB on GitHub Actions):
* **Do NOT pass worker-incompatible flags**: Flags like `--v8-pool-size` or `--max-semi-space-size` cause Node worker threads (used by Next.js and Vitest) to crash with `ERR_WORKER_INVALID_EXEC_ARGV`.
* **Sanitized `NODE_OPTIONS`**:
  ```bash
  export NODE_OPTIONS="--max-old-space-size=3584"
  ```

### 2. Native Go Concurrency Control
Because Go automatically detects all available host CPUs (`GOMAXPROCS`), running inside shared VM containers with noisy neighbors or cgroup CPU limits can cause over-subscription.

Set `GOMAXPROCS` explicitly to match container CPU quotas if needed:
```bash
# In CI with 4 vCPUs:
export GOMAXPROCS=4
```

### 3. Memory Footprint Reduction
* Legacy Node.js `tsc` frequently exceeded 3.5 GB on monorepos, requiring 4 GB+ old-space limits.
* Native `tsgo` / `tsc 7.0` stays well under 500 MB RAM, completely preventing Out-Of-Memory (OOM) aborts in tight CI environments.

## CI Runner Matrix

```yaml
# GitHub Actions Example
- name: Typecheck
  run: pnpm run type-check

- name: Lint
  run: pnpm run lint

- name: Build
  run: pnpm run build
```

## Cloudflare Workers Builds Invariants
* Single shard: `CF_SHARDS=1`
* Fast native typecheck: `tsgo --noEmit` / `tsc --noEmit`
* Fullstack build: Vite SPA + Next.js Turbopack

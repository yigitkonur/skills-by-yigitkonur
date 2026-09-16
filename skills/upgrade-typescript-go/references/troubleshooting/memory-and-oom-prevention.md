# Memory Limits & OOM Crash Prevention

## Overview

One of the primary motivations for migrating to TypeScript's Go engine is eliminating V8 garbage collection heap limits and Out-Of-Memory (`JavaScript heap out of memory`) crashes.

## Comparing Memory Profiles

| Characteristic | Legacy Node.js `tsc` | Native Go `tsgo` / `tsc 7.0` |
| :--- | :--- | :--- |
| **Garbage Collector** | V8 Mark-Sweep (Single-threaded stop-the-world) | Go Concurrent GC (Low latency, thread-aware) |
| **Heap Limit Constraint** | Must configure `--max-old-space-size` | Adapts dynamically to system memory |
| **Typical Monorepo RAM** | 3.5 GB – 6.0 GB | **200 MB – 600 MB** |
| **Worker Threads** | Spawns heavy Node processes | Lightweight Goroutines |

## Common Memory Traps in Hybrid Toolchains

While the native Go compiler will not OOM, surrounding Node.js tools in the build pipeline (Next.js worker threads, Vitest workers, ESLint) can still encounter memory limits.

### 1. The `NODE_OPTIONS` Invalid Worker Flag Trap
When setting memory limits in CI:
```bash
# ❌ DANGEROUS in hybrid Node environments:
export NODE_OPTIONS="--max-old-space-size=4096 --v8-pool-size=16"
# (Node worker threads reject --v8-pool-size and abort)

# ✅ CLEAN & SAFE:
export NODE_OPTIONS="--max-old-space-size=3584"
```

### 2. Parallel Test Workers Overload
In test suites (Vitest / Jest) on high-core machines (e.g. 80 CPUs):
* Spawning 80 full Vitest workers simultaneously can saturate available RAM.
* Use `--max-workers` or `testWorkers` in local resource profile:
  ```bash
  vitest run --maxWorkers=16
  ```

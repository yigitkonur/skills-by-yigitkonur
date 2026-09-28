# Isolate Vite Dependency Cache Across Concurrent Dev and Build Instances

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

By default, Vite stores pre-bundled dependency artifacts in `node_modules/.vite`. When multiple Astro processes run simultaneously—such as parallel test suites, CI sharded builds, or multi-port dev servers for subagents and worktrees—concurrent processes read and write to the same `.vite` cache directory. This creates race conditions, lock file contention (`EBUSY` / `EPERM`), and corrupted cache manifests that crash the server with obscure module resolution errors.

## 2. How It Differs From Classic React / Next.js

Webpack and Next.js isolate cache outputs per build target or runtime under `.next/cache`. Vite's dependency optimizer defaults to a single shared folder in `node_modules/.vite/deps`. In Astro multi-instance workflows, Vite's cache directory must be explicitly partitioned per port or process ID.

## 3. Common Mistakes & Anti-Patterns

Spawning concurrent dev servers on ports `4321` and `4322` or running `astro build` while an `astro dev` server is running without isolating Vite's cache directory, causing lock collisions.

### ❌ Bad Practice / Anti-Pattern

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

export default defineConfig({
  // Relies on default Vite cache dir: node_modules/.vite
  // When another dev instance or build starts, both race for dependency optimization!
})
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'

// Resolve port or instance identifier from environment
const port = process.env.PORT || '4321'
const isDev = process.env.NODE_ENV !== 'production'

export default defineConfig({
  vite: {
    // Partition Vite pre-bundle cache per instance to prevent concurrent lock corruption
    cacheDir: isDev ? `node_modules/.vite-dev-${port}` : `node_modules/.vite-build`,
    optimizeDeps: {
      holdUntilCrawlEnd: true,
    },
  },
})
```

## 4. Verification & Audit

Run two concurrent Astro dev instances on different ports and verify separate cache directories are created without lock contention:

```bash
PORT=4321 npx astro dev --port 4321 &
PORT=4322 npx astro dev --port 4322 &
ls -d node_modules/.vite-dev-*
# Output must show separate directories: .vite-dev-4321 and .vite-dev-4322
```

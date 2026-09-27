# Audit Performance Exclusively Against Production Preview Builds, Never Dev Server

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Running Lighthouse, PageSpeed Insights, or Unlighthouse against `astro dev` produces completely invalid performance diagnostics. The Vite development server injects unbundled ES modules, client-side Hot Module Replacement (HMR) WebSocket scripts (`/@vite/client`), unminified HTML/CSS, unoptimized image endpoints, and the Astro Dev Toolbar runtime. Only `astro build` runs Rollup/esbuild tree-shaking, CSS minification, asset optimization, and dead-code elimination. Auditing `astro preview` measures the authentic production payload that end users and search engine crawlers receive.

## 2. How It Differs From Classic React / Next.js

In Next.js, `next dev` also runs with HMR and unminified React development bundles (`react-dom/development`). However, because Astro strives for zero-JS on content routes, auditing `dev` creates a severe false impression: static pages appear to execute megabytes of client JavaScript solely due to Vite's dev runtime and module graph crawler. In Astro, testing production artifacts (`dist/`) is the only way to verify true island boundaries and zero-JS execution.

## 3. Common Mistakes & Anti-Patterns

Developers run automated performance scans or CI audits against `localhost:4321` while running `pnpm dev`. This triggers false-positive warnings for Total Blocking Time (TBT), First Contentful Paint (FCP), unminified assets, and excessive DOM size caused by dev toolbar injection.

### ❌ Bad Practice / Anti-Pattern

```bash
# Auditing the unbundled development server (INCORRECT)
pnpm dev &
# Dev server running at localhost:4321 with HMR, Dev Toolbar, and unminified ESM
npx unlighthouse --site http://localhost:4321
npx lighthouse-ci collect --url http://localhost:4321
```

### ✅ Best Practice / Idiomatic

```bash
# Build static assets and audit the production preview server (CORRECT)
pnpm build
pnpm preview &
# Wait for server ready on preview port (defaults to 4321)
npx unlighthouse --site http://localhost:4321
```

## 4. Verification & Audit

Verify the preview server is serving production-grade minified assets without dev artifacts:

```bash
# Ensure curl output contains no Vite HMR or dev toolbar scripts
curl -s http://localhost:4321/ | grep -E "(@vite/client|astro/toolbar)" || echo "PASS: Clean production HTML"
```

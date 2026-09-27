# Persist Content Layer DataStore in CI/CD Runners to Enable Incremental Builds

> **Context:** Content Layer & Collections | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Astro 5's Content Layer stores normalized collection entries, content digests, and loader metadata inside the `.astro/` cache directory. When subsequent builds execute, the DataStore compares incoming content digests against cached entries; if an entry has not changed, Astro skips HTML rendering and image reprocessing. If CI/CD runners discard `.astro/` on every run, the build pipeline loses incremental cache benefits, forcing full content re-downloads and re-compilations on every commit.

## 2. How It Differs From Classic React / Next.js

In Next.js, preserving `.next/cache` is required to reuse static page artifacts across CI builds. Similarly in Astro 5, persisting the `.astro/` directory across GitHub Actions, GitLab CI, or Cloudflare Workers Builds preserves the reactive DataStore, enabling sub-second content syncs and up to 5x faster overall build speeds on large sites.

## 3. Common Mistakes & Anti-Patterns

Configuring CI actions that cache only `node_modules` or package manager stores while omitting `.astro/`. Every push triggers a cold build where custom loaders must re-query APIs and rebuild the SQLite/JSON datastores from scratch.

### ❌ Bad Practice / Anti-Pattern

```yaml
# .github/workflows/deploy.yml (Omitted .astro cache)
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: ~/.pnpm-store
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
# ❌ Missing .astro/ cache; forces complete cold build and drops Content Layer digests!
```

### ✅ Best Practice / Idiomatic

```yaml
# .github/workflows/deploy.yml (Preserving Content Layer datastore)
- name: Cache pnpm dependencies
  uses: actions/cache@v4
  with:
    path: ~/.pnpm-store
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}

- name: Cache Astro Content Layer and Vite store
  uses: actions/cache@v4
  with:
    # ✅ Cache the Content Layer DataStore and Vite transform cache
    path: |
      .astro
      node_modules/.vite
    key: ${{ runner.os }}-astro-content-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-astro-content-
```

## 4. Verification & Audit

In CI job logs, inspect the Astro build timing and digest invalidation step:

```bash
pnpm astro build --verbose
```

Verify that subsequent commits touching only a single markdown file report incremental digest hits for unchanged entries instead of full collection re-renders.

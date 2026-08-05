# Detect: build-performance-turbopack

**Corpus lineage:** build-performance-turbopack/00-overview-feature-inventory.md,
build-performance-turbopack/03-implementation-cache-migration.md,
build-performance-turbopack/05-diagnostics-slow-build-recipe.md,
build-performance-turbopack/07-pitfalls-practitioner.md,
build-performance-turbopack/08-version-lockin-seo-vercel.md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| Turbopack for `next dev` | v15.0 stable | n/a | n/a | Always applicable on any repo targeting Next.js ≥15.0. Probe: `next dev` output banner should show `(Turbopack)` unless `--webpack` is passed. |
| Turbopack for `next build` | alpha v15.3 → beta v15.5 → **stable, default for dev AND build v16.0** | n/a; opt-in flag on 15.3–15.5 | n/a | NOT APPLICABLE (still opt-in, do not assume default) if installed `next` <16.0.0 — check for an explicit `--turbopack`/`--turbo` build flag on 15.x instead of assuming it runs. BLOCKED if a `webpack()` config block or webpack-only plugin is present — resolve via the migration recipe first, never force a plugin-dependent repo onto default Turbopack. |
| `next dev --webpack` / `next build --webpack` | retained in 16.x | n/a | n/a | Always available. INFORMATIONAL if used with no adjacent comment naming the blocker (plugin, Sass function, Yarn PnP); the opt-out itself is never a finding by default. |
| top-level `turbopack` config key | v15.3; replaced `experimental.turbo` | n/a | n/a | NOT APPLICABLE pre-15.3. |
| `experimental.turbo` (legacy location) | v13.0.0–15.2.x | n/a | **Removed by v16** | REMOVE if found on an install ≥16.0.0 — probe first per `references/gating/capability-probe.md`; do not blind-delete on an install still on 15.2.x, where it is the only valid location. |
| `turbopack.rules` / `turbopack.resolveAlias` / `resolveExtensions` | stable, same floor as top-level key | top-level `turbopack` key present | n/a | NOT APPLICABLE if the repo has no webpack `resolve.alias`/loader config to port. |
| `experimental.turbopackFileSystemCacheForDev` | v15.5 experimental; **default-on v16.1** | n/a | n/a | NOT APPLICABLE if installed <15.5. On ≥16.1 the key defaults `true` — do not propose "enable" if the key is absent or already `true` on ≥16.1; absence on ≥16.1 means enabled, not missing. |
| `experimental.turbopackFileSystemCacheForBuild` | separate flag v16.0; **default-on v16.3** | n/a | n/a | On 16.0–16.2 there is no documented default-on state — probe the installed schema before assuming either default. On ≥16.3 the key defaults `true`. |
| `experimental.turbopackMemoryEviction` | v16.3 | `turbopackFileSystemCacheForDev: true`; dev-only | n/a | NOT APPLICABLE if installed <16.3 or the dev filesystem cache is disabled — this key only affects `next dev` sessions with that cache enabled. |
| `reactCompiler` | stable opt-in v16.0 | `babel-plugin-react-compiler` dependency | n/a | NOT APPLICABLE if installed <16.0.0. |
| `experimental.turbopackRustReactCompiler` | v16.3 | `reactCompiler: true` | n/a | BLOCKED if `reactCompiler` is absent or `false` — the Rust path has nothing to replace. NOT APPLICABLE if installed <16.3. |
| `typescript@^7` + `experimental.useTypeScriptCli` | v16.3 docs; `useTypeScriptCli` defaults `true` | project-local `typescript@^7` for the CLI path to matter | n/a | NOT APPLICABLE if installed <16.3. BLOCKED (`next build` exits) if TS7 is installed **and** `useTypeScriptCli: false` — TS7's JS compiler API is unavailable. |
| `productionBrowserSourceMaps` | existing, stable opt-in | n/a | n/a | Presence alone is not a finding; `true` in production without a stated stack-trace need is a cost finding, not a version gate. |
| `generateStaticParams` / `dynamicParams` | v13 / App Router | n/a | n/a | Always applicable on App Router. |
| `experimental.staticGeneration{RetryCount,MaxConcurrency,MinPagesPerWorker}` | current, experimental | n/a | n/a | Experimental, production-discouraged in current docs. Presence alone is not a finding — unjustified/undiagnosed use is (see false-positive filters). |
| Vercel Build Cache (`.next/cache` restore) | platform behavior | n/a | n/a | Applies detection only to `.github/workflows/*` or other external CI config — Vercel's own build step configures this automatically and needs no repo-side finding. |
| Turborepo Remote Cache | platform/team feature | Turborepo as the monorepo tool | n/a | NOT APPLICABLE if the repo has no `turbo.json` / is not a Turborepo monorepo. |

## Detection commands

```bash
# 1. webpack() config block or webpack-only plugin usage — blocks default Turbopack
rg -n "webpack\s*[:(]" --glob 'next.config.*' <target-repo-root>
```

```bash
# 2. legacy experimental.turbo key — dead surface on Next.js >=16
rg -n "experimental\.turbo\b" --glob 'next.config.*' <target-repo-root>
```

```bash
# 3. production source maps enabled — build-time and memory cost
rg -n "productionBrowserSourceMaps\s*:\s*true" --glob 'next.config.*' <target-repo-root>
```

```bash
# 4. generateStaticParams call sites — open -A10 and check for a bound (.slice/.filter/limit)
rg -n "generateStaticParams" -A 10 --glob 'app/**/*.{ts,tsx}' <target-repo-root>
```

```bash
# 5. CI workflow cache configuration — confirm .next/cache is a restored/saved path
rg -n "\.next/cache" --glob '.github/workflows/*.{yml,yaml}' <target-repo-root>
```

```bash
# 6. --webpack still pinned in package.json scripts
rg -n '"(dev|build)"\s*:\s*".*--webpack' --glob 'package.json' <target-repo-root>
```

```bash
# 7. Rust React Compiler flag without its prerequisite
rg -n "turbopackRustReactCompiler|reactCompiler" --glob 'next.config.*' <target-repo-root>
```

```bash
# 8. useTypeScriptCli explicitly disabled — cross-check against installed TypeScript major
rg -n "useTypeScriptCli\s*:\s*false" --glob 'next.config.*' <target-repo-root>
```

```bash
# 9. static-generation worker tuning — experimental, production-discouraged
rg -n "staticGeneration(RetryCount|MaxConcurrency|MinPagesPerWorker)" --glob 'next.config.*' <target-repo-root>
```

```bash
# 10. turbo.json existence and outputs — confirms Turborepo Remote Cache applicability
rg -n '"outputs"' --glob 'turbo.json' <target-repo-root>
```

## Domain severity rubric

- **critical**
  - `next build` exits because `typescript@^7` is installed and `useTypeScriptCli: false` — documented, immediate build failure.
  - A `webpack()` config block or a webpack-only plugin dependency exists while `next build`/`next dev` run without `--webpack` — Turbopack silently ignores the block ("Webpack is configured while Turbopack is not, which may cause problems") and plugin behavior is lost, not merely slower.

- **major**
  - `productionBrowserSourceMaps: true` shipped to production with no stated stack-trace-fidelity requirement — unconditional build-time/memory cost the docs warn about, paid on every build.
  - `generateStaticParams` returns every item from a catalog-scale data source (thousands+ rows, no `.slice`/popularity cutoff) — each prerendered route "increases build work and produces output that has to be stored and deployed."
  - A CI workflow (`.github/workflows/*`) runs `next build` with no `.next/cache` restore/save step — every build behaves like a cold build regardless of how small the change was.
  - `experimental.turbopackRustReactCompiler: true` set while `reactCompiler` is absent/`false` — the flag has nothing to accelerate; dead, ineffective config.

- **minor**
  - `experimental.turbo` present on an install ≥16.0.0 where the probe confirms it is genuinely dead (mechanical rename available, no behavior risk today).
  - `--webpack` pinned in `package.json` scripts with no adjacent comment naming the blocker — forgoes the 2–5×/10× vendor-claimed gains for an unstated or stale reason.
  - `experimental.staticGeneration*` worker-tuning keys set to values that don't trace to a prior diagnosis (no comment, no linked build-time evidence) — experimental, production-discouraged tier, tuned without justification.

- **informational**
  - Both filesystem cache flags already at their version-appropriate default (unset on ≥16.1 dev / ≥16.3 build, or explicitly `true`) — nothing to propose.
  - `--webpack` used with an adjacent comment naming a specific blocker (required plugin, custom Sass function, Yarn PnP) — correct, documented decision.
  - `generateStaticParams` already returns a bounded, popularity-ranked subset with `dynamicParams` left at its default — the documented pattern, not a gap.

## False-positive filters

- **Comments/docstrings are not live usage.** A `webpack(` or `experimental.turbo` match inside a `//` or `/* */` block, or a doc-comment explaining why the project avoided it, is not a finding.
- **Test/fixture files are excluded.** `**/*.test.{ts,tsx}`, `**/*.spec.{ts,tsx}`, `__tests__/`, `__mocks__/` — config snippets in fixtures are not production build behavior.
- **A `webpack()` callback gated behind `process.env.ANALYZE` for `@next/bundle-analyzer`'s webpack mode is not automatically a Turbopack blocker.** Bundle analyzer is typically invoked via a separate script (`ANALYZE=true next build`), not the default dev/build command — confirm the callback actually executes on the default path before filing critical severity; downgrade to informational if it is conditionally gated and documented.
- **Image optimization is never a valid slow-build cause.** Next.js optimizes images on-demand at request time, not at build time — a repo with "many images" is not evidence of a build bottleneck. Do not file a build-performance finding that attributes slow builds to image count; route that report to `image-optimization` instead if it's about runtime transformation cost.
- **`generateStaticParams` findings require the unbounded case.** A call site that already slices, filters, or otherwise bounds its return set is not a finding — only an unbounded return over a data source with unknown or catalog-scale size counts.
- **`.next/cache` in `.gitignore` is normal and not itself a finding.** The CI-cache finding is about the *workflow* never restoring/saving the directory across runs, not about whether it's tracked in git.
- **`experimental.staticGeneration*` keys copy-pasted from documentation examples inside a comment are not live usage** — confirm the match is an active config assignment, not a commented-out example.
- **Matches inside `.next/`, `node_modules/`, or other build/dependency output are not live usage** — restrict globs to `next.config.*`, `package.json`, and source directories.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/build-performance-turbopack/` must include:
- `file:line` (exact)
- literal matched text (copied from the `rg` output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (drawn from the corpus prose above)
- suggested fix recipe section name from `references/fix/build-performance-turbopack.md`
- the resolved `next` version from the capability probe — every gate row in this domain depends on it, so record it once at the top of the findings file

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Dev/build CPU or memory climbs unbounded over a long session | Dev in-memory cache without eviction, or a genuine leak in application code | Confirm `turbopackFileSystemCacheForDev` and `turbopackMemoryEviction` are enabled/`'auto'`; if memory is still high, produce a runnable reproduction | Dev memory eviction |
| `.next/dev/cache/turbopack` or `.next/cache/turbopack` grows to double-digit GB, new-page compiles slow to 30+ seconds | Persistent cache accumulating stale/duplicate entries over many sessions in medium/large repos | Delete the specific cache directory and restart; treat as a recurring maintenance step | Filesystem cache flags (dev + build) |
| "Webpack is configured while Turbopack is not, which may cause problems" | A `webpack()` block remains in `next.config.js` alongside default Turbopack usage | Remove the `webpack()` callback or port its logic into the `turbopack` config surface, or run `--webpack` explicitly | Webpack config migration |
| Alias-imported asset loses its query string inside a custom Turbopack loader (`this.resourceQuery` empty) | Turbopack drops the resource query for aliased imports specifically, not relative imports | Import by relative path when the loader depends on `resourceQuery` | Webpack config migration |
| CSS renders in an unexpected order after migrating from webpack | Webpack sometimes ignores JS-inferred order for side-effect-free files; Turbopack follows import order strictly | Force ordering with an explicit `@import` in the dependent CSS module | Webpack config migration |
| `next build` exits when TypeScript 7 is installed and `useTypeScriptCli` is `false` | TS7's JavaScript compiler API is unavailable; only the CLI path works | Keep `useTypeScriptCli` at its default `true` while on TypeScript 7 | TypeScript 7 native checker |
| Vercel build cancelled with an unclear resource message | Hard container caps: 8192MB memory / 4 CPUs / 32GB disk on the default Standard tier | Set `VERCEL_BUILD_SYSTEM_REPORT=1` for a resource report, or move to a larger machine tier only after confirming the bottleneck | Ordered slow-build diagnosis recipe |
| Build minutes suddenly far more expensive with no explicit machine-type change | Build machine defaulted to a higher tier (e.g. Turbo, 30 vCPU) — a build-pricing issue, distinct from any Fluid Compute or ISR cost driver | Confirm the current build machine assignment in Project Settings → Build and Deployment before assuming a runtime-cost cause | Vercel Build Cache and `vercel build` |

## Cross-domain interactions

1. **A misdiagnosed "Vercel cost spike" is sometimes a build-machine assignment issue, not a runtime lever.** Before routing a cost finding to `vercel-platform-deployment` (Fluid Compute, region, ISR writes), confirm the current build machine tier here first — see `references/gating/cost-model.md`.
2. **`generateStaticParams` scope reduction interacts with `rendering-strategy-caching`'s static-shell/dynamic-hole boundaries.** Coordinate before narrowing prerender scope on a live app — fewer prerendered routes is product-visible at runtime, not just a build-time change.
3. **Image optimization is never a build-performance finding.** If a repo report attributes slow builds to "many images," redirect that investigation to the `image-optimization` domain (on-demand, request-time cost) rather than filing here.

## Reference pointer

Fix recipes for this domain live in `references/fix/build-performance-turbopack.md`.

# Detect: bundle-code-splitting

**Corpus lineage:** bundle-code-splitting/00-overview-feature-inventory.md, bundle-code-splitting/03-when-to-use.md, bundle-code-splitting/07-pitfalls-anti-patterns.md, bundle-code-splitting/08-version-lockin-seo-vercel-practitioners.md

## Applicability gate

**The build output "Size" / "First Load JS" table was REMOVED from `next build` in
16.0.0.** Never instruct an agent to read that table, cite a red/yellow/green byte
threshold from a pre-16 tutorial, or treat its absence as a bug. Bundle measurement now
lives exclusively in `next experimental-analyze` (Turbopack, experimental, 16.1.0+) or
`@next/bundle-analyzer` (`--webpack` only). Probe `experimental.optimizePackageImports`,
`reactCompiler`, `experimental.turbopackRustReactCompiler`, and `serverExternalPackages`
against the installed schema per `references/gating/capability-probe.md` before proposing
any of them — do not reason from the version string alone.

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| Automatic per-route-segment code splitting (Server Components) | Core App Router behavior | none | n/a | Always applicable, default-on, nothing to configure. A finding here is never "enable this" — it is a `'use client'`-boundary finding instead. |
| `'use client'` directive / module graph boundary | Core App Router primitive | none | n/a | Always applicable. Once a file has `'use client'`, "all of its imports and the components it directly renders are included in the client bundle" — the boundary's *placement* is the finding, not its existence. |
| `next/dynamic` (`React.lazy` + `Suspense` composite) | Long-standing | none | n/a | Always applicable. The gate that matters: current docs say "when a Server Component dynamically imports a Client Component, automatic code splitting is currently not supported" — `dynamic()` must sit inside a Client Component wrapper to reliably split. |
| `ssr: false` option of `next/dynamic` | Long-standing | **Client Components only** | n/a | Always applicable as an option, but exact current error if misplaced: `"ssr: false" is not allowed with next/dynamic in Server Components. Please move it into a Client Component.` Any `ssr: false` found inside a Server Component file is a `critical` finding — it throws. |
| `loading` option of `next/dynamic` | Long-standing | incompatible with `suspense: true` | n/a | Always applicable. `{ suspense: true, loading: ... }` is invalid — current docs: "You should remove `loading` from `next/dynamic` usages, and use `<Suspense />`'s `fallback` prop." |
| Magic comments `webpackIgnore`/`turbopackIgnore`/`turbopackOptional` | Current, 16.3.0 docs | bundler-specific (webpack vs Turbopack) | n/a | Always applicable, documented. Presence is informational unless the wrong comment is paired with the active bundler (e.g. `webpackIgnore` under a Turbopack build has no effect). |
| `experimental.optimizePackageImports` | Pre-14.2 | `next.config` key | n/a — **still formally experimental** | Probe schema for presence (it is on any 16.x install). **Never describe this as stable** — the live doc page carries an explicit experimental banner ("not recommended for production") despite being de-facto production-relied-on. Flag any finding text that assumes stability as itself wrong. |
| Default-optimized package list (`lucide-react`, `date-fns`, `recharts`, MUI, etc. — 26 patterns) | Same feature | none | n/a | Always applicable — no config needed for listed packages. Re-adding a listed package to the custom array is a redundant-config finding, not a correctness issue. |
| `serverExternalPackages` | Stable since v15.0.0 | none | n/a — **renamed from `serverComponentsExternalPackages`** | `serverComponentsExternalPackages` found in config on any install → migration finding (mechanical rename). `serverExternalPackages` affects **server bundles only** — using it to justify a client-bundle-size claim is itself a finding. |
| `next experimental-analyze` | Shipped v16.1.0 | Next.js ≥16.1.0; Turbopack build | n/a — **experimental, "in early development"** | NOT APPLICABLE if installed next <16.1.0 — propose `@next/bundle-analyzer` instead, or a version-upgrade task as its own separate item. |
| `@next/bundle-analyzer` (webpack plugin) | Long-standing | `next build --webpack` | n/a | Always applicable as a devDependency; does **not** run under a Turbopack build — do not propose adding the plugin without also requiring `--webpack` in the analysis command. |
| `reactCompiler: true` | **Stable opt-in since v16.0.0** | `babel-plugin-react-compiler` installed | n/a | NOT APPLICABLE if installed next <16.0.0 (still experimental namespace pre-16). Stable ≥16.0.0 but **off by default** — absence is not itself a finding; presence with a bundle-size justification in a comment IS a finding (see rubric). |
| `reactCompiler.compilationMode: 'annotation'` + `"use memo"` | Same v16.0.0 feature | `reactCompiler` config present | n/a | Same floor as above. Annotation mode requires the `"use memo"` directive per targeted component/hook — absence of the directive on an annotation-mode repo means that component is NOT compiled, not a bug. |
| `experimental.turbopackRustReactCompiler` | Shipped experimental in 16.3.0 | `reactCompiler: true` already set | n/a | NOT APPLICABLE if installed next <16.3.0, or if `reactCompiler` is not already enabled — this flag has no independent effect without the base compiler on. |
| Turbopack tree-shaking flags (`turbopackRemoveUnusedImports`/`Exports`, `turbopackInferModuleSideEffects`, `turbopackScopeHoisting`) | Documented as of 16.3.0 | Turbopack build | n/a | Always applicable on a Turbopack build. Dev-mode defaults differ from build-mode defaults for several flags — a finding based on inspecting `next dev` output instead of a production build is invalid; see false-positive filters. |
| `server-only` / `client-only` npm packages | Long-standing pattern | none — **installation optional**, Next.js handles both internally | n/a | Always applicable; the guard works whether or not the zero-content package is installed. Absence of the import is not itself a finding — only a proven environment-poisoning risk (server secret reachable from a Client Component import chain) is. |
| Build output "Size"/"First Load JS" table | **Removed in v16.0.0** | n/a | v16.0.0 | Any documentation, script, or CI check in the repo that parses/expects this table is a `critical` finding on ≥16.0.0 — it will silently stop producing output, not error loudly. |

## Detection commands

Read-only only. Every command maps 1:1 to a gate row or a pitfall signature below.

```bash
# 1. 'use client' directives in layout/root-level files — boundary-too-high candidates
rg -n "^'use client'" --glob '{layout,template}.tsx' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 2. Overall 'use client' file count vs total tsx/jsx file count (ratio context, not a finding by itself)
rg -l "^'use client'" --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root> | wc -l
```

```bash
# 3. ssr: false usage — must confirm enclosing file is a Client Component
rg -n -B10 'ssr:\s*false' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 4. dynamic() call sites inside files that are NOT 'use client' — Server Component placement risk
rg -l 'dynamic\(' --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root> | xargs -I{} sh -c "rg -L \"^'use client'\" {} && echo {}"
```

```bash
# 5. { suspense: true, loading: ... } or { suspense: true, ssr: false } — invalid dynamic() option combinations
rg -n -U 'suspense:\s*true(?:(?!\}).)*?(loading|ssr:\s*false)' -P --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 6. serverComponentsExternalPackages — legacy key renamed in 15.0.0
rg -n 'serverComponentsExternalPackages' --glob 'next.config.*' <target-repo-root>
```

```bash
# 7. Barrel-file re-export files (index.ts with multiple export * lines) — internal barrel candidates
rg -n -c 'export \* from' --glob 'index.{ts,tsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 8. Namespace imports of large packages — defeats tree-shaking
rg -n 'import \* as \w+ from' --glob '*.{ts,tsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 9. reactCompiler config presence and mode
rg -n 'reactCompiler' -A3 --glob 'next.config.*' <target-repo-root>
```

```bash
# 10. Repo scripts/CI/docs referencing the removed Size / First Load JS build table
rg -rn 'First Load JS|next build.*Size' --glob '{package.json,*.yml,*.yaml,README*,CONTRIBUTING*}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 11. Heavy library imports (chart/editor/map/pdf) not behind a dynamic() call — lazy-loading candidates
rg -n "from ['\"](recharts|chart\.js|monaco-editor|@monaco-editor|react-pdf|mapbox-gl|leaflet)['\"]" --glob '*.{tsx,jsx}' -g '!**/node_modules/**' <target-repo-root>
```

```bash
# 12. optimizePackageImports config — check for redundant entries already on the default list
rg -n 'optimizePackageImports' -A10 --glob 'next.config.*' <target-repo-root>
```

## Domain severity rubric

- **critical** — removed API/flag in live use; architectural precondition violated; user-visible breakage likely or build/runtime failure likely
  - `ssr: false` found inside a Server Component file (`page.tsx`/`layout.tsx` without `'use client'`) — throws the exact documented error.
  - `{ suspense: true, ssr: false }` combined — `ssr: false` is silently ignored, not a build error, but produces broken/unexpected behavior.
  - A CI script, doc, or check that parses the removed `next build` Size/First Load JS table on an installed next ≥16.0.0 — the check will pass vacuously or fail opaquely, not loudly.
  - `serverExternalPackages` (or its externalized packages) used to justify a client-bundle-size reduction claim — it has zero client-bundle effect; this is a correctness/documentation error, not a style nit.
- **major** — P0-tier practice absent or misconfigured for this archetype; likely measurable CWV/UX harm
  - A large layout/page marked `'use client'` at or near the root solely because one leaf is interactive (boundary too high) — pulls static logo/footer/utility code into the client graph unnecessarily.
  - A heavy client-side library (chart, editor, map, PDF renderer) imported statically and always shipped, when it is not needed for first useful paint.
  - `dynamic(() => import('./ClientWidget'))` placed directly in a Server Component with no Client Component wrapper — current docs confirm this does not currently split; the analyzer will show the full dependency graph still present.
  - A one-line barrel (`export * from`) re-exporting 20+ internal components, consumed via the barrel path rather than direct imports, materially inflating the module graph.
- **minor** — stable opt-in not adopted; deprecated-but-still-functional surface; quality gap without current breakage
  - `serverComponentsExternalPackages` (legacy key) still in config — still parses, migrate to `serverExternalPackages`.
  - A package with hundreds of named exports imported via its barrel entry point, and not on the `optimizePackageImports` default list, with no custom config added.
  - `reactCompiler` off with an interaction-heavy client app showing profiler evidence of cascading re-renders (P1 for SaaS, P2 otherwise per archetype).
  - `next experimental-analyze` or `@next/bundle-analyzer` never run in the project's history — no bundle baseline exists to compare against.
- **informational** — intentional divergence, wrapper indirection, or a note a fixer should know, but not a task by itself
  - A high `'use client'` file count where boundaries sit correctly at leaf/island level (see false-positive filters — this is the canonical non-finding).
  - `ssr: false` correctly scoped to a genuinely browser-only widget (WebGL, DOM-selection editor).
  - `optimizePackageImports` custom entries limited to packages genuinely absent from the default list, with a comment noting why.
  - `reactCompiler: true` enabled with a comment noting it targets INP/re-renders, not bundle size.

## False-positive filters

- **A high `'use client'` count is not itself a finding if the boundaries sit at leaf/island level.** Real observed case: 254 of 587 `.tsx` files carried `'use client'`, but every layout remained a Server Component — that is a healthy architecture, not drift. Count the ratio for context only; the finding is boundary *placement* (root/layout-level directives), never the raw count.
- **`ssr: false` on a genuinely browser-only widget is correct**, not a finding — WebGL canvases, `window`-dependent editors, DOM Selection API code. The current docs frame this as the correct escape hatch: "It is not needed merely to code-split; normal dynamic imports already split and Client Components are prerendered by default." Only flag `ssr: false` when (a) it is inside a Server Component (throws) or (b) it hides genuinely indexable primary content.
- Comments/docstrings mentioning `'use client'`, `dynamic`, `ssr`, etc. do not count as live usage.
- Test files (`*.test.*`, `*.spec.*`, `__tests__/**`, `.storybook/**`) are excluded from every command above.
- **Turbopack dev-mode output is not production truth.** `turbopackRemoveUnusedImports`, `turbopackRemoveUnusedExports`, and `turbopackScopeHoisting` default to `false` in dev and `true` in build — a module visible in the dev Sources panel or dev-mode analyzer run is not proof that production tree-shaking failed. Always analyze a production build (`next experimental-analyze` or `@next/bundle-analyzer` against a real build), never dev-server output.
- **A default-optimized package re-added to a custom `optimizePackageImports` array is redundant, not broken** — `lucide-react`, `date-fns`, `recharts`, MUI, and 22 other patterns are already covered; flag as `minor`/informational cleanup, never as a correctness bug.
- **`optimizePackageImports` on a local monorepo workspace barrel behind a symlinked `node_modules` entry** is a known, currently-unresolved Turbopack gap (issue #75148) — do not treat the barrel staying unoptimized as a repo misconfiguration; the fix direction is direct imports for internal packages, not "configure it correctly."
- **`react-icons/*` appearing fully bundled in a *dev*-mode inspection** is a known dev-mode-only report (issue #70666) — confirm against a **production** analyzer run before filing; if the production graph is clean, this is not a finding.
- A `serverExternalPackages` entry for a package already on Next.js's automatically-externalized list (`@prisma/client`, `sharp`, `bcrypt`, `puppeteer`, `mongodb`, `pg`, `sqlite3`, `canvas`, `shiki`, `@aws-sdk/client-s3`, etc.) is redundant, not wrong — note as informational, don't propose removal as a required fix unless it is the sole content of an otherwise-empty finding.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/bundle-code-splitting/` must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/bundle-code-splitting.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| `"ssr: false" is not allowed with next/dynamic in Server Components. Please move it into a Client Component.` | `ssr: false` used inside `page.tsx`/`layout.tsx` (Server Component by default) | Move the `dynamic()` call into a small `'use client'` wrapper component | Lazy-load a heavy component (`loading` / `ssr: false`) |
| `ssr: false` silently has no effect | Combined with `{ suspense: true }` — React 18+ always resolves Suspense boundaries server-side, so this cannot be disabled | Write the component to render on both server and client, or drop `suspense: true` and use `loading` | Lazy-load a heavy component (`loading` / `ssr: false`) |
| Two competing fallback mechanisms rendered | `{ suspense: true, loading: ... }` set together | Remove `loading`; use `<Suspense fallback>` instead | Lazy-load a heavy component (`loading` / `ssr: false`) |
| Analyzer still shows the full Client Component subtree despite a `dynamic()` call | `dynamic()` placed in a Server Component — current docs: automatic code splitting is "currently not supported" for that placement | Move `dynamic()` into a Client Component wrapper | Lazy-load a heavy component (`loading` / `ssr: false`) |
| Analyzer route looks huge despite a working dynamic import | Experimental analyzer doesn't yet distinguish sync vs async modules at a glance | Click the module, inspect its full import chain, verify actual network loading on cold reload | Run the Bundle Analyzer (Turbopack / webpack) |
| CI/doc check expecting Size/First Load JS output finds nothing | Table removed from `next build` in v16.0.0 | Replace with `next experimental-analyze` or `@next/bundle-analyzer --webpack`; update any doc/script referencing the old table | Run the Bundle Analyzer (Turbopack / webpack) |
| `optimizePackageImports` appears to do nothing for a local workspace package | Known open Turbopack gap for symlinked local barrel packages (#75148) | Use direct imports or feature-scoped barrels for internal packages; reserve `optimizePackageImports` for real external npm packages | Barrel-file discipline for internal code |
| `react-icons/*` (or similar) bundles the whole icon pack in dev | Turbopack dev intentionally disables some build-only pruning | Re-check on a **production** analyzer run before treating as broken; if reproduced in production, use direct per-icon imports | `optimizePackageImports` config |
| Broad `'use client'` pulls logo/footer/utility code into the client graph | `'use client'` at layout/page root instead of the interactive leaf | Restore the layout/page to a Server Component; extract only the stateful leaf | Client-boundary pushdown (before/after) |
| Externalizing a package via `serverExternalPackages` is claimed to shrink client JS | The option opts a dependency out of **Server Components** bundling only, using native `require` — no client-bundle effect | Correct the client boundary/import first; use `serverExternalPackages` solely for Node/native server correctness | `serverExternalPackages` for Node-native server deps |
| `reactCompiler: true` enabled to reduce First Load JS | Compiler's goal is fewer re-renders, not fewer bytes; runtime gating mode can even increase bundle size | Measure React commit duration/INP to justify adoption, not bundle bytes; run analyzer before/after to confirm the bundle size is unchanged, as expected | Enable React Compiler + measure |
| Dev-graph module presence treated as production proof | `turbopackRemoveUnusedImports`/`Exports`/`turbopackScopeHoisting` default off in dev, on in build | Always run the production analyzer before changing architecture based on a dev-mode observation | Run the Bundle Analyzer (Turbopack / webpack) |

## Cross-domain interactions

1. If a route's `next/dynamic` boundary needs a shape-preserving loading state, coordinate
   with `image-optimization`/`micro-interactions-react19-fluidity` for CLS-safe skeleton
   sizing rather than an unbounded spinner — reserve the eventual component's dimensions.
2. Third-party npm SDKs imported into Client Components are this domain's concern
   (dynamic import / on-event import); external `<script src>` loading strategy belongs to
   `font-script-optimization` — do not conflate the two when a heavy third-party widget
   ships both an npm package and an external script tag.
3. `reactCompiler` adoption depends on `measurement-regression-guardrails` for a React
   Profiler + INP before/after baseline — never claim a compiler win without measuring the
   actual interaction, and never claim it reduced bundle bytes at all.
4. A client-boundary pushdown that moves previously client-only content to server rendering
   should be re-checked against `seo-metadata` — this is usually a positive change (content
   becomes crawlable) but confirm no client-only interactivity was accidentally lost.

## Reference pointer

Fix recipes for this domain live in `references/fix/bundle-code-splitting.md`.

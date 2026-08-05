# Fix: bundle-code-splitting

**Corpus lineage:** bundle-code-splitting/04-implementation-dynamic-boundaries.md, bundle-code-splitting/05-implementation-analysis-compiler.md, bundle-code-splitting/08-version-lockin-seo-vercel-practitioners.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs. Confirm any
config key against the installed package first — see `references/gating/capability-probe.md`.

**Read this before applying anything below:** the `next build` Size / First Load JS
console table was **removed in Next.js 16.0.0**. No recipe here instructs reading that
table for verification — every "Verify after applying" step uses
`next experimental-analyze` (Turbopack, experimental) or `@next/bundle-analyzer`
(webpack-only) instead. A repo whose own docs/scripts still reference the old table is
itself a finding — see the detect file's pitfall table.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Client-boundary pushdown (before/after) | none | fully-reversible | Broad `'use client'` at layout/page root pulling static content into the client graph |
| Lazy-load a heavy component (`loading` / `ssr: false`) | Client Component wrapper pattern | fully-reversible | Heavy chart/editor/map imported statically, or requiring browser-only APIs |
| On-event `import()` | none | fully-reversible | Dependency needed only after explicit user action (search, export, compress) |
| Server Component offload | none | fully-reversible | Client-side transform library (syntax highlight, markdown, chart data) with no browser-API requirement |
| `optimizePackageImports` config | still formally experimental | fully-reversible | Package with hundreds of named exports entering via a barrel, not on the default list |
| Barrel-file discipline for internal code | none | migration-required at repo scale | Internal `index.ts` barrel re-exporting 20+ components consumed broadly |
| `serverExternalPackages` for Node-native server deps | stable since v15.0.0 | fully-reversible | Node-native/native-binding dependency incorrectly bundled into Server Components |
| Run the Bundle Analyzer (Turbopack / webpack) | Next.js ≥16.1.0, or `next build --webpack` | n/a — analysis only | Any bundle-size question with no current baseline |
| Enable React Compiler + measure | Next.js ≥16.0.0 stable; `babel-plugin-react-compiler` | component-level-revert | Profiler shows cascading re-renders or expensive repeated calculations |
| `serverComponentsExternalPackages` → `serverExternalPackages` | Next.js ≥15.0.0 | fully-reversible | Legacy config key found |

## Client-boundary pushdown (before/after) — requires Next.js (any App Router version)

**When to apply:** `'use client'` sits at or near a layout/page root because one leaf
needs interactivity, pulling static logo/footer/utility code into the client graph.

```tsx
// app/layout.tsx — Next.js 16.3.0 — WRONG: broad client boundary
'use client'
import { useState } from 'react'
import { Logo } from './ui/logo'
import { Footer } from './ui/footer'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [query, setQuery] = useState('')
  return (
    <html lang="en">
      <body>
        <nav><Logo /><input value={query} onChange={(e) => setQuery(e.target.value)} /></nav>
        {children}
        <Footer />
      </body>
    </html>
  )
}
```

```tsx
// app/layout.tsx — Next.js 16.3.0 — Server Component; only the search control hydrates
import { Footer } from './ui/footer'
import { Logo } from './ui/logo'
import { Search } from './ui/search'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav><Logo /><Search /></nav>
        {children}
        <Footer />
      </body>
    </html>
  )
}
```

```tsx
// app/ui/search.tsx — Next.js 16.3.0 — the only Client Component
'use client'
import { useState } from 'react'

export function Search() {
  const [query, setQuery] = useState('')
  return <input aria-label="Search" value={query} onChange={(e) => setQuery(e.currentTarget.value)} />
}
```

**Why:** once a file has `'use client'`, "all of its imports and the components it
directly renders are included in the client bundle" — `Logo`/`Footer` were pulled into
client JS purely by proximity to the search input. The fix extracts only the genuinely
interactive leaf; this is a module-graph control, not a component-count contest — don't
fragment every button into its own file.

**Verify after applying:** `npx next experimental-analyze --output`, compare the `/`
**client** view before/after — `logo`, `footer`, and their dependencies disappear from
the client graph unless imported elsewhere by a Client Component; loading the page with
JavaScript disabled still renders `Logo`/`Footer`.

**Lock-in / reversibility:** fully-reversible — move `'use client'` back up and re-add
state at the parent if ever needed.

**Rollback:** restore the `'use client'` directive at the layout/page level and inline
the extracted component back into it.

## Lazy-load a heavy component (`loading` / `ssr: false`) — requires Next.js (any version); `ssr: false` is Client-Components-only

**When to apply:** a heavy client-side library (chart, editor, map SDK) is imported
statically though not needed for first paint, or a module requires a browser-only API
(`window`, WebGL, DOM Selection) and cannot execute on the server. `next/dynamic` must
live inside a Client Component for supported client code splitting and to allow
`ssr: false`.

```tsx
// app/dashboard/page.tsx — Next.js 16.3.0 — Server Component
import { RevenueChartIsland } from './revenue-chart-island'

export default async function DashboardPage() {
  const points = await getRevenuePoints()
  return (
    <main>
      <h1>Revenue</h1>
      <RevenueChartIsland points={points} />
    </main>
  )
}
```

```tsx
// app/dashboard/revenue-chart-island.tsx — Next.js 16.3.0 — Client Component
'use client'
import dynamic from 'next/dynamic'

type Point = { month: string; revenue: number }

const RevenueChart = dynamic(
  () => import('./revenue-chart').then((mod) => mod.RevenueChart),
  { loading: () => <div aria-label="Loading revenue chart" style={{ minHeight: 320, background: '#f4f4f5', borderRadius: 8 }} /> },
)

export function RevenueChartIsland({ points }: { points: Point[] }) {
  return <RevenueChart points={points} />
}
```

```tsx
// app/editor/editor-island.tsx — Next.js 16.3.0 — Client Component; browser-only module
'use client'
import dynamic from 'next/dynamic'

const BrowserEditor = dynamic(() => import('./browser-editor'), {
  ssr: false,
  loading: () => <div style={{ minHeight: 480 }}>Loading editor…</div>,
})

export function EditorIsland({ initialValue }: { initialValue: string }) {
  return <BrowserEditor initialValue={initialValue} />
}
```

**Why:** dynamic named export uses `.then((mod) => mod.RevenueChart)`, the documented
form. `loading` renders a shape-preserving placeholder while the import resolves,
avoiding CLS. `ssr: false` must live inside a Client Component — the exact current
failure if misplaced directly in a Server Component: `"ssr: false" is not allowed with
next/dynamic in Server Components. Please move it into a Client Component.` Do **not**
combine `{ suspense: true, ssr: false }` — React always resolves Suspense boundaries
server-side, so Next.js ignores `ssr: false` there; use `loading` instead. A Server
Component's own `dynamic()` import of a Client Component currently does not split —
always wrap in a Client Component as shown. `recharts` is already on Next.js's
default-optimized `optimizePackageImports` list; no extra config needed.

**Verify after applying:**
1. `npx next experimental-analyze --output` before/after; locate the library in the
   **client** view and inspect its import chain — the analyzer does not yet distinguish
   sync vs async modules at a glance, so trace the chain, don't rely on rectangle area.
2. For `ssr: false`: inspect server-rendered HTML — `<h1>` exists, editor DOM does not;
   confirm no `window is not defined` error after hydration; confirm via
   `references/gating/seo-obligations.md` that no primary/indexable content sits inside
   an `ssr: false` region.
3. On a throttled network profile, reload: the heading/parent paints before the chunk
   arrives; the placeholder holds its reserved dimensions so CLS stays near zero.

**Lock-in / reversibility:** fully-reversible — remove `dynamic()`/`ssr: false`, restore
a static import (only after confirming the component renders safely on the server).

**Rollback:** replace the `dynamic(() => import(...))` call with a direct static import.

## On-event `import()` — requires Next.js (any version)

**When to apply:** a dependency is needed only after explicit user intent — a
fuzzy-search engine after typing, a PDF export after clicking Export. Do not apply when
the action is the primary path and users trigger it immediately (prefer preload on
hover/focus, or a static import, in that case).

```tsx
// app/search/fuzzy-search.tsx — Next.js 16.3.0 — Client Component
'use client'
import { useState } from 'react'

const names = ['Ada', 'Grace', 'Linus', 'Margaret']
type Match = { item: string; score?: number }

export function FuzzySearch() {
  const [matches, setMatches] = useState<Match[]>([])

  async function handleChange(value: string) {
    if (!value) { setMatches([]); return }
    const Fuse = (await import('fuse.js')).default
    const fuse = new Fuse(names, { includeScore: true })
    setMatches(fuse.search(value))
  }

  return (
    <>
      <label htmlFor="name-search">Search names</label>
      <input id="name-search" onChange={(e) => void handleChange(e.currentTarget.value)} />
      <ul>{matches.map(({ item }) => <li key={item}>{item}</li>)}</ul>
    </>
  )
}
```

**Why:** this is the exact documented pattern (`fuse.js` via `await import()` inside the
input handler) — the module fetches "only after the user types in the search input," so
the dependency cost is paid at demonstrated intent, not by every visitor.

**Verify after applying:** with Network open and cache disabled, reload — no Fuse chunk
loads; type the first character — exactly then a new chunk arrives. If first-keypress
latency under throttling is unacceptable, preload on focus instead.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** restore `import Fuse from 'fuse.js'` as a static import.

## Server Component offload — requires Next.js (any App Router version)

**When to apply:** a client-side library exists only to transform data into UI (syntax
highlighting, markdown parsing, chart-data aggregation) with no browser-API or
interaction requirement. Stronger than `next/dynamic`: dynamic import delays the cost,
server offload deletes the transform library from the client graph entirely.

```tsx
// app/blog/[slug]/page.tsx — Next.js 16.3.0 — Server Component
import { codeToHtml } from 'shiki'

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPostSource(slug)
  const highlightedHtml = await codeToHtml(post.codeSample, { lang: 'tsx', theme: 'github-dark' })
  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
    </article>
  )
}
```

**Why:** `shiki` runs entirely on the server here — "the client will only receive the
rendered markup," so the highlighting library never enters the client bundle, unlike a
client-side Prism setup that ships and executes the highlighter in the browser. `shiki`
is already on Next.js's automatically-externalized server package list; no
`serverExternalPackages` entry is needed.

**Verify after applying:** `npx next experimental-analyze --output` confirms the
highlighting library does not appear in the **client** view for this route; rendered
HTML shows the markup with no client JS execution required; server response time is
acceptable — this trades client bytes for server CPU/latency, measure both sides.

**Lock-in / reversibility:** fully-reversible — revert to a client-side library and
Client Component rendering if server CPU/latency becomes the bottleneck.

**Rollback:** move the transform call back into a Client Component with the client-side
library.

## `optimizePackageImports` config — requires Next.js (pre-14.2+, still formally experimental)

**When to apply:** the analyzer shows a package with hundreds of named exports entering
via a barrel entry point, and it is **not already on the default-optimized list**.

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  experimental: { optimizePackageImports: ['@acme/ui-kit', 'my-icon-library'] },
}

export default nextConfig
```

Verified current default list (verbatim) — check before adding anything below, it is
redundant: `lucide-react, date-fns, lodash-es, ramda, antd, react-bootstrap, ahooks,
@ant-design/icons, @headlessui/react, @headlessui-float/react,
@heroicons/react/20/solid, @heroicons/react/24/solid, @heroicons/react/24/outline,
@visx/visx, @tremor/react, rxjs, @mui/material, @mui/icons-material, recharts,
react-use, @material-ui/core, @material-ui/icons, @tabler/icons-react, mui-core,
react-icons/*, effect, @effect/*`.

**Why:** lives under `experimental` — the docs carry a banner: "This feature is
currently experimental and subject to change, it's not recommended for production."
Despite this it has shipped since before 14.2 and is directly recommended by the
package-bundling guide — treat it as **de-facto stable in practice, formally
experimental in the docs**, and say so, never silently upgrade its tier in finding text.
**Known correctness gap:** does not reliably optimize a **local** workspace package
re-exported through a symlinked `node_modules` entry under Turbopack (issue #75148,
open). Reserve this config for genuine external npm packages; use direct imports for
internal monorepo packages instead.

**Verify after applying:** `npx next experimental-analyze --output` before/after; open
the client view, filter by package name, confirm only actually-imported modules appear.
Diff saved analyzer output directories to quantify the change.

**Lock-in / reversibility:** fully-reversible — remove the package name from the array.
Because the feature is formally experimental, keep the direct-import fallback path
documented alongside it.

**Rollback:** remove the entry; imports continue via the barrel without the rewrite.

## Barrel-file discipline for internal code — requires Next.js (any version)

**When to apply:** an internal `index.ts` barrel re-exports 20+ components, and
consumers importing one component through it pull in the whole re-exported graph.
`optimizePackageImports` does not fix your own barrels — it targets external packages.

```ts
// components/index.ts — Next.js 16.3.0 — BEFORE: re-exports 40+ components
export * from './button'
export * from './modal'
export * from './data-table' // pulls in a heavy dependency graph
```

```tsx
// app/page.tsx — Next.js 16.3.0 — consuming file
// BEFORE: imports the whole barrel for one component
import { Button } from '@/components'
// AFTER — direct import bypasses barrel evaluation
import { Button } from '@/components/button'
```

**Why:** "When you do a barrel file import, the bundler has to discover if any of the
files imported into the barrel file has side-effects... Direct imports remove this doubt
altogether." For **external** packages, prefer `optimizePackageImports` over manual
barrel avoidance; for **your own code**, prefer direct imports or feature-scoped barrels
(`@/features/billing/components`) instead of one root barrel.

**Verify after applying:** in the analyzer, confirm direct imports remove modules only
reachable through the barrel's re-export chain; compare dev Fast Refresh time for an
edit in the affected feature before/after.

**Lock-in / reversibility:** migration-required at repo scale (many imports change
across many files — do it incrementally per feature folder, not one repo-wide sweep),
though each individual file's revert is mechanical.

**Rollback:** restore the barrel re-export and revert the consuming import.

## `serverExternalPackages` for Node-native server deps — stable since v15.0.0

**When to apply:** a Server Component/Route Handler dependency uses Node.js-specific
features or native bindings that cannot be safely bundled. **Never use this to justify a
client-bundle-size reduction — server bundles only.**

```ts
// next.config.ts — Next.js 16.3.0
import type { NextConfig } from 'next'

const nextConfig: NextConfig = { serverExternalPackages: ['@acme/native-pdf-renderer'] }

export default nextConfig
```

**Why:** "If a dependency is using Node.js specific features, you can choose to opt-out
specific dependencies from the Server Components bundling and use native Node.js
`require`." Many popular Node-native packages are already externalized automatically —
do not re-declare `@prisma/client`, `sharp`, `bcrypt`, `better-sqlite3`, `puppeteer`,
`playwright`, `mongodb`, `pg`, `sqlite3`, `canvas`, `shiki`, `@aws-sdk/client-s3`. A 16.1
fix correctly resolves transitive dependencies under Turbopack without extra config.

**Verify after applying:** `next build`, then `next start` (or deploy), exercise the
route using the native dependency; confirm no bundling-related runtime error (missing
native binary, `Module not found` for a `.node` file). This is a **correctness check**,
not a bundle-size check.

**Lock-in / reversibility:** fully-reversible — remove the package name; verify server
bundling still succeeds.

**Rollback:** remove the entry; confirm the deployment runtime can still resolve the
package before removing the externalization if it was load-bearing.

## Run the Bundle Analyzer (Turbopack / webpack) — requires Next.js ≥16.1.0 for Turbopack path; any version for webpack path

**When to apply:** any bundle-size question with no current baseline, or before/after a
code-splitting change.

**Turbopack (default, requires Next.js ≥16.1.0):**

```bash
npx next experimental-analyze              # opens interactive UI; filter by route/env/type; click a module for size + import chain
npx next experimental-analyze --output     # writes .next/diagnostics/analyze instead
cp -r .next/diagnostics/analyze ./analyze-before-refactor   # copy immediately — a second run overwrites
```

| Option | Effect |
|---|---|
| `[directory]` | Directory to analyze; defaults to current directory |
| `--no-mangling` | Disables mangling (debugging only) |
| `--profile` | Enables React production profiling |
| `-o, --output` | Writes to `.next/diagnostics/analyze` without starting the server |
| `--port <port>` | Server port, default `4000` |

**Webpack (`next build --webpack` only):**

```bash
npm install @next/bundle-analyzer
```

```js
// next.config.js — Next.js 16.3.0 (webpack build)
const withBundleAnalyzer = require('@next/bundle-analyzer')({ enabled: process.env.ANALYZE === 'true' })
module.exports = withBundleAnalyzer({})
```

```bash
ANALYZE=true npm run build -- --webpack
```

**Why:** "This command doesn't produce an application build" — the Turbopack analyzer is
analysis-only; never run it as (or instead of) the deploy build. It "filter[s] bundles
by route and switch[es] between client and server views... trace[s] imports across
server-to-client component boundaries and dynamic imports" — the correct default tool
over the removed build-output table. Turbopack does not run webpack plugins — the
webpack analyzer needs `--webpack` explicitly. "The report will open three new tabs"
(client, server/nodejs, edge where relevant).

**Verify after applying:** the targeted module/route appears with its correct import
chain; save a named before/after pair rather than trusting rectangle totals alone
(current Turbopack UI does not yet distinguish sync vs async modules at a glance); for
webpack, confirm three tabs open.

**Lock-in / reversibility:** n/a for the Turbopack command (analysis-only). For the
webpack plugin: fully-reversible — remove the wrapper and dependency; no production
behavior change from having installed it (only active when `ANALYZE=true`).

**Rollback:** remove `withBundleAnalyzer(...)` wrapping and the devDependency.

## Enable React Compiler + measure — requires Next.js ≥16.0.0 stable, `babel-plugin-react-compiler`

**When to apply:** a React Profiler trace shows cascading re-renders or expensive
repeated calculations in a client-heavy app. **Do not apply this to reduce bundle size —
it is not a bundle-size lever; it can increase bundle size in gating mode and has no
official bundle-size-reduction claim in normal mode.** It optimizes re-renders and INP,
not bytes.

```bash
npm install -D babel-plugin-react-compiler
```

```ts
// next.config.ts — Next.js 16.3.0 — whole-app
const nextConfig: NextConfig = { reactCompiler: true }
```

```ts
// next.config.ts — Next.js 16.3.0 — annotation mode (bound the blast radius first)
const nextConfig: NextConfig = { reactCompiler: { compilationMode: 'annotation' } }
```

```tsx
// app/dashboard/expensive-table.tsx — Next.js 16.3.0
export default function ExpensiveTable() {
  'use memo' // component body only compiled because of this directive in annotation mode
}
```

```ts
// next.config.ts — Next.js 16.3.0 — experimental faster build path, requires reactCompiler: true already set
const nextConfig: NextConfig = { reactCompiler: true, experimental: { turbopackRustReactCompiler: true } }
```

**Why:** "The React Compiler automatically memoizes components, reducing unnecessary
re-renders with zero manual code changes" — an **update-performance** optimization,
never a bundle-size lever. "It is not enabled by default as we continue gathering build
performance data... Expect compile times in development and during builds to be higher
... as the React Compiler relies on Babel." Next.js's SWC pre-filter limits the compiler
to files with JSX/Hooks, reducing but not eliminating the cost. Annotation mode +
`"use memo"` bounds the blast radius to measured hot components before whole-app
adoption. `turbopackRustReactCompiler` has **no independent effect** without
`reactCompiler: true` already set — the reported 34%/46% cold/warm `next dev`-to-ready
improvement was measured against the Babel path on a large app (`v0`), not
compiler-off vs compiler-on.

**Verify after applying:** `next build` wall-clock time before/after (no universal
percentage exists — measure on the target CI workload); React DevTools Profiler
re-render count and commit duration for the target interaction, before/after; field or
lab INP for the same interaction; `next experimental-analyze` client bundle size is
**not** meaningfully changed — a large unexpected delta signals misconfiguration, not
the expected effect.

**Lock-in / reversibility:** component-level-revert — disabling framework-wide is a
single flag flip, but code that intentionally relied on compiler-inferred memoization
(e.g. a previously removed manual `useMemo`) needs re-audit if reverted. Adopt via
annotation mode first specifically to bound this cost.

**Rollback:** set `reactCompiler: false` (or remove the key); re-audit any component
that had manual memoization deliberately removed after the compiler was enabled.

## `serverComponentsExternalPackages` → `serverExternalPackages` — requires Next.js ≥15.0.0

**When to apply:** the legacy key was found — renamed in v15.0.0. Still parses on many
installs, but the current name should be used going forward.

```diff
 const nextConfig: NextConfig = {
-  experimental: { serverComponentsExternalPackages: ['@acme/native-pdf-renderer'] },
+  serverExternalPackages: ['@acme/native-pdf-renderer'],
 }
```

**Why / Verify / Lock-in / Rollback:** the key moved out of `experimental` as part of its
v15.0.0 stabilization/rename — a mechanical rename; the mechanism is identical under the
new name. Verify: `rg -n 'serverComponentsExternalPackages' next.config.*` returns zero
matches; `next build` compiles; the previously-externalized package's routes still
function. Fully-reversible. Rollback: rename back if targeting an install predating the
rename.

## Ordering within this domain

1. **Client-boundary pushdown first** — config-free and fully-reversible; every later
   recipe is more effective once the client graph is minimal, and a fixed boundary can
   make a later "heavy component" finding disappear entirely.
2. **Establish an analyzer baseline** before any bytes-focused change — every later
   "Verify after applying" step assumes a before-state to diff against.
3. **Apply component-level splitting** (`next/dynamic`, on-event `import()`, Server
   Component offload) next.
4. **Fix imports** (`optimizePackageImports`, barrel discipline) after splitting —
   confirm a package is not already default-optimized before adding custom config.
5. **Trial React Compiler last, and only for interaction-heavy apps** — never a
   substitute for the byte-focused steps above; annotation mode with a measured profiler
   baseline before whole-app adoption.
6. **`serverExternalPackages` is correctness-only** and can be applied independently at
   any point.

## Conflicts to watch

- Do not enable `reactCompiler: true` and report it as the reason a bundle got smaller —
  cross-check the analyzer delta; an unexpected size change signals misconfiguration.
- Do not add a package to `optimizePackageImports` that is already on the default list.
- A client-boundary pushdown and a Server Component offload can target the same file —
  apply boundary pushdown first; re-evaluate whether offload is still needed once the
  component is no longer forced client-side by an unrelated ancestor.
- `serverExternalPackages` entries must remain resolvable at runtime in the deployment
  target — narrowing or removing an entry without confirming availability is a
  correctness risk, not a pure cleanup.
- Turbopack tree-shaking flags differ between dev and build — never base a fix decision
  on a dev-mode-only observation; always confirm against a production analyzer run.

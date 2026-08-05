# Detect: micro-interactions-react19-fluidity

**Corpus lineage:** micro-interactions-react19-fluidity/00-overview-feature-inventory.md,
micro-interactions-react19-fluidity/03-when-to-use-boundaries.md,
micro-interactions-react19-fluidity/07-pitfalls-antipatterns.md,
micro-interactions-react19-fluidity/08-version-lockin-seo-vercel-practitioner.md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `useTransition` / standalone `startTransition` | React 18 | none (stable) | n/a | Always APPLICABLE — no gate needed. |
| `useOptimistic` | React 19 | React ≥19.0 | n/a | NOT APPLICABLE if the probed React version is <19.0. |
| `useDeferredValue` | React 18; `initialValue` param added React 19 | React ≥18 for base hook, ≥19 for `initialValue` | n/a | Base hook always APPLICABLE. Gate the `initialValue` argument specifically on React ≥19.0. |
| `<Activity mode>` | React 19.2 (2025-10-01) | React ≥19.2 | n/a (evolving — more modes planned) | **PROBE the installed React version first.** NOT APPLICABLE if <19.2 — do not recommend `<Activity>` on an older React, even if Next.js is 16.x. |
| `useEffectEvent` | React 19.2 (2025-10-01) | React ≥19.2 | n/a | Same gate as `<Activity>` — probe React version, NOT APPLICABLE if <19.2. Also requires an updated `eslint-plugin-react-hooks` or the linter will incorrectly insert the Effect Event into a dependency array. |
| Next.js automatic `<Activity>` route preservation | Next.js 16.0.0 | `cacheComponents: true` (probe per `references/gating/capability-probe.md`) AND React ≥19.2 bundled by the App Router | n/a | BLOCKED if `cacheComponents` probe is `absent`. This is framework-level behavior, not an app-level API call — never write app code "enabling" it beyond the `cacheComponents` flag itself. |
| `loading.tsx` | Next.js App Router 13.0.0 | none | n/a | Always APPLICABLE on any App Router project. |
| inline `<Suspense>` | React 18 / App Router 13 | none | n/a | Always APPLICABLE. |

### React version is the primary gate for this domain

Unlike `page-transitions-view-transitions` (gated on Next.js/browser), this domain's two
newest primitives — `<Activity>` and `useEffectEvent` — are gated on the **React** version,
not the Next.js version. A repo can be on Next.js 16.3.0 and still resolve an older React
pin in an unusual monorepo/hoisting setup. Probe `node_modules/react/package.json` →
`.version` per `references/gating/capability-probe.md` before recommending either API.
`unresolved` → fall back to the declared `react`/`react-dom` range in `package.json` and
stamp `confidence: version-inferred`.

## INP mechanism linkage

INP (Interaction to Next Paint) observes click/tap/keyboard latency across a page visit;
web.dev's good threshold is **≤200ms at p75**. This domain's primitives move or
deprioritize the work that causes long tasks (>50ms) to delay the next paint —
`useTransition`/`startTransition` make selected renders interruptible background work,
`useDeferredValue` lets an expensive subtree lag behind urgent input, `<Activity>` hidden
mode schedules updates after visible work. None of these primitives reduce total CPU work;
a genuinely slow synchronous computation still costs the same wall-clock time, just at
lower scheduling priority or off the critical interaction path. **Do not claim an INP
number in a finding** — this domain supplies the mechanism only; instrumentation and the
p75 measurement itself belong to `measurement-regression-guardrails` (see Cross-domain
interactions below). A finding should say "candidate for INP improvement via `<primitive>`
— verify against field/lab INP after applying," never "will improve INP by Xms."

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed.

```bash
# Expensive filtered/rendered lists with no useDeferredValue or useTransition nearby —
# candidates for INP-harming synchronous large renders
rg -n '\.filter\(|\.map\(' --glob '*.{tsx,jsx}' <target-repo-root> -l | \
  xargs -I{} sh -c 'rg -L "useDeferredValue|useTransition" {} || echo {}'

# Mutations (client fetch / Server Action calls) with no useOptimistic nearby
rg -n "await fetch\(|useActionState|formAction" --glob '*.{tsx,jsx}' <target-repo-root> -l | \
  xargs -I{} sh -c 'rg -L "useOptimistic" {} || echo {}'

# Route segments with slow/async data and no loading.tsx sibling
rg -n 'async function.*Page|export default async function' --glob 'page.{tsx,jsx}' \
  <target-repo-root>
# then check each matching directory for a sibling loading.tsx

# useEffect cleanup that plausibly assumes route unmount (dropdown/dialog/timer patterns)
# — an audit signal, not a definitive finding; pair with the cacheComponents probe
rg -n 'useEffect\(' -A 8 --glob '*.{tsx,jsx}' <target-repo-root> | \
  rg -n 'setIsOpen\(false\)|clearInterval|clearTimeout|\.pause\(\)|disconnect\(\)'

# Direct <Activity> usage already present — inventory before proposing new adoption
rg -n '<Activity\b|import \{[^}]*Activity[^}]*\} from .react.' \
  --glob '*.{tsx,jsx}' <target-repo-root>

# useEffectEvent usage — confirm eslint-plugin-react-hooks version supports it
rg -n 'useEffectEvent' --glob '*.{ts,tsx}' <target-repo-root>
rg -n '"eslint-plugin-react-hooks"' --glob 'package.json' <target-repo-root>

# Spinner-only loading states where a skeleton would fit better (heuristic: a loading
# component with no dimension/layout hints)
rg -n 'Spinner|Loading\.\.\.|<CircularProgress' --glob '*.{tsx,jsx}' <target-repo-root>

# Duplicate-DOM-sensitive E2E selectors — risk once cacheComponents/Activity is adopted
rg -n 'page\.click\(|page\.locator\(|getByTestId\(|getByText\(' \
  --glob '*.{spec,test}.{ts,tsx}' <target-repo-root>

# cacheComponents probe cross-check (this domain's automatic-Activity gate)
rg -n 'cacheComponents' --glob 'next.config.*' <target-repo-root>

# React version declared vs installed — feeds the React-version gate above
rg -n '"react":\s*"' --glob 'package.json' <target-repo-root>

# useRef-latest-value workaround — a useEffectEvent adoption candidate once React >=19.2
# is confirmed (pattern: a ref synced in one Effect and read inside another's handler)
rg -n 'useRef\(' -A 5 --glob '*.{tsx,jsx}' <target-repo-root> | rg -n '\.current\s*='
```

## Domain severity rubric

- **critical** — a repo enables `cacheComponents: true` (and therefore inherits automatic
  `<Activity>` route preservation) with confirmed unmount-dependent logic still in place
  (open dropdowns that never close, dialog init Effects that never re-run) — this is a
  correctness break, not a quality gap; `<Activity>`/`useEffectEvent` used while the
  probed React version is <19.2 (will not build/run).
- **major** — an expensive, unmemoized filtered list with no `useDeferredValue`/
  `useTransition` on a route with a real dataset size (measurable INP harm likely); a
  mutation with no optimistic UI on a user-facing action where the round-trip is
  noticeable; a slow route with no `loading.tsx` and no inline `<Suspense>` (blank screen
  or frozen-feeling navigation).
- **minor** — `useDeferredValue` used without pairing the consumer in `memo` (present but
  ineffective); a spinner used where a skeleton would better communicate structure for a
  predictable-layout region; `useEffectEvent` opportunity present (stale-closure-prone
  `useRef` latest-value workaround) but not yet adopted.
- **informational** — a repo deliberately keeps a route uncached/dynamic and accepts
  synchronous rendering because the dataset is small enough that no primitive would move
  the needle; a hidden-tab pattern implemented with plain conditional rendering + CSS
  instead of `<Activity>` because state-loss on hide is the desired behavior.

## False-positive filters

- Comments/docstrings mentioning `useTransition`, `useOptimistic`, `<Activity>`, etc. do
  not count as live usage.
- Test/fixture files (`*.test.tsx`, `*.spec.tsx`, `__tests__/`) are excluded from
  live-usage findings but are useful evidence for the E2E-selector pitfall.
- A `useEffect` cleanup calling `clearTimeout`/`clearInterval`/`.pause()` is only a
  route-unmount-assumption risk if `cacheComponents` probes `present` — on a repo without
  Cache Components, routes still fully unmount on navigation and this pattern is correct
  as-is; do not flag it as a risk in that case.
- A spinner used for an operation scoped to a single small control (a button's own pending
  state) is not a skeleton-candidate — the corpus explicitly recommends spinners/compact
  pending labels for single-control operations with unpredictable final geometry; only flag
  spinner-for-skeleton when the loading region is a page/card-level area with a predictable
  final layout.
- `useDeferredValue`/`useTransition` absence on a list that is already small (roughly under
  a few hundred rows, or already server-filtered) is not automatically a finding — cluster
  by measured or plausible dataset size, not by the mere presence of `.filter()`/`.map()`.
- `<Activity>` findings limited to Next.js's automatic route preservation (triggered solely
  by `cacheComponents: true`) are a framework-behavior note, not an app-level adoption
  finding — do not suggest the app "add `<Activity>`" when the real gap is an unmount-
  assumption audit for the automatic behavior already in effect.

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under
`findings/micro-interactions-react19-fluidity/` must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/micro-interactions-react19-fluidity.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| A Transition-wrapped `setState` on a controlled text input does nothing | Wrapping the state that directly controls an `<input value>` in `startTransition` — React documents this as unsupported | Keep the input's own state urgent (outside the Transition); pass a Transition-wrapped or `useDeferredValue`-derived value to the expensive consumer only | `useTransition` search/filter |
| A `set` call after `await` inside an async Action isn't treated as a Transition | Missing a second `startTransition` wrapper around the post-await state update | Wrap the post-await `set` call in its own nested `startTransition` | `useOptimistic` list mutation |
| Rapid overlapping async Transitions resolve out of order | Multiple in-flight async Transitions with no request ordering | Use `useActionState`/form Actions for automatic sequencing, or explicit request IDs/`AbortController` | `useOptimistic` list mutation |
| Optimistic UI shows a permanent ghost row | Temporary entry's ID never reconciles with the confirmed server record, or the error path never clears it | Always branch success/failure explicitly; on success replace with the server record, on failure clear the optimistic entry and show an error affordance | `useOptimistic` list mutation |
| `useDeferredValue` has no visible effect | The consumer isn't wrapped in `memo`, so it rerenders synchronously with the parent regardless of the deferred value | Wrap the expensive child in `memo`; confirm in the Profiler its render is skipped/delayed relative to the urgent pass | `useDeferredValue` expensive list |
| Dropdown/menu stays open after navigating back (Activity-preserved routes) | Transient `isOpen` state is ordinary component state, so Activity preserves it across hidden/visible like any other state | Close transient UI in a `useLayoutEffect` cleanup that runs when the component is hidden | Unmount-assumption audit |
| Dialog's mount-time Effect (e.g., autofocus) does not re-run on reopen | `isDialogOpen` was already `true` when the route was hidden; the dependent Effect never sees a change | Derive `isDialogOpen` from something outside preserved state, such as a URL search parameter | Unmount-assumption audit |
| E2E test clicks/asserts against a hidden but still-present element | Hidden `<Activity>` content has `display:none` but remains in the DOM; naive selectors match it | Use visibility-aware queries (`getByRole`, `{ visible: true }`) since the accessibility tree excludes hidden elements | Unmount-assumption audit |
| Route-scoped global styles leak into the visible route while hidden | Page-level CSS variables/z-index/global classes from a hidden-but-preserved route still apply | Toggle the hidden route's `<style>` element `media` attribute to `'not all'` when hidden | Unmount-assumption audit |
| A hidden Activity subtree silently consumes memory/CPU for minutes before crashing the tab | An accidental infinite/recursive component tree renders at low priority without effects or DOM commits, masking the bug while the visible UI stays responsive | Do not treat "UI still feels fine" as evidence a hidden subtree is correct; add automated recursion/render-bound tests for any component behind Activity | Direct `<Activity>` hidden tab |
| Two cached component instances (hidden + visible) coexist and break a module-level singleton assumption | Pre-existing code assumed exactly one mounted instance of a component at a time; Activity makes this assumption visible, not the cause | Audit module-level mutable state and Effects for single-instance assumptions before/when enabling `cacheComponents` | Unmount-assumption audit |

## Cross-domain interactions

1. **INP measurement is owned elsewhere.** This domain supplies the mechanism
   (`useTransition`, `useDeferredValue`, etc.) that can move the INP ≤200ms p75 field
   threshold; the measurement/instrumentation itself belongs to
   `measurement-regression-guardrails`. Never claim an INP improvement in a finding without
   pointing to that domain's instrumentation as the verification path.
2. **`cacheComponents` is a hard prerequisite for automatic `<Activity>`.** If the
   capability probe returns `absent` for `cacheComponents`, skip every automatic-Activity
   finding entirely — downgrade to NOT APPLICABLE, not a lower severity.
3. **Do not conflate this domain's `useTransition` with `page-transitions-view-transitions`'s
   `<ViewTransition>`.** `useTransition` is a scheduler/pending-state hook; `<ViewTransition>`
   animates visual snapshots. A finding recommending one must not imply it substitutes for
   the other — see `references/gating/conflicts.md` for where they legitimately compose.
4. **Server Actions, `useActionState`, and cache invalidation (`updateTag`,
   `revalidatePath`) belong to `data-fetching-patterns`.** This domain owns only the
   immediate UI feel and rollback affordance of `useOptimistic` — do not write findings
   about Server Function signatures or revalidation from this domain's fix file.

## Reference pointer

Fix recipes for this domain live in `references/fix/micro-interactions-react19-fluidity.md`.

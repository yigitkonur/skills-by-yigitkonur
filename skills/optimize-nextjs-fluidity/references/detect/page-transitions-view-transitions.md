# Detect: page-transitions-view-transitions

**Corpus lineage:** page-transitions-view-transitions/00-overview-feature-inventory.md,
page-transitions-view-transitions/03-when-to-use.md,
page-transitions-view-transitions/07-pitfalls-anti-patterns.md,
page-transitions-view-transitions/08-version-lockin-seo-vercel-practitioner.md

## Applicability gate

| Feature / config key | Introduced | Requires | Removed-in | Gate rule |
|---|---|---|---|---|
| `import { ViewTransition } from 'react'` | React canary via App Router, zero-config | Next.js App Router, any 16.x | n/a (canary-channel, no removal date) | APPLICABLE on any 16.x repo. No flag needed — do not gate this on `experimental.viewTransition`. |
| `experimental.viewTransition` (next.config) | 15.x | — | Recorded removed in the 16 line | **PROBE FIRST — see "The trickiest gate" below.** Never blind-delete. |
| `unstable_ViewTransition` import alias | 15.x | — | Superseded by plain `ViewTransition` | REMOVE if found — mechanical rename, always safe regardless of probe result (the import alias itself 404s in 16.x `react` types independent of the config flag). |
| `<Link transitionTypes>` | Next.js `v16.2.0` | Next.js ≥16.2.0 | n/a | NOT APPLICABLE (installed version <16.2.0) → route to the manual `startTransition` + `addTransitionType` pattern instead. BLOCKED if a repo already uses `transitionTypes` on Next.js <16.2.0 — flag as a version floor violation, not a style issue. |
| `router.push/replace({ transitionTypes })` | mirrors Link's 16.2.0 addition | Next.js ≥16.2.0 | n/a | Same rule as `<Link transitionTypes>`. |
| `addTransitionType` | React canary (bundled by Next.js App Router) | Next.js App Router | n/a | APPLICABLE on any 16.x repo; no separate flag. |
| CSS `::view-transition-*` pseudo-elements | Browser-native (Chrome 111+ base) | none — pure CSS | n/a | Always APPLICABLE; not gated on any package version. |

### The trickiest gate: `experimental.viewTransition`

The version graveyard (`references/gating/version-matrix.md`) records this flag as
**Tier 4 — removed/superseded**, 404ing on current Next.js docs. But a real 16.2.9 install
probed during this skill's design still carried the key in its config schema, **and the
project had it deliberately set to `true`** (`references/gating/capability-probe.md`,
worked example). Blind removal on the graveyard alone is a breaking change on that install.

**The rule, stated explicitly, no exceptions:**

1. Run the capability probe (`references/gating/capability-probe.md`) against
   `node_modules/next/dist/server/config-schema.js` for the key `viewTransition` under
   `experimental`.
2. **`present`** — the installed schema still accepts the key. Do **not** emit a removal
   task. At most emit one `minor`, `informational`-adjacent task: "flag slated for
   removal per the 16.x docs graveyard; re-check when upgrading to ≥16.3." No code change
   is proposed by this task.
3. **`absent`** while the repo's `next.config.*` still sets `experimental.viewTransition`
   — now removal is correct. Emit a `critical`-or-`major` finding (config validation may
   throw at build) recommending deletion of the key, severity depends on whether it
   currently breaks the build (`next build`/`next dev` config validation) or is silently
   ignored — verify by running the config through the installed Next.js, not by reading
   the schema alone.
4. **`unresolved`** (no `node_modules`, unusual hoisting) — fall back to version
   comparison against the declared `next` version in `package.json`, and stamp
   `confidence: version-inferred` on the finding per `references/gating/capability-probe.md`.

Never skip step 1. A version-only gate ("this repo declares next ^16.x, so the flag is
gone") is exactly the failure mode `references/gating/capability-probe.md` names as
mistake #2 in "Why version arithmetic is not enough."

## Detection commands

Read-only only. Prefer `rg`; fall back to `grep -rn` if needed.

```bash
# Legacy 15.x import alias — always a removal candidate regardless of probe result
rg -n 'unstable_ViewTransition' --glob '*.{ts,tsx,js,jsx}' <target-repo-root>

# experimental.viewTransition in next.config — feeds the probe-gated rule above
rg -n 'viewTransition' --glob 'next.config.*' <target-repo-root>

# Live <ViewTransition> usage — inventory before recommending patterns
rg -n "<ViewTransition\b|from 'react'.*ViewTransition|ViewTransition.*from 'react'" \
  --glob '*.{tsx,jsx}' <target-repo-root>

# addTransitionType usage — confirms typed-transition adoption already in progress
rg -n 'addTransitionType' --glob '*.{ts,tsx,js,jsx}' <target-repo-root>

# <Link transitionTypes> usage — cross-check against the installed Next.js version floor
rg -n 'transitionTypes' --glob '*.{tsx,jsx}' <target-repo-root>

# prefers-reduced-motion guard — confirm the accessibility floor exists wherever
# ::view-transition-* animations are defined
rg -n 'prefers-reduced-motion' --glob '*.{css,scss}' <target-repo-root>

# ::view-transition-* CSS customization already present — inventory before proposing new CSS
rg -n '::view-transition' --glob '*.{css,scss}' <target-repo-root>

# Third-party route-transition libraries — may indicate a migration-off candidate or a
# gesture/physics need View Transitions cannot cover (see conflicts.md)
rg -n "from 'framer-motion'|from 'motion'|from 'motion/react'|AnimatePresence|gsap" \
  --glob '*.{ts,tsx,js,jsx}' <target-repo-root>

# Duplicate/non-unique view-transition-name literal — common silent-no-morph cause
rg -n "viewTransitionName:\s*['\"][a-zA-Z-]+['\"]" --glob '*.{tsx,jsx}' <target-repo-root>

# Layout-level ViewTransition wrapping {children} — breaks nested page-level enter/exit
rg -n '<ViewTransition' --glob 'layout.{tsx,jsx}' <target-repo-root>

# Manual document.startViewTransition() calls — the raw browser API; flag only if it
# coexists with React's <ViewTransition> in the same tree (see false-positive filter below)
rg -n 'document\.startViewTransition' --glob '*.{ts,tsx,js,jsx}' <target-repo-root>
```

## Domain severity rubric

- **critical** — `experimental.viewTransition` set while the probe returns `absent`
  (config validation throws at build/dev); a layout-level `<ViewTransition>` wrapping
  `{children}` that silently kills every nested page-level transition in production.
- **major** — `<Link transitionTypes>` used below the Next.js 16.2.0 floor; a
  shared-element morph pattern implemented on a route whose destination data is not
  cache-hot (the "smooth but wrong" conflict, see below) with no fallback plan; missing
  `prefers-reduced-motion` guard on a repo that ships directional slides; a third-party
  route-transition library still fully wired for cases the four native patterns already
  cover, indicating a stale migration that was never finished.
- **minor** — `experimental.viewTransition` present-and-set but probe confirms it is
  still accepted (informational re-check note only, not a removal); `unstable_ViewTransition`
  legacy import found (mechanical, low-risk rename); duplicate `view-transition-name`
  literal risk without confirmed duplication; missing `::view-transition { pointer-events:
  none; }` interactivity guard.
- **informational** — a repo has deliberately not adopted View Transitions at all (valid,
  zero-config means zero cost to skip); a third-party animation library retained
  specifically for gesture/physics interactions View Transitions cannot do (per
  `06-tradeoffs.md`, this is a legitimate scoped-down coexistence, not a migration target).

## False-positive filters

- Comments/docstrings containing `unstable_ViewTransition` or `viewTransition` as prose do
  not count as live usage — only real `import`/`require` statements and `next.config.*`
  key assignments count.
- Test/fixture files (`*.test.tsx`, `*.spec.tsx`, `__tests__/`, `e2e/`) are excluded from
  live-usage findings but may still surface useful evidence of intended patterns.
- `::view-transition` selectors inside a CSS file that is never imported/loaded by any
  route (a dead stylesheet) are informational only, not a live-usage finding.
- A `viewTransitionName` CSS property value that is dynamically templated
  (`` `photo-${id}` ``) is not a duplicate-name risk by itself — only a **literal, static**
  name shared across multiple simultaneously-rendered elements is the real risk; static
  analysis can only flag the literal-name case, not prove runtime duplication.
- A repo using `document.startViewTransition()` directly (the raw browser API, not
  React's `<ViewTransition>`) is a **different, out-of-scope mechanism** shared with
  `dark-light-theme-switching`/`instant-i18n-locale-switching` — do not flag it as a
  page-transitions-view-transitions finding unless it is mixed with `<ViewTransition>` in
  the same tree (see pitfall row below).

## Evidence format — what each finding file must contain

Every finding the audit subagent writes under `findings/page-transitions-view-transitions/`
must include:
- `file:line` (exact)
- literal matched text (copied from rg/grep output)
- which gate row or pitfall signature it maps to
- severity
- one-line why-this-matters (verbatim or near-verbatim from the corpus-derived prose below)
- suggested fix recipe section name from `references/fix/page-transitions-view-transitions.md`

## Pitfall signatures

| Failure signature | Cause | Fix direction | Recipe section |
|---|---|---|---|
| Navigation happens instantly with no animation, no console error | Two elements share one literal `view-transition-name` — browser skips the transition | Template `name` with a unique per-item identifier | Shared-element list→detail morph |
| A named pair's own morph silently stops working after adding `default="none"` | `default="none"` without an explicit `share` on the same element | Always pair `default="none"` with an explicit `share`/`enter`/`exit` | Shared-element list→detail morph |
| Page-level enter/exit stops animating after a layout wrapper was added | Nested `<ViewTransition>` inside a parent VT never fires its own enter/exit | Remove the layout-level VT; wrap `page.tsx` files only | Directional/typed transition |
| Prod shows the Suspense skeleton mid-transition instead of the morphed destination; works locally | Destination content suspends into a fallback instead of committing in the same navigation commit (uncached data) | Cache the destination's data fetch (`use cache`/`cache()`) — cross-domain fix, not a VT-layer change | Cross-domain — see "smooth but wrong" below |
| Clicks/taps during a transition appear unresponsive | `::view-transition` overlay captures pointer events by default | `::view-transition { pointer-events: none; }` | CSS `::view-transition-*` customization |
| Identical code animates in Chrome/Safari, cuts instantly in Firefox, no console error | Confirmed open React-integration bug (facebook/react#34952), not a caniuse gap | Test explicitly in Firefox before shipping; treat as progressive enhancement | (see "Browser support" in this file) |
| Same-route dynamic-segment navigation doesn't trigger enter/exit reliably | Router swaps subtrees keyed by segment value rather than unmount/mount | Use `key={slug}` + `name` + `share="auto"` | Same-route crossfade (tabs, dynamic segments) |
| A type-keyed `share`/CSS pair works from one entry point but not another | A plain (untyped) `<Link>` resolves the share map's `default`, which is `none` | Every `<Link>` between the two views must carry the same `transitionTypes` | Directional/typed transition |
| Browser back button navigation never plays the directional slide | Browser-initiated back navigations don't carry a transition type — this is expected, not a bug | Design the `default: 'none'` fallback deliberately; the shared-element morph still fires if `name`s match | Directional/typed transition |

## Browser support — progressive enhancement, not a correctness gate

React's `<ViewTransition>` uses the browser's **same-document** View Transitions
mechanism (Chrome/Edge 111+, Firefox 144+, Safari 18.0+ — global usage ~88%), which is
materially ahead of **cross-document** (native multi-page-app) support (Firefox: disabled
by default on some recent versions, partial on others; not this pack's mechanism unless a
repo mixes MPA sections). A repo relying on `document.startViewTransition()` directly for
cross-document transitions is on a different, weaker-supported surface — do not assume
same-document support numbers apply to it.

Raw caniuse availability does not guarantee parity in React's own integration layer: a
confirmed, still-open Firefox rendering bug (facebook/react#34952, filed against React
19.2) makes transitions silently not animate in Firefox with no console error, despite
caniuse reporting Firefox 144+ as supported. Treat "supported per caniuse" and "verified
working in React's integration" as two separate claims — a finding recommending View
Transitions adoption should note that Firefox needs explicit manual testing, not an
assumption of parity with Chrome/Safari.

Without browser support (or when the Firefox bug is hit), navigation completes normally
with no animation — this is confirmed degraded-but-functional behavior, never breakage. A
finding must never describe missing animation alone as a "bug" without first confirming
the target browser/version actually supports the same-document API.

## Cross-domain interactions

1. **"Smooth but wrong" — availability precedes choreography.** A shared-element morph or
   Suspense-reveal into a route whose data isn't cache-hot animates into the loading
   fallback, not the destination. If a `rendering-strategy-caching` or
   `navigation-prefetching` finding exists for the same route, treat those as `Depends on`
   prerequisites for any View Transitions task on that route. See
   `references/gating/conflicts.md` §1 for the full rule and verification steps (test both
   a warmed/prefetched route and a forced-cold route).
2. **`micro-interactions-react19-fluidity` composes, does not conflict.** `<Activity>`'s
   automatic nav-state preservation (when `cacheComponents` is enabled) and
   `<ViewTransition>` are independent React 19.2-era primitives that can coexist in the
   same layout/page pair without special handling — do not conflate `useTransition`
   (scheduling) with `<ViewTransition>` (visual choreography) in a finding.
3. **Browser-support reality is a shipping gate, not a style note** — see
   `references/gating/conflicts.md` §8. Never let animation be the sole signal of
   navigation completion; navigation must succeed identically whether or not the browser
   animates it.

## Reference pointer

Fix recipes for this domain live in `references/fix/page-transitions-view-transitions.md`.

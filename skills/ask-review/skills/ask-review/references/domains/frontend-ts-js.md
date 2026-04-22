# Frontend TypeScript / JavaScript Review

Author-side checklist for PRs that touch client-side TS/JS — React/Vue/Svelte/Solid components, state management, client data fetching, framework routes. Use when classifying the diff's domain as **frontend** in SKILL.md Step 4.

## What frontend reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Type safety** | Implicit `any` / loose unions silently break at runtime | `tsc --noEmit` passes; no `as` casts without explanation |
| **Render correctness** | Stale closures, missing deps in `useEffect`, leaked subscriptions | Exhaustive-deps lint passes; cleanup on unmount |
| **Bundle cost** | A new import can ship 200kB to every user | Bundle-size impact checked; no accidental server-package imports |
| **State lifecycle** | Where state lives, who owns it, when it resets | Clear ownership; no duplicated source of truth |
| **Error + empty + loading states** | Each route has four states, not one | All four covered; no silent spinners forever |
| **Accessibility** | Keyboard, screen reader, focus management | Labels on inputs, focus trap on modals, visible focus ring |
| **Async cancellation** | Switching routes mid-fetch leaks promises | AbortController or query library that handles it |
| **Form validation boundary** | Client validation is UX, server validation is trust | Both, with consistent error shapes |

## Weaknesses the author should pre-empt

- **useEffect dependency drift.** Is the dep array accurate? Run `pnpm lint` with `react-hooks/exhaustive-deps` and paste the result.
- **Event handler identity churn.** If you passed a new function every render to a memoized child, the memoization does nothing. `useCallback` where it matters; explain when you chose not to.
- **Server-client data mismatch.** If the component hydrates from SSR, does the initial render match the server? Mismatches cause flicker and hydration errors.
- **Loading + error fallback.** What does the UI show during the first fetch? What if the fetch fails? What if it succeeds with empty data?
- **Focus management on navigation.** When the route changes, where does focus go? Keyboard users depend on this.
- **Client-only code in SSR path.** `window`, `document`, `localStorage` crash during SSR. Guard with `typeof window !== 'undefined'` or a framework-specific `useIsomorphicLayoutEffect`.
- **Tree-shaking.** Did you import the whole library (`import _ from 'lodash'`) or just the function (`import debounce from 'lodash/debounce'`)? Ship size depends on this.
- **Dark mode / theme.** New component — does it respect the theme tokens, or did you hardcode `text-gray-900`?

## Questions to ask the reviewer explicitly

- "The `useMemo` on L42 guards against a re-sort of a 500-element list. Is the trade-off (memo overhead vs. sort cost) worth it at this size, or am I over-optimizing?"
- "I handled the error state with a toast instead of a block-level error. Preferred pattern in this codebase?"
- "The new `<Tabs>` component uses `role='tablist'` but keyboard arrow-key navigation is manual. Is this enough for a11y, or do we need a tested pattern?"
- "Bundle impact of this new import: +18kB gzipped (confirmed with `pnpm build`). Acceptable or should we lazy-load?"
- "Switched from Zustand to TanStack Query for server state — existing stores stay. Is the split okay, or should we migrate everything?"

## What to verify before opening the PR

- [ ] `tsc --noEmit` passes
- [ ] Lint passes (especially `react-hooks/exhaustive-deps` for React)
- [ ] Dev build runs without console errors/warnings on the changed route
- [ ] Production build succeeds
- [ ] Bundle size delta checked (`pnpm build` output; or build stats plugin)
- [ ] Keyboard-only walkthrough of the new interaction
- [ ] Empty-state, loading-state, error-state all exercised manually
- [ ] If SSR: reload the page, confirm no hydration warning in console

## Signals the review is off-track

- "TypeScript is complaining, I'll cast it." → Don't cast without reading the error. Usually the cast hides a real bug.
- "The loading spinner is fine as a fallback." → What about error? What about empty?
- "I'll optimize the re-renders later." → Either ship it or optimize. Not "later" — re-render bugs become flaky Playwright tests.
- "A11y is a follow-up." → Keyboard trap on a modal breaks for real users today.

## When to split the PR

- A component change + a data-layer change + a route change in one PR → split
- New feature + refactor of unrelated code → split
- >25 component files in one PR → usually too many

## Framework-specific flags (brief)

| Framework | Watch for |
|---|---|
| Next.js | Server vs. client component split; `"use client"` placement; dynamic imports for heavy client-only code |
| Vue | `ref` vs. `reactive` choice; `watch` vs. `watchEffect`; Composition API vs. Options API consistency |
| Svelte | Reactivity via `$:` vs. stores; runes (Svelte 5) migration state |
| Solid | Fine-grained reactivity — no `useState` equivalents; signals and `createEffect` |
| React Native | Platform differences (iOS vs. Android); `FlatList` vs. `ScrollView` at scale |

If the project uses framework-specific skills (e.g., `build-mcp-use-apps-widgets`), route additionally to those for framework details.

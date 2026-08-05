# Fix: micro-interactions-react19-fluidity

**Corpus lineage:** micro-interactions-react19-fluidity/04-implementation-transitions-deferred-optimistic.md,
micro-interactions-react19-fluidity/05-implementation-activity-loading-effects.md,
micro-interactions-react19-fluidity/08-version-lockin-seo-vercel-practitioner.md

**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 and React 19.2 docs.
Confirm the installed React version against `references/gating/capability-probe.md` before
applying any `<Activity>` or `useEffectEvent` recipe — both require React ≥19.2, a
stricter gate than the Next.js version alone guarantees.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| `useTransition` search/filter | React 18+ | fully-reversible | Controlled input drives an expensive render; typing feels blocked |
| `useDeferredValue` expensive list | React 18+ (`initialValue` needs React 19+) | fully-reversible | Value arrives via props/custom Hook; caller doesn't own the setter |
| `useOptimistic` list mutation | React 19+ | fully-reversible | Predictable-success mutation makes users wait for a "dead click" |
| Direct `<Activity>` hidden tab | React ≥19.2 | component-level-revert | Tabs/panels should preserve state/Effects while hidden |
| `useEffectEvent` | React ≥19.2, updated eslint-plugin-react-hooks | component-level-revert | Effect subscribes on one value but must read another value fresh |
| `loading.tsx` + inline Suspense pair | Next.js App Router 13+ | fully-reversible | Route blocks blank/frozen with no meaningful loading UI |
| Unmount-assumption audit/cleanup | `cacheComponents: true` (probe first) | fully-reversible per fix | Enabling or already on Cache Components |

## `useTransition` search/filter — requires React ≥18

**When to apply:** a controlled search/filter input drives an expensive render and
keystrokes feel delayed because the render blocks the next paint.

```tsx
// app/catalog/product-search.tsx — Next.js 16.3.0
'use client'

import { useMemo, useState, useTransition } from 'react'

type Product = { id: string; name: string }

export function ProductSearch({ products }: { products: Product[] }) {
  const [input, setInput] = useState('')
  const [filter, setFilter] = useState('')
  const [isPending, startTransition] = useTransition()

  const visibleProducts = useMemo(() => {
    const normalized = filter.trim().toLowerCase()
    if (!normalized) return products
    return products.filter((p) => p.name.toLowerCase().includes(normalized))
  }, [filter, products])

  function handleChange(nextValue: string) {
    setInput(nextValue) // urgent: controls what the user is typing
    startTransition(() => {
      setFilter(nextValue) // non-urgent: may trigger a large render
    })
  }

  return (
    <section aria-busy={isPending}>
      <label htmlFor="product-search">Search products</label>
      <input id="product-search" value={input} onChange={(e) => handleChange(e.target.value)} />
      <span aria-live="polite">{isPending ? 'Updating results…' : ''}</span>
      <ul>{visibleProducts.map((p) => <li key={p.id}>{p.name}</li>)}</ul>
    </section>
  )
}
```

**Why:** two state variables are required — React does not support wrapping the state
that controls an `<input value>` in a Transition; doing so makes typing appear inert.
`startTransition` wraps only the expensive-render-triggering `setFilter`, never `setInput`.

**Verify after applying:** Performance panel with CPU throttling — each keystroke paints
before the full list commit; Profiler shows result renders restarted/abandoned on rapid
input while input commits stay immediate.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove `useTransition`; call `setFilter` directly inside `handleChange`.

## `useDeferredValue` expensive list — requires React ≥18 (`initialValue` needs React ≥19)

**When to apply:** the caller doesn't own the state setter (value arrives via props/custom
Hook), or a lagging value plus a staleness indicator is enough — no pending-flag needed.

```tsx
// app/search/deferred-search.tsx — Next.js 16.3.0
'use client'

import { memo, useDeferredValue, useMemo, useState } from 'react'

type Result = { id: string; title: string }

export function DeferredSearch({ allResults }: { allResults: Result[] }) {
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query, '')
  const isStale = query !== deferredQuery

  return (
    <section>
      <label htmlFor="search">Search</label>
      <input id="search" value={query} onChange={(e) => setQuery(e.target.value)} />
      <div aria-busy={isStale} style={{ opacity: isStale ? 0.55 : 1 }}>
        <SlowResults query={deferredQuery} results={allResults} />
      </div>
    </section>
  )
}

const SlowResults = memo(function SlowResults({ query, results }: { query: string; results: Result[] }) {
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    return results.filter((r) => r.title.toLowerCase().includes(normalized))
  }, [query, results])
  return <ul>{filtered.map((r) => <li key={r.id}>{r.title}</li>)}</ul>
})
```

**Why:** `SlowResults` **must** be wrapped in `memo` — `useDeferredValue` has no effect on
an unmemoized consumer; it still rerenders synchronously with every parent pass regardless
of the deferred value (this is the single most common reason this recipe "does nothing").
`initialValue` (`''`) lets the first render show a cheap placeholder — but if the
server-rendered initial content must be SEO-accurate, render authoritative server content
and defer only subsequent client changes. `isStale` is the staleness signal —
`useDeferredValue` provides no dedicated pending flag, unlike `useTransition`'s `isPending`.

**Verify after applying:** input updates immediately while the result region briefly dims;
in the Profiler, `SlowResults` should not rerender for the urgent parent pass when its
props are unchanged — if it still rerenders every keystroke, check for missing memoization
or unstable `results` identity.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** replace `useDeferredValue(query, '')` with `query` directly.

## `useOptimistic` list mutation — requires React ≥19

**When to apply:** a like, star, reorder, or append mutation has a predictable success
result and the current UI makes users wait for the full round-trip. **Do not apply** to
destructive, high-failure, permission-sensitive, or inventory/payment-affecting operations.

```tsx
// app/tasks/optimistic-task-list.tsx — Next.js 16.3.0
'use client'

import { startTransition, useOptimistic, useState } from 'react'

type Task = { id: string; title: string; pending?: boolean }

async function createTask(title: string): Promise<Task> {
  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!response.ok) throw new Error('Task could not be created')
  return (await response.json()) as Task
}

export function OptimisticTaskList({ initialTasks }: { initialTasks: Task[] }) {
  const [tasks, setTasks] = useState(initialTasks)
  const [error, setError] = useState<string | null>(null)
  const [optimisticTasks, addOptimisticTask] = useOptimistic(
    tasks,
    (current, task: Task) => [task, ...current],
  )

  function handleAdd(title: string) {
    const trimmed = title.trim()
    if (!trimmed) return
    setError(null)
    const temporaryTask: Task = { id: `optimistic-${crypto.randomUUID()}`, title: trimmed, pending: true }

    startTransition(async () => {
      addOptimisticTask(temporaryTask)
      try {
        const confirmedTask = await createTask(trimmed)
        startTransition(() => setTasks((current) => [confirmedTask, ...current]))
      } catch {
        setError('Task was not saved. Try again.')
        // When the Action settles without changing `tasks`, React drops the temporary state.
      }
    })
  }

  return (
    <section>
      <form onSubmit={(e) => {
        e.preventDefault()
        const title = String(new FormData(e.currentTarget).get('title') ?? '')
        handleAdd(title)
        e.currentTarget.reset()
      }}>
        <input name="title" aria-label="New task" />
        <button type="submit">Add task</button>
      </form>
      {error ? <p role="alert">{error}</p> : null}
      <ul>
        {optimisticTasks.map((task) => (
          <li key={task.id} aria-busy={task.pending || undefined}>
            {task.title} {task.pending ? <small>Saving…</small> : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
```

**Server Action variant:** the optimistic contract above is identical whether the mutation
is a client `fetch` (shown) or a Server Action wired through `useActionState` —
`useOptimistic` is documented for both. Server Function creation, `action`/
`useActionState` signatures, and cache invalidation (`updateTag`, `revalidatePath`) belong
to `data-fetching-patterns`; this recipe owns only the immediate optimistic UI and
rollback. When pairing with a Server Action, replace the client `createTask` call with
`await someServerAction(formData)` inside the same `startTransition` boundary and keep the
success/failure branching identical.

**Why:** the outer `startTransition` makes `addOptimisticTask` legal inside an Action; the
**nested** `startTransition` after `await` is required separately — post-await `set` calls
need their own Transition wrapper. The temporary task's client-generated ID distinguishes
it from the eventual server-confirmed record — omitting this produces a "permanent ghost
row." The `catch` block explicitly clears the optimistic path via an error state rather
than leaving it to resolve silently.

**Verify after applying:** throttle the API — the pending task appears in the first paint
after submit; force a 500 — the temporary task disappears and a live error appears; submit
several tasks quickly and confirm ordering (add request IDs or move to `useActionState` if
async Transitions can complete out of order).

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove `useOptimistic`; render `tasks` directly; move `setTasks` to run
synchronously on response.

## Direct `<Activity>` hidden tab — requires React ≥19.2

**When to apply:** tabs/panels/forms should preserve local and DOM state while hidden
(scroll, expanded `<details>`, form drafts, in-flight fetches) instead of remounting on
every reveal. **Confirm React ≥19.2 via the capability probe first — a hard version floor.**

```tsx
// app/posts/[id]/page.tsx — Next.js 16.3.0
import { ExpandableComments } from './expandable-comments'

async function getComments(postId: string) { return db.comments.findMany({ where: { postId } }) }

export default function PostPage({ params }: { params: { id: string } }) {
  const commentsPromise = getComments(params.id)
  return <ExpandableComments commentsPromise={commentsPromise} />
}
```

```tsx
// app/posts/[id]/expandable-comments.tsx — Next.js 16.3.0
'use client'

import { Activity, Suspense, use, useState } from 'react'

type Comment = { id: string; text: string }

export function ExpandableComments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <>
      <button onClick={() => setExpanded((c) => !c)}>{expanded ? 'Hide comments' : 'Show comments'}</button>
      <Activity mode={expanded ? 'visible' : 'hidden'}>
        <Suspense fallback={<div>Loading comments…</div>}>
          <Comments commentsPromise={commentsPromise} />
        </Suspense>
      </Activity>
    </>
  )
}

function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise)
  return <ul>{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>
}
```

**Media note:** `display:none` alone does not stop `<video>`/`<audio>` playback. For a
media tile wrapped in `<Activity>`, add a `useLayoutEffect` cleanup that calls
`videoRef.current?.pause()` — the cleanup fires when Activity hides the component, so
playback stops while the DOM node and position are preserved; hovering back resumes at the
same time offset. This is the one documented exception to "hiding is enough."

**Why:** starting the fetch in the Server Component **before** the `<Activity>` boundary
means data loads immediately at lower priority even while hidden — reveal shows
already-resolved content instead of a fetch-on-click delay. `mode` is `'visible'`/`'hidden'`
only today — React's 19.2 notes state more modes are planned, so avoid exhaustive
`switch`/type assumptions about a fixed mode set.

**Verify after applying:** DevTools Components panel — hidden subtree stays mounted with
`display:none`; toggling reveals prior scroll/DOM state intact. Network panel — the
request starts on page load, not on click. For a media tile — hover on/off and confirm
`paused` flips without unmounting, and CPU/network usage actually drops while hidden.

**Lock-in / reversibility:** component-level-revert — replace with conditional rendering
or CSS-only hiding; explicitly decide whether losing preserved state is acceptable.

**Rollback:** remove `<Activity mode=...>`; replace with `{expanded ? <Comments .../> : null}`.

## `useEffectEvent` — requires React ≥19.2, updated eslint-plugin-react-hooks

**When to apply:** an Effect's subscription depends on one reactive value (`roomId`) but a
callback inside it must read another value fresh (`theme`) without resubscribing.

```tsx
// app/chat/chat-room.tsx — Next.js 16.3.0
'use client'

import { useEffect, useEffectEvent } from 'react'

type Connection = { on: (e: 'connected', h: () => void) => void; connect: () => void; disconnect: () => void }
declare function createConnection(roomId: string): Connection
declare function showNotification(message: string, theme: string): void

export function ChatRoom({ roomId, theme }: { roomId: string; theme: string }) {
  const onConnected = useEffectEvent(() => {
    showNotification('Connected!', theme) // Always reads the latest theme.
  })

  useEffect(() => {
    const connection = createConnection(roomId)
    connection.on('connected', () => onConnected())
    connection.connect()
    return () => connection.disconnect()
  }, [roomId]) // theme is intentionally excluded — Effect Events are not dependencies.

  return null
}
```

**Why:** `onConnected` is declared with `useEffectEvent`, not a plain function, so it can
be called from inside the Effect without being a dependency — a plain function would need
to be in the array (forcing reconnection on every `theme` change) or would close over a
stale `theme`. `roomId` stays a normal dependency because it should genuinely
resynchronize the external system. `eslint-plugin-react-hooks` must be upgraded first —
the older linter tries to insert `onConnected` into the dependency array, the exact bug
this hook avoids.

**Verify after applying:** change `theme` while connected — no reconnect fires; a later
notification uses the new theme. Change `roomId` — the cleanup/reconnect sequence runs.

**Lock-in / reversibility:** component-level-revert.

**Rollback:** replace with a `useRef` holding the latest `theme`, read `.current` inside
the Effect, keep `theme` out of the dependency array manually.

## `loading.tsx` + inline Suspense skeleton pair — requires Next.js App Router 13+

**When to apply:** a route shows a blank/frozen wait during data load, and/or independent
regions have different latency that shouldn't gate each other.

```tsx
// app/dashboard/loading.tsx — Next.js 16.3.0
export default function Loading() {
  return (
    <div aria-busy="true" aria-label="Loading dashboard">
      <div style={{ height: 32, width: 220, background: '#e5e5e5' }} />
      <div style={{ height: 160, marginTop: 16, background: '#eee' }} />
    </div>
  )
}
```

```tsx
// app/dashboard/page.tsx — Next.js 16.3.0
import { Suspense } from 'react'
import { RevenueCard } from './revenue-card'
import { ActivityFeed } from './activity-feed'

export default function DashboardPage() {
  return (
    <section>
      <h1>Dashboard</h1>
      <Suspense fallback={<CardSkeleton label="Revenue" />}><RevenueCard /></Suspense>
      <Suspense fallback={<CardSkeleton label="Activity" />}><ActivityFeed /></Suspense>
    </section>
  )
}

function CardSkeleton({ label }: { label: string }) {
  // Dimensions approximate the real card's final size — see "Why" below.
  return <div aria-busy="true" aria-label={`Loading ${label.toLowerCase()}`} style={{ height: 110, width: 280 }} />
}
```

**Why:** `loading.tsx` covers the route's instant, prefetchable fallback — it wraps
`page.tsx` and descendants automatically, but not the segment's `layout.tsx`/`template.tsx`/
`error.tsx`, and does not cover uncached/runtime data read by the layout. The two
independent inline boundaries let `RevenueCard` reveal without waiting on a slower
`ActivityFeed` — one shared boundary would hide fast content behind the slowest region.
Skeleton dimensions approximate final card size deliberately — a mismatched skeleton trades
perceived speed for a CLS regression. Use a skeleton (not a spinner) because the layout is
predictable; reserve spinners for single-control operations with unpredictable geometry.

**Verify after applying:** throttle only `ActivityFeed`'s data source — `RevenueCard`
reveals first; the route skeleton disappears once the shell streams, not once every card
resolves. Run a Lighthouse/field CLS check after the swap — should stay ≤0.1 at p75.

**Lock-in / reversibility:** fully-reversible.

**Rollback:** remove `loading.tsx` and/or the inline boundaries; render children directly.

## Unmount-assumption audit/cleanup — requires `cacheComponents: true` (probe first)

**When to apply:** the repo is enabling, or has already enabled, Cache Components — probe
`cacheComponents` first. This is a **prerequisite audit**, not an optional add-on:
automatic `<Activity mode="hidden">` route preservation changes "navigated away" from
unmount to hidden, and code assuming unmount as a cleanup trigger will misbehave.

```tsx
// app/components/dropdown-menu.tsx — Next.js 16.3.0 (fix: dropdown stays open)
'use client'
import { useLayoutEffect, useState } from 'react'

export function DropdownMenu() {
  const [isOpen, setIsOpen] = useState(false)
  useLayoutEffect(() => {
    return () => { setIsOpen(false) } // Runs when hidden by Activity, not only on unmount.
  }, [])
  return (
    <div>
      <button onClick={() => setIsOpen((c) => !c)}>Menu</button>
      {isOpen ? <ul role="menu">{/* items */}</ul> : null}
    </div>
  )
}
```

```tsx
// app/components/confirm-dialog.tsx — Next.js 16.3.0 (fix: mount-time Effect never re-runs)
'use client'
import { useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'

export function ConfirmDialog() {
  const searchParams = useSearchParams()
  const isDialogOpen = searchParams.get('dialog') === 'confirm' // URL-derived, not preserved state
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isDialogOpen) inputRef.current?.focus()
  }, [isDialogOpen])

  if (!isDialogOpen) return null
  return <dialog open><input ref={inputRef} /></dialog>
}
```

**E2E selector fix:** replace DOM-presence locators (`page.locator('input[name=email]')`)
with visibility-aware queries — `await expect(page.getByRole('textbox', { name: 'Email'
})).toBeVisible()`. `getByRole` queries the accessibility tree and excludes hidden
elements, avoiding a Playwright strict-mode failure when a duplicate hidden field from
another preserved route (e.g. `/sign-up`) matches alongside the visible one.

**Why:** the dropdown's `useLayoutEffect` **cleanup** (not a plain `useEffect`) resets
`isOpen` — this fires when Activity hides the component, matching the documented Next.js
"Preserving UI state" pattern. `isDialogOpen` is derived from `useSearchParams()` instead
of local state so it genuinely changes on each open/close even when local state would
otherwise be preserved unchanged, letting the focus Effect actually re-run. The E2E fix
matters because hidden `<Activity>` content has `display:none` but remains in the DOM — a
naive locator can match a duplicate hidden field from another preserved route.

**Verify after applying:** navigate away and back with an open popover, an edited form, and
an open dialog — each must follow an explicit preserve-or-reset policy. Run the affected
E2E suite with `cacheComponents: true` enabled and confirm no strict-mode/hidden-element
failures. Audit module-level mutable state (singletons, caches) for single-instance
assumptions — a documented production report (`vercel/next.js` discussion #89160) confirms
two cached component instances (hidden + visible) can coexist simultaneously.

**Lock-in / reversibility:** fully-reversible per individual fix, but the audit itself must
run **before** `cacheComponents: true` is treated as safe to enable — per
`references/gating/lockin-reversibility.md`, that flag flip is itself `migration-required`
at the domain level and never auto-applied; this recipe is what the pre-flight checklist's
"audited unmount-dependent UI" line requires in practice.

**Rollback:** revert the `useLayoutEffect` cleanup to a no-op; revert `isDialogOpen` to
local `useState`; revert E2E selectors to DOM-presence queries only if `cacheComponents`
is also being disabled.

## Ordering within this domain

1. Confirm field INP instrumentation exists (`measurement-regression-guardrails`) before
   claiming any recipe here "improved" responsiveness — this domain supplies mechanism,
   not measurement.
2. `useDeferredValue`/`useTransition` at known hot interactions first — smallest blast
   radius, immediate INP-relevant payoff.
3. `useOptimistic` on low-risk mutations next, with forced-failure tests in place.
4. `loading.tsx` + inline Suspense pairs for routes/regions still showing blank/frozen waits.
5. Direct `<Activity>` for one bounded tab/panel, verified for Effects/memory.
6. The unmount-assumption audit must run **before**, not after, `cacheComponents: true` —
   a hard ordering constraint: Cache Components is a cross-cutting migration whose
   automatic Activity behavior this domain's audit recipe exists specifically to de-risk.

## Conflicts to watch

- **Activity preservation × unmount-dependent logic** — with `cacheComponents` enabled,
  Next.js hides rather than unmounts the previous route. Any Cache Components task must
  carry the unmount-dependency audit (dropdowns, dialogs, mounted form init, media,
  subscriptions, timers, post-submit resets, scroll restoration, E2E selectors) in its
  body — never treat it as optional cleanup. See `references/gating/conflicts.md` §2.
- **Activity retention bounds × `bfcacheId`** — preservation is bounded to roughly the
  three most recent routes; older routes evict and re-render fresh. Never describe route
  state as durably preserved — persist real drafts to application storage if durability
  matters. See `references/gating/conflicts.md` §3.
- **Hidden Activity prerendering × delayed catastrophic bugs** — a hidden subtree needs the
  same termination/bounded-size guarantees as a visible one; a responsive foreground is not
  evidence the hidden workload is healthy. See `references/gating/conflicts.md` §4.
- **Do not conflate with `page-transitions-view-transitions`** — `useTransition` is a
  scheduler/pending-state hook; `<ViewTransition>` animates visual snapshots. They compose
  (a route can use both), but a fix in this file must never claim to produce visual
  transition choreography.

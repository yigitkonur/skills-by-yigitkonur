# Fix: data-fetching-patterns

**Corpus lineage:** data-fetching-patterns/04-implementation-fetching.md,
data-fetching-patterns/05-implementation-actions.md, data-fetching-patterns/07-pitfalls-waterfalls.md,
data-fetching-patterns/08-constraints-lockin-seo-vercel-practitioner.md
**Knowledge baseline:** verified 2026-08-05 against Next.js 16.3.0 docs (React 19.2 canary,
bundled). Confirm any config key against the installed package first — see
`references/gating/capability-probe.md`.

## Recipe index

| Recipe | Requires | Reversibility | Triggered by |
|---|---|---|---|
| Parallel fetching with `Promise.all` | App Router (Next.js ≥13.0.0) | fully-reversible | Detect Pattern A — same-component sequential waterfall |
| Preload pattern (`preload()` + `cache()` + `server-only`) | React ≥19, Server Components | fully-reversible | Eager-start opportunity before other blocking work |
| Genuine dependency chain → outer Suspense/`loading.js` | App Router, Suspense stable | fully-reversible | Detect Pattern B — parent-child chain, not `Promise.all`-fixable |
| `use(promise)` handoff, Server → Client Component | React ≥19.0.0 | component-level-revert | Detect Pattern C — client-side `useEffect` fetch cascade |
| `React.cache` dedup for non-`fetch`/ORM reads | React ≥19, Server Components only | fully-reversible | Detect Pattern D — cache-instance mismatch |
| Server Action mutation: `useActionState` + `useOptimistic` + revalidation | React ≥19, `'use server'` (Next.js ≥14) | component-level-revert | Missing optimistic UI; stale-flash-on-mutation |
| `useFormState` → `useActionState` migration | React ≥19 | fully-reversible | Detect: live `useFormState` import/usage |
| Single-arg `revalidateTag` → two-arg / `updateTag` migration | Next.js ≥16.3.0 for `updateTag` | migration-required (small) | Detect: `revalidateTag(tag)` single-argument call |
| Streaming page with granular Suspense boundaries | App Router, Suspense stable | fully-reversible | `page.tsx` with no `Suspense`; whole-route blocking |

## Parallel fetching with `Promise.all` — requires Next.js ≥13.0.0 (App Router)

**When to apply:** Detect Pattern A — independent `await` calls placed sequentially in one
Server Component.

```tsx
// app/artist/[username]/page.tsx — Next.js 16.3.0
import Albums from './albums'

async function getArtist(username: string) {
  const res = await fetch(`https://api.example.com/artist/${username}`)
  return res.json()
}
async function getAlbums(username: string) {
  const res = await fetch(`https://api.example.com/artist/${username}/albums`)
  return res.json()
}

export default async function Page({ params }: { params: Promise<{ username: string }> }) {
  const { username } = await params
  // Initiate requests — they begin as soon as fetch is called, NOT awaited yet
  const artistData = getArtist(username)
  const albumsData = getAlbums(username)
  const [artist, albums] = await Promise.all([artistData, albumsData])
  return (
    <>
      <h1>{artist.name}</h1>
      <Albums list={albums} />
    </>
  )
}
```

**Why:** calling both functions without `await` first starts both requests immediately — only
`Promise.all` blocks. Swap in `Promise.allSettled` if one failure shouldn't fail the whole
render.

**Verify:** Network tab — both requests' Start Time bars begin at approximately the same
timestamp, not one after the other's End Time. Total time drops from `sum(t1, t2)` toward
`max(t1, t2)`.

**Lock-in / reversibility:** fully-reversible — pure code restructuring, no config.

**Rollback:** revert to two sequential `await` statements.

## Preload pattern (`preload()` + `cache()` + `server-only`) — requires React ≥19 (Server Components)

**When to apply:** a data read is needed later in the tree while other blocking work happens
first — start the fetch immediately, read it later.

```ts
// lib/get-item.ts — Next.js 16.3.0
import { cache } from 'react'
import 'server-only'

export const getItem = cache(async (id: string) => {
  /* fetch or DB call */
})

export const preload = (id: string) => {
  void getItem(id)
}
```

```tsx
// app/item/[id]/page.tsx — Next.js 16.3.0
import { getItem, preload } from '@/lib/get-item'
import { checkIsAvailable } from '@/lib/availability'

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  preload(id) // start loading item data
  const isAvailable = await checkIsAvailable() // runs while getItem's promise is in flight
  return isAvailable ? <Item id={id} /> : null
}

async function Item({ id }: { id: string }) {
  const result = await getItem(id)
  return <div>{JSON.stringify(result)}</div>
}
```

**Why:** `cache(fn)` scopes `getItem` per-request, so the `<Item>` call hits the cache instead
of re-fetching — this is what makes "start early, read later" safe. `void getItem(id)` discards
the return value while still triggering the fetch. `server-only` guarantees this utility can
never be bundled into client code.

**Verify:** `getItem`'s Start Time overlaps `checkIsAvailable`'s bar; exactly one request fires
for `getItem` despite two call sites.

**Lock-in / reversibility:** fully-reversible — unwrap and call directly; no persisted state.

**Rollback:** remove `preload()`/`cache()`; call the plain async function directly.

## Genuine dependency chain → outer Suspense/`loading.js` — requires Next.js ≥13.0.0 (Suspense stable)

**When to apply:** Detect Pattern B — a child structurally needs a parent's resolved value.
**Not a `Promise.all` fix** — the second call cannot start before the first resolves.

```tsx
// app/artist/[username]/page.tsx — Next.js 16.3.0
import { Suspense } from 'react'

export default async function Page({ params }: { params: Promise<{ username: string }> }) {
  const { username } = await params
  const artist = await getArtist(username) // genuinely blocks everything below it
  return (
    <>
      <h1>{artist.name}</h1>
      <Suspense fallback={<div>Loading...</div>}>
        <Playlists artistID={artist.id} />
      </Suspense>
    </>
  )
}

async function Playlists({ artistID }: { artistID: string }) {
  const playlists = await getArtistPlaylists(artistID) // cannot start before artist.id exists
  return <ul>{playlists.map((p: { id: string; name: string }) => <li key={p.id}>{p.name}</li>)}</ul>
}
```

```tsx
// app/artist/[username]/loading.tsx — Next.js 16.3.0
export default function Loading() {
  return <div>Loading artist…</div> // shown while the blocking getArtist() call resolves
}
```

**Why:** the inner `<Suspense>` streams only the playlists section — `artist.name` still
depends on the full `await getArtist`. `loading.tsx` adds the *outer* boundary docs call out
directly: without it, "the page still waits for the artist data before displaying anything."
Optimize or cache the blocking first call (`React.cache`/`use cache`) to reduce cost frequency
— the dependency itself can't be removed.

**Verify:** the `loading.tsx` skeleton paints immediately on cold navigation, before
`artist.name`; `artist.name` then appears before `<Playlists>`'s fallback resolves — three
distinct visible stages.

**Lock-in / reversibility:** fully-reversible — additive files/wrappers only.

**Rollback:** delete `loading.tsx` and/or the inner `<Suspense>` wrapper.

## `use(promise)` handoff from Server Component to Client Component — requires React ≥19.0.0

**When to apply:** Detect Pattern C — a Client Component fires its own `useEffect`+`fetch` for
data a Server Component could originate instead.

```tsx
// app/blog/page.tsx — Next.js 16.3.0 (Server Component)
import Posts from '@/app/ui/posts'
import { Suspense } from 'react'

export default function Page() {
  const posts = getPosts() // don't await — hand down the unresolved Promise
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Posts posts={posts} />
    </Suspense>
  )
}
```

```tsx
// app/ui/posts.tsx — Next.js 16.3.0 (Client Component)
'use client'
import { use } from 'react'

export default function Posts({ posts }: { posts: Promise<{ id: string; title: string }[]> }) {
  const allPosts = use(posts)
  return <ul>{allPosts.map((post) => <li key={post.id}>{post.title}</li>)}</ul>
}
```

**Why:** `getPosts()` called without `await` starts the fetch immediately but hands an
unresolved `Promise` down as a prop, letting the parent's synchronous render finish and the
shell ship instantly. `<Suspense>` is required where `use()` will suspend while the promise
settles. Promises passed to `use` must be **cached (stable across re-renders)** — never
re-created inside the Client Component; this is why the promise always originates server-side.
If several components read the same data, wrap the origin function in `React.cache` so they
share one call.

**Verify:** DevTools Network — the promise's backing request appears in the initial document
response (streamed via `self.__next_f.push` chunks), not as a separate client-initiated
`fetch` after hydration.

**Lock-in / reversibility:** component-level-revert — reverting means converting the Client
Component back to a synchronous prop consumer or reintroducing `useEffect`+`fetch`; moderate,
localized rework, no persisted state.

**Rollback:** remove the `use(promise)` call and promise prop; restore a `useEffect` fetch or
pass already-resolved data from an `await`-ing parent.

## `React.cache` dedup for non-`fetch`/ORM reads — requires React ≥19 (Server Components only)

**When to apply:** Detect Pattern D — duplicate DB/ORM calls for the same logical read across
components in one render pass. `fetch`'s automatic memoization only covers identical
`fetch(url, options)` calls, not ORM/database calls.

```ts
// app/lib/user.ts — Next.js 16.3.0
import { cache } from 'react'
import { db } from '@/lib/db'

export const getUser = cache(async (userId: string) => {
  return db.user.findUnique({ where: { id: userId } })
})
```

```tsx
// app/dashboard/page.tsx — Next.js 16.3.0
import { getUser } from '../lib/user'

export default async function DashboardPage() {
  const user = await getUser('current') // cached - same request, no duplicate fetch
  return <h1>Dashboard for {user?.name}</h1>
}
```

**Why:** `React.cache` dedups by **function + arguments**, covering ORM/database calls that
never touch `fetch`. Caveat: "React will invalidate the cache for all memoized functions for
each server request" — per-request only, never cross-request (that's `use cache`'s job).
"`cache` is for use in Server Components only" — a Client Component call site is a gate
violation. Every call site must import the **same exported instance**; a fresh local
`cache(fn)` call creates a separate, non-sharing cache — exactly Pattern D's root cause.

**Verify:** add a temporary `console.log` inside the un-cached body, call from two Server
Components in one render, confirm the log fires exactly once per request.

**Lock-in / reversibility:** fully-reversible — unwrap the function; no persisted state.

**Rollback:** remove the `cache()` wrapper, call the plain async function directly at each site.

## Server Action mutation: `useActionState` + `useOptimistic` + revalidation — requires React ≥19, Next.js ≥14 (stable `'use server'`)

**When to apply:** a mutating control shows stale data until the next full round trip, or lacks
server-side validation/pending-state wiring.

```ts
// app/actions.ts — Next.js 16.3.0
'use server'

import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { auth } from '@/lib/auth'
import { db } from '@/lib/db'

const schema = z.object({ message: z.string().min(1, 'Message cannot be empty') })
type SendState = { message: string; errors?: Record<string, string[]> }

// useActionState changes the signature: prevState first, then formData.
export async function send(prevState: SendState, formData: FormData): Promise<SendState> {
  const session = await auth()
  if (!session?.user) throw new Error('Unauthorized')

  const validatedFields = schema.safeParse({ message: formData.get('message') })
  if (!validatedFields.success) {
    return { message: '', errors: validatedFields.error.flatten().fieldErrors }
  }

  await db.message.create({ data: { text: validatedFields.data.message, authorId: session.user.id } })
  revalidatePath('/thread') // refresh the thread for every other visitor's next read
  return { message: '' }
}
```

```tsx
// app/thread.tsx — Next.js 16.3.0
'use client'
import { useActionState, useOptimistic } from 'react'
import { send } from './actions'

type Message = { message: string }
const initialState = { message: '' }

export function Thread({ messages }: { messages: Message[] }) {
  const [state, formAction, isPending] = useActionState(send, initialState)
  const [optimisticMessages, addOptimisticMessage] = useOptimistic<Message[], string>(
    messages,
    (current, newMessage) => [...current, { message: newMessage }]
  )

  async function clientAction(formData: FormData) {
    addOptimisticMessage(formData.get('message') as string)
    await formAction(formData)
  }

  return (
    <div>
      {optimisticMessages.map((m, i) => <div key={i}>{m.message}</div>)}
      <form action={clientAction}>
        <input type="text" name="message" required />
        {state.errors?.message && <p aria-live="polite">{state.errors.message[0]}</p>}
        <button disabled={isPending}>Send</button>
      </form>
    </div>
  )
}
```

**Why:** `useActionState(send, initialState)` receives `prevState` first, exposing validation
errors and `isPending` without a separate `useState`. `useOptimistic(messages, reducer)` seeds
from the **server-rendered** prop, so it starts in sync. `addOptimisticMessage` runs **before**
`await formAction(formData)` — the setter must run inside an Action (it does, as `clientAction`
is the form's `action`), and calling it pre-`await` puts the message on the click's own frame.
`revalidatePath('/thread')` refreshes every other visitor's next read; since this action calls
no `redirect`/`updateTag`/`refresh()`, the single-roundtrip response includes a re-render, so
the real message lands in `messages` on the same response. Auth is checked **inside** the
action — Server Functions are reachable via direct POST, not just the UI.

**Verify:** click "Send" with DevTools open — (1) the message appears on the click's own
animation frame, (2) exactly one Network request fires, (3) after it resolves, the optimistic
message is replaced by the server-confirmed one without a flash.

**Lock-in / reversibility:** component-level-revert — remove the hooks, fall back to plain
controlled state + manual pending flags; no persisted data involved.

**Rollback:** remove `useOptimistic`/`useActionState`, replace with plain `useState` and a
direct `formAction` call without optimistic seeding.

## `useFormState` → `useActionState` migration — requires React ≥19

**When to apply:** Detect finding — a live `useFormState` import, renamed in React 19.

```tsx
// app/ui/signup.tsx — Next.js 16.3.0
'use client'
// BEFORE: import { useFormState } from 'react-dom'
import { useActionState } from 'react'
import { createUser } from '@/app/actions'

export function Signup() {
  // BEFORE: const [state, formAction] = useFormState(createUser, initialState)
  const [state, formAction, pending] = useActionState(createUser, initialState)
  return (
    <form action={formAction}>
      <button disabled={pending}>Sign up</button>
    </form>
  )
}
```

**Why:** the import moves from `react-dom` to `react`. The hook now returns a **third value**,
`isPending`, replacing whatever manual pending-state tracking a `useFormState`-era component
built separately.

**Verify:** submit the form; the button's `disabled` now tracks `pending` from the hook;
`state` still reflects the same validation errors as before.

**Lock-in / reversibility:** fully-reversible — rename import and hook call back.

**Rollback:** re-import `useFormState` from `react-dom`, drop the third return value.

## Single-arg `revalidateTag` → two-arg / `updateTag` migration — requires Next.js ≥16.3.0 for `updateTag`; two-arg `revalidateTag` at any currently supported version

**When to apply:** Detect finding — `revalidateTag(tag)` called with exactly one argument
(deprecated: "may be removed in a future version").

```ts
// app/actions.ts — Next.js 16.3.0
'use server'
import { revalidateTag, updateTag } from 'next/cache'

export default async function submit() {
  await addPost()
  // BEFORE (deprecated): revalidateTag('posts')

  // Background refresh acceptable — stale-while-revalidate; next visitor may see stale once.
  revalidateTag('posts', 'max')

  // OR — read-your-own-writes required (Server Actions only, not Route Handlers):
  updateTag('posts')
}
```

**Why:** `revalidateTag(tag, profile)` requires the second argument going forward — `'max'` is
the documented stale-while-revalidate profile. The choice isn't stylistic: `updateTag` is
**Server-Actions-only** and expires immediately; `revalidateTag` also works from Route Handlers
but "the action's own re-render does **not** wait for the new data." Need Route Handler
support? `updateTag` is not an option.

**Verify:** trigger the mutation, reload a *different* session on a page reading the tagged
data. With `revalidateTag(tag, 'max')`, the first reload may still show the old value; a later
reload is fresh. With `updateTag`, the very next read — including this action's own re-render —
is already fresh.

**Lock-in / reversibility:** migration-required, but small — soft one-way door (deprecation
window open, not yet closed). Exit cost: add the second argument at every call site.

**Rollback:** revert to the single-argument call (still functions today with TS errors
suppressed) — emergency revert only, not a durable state.

## Streaming page with granular Suspense boundaries — requires Next.js ≥13.0.0 (Suspense stable)

**When to apply:** Detect finding — a `page.tsx` with no `Suspense` reference, where the whole
route blocks on its slowest query.

```tsx
// app/blog/page.tsx — Next.js 16.3.0
import { Suspense } from 'react'
import BlogList from '@/components/BlogList'
import BlogListSkeleton from '@/components/BlogListSkeleton'
import Sidebar from '@/components/Sidebar'
import SidebarSkeleton from '@/components/SidebarSkeleton'

export default function BlogPage() {
  return (
    <div>
      <header>
        <h1>Welcome to the Blog</h1>
      </header>
      <main>
        {/* Each independently slow region gets its own boundary */}
        <Suspense fallback={<BlogListSkeleton />}>
          <BlogList />
        </Suspense>
        <Suspense fallback={<SidebarSkeleton />}>
          <Sidebar />
        </Suspense>
      </main>
    </div>
  )
}
```

**Why:** everything outside a `<Suspense>` boundary (the `<header>`) ships in the static shell
immediately. `<BlogList>` and `<Sidebar>` each get their **own** boundary — a slow sidebar query
streams independently instead of the fastest content waiting on the slowest. Fallbacks must
match the content's dimensions or CLS regresses on swap. Wrapping a purely synchronous
component in `<Suspense>` gains nothing — it "will complete during prerendering regardless."

**Verify:** DevTools Network → document request → Timing tab shows a long "Content Download"
phase with an early "Time to First Byte" — confirms streaming, not one blocking response. The
header paints before either Suspense section's content appears.

**Lock-in / reversibility:** fully-reversible — additive JSX only.

**Rollback:** remove the `<Suspense>` wrappers (or wrap the whole page in one `loading.tsx`
boundary as a coarser, still-reversible step back).

## Ordering within this domain

1. Fix Pattern A/C waterfalls (`Promise.all`, `use(promise)` handoff) before Suspense boundaries
   — a parallelized fetch needs fewer boundaries than a sequential one.
2. Add outer `loading.js`/Suspense for Pattern B only after confirming the chain truly can't be
   parallelized.
3. Migrate `useFormState`/single-arg `revalidateTag` before adding new `useOptimistic` wiring.
4. Land `React.cache`/preload dedup before Cache Components adoption
   (`references/gating/composition-recipe.md` step 5 precedes step 6).

## Conflicts to watch

- **View Transitions × unprefetched destinations** (`references/gating/conflicts.md` §1): a
  route with an unresolved waterfall/missing-Suspense finding here is not cache-hot — any
  `page-transitions-view-transitions` task on it is `Depends on` this domain's fix.
- **Mixed client-cache + RSC data ownership** (`references/gating/lockin-reversibility.md` door
  #6): SWR/TanStack client refetching alongside Server-Action `revalidatePath`/`updateTag` on
  the same resource creates two sources of truth. Resolve ownership per-resource first.
- **Server Actions dispatch sequentially per client** — never wrap multiple Server Action calls
  in `Promise.all` expecting parallelism, regardless of this domain's `fetch`-`Promise.all`
  recipe.

# SSR & Data Fetching: Nuxt → Next.js

Converting Nuxt data fetching, rendering modes, and server patterns to Next.js App Router.

---

## Pattern Mapping Table

| Nuxt Pattern | Next.js Equivalent | Key Differences |
|---|---|---|
| `useFetch('/api/posts')` | `fetch()` in async Server Component | Nuxt: reactive `{data, pending, error}`; Next: plain data |
| `useAsyncData('key', fn)` | `fetch()` in RSC with cache options | Nuxt: explicit key; Next: auto-dedupes by URL |
| `$fetch('/api/user')` | Native `fetch()` or direct DB call | Nuxt auto-throws on 4xx/5xx; `fetch` needs `res.ok` check |
| `useFetch(url, { server: false })` | Client Component with `useEffect`/SWR | Add `'use client'` + client-side library |
| `useFetch(url, { lazy: true })` | `<Suspense>` boundary + RSC | Streaming |
| `useFetch(url, { watch: [ref] })` | Client Component with TanStack Query | Reactive refetch needs client lib |
| `server/api/*.ts` (Nitro) | `app/api/*/route.ts` | `defineEventHandler` → `GET`/`POST` exports |
| `server/middleware/*.ts` | `middleware.ts` at root | Multiple files → single file with `matcher` |
| `<ClientOnly>` | `'use client'` directive | Component-level split |
| `routeRules: { swr: N }` | `export const revalidate = N` | Per-route ISR |
| `NuxtLink` | `<Link>` from `next/link` | `to` → `href` |

---

## Server-Side Data Fetching

### Nuxt useFetch → Async Server Component

**Nuxt:**
```vue
<script setup>
const { data: posts, pending, error } = await useFetch('/api/posts')
</script>
<template>
  <div v-if="pending">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <ul v-else>
    <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
  </ul>
</template>
```

**Next.js:**
```tsx
// app/posts/page.tsx — Server Component (default)
export default async function PostsPage() {
  const res = await fetch('https://api.example.com/posts', {
    next: { revalidate: 3600 },
  });
  if (!res.ok) throw new Error('Failed to fetch');
  const posts: Post[] = await res.json();
  return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>;
}

// app/posts/loading.tsx — replaces v-if="pending"
export default function Loading() { return <div>Loading...</div>; }

// app/posts/error.tsx — replaces v-else-if="error"
'use client';
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <div><p>Error: {error.message}</p><button onClick={reset}>Retry</button></div>;
}
```

### Key useFetch Option Conversions

| Nuxt Option | Next.js Equivalent |
|---|---|
| `{ key: 'x' }` | Auto-deduplication (no key needed) |
| `{ lazy: true }` | Wrap in `<Suspense>` |
| `{ server: false }` | `'use client'` + `useEffect`/SWR |
| `{ cache: true }` | `{ cache: 'force-cache' }` or `{ next: { revalidate: N } }` |
| `{ watch: [ref] }` | Client Component with TanStack Query |
| `{ transform: fn }` | Inline after `await res.json()` |

### Client-Side Reactive Fetching

**Nuxt:** `useFetch('/api/search', { query: { q: search }, watch: [search] })`

**Next.js:**
```tsx
'use client';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

export default function SearchPage() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['search', search],
    queryFn: () => fetch(`/api/search?q=${search}`).then(r => r.json()),
    enabled: search.length > 0,
  });
  return <>
    <input value={search} onChange={e => setSearch(e.target.value)} />
    {isLoading ? <p>Searching...</p> : data?.map((i: Item) => <div key={i.id}>{i.name}</div>)}
  </>;
}
```

### Don't Port onMounted(fetch...) Blindly

A lot of Vue components fetch data in `onMounted` or in watchers reacting to route params. In Next App Router, the better default is to **fetch on the server**.

**Decision framework:**

| Vue Pattern | Next.js Default | When to Deviate |
|---|---|---|
| Component **only displays** fetched data | Server Component with `await fetch()` | — |
| Component **displays data AND has rich interaction** | Fetch in Server Component, pass as props to Client Component | — |
| Data must be **refreshed from client interactions** | Choose: `router.refresh()`, Server Actions, or client-side fetching | Use client fetch for real-time/polling |

Before reaching for `useEffect` + `fetch`, ask: *"Can this data be fetched before the component renders?"* If yes, use a Server Component.

---

## Server vs Client Components

| Server Component (default) | Client Component (`'use client'`) |
|---|---|
| Fetch data, access backend, keep secrets | Interactive UI, browser APIs, state/effects |

### Decision Criteria

Make it a **Client Component** (`'use client'`) if it needs:
- Local state (`useState`), event handlers (`onClick`, `onChange`)
- `useEffect`, refs, imperative DOM access
- Browser APIs (`window`, `localStorage`, `IntersectionObserver`)
- Client-side router/store hooks (`useRouter`, `useSearchParams`)

Make it a **Server Component** (default) when mostly:
- Rendering static markup or fetched data
- Using secrets, env vars, or server-only modules
- Composing non-interactive content

> **Migration tip:** During migration, bias toward Client Components for parity. Optimize to Server Components later — correctness first, performance second.

### The Donut Pattern

Server wrapper with client interior — data on server, interactivity on client:

```tsx
// app/products/page.tsx — Server Component
export default async function ProductsPage() {
  const products = await db.product.findMany();
  return <ProductFilter products={products} />; // pass to client
}

// components/ProductFilter.tsx
'use client';
export function ProductFilter({ products }: { products: Product[] }) {
  const [query, setQuery] = useState('');
  const filtered = products.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
  return <>
    <input value={query} onChange={e => setQuery(e.target.value)} />
    {filtered.map(p => <ProductCard key={p.id} product={p} />)}
  </>;
}
```

Push `'use client'` as low in the tree as possible.

### Serialization Boundary Warning

Props passed from a Server Component to a Client Component **must be serializable** — you cannot pass functions, class instances, or Dates across that boundary.

```tsx
// ❌ BROKEN — function prop crosses the server/client boundary
export default async function Page() {
  const handleClick = () => console.log('clicked'); // not serializable
  return <ClientButton onClick={handleClick} />;
}

// ✅ CORRECT — keep callbacks inside the client island
'use client';
export function ClientButton() {
  const handleClick = () => console.log('clicked');
  return <button onClick={handleClick}>Click</button>;
}
```

This is why callback-heavy component hierarchies should stay inside a single `'use client'` island at first — split later once the boundary is clear.

---

## Server Actions

**Nuxt mutation:** `await $fetch('/api/posts', { method: 'POST', body: data })`

**Next.js Server Action:**
```tsx
// app/posts/actions.ts
'use server';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  await db.post.create({ data: { title: formData.get('title') as string } });
  revalidatePath('/posts');
}

// app/posts/new/page.tsx — no 'use client' needed!
import { createPost } from '../actions';
export default function NewPost() {
  return <form action={createPost}><input name="title" required /><button type="submit">Create</button></form>;
}
```

> **Constraint:** `revalidatePath`/`revalidateTag` can only be called from Server Actions or Route Handlers — not from Client Components or proxied imports.

### Optimistic Updates

```tsx
'use client';
import { useOptimistic } from 'react';

export function TodoList({ todos }: { todos: Todo[] }) {
  const [optimistic, addOptimistic] = useOptimistic(todos,
    (state, newTitle: string) => [...state, { id: 'temp', title: newTitle, pending: true }]
  );
  async function handleSubmit(formData: FormData) {
    addOptimistic(formData.get('title') as string);
    await addTodo(formData);
  }
  return <form action={handleSubmit}>
    <input name="title" /><button type="submit">Add</button>
    <ul>{optimistic.map(t => <li key={t.id} style={{ opacity: t.pending ? 0.5 : 1 }}>{t.title}</li>)}</ul>
  </form>;
}
```

---

## SSG / ISR

| Nuxt Config | Next.js Equivalent |
|---|---|
| `routeRules: { '/': { prerender: true } }` | `export const dynamic = 'force-static'` |
| `routeRules: { '/blog/**': { swr: 3600 } }` | `export const revalidate = 3600` |
| `routeRules: { '/dash/**': { ssr: true } }` | `export const dynamic = 'force-dynamic'` |
| `nitro: { static: true }` | `next.config: { output: 'export' }` |

**ISR with static params:**
```tsx
// app/blog/[slug]/page.tsx
export const revalidate = 3600;

export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return posts.map((p: Post) => ({ slug: p.slug }));
}

export default async function BlogPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json());
  return <article>{post.content}</article>;
}
```

**On-demand revalidation:** `revalidatePath('/posts')` or `revalidateTag('posts')` from Server Actions or Route Handlers.

### ISR via Route Config

Add `export const revalidate = 60` in any `page.tsx`/`layout.tsx` for time-based ISR — stale pages regenerate in the background on next request. For event-driven freshness, tag fetches with `{ next: { tags: ['posts'] } }` and call `revalidateTag('posts')` from a Server Action or Route Handler.

---

## API Routes

**Nuxt:** `server/api/posts/[id].get.ts` with `defineEventHandler`
**Next.js:** `app/api/posts/[id]/route.ts` with named exports

```ts
// app/api/posts/[id]/route.ts
import { NextResponse } from 'next/server';

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const post = await db.post.findUnique({ where: { id } });
  if (!post) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(post);
}

export async function POST(request: Request) {
  const body = await request.json();
  const post = await db.post.create({ data: body });
  return NextResponse.json(post, { status: 201 });
}
```

Prefer direct DB access in Server Components over API routes. Only use Route Handlers for external consumers or Client Component endpoints.

---

## Middleware

**Nuxt:** Multiple files in `server/middleware/`, full Node.js runtime, can access DB.
**Next.js:** Single `middleware.ts`, Edge Runtime, headers/cookies/redirects only.

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}
export const config = { matcher: ['/dashboard/:path*'] };
```

Complex auth requiring DB → move to Route Handlers or Server Actions.

---

## Loading, Error & Streaming

**Loading:** Nuxt `v-if="pending"` → Next.js `loading.tsx` (auto-wraps page in Suspense) or manual `<Suspense fallback={}>`.

**Error:** Nuxt error handling → Next.js `error.tsx` (must be `'use client'`, receives `{ error, reset }`).

**Streaming:** Nest `<Suspense>` boundaries for independent progressive rendering:
```tsx
export default function Dashboard() {
  return <div>
    <h1>Dashboard</h1>
    <Suspense fallback={<StatsSkeleton />}><StatsPanel /></Suspense>
    <Suspense fallback={<ChartSkeleton />}><RevenueChart /></Suspense>
  </div>;
}
```

Each async Server Component streams independently — no waterfall.

---

## Page Migration Pattern

The recommended order for migrating a Vue/Nuxt page component to Next.js App Router:

1. **Move page entry** into `app/.../page.tsx`
2. **Create a route-local Client Component** (preserves all interactive logic with `'use client'`)
3. **Pull out leaf child components** — migrate children first, parents last
4. **Separate data-loading from view logic** (only after parity is achieved)
5. **Move route-level UX** into `loading.tsx` and `error.tsx`

**Common end state** — server page fetches, client component renders:

```tsx
// app/users/[id]/page.tsx — Server Component
import UserPageClient from './UserPageClient';
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  return <UserPageClient initialUser={await getUser((await params).id)} />;
}
// app/users/[id]/UserPageClient.tsx — 'use client'
export default function UserPageClient({ initialUser }: { initialUser: User }) {
  return <div>{/* All original Vue interactivity lives here */}</div>;
}
```

---

## Freshness SLAs

Map each route to a freshness policy: **static** (`dynamic = 'force-static'`), **dynamic** (`dynamic = 'force-dynamic'`), **ISR-N** (`revalidate = N`), or **on-demand** (`revalidateTag()`). Match each Vue data pattern — `useFetch` with caching → ISR, `$fetch` on interaction → dynamic, prerendered → static. Document per-route SLAs to prevent over-fetching or stale data.

---

## Hydration & Conversion Checklist

| Nuxt | Next.js |
|---|---|
| Full DOM hydration | Partial — only `'use client'` hydrates |
| `<ClientOnly>` | `'use client'` directive |
| `process.server` checks | Server Components (default) vs Client |
| `refreshNuxtData()` | `router.refresh()` |
| `clearNuxtData()` | `revalidatePath()` / `revalidateTag()` |

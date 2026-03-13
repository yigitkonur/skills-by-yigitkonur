# Routing Conversion: Vue Router → Next.js App Router

Converting Vue Router's config-based routing to Next.js file-system routing.

---

## File Structure Mapping

Vue Router uses an explicit config object. Next.js uses the `app/` directory tree.

**Vue Router config:**
```ts
const routes = [
  { path: '/', component: Home },
  { path: '/about', component: About },
  {
    path: '/dashboard', component: DashboardLayout,
    children: [
      { path: '', component: DashboardHome },
      { path: 'analytics', component: Analytics },
      { path: 'settings', component: SettingsLayout, children: [
        { path: '', component: SettingsGeneral },
        { path: 'profile', component: Profile },
      ]},
    ],
  },
  { path: '/users/:id', component: UserDetail },
  { path: '/docs/:slug+', component: DocsPage },
  { path: '/:pathMatch(.*)*', component: NotFound },
]
```

**Next.js equivalent:**
```
app/
  page.tsx                    ← / (Home)
  about/page.tsx              ← /about
  dashboard/
    layout.tsx                ← DashboardLayout
    page.tsx                  ← /dashboard
    analytics/page.tsx        ← /dashboard/analytics
    settings/
      layout.tsx              ← SettingsLayout
      page.tsx                ← /dashboard/settings
      profile/page.tsx        ← /dashboard/settings/profile
  users/[id]/page.tsx         ← /users/:id
  docs/[...slug]/page.tsx     ← /docs/:slug+
  not-found.tsx               ← 404
```

**Conversion rules:** Replace `:param` → `[param]`, `:param+` → `[...param]`, `:param*` → `[[...param]]`. Routes with `children` → `layout.tsx` + nested folders. Child `path: ''` → `page.tsx` in parent.

---

## Route Syntax Mapping

| Vue Router | Next.js App Router | Notes |
|---|---|---|
| `path: '/'` | `app/page.tsx` | Root page |
| `path: '/about'` | `app/about/page.tsx` | Static route |
| `path: '/users/:id'` | `app/users/[id]/page.tsx` | Dynamic segment |
| `path: '/post/:year/:month'` | `app/post/[year]/[month]/page.tsx` | Multiple params |
| `path: '/docs/:slug+'` | `app/docs/[...slug]/page.tsx` | Catch-all (1+) |
| `path: '/docs/:slug*'` | `app/docs/[[...slug]]/page.tsx` | Optional catch-all |
| `path: '/:pathMatch(.*)*'` | `app/not-found.tsx` | 404 |
| `children: [...]` | Nested folders + `layout.tsx` | Nested routes |
| Named views | `@slot` parallel routes | `@sidebar/page.tsx` |
| `alias` | `next.config.js` `rewrites` | URL aliasing |
| `redirect` | `next.config.js` `redirects` | Redirect |

### Route Parity Matrix

Track migration progress route-by-route using this template:

| Vue Route | Next Segment | Owner | SSR Needs | Status |
|---|---|---|---|---|
| `/user/:id` | `app/users/[id]/page.tsx` | @team | `generateMetadata` + dynamic params | ✅ Done |
| `/settings` | `app/(app)/settings/page.tsx` | — | Static | 🔲 Todo |

---

## Layouts

**Vue:** `<router-view />` renders child routes.
**Next.js:** `layout.tsx` with `{children}` renders child pages.

```vue
<!-- Vue: DashboardLayout.vue -->
<template>
  <div class="dashboard">
    <Sidebar />
    <main><router-view /></main>
  </div>
</template>
```

```tsx
// Next.js: app/dashboard/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dashboard">
      <Sidebar />
      <main>{children}</main>
    </div>
  );
}
```

Layouts persist across navigations within their segment — state is preserved.

> **Client State Persistence:** Components rendered inside a shared `layout.tsx` maintain React state across navigations. Components outside the layout boundary (or in a different layout segment) will remount and lose state. Plan your layout hierarchy to align with state-persistence needs.

---

## Navigation

### `<router-link>` → `<Link>`

```vue
<!-- Vue -->
<router-link to="/about">About</router-link>
<router-link :to="{ name: 'user', params: { id: 1 } }">User</router-link>
```

```tsx
// Next.js — uses href, not to. No named routes.
import Link from 'next/link';
<Link href="/about">About</Link>
<Link href={`/users/${id}`}>User</Link>
```

> **Link Prefetch Behavior:** Next.js `<Link>` automatically prefetches routes when the link enters the viewport (production only). This is a significant performance win over Vue Router, which requires manual `prefetch` hints. Use `prefetch={false}` to disable on low-priority links.

### Programmatic Navigation

```ts
// Vue
const router = useRouter()
router.push('/dashboard')
router.replace('/login')
router.go(-1)

// Next.js
import { useRouter } from 'next/navigation';
const router = useRouter();
router.push('/dashboard');
router.replace('/login');
router.back();
```

### Route Params & Query

```ts
// Vue
const route = useRoute()
route.params.id       // dynamic param
route.query.search    // query string
route.path            // current path

// Next.js (client components)
import { useParams, useSearchParams, usePathname } from 'next/navigation';
useParams().id                    // { id: '123' }
useSearchParams().get('search')   // query string
usePathname()                     // '/users/123'
```

> ⚠️ **useSearchParams / useParams are Client Component hooks only.** They are not available in Server Components. `useSearchParams` can return stale values during partial rendering. **Decision:** prefer reading route params from server page props (`params`, `searchParams`) when possible; fall back to client hooks only for client-interactive features.

### Server-Side Redirect

```tsx
import { redirect } from 'next/navigation';
export default async function ProtectedPage() {
  const session = await getSession();
  if (!session) redirect('/login');
  return <Dashboard />;
}
```

---

## Navigation Guards → Middleware

| Vue Guard | Next.js Equivalent |
|---|---|
| `router.beforeEach` (global) | `middleware.ts` at project root |
| `router.afterEach` (global) | `useEffect` in root layout |
| `beforeEnter` (per-route) | `middleware.ts` with pathname matching |
| `beforeRouteEnter` (component) | Server Component check / middleware |
| `beforeRouteLeave` (component) | `onbeforeunload` / custom hook |
| `beforeRouteUpdate` (component) | `useEffect` with params dep |

### Auth Guard Example

**Vue:**
```ts
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})
```

**Next.js:**
```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*', '/admin/:path*'],
};
```

| Aspect | Vue Guards | Next.js Middleware |
|---|---|---|
| Runs on | Client-side | Edge/server (before page loads) |
| Access to | Store, component | Request/response only |
| Cancel | `return false` | `NextResponse.redirect()` |
| Multiple | Chain guards | Single file, conditionals |
| Runtime | Full Node.js | Edge Runtime (limited APIs) |

### beforeRouteLeave → Unsaved Changes

```tsx
'use client';
export function useUnsavedChanges(isDirty: boolean) {
  useEffect(() => {
    if (!isDirty) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ''; };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDirty]);
}
```

### proxy.ts (Next 16+)

Next 16+ introduces `proxy.ts` as the explicit network boundary, replacing `middleware.ts` for request-time logic (redirects, rewrites, headers). Codemods are available (`npx @next/codemod@latest middleware-to-proxy`) for migration.

```ts
// proxy.ts — runs at the network edge
import { NextProxy } from 'next/proxy';

export default function proxy(request: NextProxy) {
  if (!request.cookies.get('auth-token')) {
    return request.redirect('/login');
  }
  request.headers.set('x-custom', 'value');
  return request.next();
}

export const config = { matcher: ['/dashboard/:path*'] };
```

> ⚠️ **proxy.ts runs at the network edge** — don't rely on it for full authorization (use server-side checks too). Fetch caching options (`next.revalidate`, `cache`) have no effect inside proxy handlers.

---

## Route Meta

| Vue `meta` Usage | Next.js Equivalent | Location |
|---|---|---|
| `meta.title` | `export const metadata` or `generateMetadata()` | `page.tsx` |
| `meta.requiresAuth` | Pathname matching | `middleware.ts` |
| `meta.roles` | Token/session check | `middleware.ts` |
| `meta.layout` | Folder structure | File system |
| `meta.revalidate` | `export const revalidate = N` | `page.tsx` |

**Dynamic metadata:**
```tsx
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);
  return { title: post.title, description: post.excerpt };
}
```

---

## Route Groups & Parallel Routes

**Route groups** `(groupName)` organize routes without affecting URLs:
```
app/
  (marketing)/layout.tsx    ← Marketing layout
  (marketing)/about/page.tsx  ← /about
  (app)/layout.tsx          ← App layout (with sidebar)
  (app)/dashboard/page.tsx  ← /dashboard
```

**Parallel routes** render multiple pages simultaneously using `@slot`:
```tsx
// app/layout.tsx — receives named slots as props
export default function Layout({ children, sidebar }: {
  children: React.ReactNode; sidebar: React.ReactNode
}) {
  return <div className="flex"><aside>{sidebar}</aside><main>{children}</main></div>;
}
```

This replaces Vue Router's named views (`<router-view name="sidebar">`).

**Intercepting routes** use `(.)` convention for modal-over-list patterns (e.g., Instagram-style photo modals). Vue has no equivalent.

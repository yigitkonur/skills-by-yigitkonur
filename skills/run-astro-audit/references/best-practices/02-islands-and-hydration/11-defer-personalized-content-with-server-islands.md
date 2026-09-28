# Defer Personalized Content With Server Islands

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 5

## 1. Why We Do This

In traditional web architecture, having a single dynamic or personalized widget on a page (e.g. logged-in user avatar, personalized discounts, real-time cart counts) forces the entire route to be rendered dynamically on every request (`prerender = false`). This eliminates CDN edge caching and dramatically increases Time to First Byte (TTFB). Astro 5's **Server Islands** (`server:defer`) allow the main page to be statically generated and cached at the CDN edge, while dynamic components render independently on-demand.

## 2. How It Differs From Classic React / Next.js

In Next.js, Partial Prerendering (PPR) requires Next.js 14/15 experimental runtime features and edge infrastructure tied to specific hosting providers. In Astro 5, Server Islands are host-agnostic, working across Node.js, Cloudflare, Netlify, and Vercel by converting deferred components into standalone HTTP endpoints fetched asynchronously.

## 3. Common Mistakes & Anti-Patterns

Omitting fallback UI, which creates jarring layout shifts (CLS) when the server island HTML arrives and swaps into the document.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/dashboard.astro - Uncontrolled CLS when user profile arrives
import UserProfile from '../components/UserProfile.astro';
---
<header>
  <h1>Dashboard</h1>
  <!-- Pop-in layout shift causes poor Core Web Vitals (CLS) -->
  <UserProfile server:defer />
</header>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/dashboard.astro - Stable fallback skeleton preventing CLS
import UserProfile from '../components/UserProfile.astro';
import ProfileSkeleton from '../components/ProfileSkeleton.astro';
---
<header>
  <h1>Dashboard</h1>
  <!-- Statically rendered fallback slot displays instantly until dynamic HTML loads -->
  <UserProfile server:defer>
    <ProfileSkeleton slot="fallback" />
  </UserProfile>
</header>
```

In `UserProfile.astro`:

```astro
---
// Runs on-demand on the server; has full access to cookies and database
const session = Astro.cookies.get('session')?.value;
const user = await db.getUser(session);
---
<div class="user-pill">
  <img src={user.avatarUrl} alt={user.name} />
  <span>{user.name}</span>
</div>
```

## 4. Verification & Audit

Run a production build with a server adapter configured:

```bash
npx astro build
```

Verify in build output that the parent page compiles to static HTML while `UserProfile` is split into an on-demand server island route under `_server-islands/`.

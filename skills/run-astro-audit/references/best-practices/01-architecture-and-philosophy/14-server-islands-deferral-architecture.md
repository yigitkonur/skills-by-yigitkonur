# Architect Fast CDN Edge Caching by Deferring Dynamic Data to Server Islands

> **Context:** Architecture & Philosophy | **Impact:** Critical | **Target:** Astro 4.12+ / Astro 5

## 1. Why We Do This

Server Islands (`server:defer`) decouple static, globally cacheable page shells from personalized or dynamic user content. By deferring dynamic components, the main document can be cached aggressively on Edge CDNs (Cloudflare, Fastly) with instant cache hits (TTFB < 50ms), while dynamic islands render independently on the server and swap in without delaying the initial page load.

## 2. How It Differs From Classic React / Next.js

In Next.js App Router, referencing user cookies or request headers in a layout or page header (like displaying a user avatar) often forces the entire route to uncacheable dynamic SSR. In Astro, the page shell remains fully static and edge-cached; only the specific deferred island executes on the origin server.

## 3. Common Mistakes & Anti-Patterns

Blowing away CDN caching across high-traffic marketing and e-commerce product pages simply to render personalized user greeting state in the navigation bar.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/product/[id].astro
// Anti-pattern: Making a 100k-visit/day product page completely uncacheable for an avatar
export const prerender = false; // Forced SSR on every request

const session = Astro.cookies.get('user_session'); // Destroys CDN caching for everyone
const user = session ? await getUser(session.value) : null;
const product = await getProduct(Astro.params.id);
---
<html>
  <body>
    <!-- Entire page load time is now gated by session verification -->
    <header>{user ? `Hi, ${user.name}` : <a href="/login">Sign In</a>}</header>
    <main><h1>{product.title}</h1></main>
  </body>
</html>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/product/[id].astro
// Idiomatic: Page is 100% static/cached on CDN; dynamic user state is deferred
import UserGreeting from '../../components/UserGreeting.astro';
import { getProduct } from '../../lib/products';

const product = await getProduct(Astro.params.id);
---
<html>
  <body>
    <header>
      <!-- Server Island: Loads independently without delaying the static product page -->
      <UserGreeting server:defer>
        <span slot="fallback" class="skeleton-avatar">Loading account...</span>
      </UserGreeting>
    </header>
    <main>
      <h1>{product.title}</h1>
    </main>
  </body>
</html>
```

```astro
---
// src/components/UserGreeting.astro
// This component renders on-demand on the server only when requested by the island
const session = Astro.cookies.get('user_session');
const user = session ? await getUser(session.value) : null;
---
<div>{user ? `Hi, ${user.name}` : <a href="/login">Sign In</a>}</div>
```

## 4. Verification & Audit

Audit HTTP response headers on the main page route:

```bash
curl -I https://mysite.com/product/running-shoes
# Verify 'cf-cache-status: HIT' (or 'age: >0') on the page, with server island loaded asynchronously
```

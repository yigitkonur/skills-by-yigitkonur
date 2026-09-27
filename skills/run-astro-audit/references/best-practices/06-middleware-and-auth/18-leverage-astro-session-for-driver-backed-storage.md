# Leverage Driver-Backed Server Sessions With `Astro.session`

> **Context:** Middleware & Auth | **Impact:** High | **Target:** Astro 5 (v5.7+ Stable)

## 1. Why We Do This

Storing user session state directly in cookies causes significant problems: sensitive data is exposed to client tampering, and browser headers are limited to 4KB per cookie. Astro's native Sessions API (`Astro.session` in pages, `context.session` in middleware and actions) persists user data server-side using unstorage-backed drivers (Redis, Cloudflare KV, filesystem, memory). Only an opaque, cryptographically signed session ID cookie is sent to the client, keeping headers small and sensitive state secure.

## 2. How It Differs From Classic React / Next.js

Next.js provides no built-in session storage abstraction in core, requiring third-party libraries (Auth.js, `iron-session`) or manual cookie serialization. Astro integrates a native session interface across the entire server lifecycle.

## 3. Common Mistakes & Anti-Patterns

Storing large user profile objects, permission arrays, and shopping carts directly in `Astro.cookies.set()`, exceeding cookie size limits and leaking user metadata.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/pages/api/login.ts
export const POST: APIRoute = async ({ request, cookies }) => {
  const user = await authenticate(request)
  // FATAL: Serializing 5KB user object into cookies breaches the 4KB HTTP header limit!
  cookies.set('user_data', JSON.stringify(user), { httpOnly: true, path: '/' })
  return new Response(null, { status: 200 })
}
```

### ✅ Best Practice / Idiomatic

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config'
import node from '@astrojs/node'

export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  session: {
    // Configures unstorage driver (e.g., redis, fs, memory, or cloudflare-kv)
    driver: 'redis',
    options: { url: process.env.REDIS_URL },
    cookie: { name: 'app_session', secure: true, httpOnly: true },
  },
})
```

```astro
---
// src/pages/dashboard.astro
export const prerender = false;

// Access session safely on-demand
const user = await Astro.session?.get('user');
if (!user) {
  return Astro.redirect('/login');
}
---
<h1>Welcome, {user.name}</h1>
```

## 4. Verification & Audit

Inspect the HTTP request/response headers in browser DevTools:

1. Verify only an opaque session ID cookie (e.g., `app_session`) is set on the client.
2. Confirm session values persist across on-demand requests without client-side cookie size inflation.

# Prefer Astro Actions Over Custom POST Endpoints for Internal Client Mutations

> **Context:** Data Fetching & Endpoints | **Impact:** High | **Target:** Astro 5

## 1. Why We Do This

Prior to Astro Actions (standardized in Astro 5), creating client-to-server mutations required writing a manual `POST` API route, establishing manual URL contracts (`fetch("/api/subscribe")`), manually parsing JSON/FormData, manually writing Zod validation, and returning ad-hoc error structures. Astro Actions (`astro:actions`) streamline this by generating end-to-end type-safe RPC functions with automatic input validation and standardized `ActionError` payloads, reducing frontend boilerplate and eliminating route-contract drift.

## 2. How It Differs From Classic React / Next.js

In Next.js, Server Actions are declared using `"use server"` inline within files. Astro separates concerns cleanly by defining all server actions in a single centralized module: `src/actions/index.ts`. On the client, actions can be imported and called like standard async functions with `{ data, error }` return tuples, or wired directly into HTML native `<form action={actions.myAction} method="POST">` for progressive enhancement.

## 3. Common Mistakes & Anti-Patterns

Writing boilerplate-heavy custom API routes for internal UI component buttons and forms.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Newsletter.astro (Legacy manual endpoint approach)
---
<form id="sub-form">
  <input name="email" type="email" required />
  <button type="submit">Subscribe</button>
</form>
<script>
  // Brittle, untyped manual fetch call prone to URL mismatch
  document.getElementById("sub-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = new FormData(e.target as HTMLFormElement).get("email");
    const res = await fetch("/api/newsletter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
  });
</script>
```

### ✅ Best Practice / Idiomatic

```ts
// 1. Define action in src/actions/index.ts
import { defineAction, ActionError } from 'astro:actions'
import { z } from 'astro/zod'

export const server = {
  subscribe: defineAction({
    input: z.object({
      email: z.string().email(),
    }),
    handler: async ({ email }) => {
      const ok = await registerSubscriber(email)
      if (!ok) {
        throw new ActionError({
          code: 'CONFLICT',
          message: 'Email already registered',
        })
      }
      return { success: true, email }
    },
  }),
}
```

```astro
---
// 2. Consume type-safely in src/components/Newsletter.astro
import { actions } from "astro:actions";
---
<form method="POST" action={actions.subscribe}>
  <input name="email" type="email" required />
  <button type="submit">Subscribe</button>
</form>

<script>
  import { actions } from "astro:actions";
  // Type-safe RPC with autocompletion and typed error handling
  const { data, error } = await actions.subscribe({ email: "user@example.com" });
  if (error) console.error(error.message);
</script>
```

## 4. Verification & Audit

Audit your codebase architecture:

- Use **Astro Actions** for UI form submissions, island mutations, and progressive enhancement.
- Reserve **APIRoutes** strictly for webhooks, external REST APIs, and non-HTML assets (RSS, sitemaps, dynamic images).

```bash
# Verify actions compile without type mismatch
pnpm astro check
```

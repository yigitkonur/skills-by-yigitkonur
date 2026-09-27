# Configure Response Headers at the Route Root Before HTML Streaming Commences

> **Context:** Data Fetching & Endpoints | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro leverages HTML chunk streaming in on-demand SSR mode to deliver components to the browser as fast as possible. Consequently, the HTTP status code and response headers are committed and flushed to the wire as soon as the top-level page begins rendering. Modifying response headers (`Astro.response.headers.set(...)`), changing status codes (`Astro.response.status`), or writing cookies (`Astro.cookies.set`) inside child components or layouts will log runtime warnings or silently fail because the HTTP header block has already closed.

## 2. How It Differs From Classic React / Next.js

In single-page React apps, all rendering happens client-side, so HTTP response headers don't exist. In Next.js App Router, modifying headers or cookies inside server components requires middleware or root layout interception. Astro's strict rule is architectural: header and cookie modifications are strictly scoped to the top-level route frontmatter script or API route handler.

## 3. Common Mistakes & Anti-Patterns

Attempting to redirect, set cookies, or alter response cache headers from inside deeply nested components.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/UserProfileCard.astro (Nested Child Component)
// ❌ FAILS IN SSR: Headers already sent to browser!
const { userId } = Astro.props;
const user = await fetchUser(userId);

if (!user) {
  // Attempting to set 404 from a child component has no effect on HTTP status!
  Astro.response.status = 404;
  Astro.response.statusText = "User Not Found";
}
---
<div>{user ? user.name : "Not found"}</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/users/[id].astro (Top-level Page Route)
export const prerender = false;

import UserProfileCard from "../../components/UserProfileCard.astro";
import { fetchUser } from "../../lib/users";

const { id } = Astro.params;
const user = await fetchUser(id);

// ✅ Set status and headers at the PAGE ROOT before HTML streaming begins:
if (!user) {
  Astro.response.status = 404;
  Astro.response.statusText = "User Not Found";
} else {
  Astro.response.headers.set(
    "Cache-Control",
    "public, max-age=60, stale-while-revalidate=300"
  );
}
---
<html>
  <body>
    {user ? <UserProfileCard user={user} /> : <p>User not found.</p>}
  </body>
</html>
```

## 4. Verification & Audit

Verify that the HTTP status matches the expected code even when errors occur:

```bash
# Verify non-existent user returns true HTTP 404 status in curl
curl -I http://localhost:4321/users/non-existent-id
```

Check that the first line of output is `HTTP/1.1 404 Not Found` rather than `200 OK`.

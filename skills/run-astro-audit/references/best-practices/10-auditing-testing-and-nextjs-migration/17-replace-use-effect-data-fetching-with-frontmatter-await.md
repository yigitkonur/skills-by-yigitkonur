# Replace useEffect Client-Side Fetching with Top-Level Frontmatter Await

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In classic React applications, data fetching is commonly delayed until after client-side hydration using `useEffect` hooks and loading spinners. This client-side waterfall delays Largest Contentful Paint (LCP), hurts SEO crawlers that do not wait for secondary fetch promises, and requires managing tedious loading/error state machines in the browser. Astro allows direct top-level `await` in the frontmatter script fence (`---`), fetching data at build or server request time before streaming fully formed HTML.

## 2. How It Differs From Classic React / Next.js

In React, components cannot be async without React Server Components (RSC) and Suspense boundaries. In Astro, every `.astro` component is inherently async. There are no lifecycle hooks (`componentDidMount`, `useEffect`) in `.astro` components; the code fence executes purely on the server.

## 3. Common Mistakes & Anti-Patterns

Porting a React component with `useState` and `useEffect` data fetching into an Astro island with `client:load`. The browser executes an empty initial render, displays a skeleton or spinner, and makes a redundant round-trip HTTP request back to an API that the server could have queried directly.

### ❌ Bad Practice / Anti-Pattern

```tsx
// React Client Component: Delayed client-side fetch waterfall
'use client'
import { useState, useEffect } from 'react'

export default function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then((data) => {
        setUser(data)
        setLoading(false)
      })
  }, [userId])

  if (loading) return <div>Loading profile...</div>
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.bio}</p>
    </div>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro Component: Direct top-level await on server; zero client JS or spinners
interface Props {
  userId: string;
}
const { userId } = Astro.props;

const response = await fetch(`https://api.internal/users/${userId}`);
const user = await response.json();
---
<div>
  <h1>{user.name}</h1>
  <p>{user.bio}</p>
</div>
```

## 4. Verification & Audit

Verify that initial rendered HTML contains the fetched text without relying on client script execution:

```bash
# Verify user name appears directly in the server-emitted HTML payload
curl -s http://localhost:4321/users/123 | grep -i "user.name"
```

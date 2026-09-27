# Prevent Hydration Mismatches From Browser APIs

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

A hydration mismatch occurs when the HTML generated on the server does not match the virtual DOM generated on the client's first render pass. When React or Vue detects a mismatch, it discards the server-rendered HTML and performs a full client re-render from scratch. This incurs a severe performance penalty, causes visible layout flash, and throws console warnings.

## 2. How It Differs From Classic React / Next.js

In Astro, framework components with `client:load`, `client:idle`, or `client:visible` are first server-rendered into static HTML during build/SSR, and then hydrated in the browser. Developers often mistakenly think Astro is "pure static" and directly access `localStorage` or `window.matchMedia` inside component initialization.

## 3. Common Mistakes & Anti-Patterns

Reading `localStorage` or `window` directly in `useState(localStorage.getItem(...))` or evaluating `new Date()` / `Math.random()` during component body execution.

### ❌ Bad Practice / Anti-Pattern

```jsx
// src/components/ThemeToggle.jsx - Non-deterministic SSR vs Client render
import { useState } from 'react'

export default function ThemeToggle() {
  // Server executes fallback 'light'; client sees 'dark' from localStorage!
  // Result: React logs "Text content did not match. Server: 'Light' Client: 'Dark'"
  const [theme, setTheme] = useState(
    typeof window !== 'undefined' ? localStorage.getItem('theme') || 'light' : 'light',
  )

  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme}</button>
}
```

### ✅ Best Practice / Idiomatic

Start with a deterministic default and reconcile client-only state after mount in `useEffect`:

```jsx
// src/components/ThemeToggle.jsx - Deterministic initial SSR render
import { useState, useEffect } from 'react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState('light') // Always deterministic on server & client initial pass

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved) setTheme(saved)
  }, [])

  return (
    <button onClick={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}>{theme}</button>
  )
}
```

_(Or use `client:only="react"` if the component has no SEO purpose and requires zero server rendering)._

## 4. Verification & Audit

Run dev mode and open the browser console:

```bash
npx astro dev
```

Verify zero React warnings containing `Hydration failed because the server rendered HTML didn't match the client` or `Text content did not match`.

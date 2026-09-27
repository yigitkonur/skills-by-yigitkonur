# Migrate Next.js App Router layout.tsx to Astro BaseLayout Using Slots

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Next.js App Router, `app/layout.tsx` wraps pages via React component nesting, taking `{children: React.ReactNode}` and relying on an external `metadata` export to inject `<head>` tags. In Astro, layouts are native `.astro` components that encapsulate the entire `<!DOCTYPE html>` shell, use web-standard `<slot />` projection for page content, and receive SEO metadata directly through typed `Astro.props` rendered straight into `<head>`.

## 2. How It Differs From Classic React / Next.js

In Next.js, layouts persist across page navigations in the client's virtual DOM state. In Astro's Multi-Page Architecture (MPA), every route navigation loads a complete, isolated document, preventing memory leaks, stale React context states, and cross-route hydration bugs.

## 3. Common Mistakes & Anti-Patterns

Developers migrating from Next.js try to declare `export const metadata = { ... }` or pass `children` as a prop in an `.astro` file. Neither works in Astro. Another mistake is wrapping the layout in a React Context Provider or client component.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js: app/layout.tsx
import type { Metadata } from 'next'
export const metadata: Metadata = { title: 'My Site' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro: src/layouts/BaseLayout.astro
interface Props {
  title: string;
  description?: string;
}

const { title, description = 'Default description' } = Astro.props;
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <meta name="description" content={description} />
  </head>
  <body>
    <header><nav>...</nav></header>
    <main>
      <!-- Web standard slot replaces React {children} -->
      <slot />
    </main>
    <footer>...</footer>
  </body>
</html>
```

## 4. Verification & Audit

Verify that the layout renders clean HTML doctype and metadata without uncompiled JSX tokens:

```bash
# Verify rendered HTML doctype and head title in dist output
grep -i '<!doctype html>' dist/index.html && grep -i '<title>My Site</title>' dist/index.html
```

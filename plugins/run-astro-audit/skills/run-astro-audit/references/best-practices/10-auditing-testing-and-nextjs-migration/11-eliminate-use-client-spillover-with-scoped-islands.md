# Eliminate Next.js "use client" Spillover by Scoping Hydration to Isolated Leaves

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Next.js App Router, declaring `'use client'` at the top of a module sets a boundary that forces the component and every single component it imports into the client JavaScript bundle. For example, making a mobile menu toggle interactive in Next.js often forces the entire navigation bar, company logo, and link list into client JS. Astro prevents client contagion: hydration directives are declared at the JSX/Astro callsite (`client:visible`), and children passed to islands via `<slot />` remain 100% static HTML.

## 2. How It Differs From Classic React / Next.js

Next.js client boundaries flow downward through the import graph. Astro island boundaries are strictly isolated containers (`<astro-island>`). An interactive island can wrap static `.astro` components; the inner content renders on the server and is preserved as static HTML inside the island's slot without entering the client JavaScript bundle.

## 3. Common Mistakes & Anti-Patterns

In Next.js migrations, developers import static content or heavy markdown into a React component that contains a button or accordion, bloating the client bundle by hundreds of kilobytes.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js: Entire HeroSection becomes client JS because of interactive modal
'use client'
import { useState } from 'react'
import StaticHeavyCopy from './StaticHeavyCopy'
import HeavySvgDiagram from './HeavySvgDiagram'

export default function HeroSection() {
  const [open, setOpen] = useState(false)
  return (
    <section>
      {/* Contaminated: Both static components are bundled into client JS */}
      <StaticHeavyCopy />
      <HeavySvgDiagram />
      <button onClick={() => setOpen(true)}>Open Demo</button>
    </section>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro: Static server content passed through slot to isolated client island
import StaticHeavyCopy from './StaticHeavyCopy.astro';
import HeavySvgDiagram from './HeavySvgDiagram.astro';
import ModalDialog from './ModalDialog.jsx';
---
<section>
  <!-- Pure static HTML: 0 KB client JS -->
  <StaticHeavyCopy />
  <HeavySvgDiagram />

  <!-- Surgical island: Only the modal code and button are hydrated -->
  <ModalDialog client:visible>
    <p>Modal content rendered on server</p>
  </ModalDialog>
</section>
```

## 4. Verification & Audit

Verify that the static child components are not present in the client JS bundle:

```bash
# Check client bundle chunks for static strings that should only exist in HTML
grep -rn "StaticHeavyCopy" dist/_astro/*.js && \
  echo "FAIL: Static content leaked into client bundle" || \
  echo "PASS: Client bundle strictly isolated"
```

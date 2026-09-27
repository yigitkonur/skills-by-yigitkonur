# Never Use Framework Context to Share State Across Islands

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Each Astro client island initializes an independent React root (`createRoot` or `hydrateRoot`). React Context, Svelte Context, and Vue Provide/Inject rely fundamentally on a shared, unified virtual DOM tree. A `<ThemeProvider>` or `<CartContext.Provider>` inside Island A cannot propagate context down to Island B across the static HTML boundary. Attempting to do so results in silent default state or `useContext must be used within Provider` runtime exceptions.

## 2. How It Differs From Classic React / Next.js

In a classic React SPA or Next.js app, the entire document is rooted under a single React tree, making root context providers standard. In Astro, islands are deliberately isolated runtime enclaves floating in static HTML.

## 3. Common Mistakes & Anti-Patterns

Wrapping page sections or layouts in a React Context Provider in `.astro` layouts and expecting separate islands across the page to read that context.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/layouts/BaseLayout.astro - Context provider cannot reach other islands!
import { CartProvider } from '../context/CartContext.jsx';
import HeaderCartBadge from '../components/HeaderCartBadge.jsx';
import AddToCartButton from '../components/AddToCartButton.jsx';
---
<!-- CartProvider creates an isolated root; HeaderCartBadge gets DEFAULT state -->
<CartProvider client:load>
  <header>
    <HeaderCartBadge client:load />
  </header>
  <main>
    <AddToCartButton client:idle />
  </main>
</CartProvider>
```

### ✅ Best Practice / Idiomatic

Use a framework-agnostic shared store like **Nanostores** exported as a module singleton:

```javascript
// src/stores/cart.js
import { atom } from 'nanostores'
export const cartCount = atom(0)
```

```astro
---
// src/layouts/BaseLayout.astro - Islands subscribe independently to Nanostore
import HeaderCartBadge from '../components/HeaderCartBadge.jsx';
import AddToCartButton from '../components/AddToCartButton.jsx';
---
<header>
  <HeaderCartBadge client:load />
</header>
<main>
  <AddToCartButton client:idle />
</main>
```

## 4. Verification & Audit

Run a component test or browser check: trigger an increment in `AddToCartButton` and observe if `HeaderCartBadge` re-renders. If using React Context across separate islands, the badge count will fail to update.

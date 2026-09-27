# Replace Global React Context Providers with Micro Nanostores Across Islands

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

In Next.js, application state (cart, auth, theme) is commonly stored in a React Context Provider wrapping the entire root layout. In Astro, every interactive island runs as an independent React root mounted into the DOM. Because Astro islands do not share a common virtual DOM parent, a React Context Provider in one island or layout cannot provide values to a separate island elsewhere on the page. Nanostores provides a framework-agnostic, micro-sized (<1 KB) atomic state solution that synchronizes state across disparate islands without a monolithic React tree.

## 2. How It Differs From Classic React / Next.js

React Context requires an uninterrupted React component tree from Provider to Consumer. Nanostores exist outside the component tree as vanilla JavaScript event emitters (`atom`, `map`). Any island (React, Svelte, Vue, or vanilla TS) can subscribe using hooks like `useStore($atom)` or direct event listeners.

## 3. Common Mistakes & Anti-Patterns

Attempting to create a `<RootProvider>` React component in `Layout.astro` and nesting `<slot />` inside it, expecting child React islands to read the context. In Astro, slot children inside a React component do not share that component's React context unless both are part of the exact same client island bundle.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js pattern that fails across Astro islands:
// src/components/CartProvider.tsx
export const CartContext = createContext<CartState>(null!)
export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState([])
  return <CartContext.Provider value={{ items, setItems }}>{children}</CartContext.Provider>
}
// Using this in Layout.astro FAILS: separate islands cannot read CartContext!
```

### ✅ Best Practice / Idiomatic

```ts
// src/stores/cart.ts - Framework-agnostic atomic store
import { atom } from 'nanostores'

export interface CartItem {
  id: string
  name: string
}
export const $cart = atom<CartItem[]>([])

export function addToCart(item: CartItem) {
  $cart.set([...$cart.get(), item])
}
```

```tsx
// src/components/CartBadge.tsx (React Island)
import { useStore } from '@nanostores/react'
import { $cart } from '../stores/cart'

export default function CartBadge() {
  const items = useStore($cart)
  return <span>Items: {items.length}</span>
}
```

## 4. Verification & Audit

Verify that two distinct islands communicate across the DOM without React Context errors:

```bash
# Verify no React Context missing provider errors in browser console
# Test island state dispatch: $cart.set([...]) updates both islands synchronously
```

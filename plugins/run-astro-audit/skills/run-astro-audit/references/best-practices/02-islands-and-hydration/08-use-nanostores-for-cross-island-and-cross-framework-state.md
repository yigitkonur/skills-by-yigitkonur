# Use Nanostores for Cross-Island and Cross-Framework State

> **Context:** Islands & Hydration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Nanostores is a zero-dependency, tiny (~1 KB) state manager designed specifically for island architectures and multi-framework environments. It uses ES module singletons, allowing a React island, a Vue island, a Svelte island, and vanilla client scripts on the same page to share synchronous state without unifying component trees or downloading heavy runtime frameworks (like Redux or Zustand).

## 2. How It Differs From Classic React / Next.js

In Next.js, state management usually binds tightly to React hooks (`useContext`, Zustand, Redux). In Astro, Nanostores decouples state from the UI framework. Each framework uses a thin adapter (`@nanostores/react`, `@nanostores/vue`, `@nanostores/svelte`) to subscribe to the exact same store instance.

## 3. Common Mistakes & Anti-Patterns

Dispatching custom DOM events (`window.dispatchEvent(new CustomEvent('cart-update'))`) or polling `localStorage` in each island instead of using reactive Nanostores.

### ❌ Bad Practice / Anti-Pattern

```javascript
// Fragile, untyped window event passing between islands
window.dispatchEvent(new CustomEvent('updateCart', { detail: { id: 'item-1' } }))
// In other island:
useEffect(() => {
  const handler = (e) => setCount(e.detail.count)
  window.addEventListener('updateCart', handler)
  return () => window.removeEventListener('updateCart', handler)
}, [])
```

### ✅ Best Practice / Idiomatic

```typescript
// src/stores/cart.ts
import { atom, map } from 'nanostores'

export type CartItem = { id: string; name: string; quantity: number }
export const isCartOpen = atom<boolean>(false)
export const cartItems = map<Record<string, CartItem>>({})

export function addCartItem(item: Omit<CartItem, 'quantity'>) {
  const existing = cartItems.get()[item.id]
  if (existing) {
    cartItems.setKey(item.id, { ...existing, quantity: existing.quantity + 1 })
  } else {
    cartItems.setKey(item.id, { ...item, quantity: 1 })
  }
}
```

In a React island (`CartBadge.jsx`):

```jsx
import { useStore } from '@nanostores/react'
import { cartItems } from '../stores/cart'

export default function CartBadge() {
  const $items = useStore(cartItems)
  const total = Object.values($items).reduce((sum, i) => sum + i.quantity, 0)
  return <span class="badge">{total}</span>
}
```

## 4. Verification & Audit

Verify bundle size contribution:

```bash
npx bundlesize dist/_astro/*nanostores*
```

Nanostores core adds < 1 KB gzipped, and subscriptions cleanly tear down when islands unmount.

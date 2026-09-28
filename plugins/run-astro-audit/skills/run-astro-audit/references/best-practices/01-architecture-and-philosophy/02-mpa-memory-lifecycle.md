# Embrace Multi-Page Architecture (MPA) Clean Memory Lifecycle Over Persistent SPA Heap

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro is built as a Multi-Page Application (MPA). On each standard navigation, the browser discards the previous document context, resets the JavaScript heap, and frees all memory allocated by DOM trees, third-party libraries, and event listeners. This eliminates persistent memory leaks, garbage collection pauses, and performance degradation during prolonged browsing sessions.

## 2. How It Differs From Classic React / Next.js

SPAs maintain a long-running JavaScript execution environment across page transitions. In Next.js, memory leaks from dangling intervals, uncancelled network requests, and detached DOM references accumulate in heap memory as the user traverses routes. Astro’s MPA model provides deterministic cleanup by default on every page turn.

## 3. Common Mistakes & Anti-Patterns

Developers accustomed to SPAs often attempt to maintain client-side runtime singletons or complex global root stores on `window`, expecting states to magically persist across standard MPA page transitions without leveraging web storage or cookies.

### ❌ Bad Practice / Anti-Pattern

```typescript
// src/scripts/cartState.ts
// Anti-pattern: Attempting to store SPA-like global mutable state on window across MPA routes
declare global {
  interface Window {
    __STORE_CART__: Array<{ id: string; quantity: number }>
  }
}

// In an MPA, window resets on navigation; items disappear when clicking another page
export function addToCart(item: { id: string; quantity: number }) {
  window.__STORE_CART__ = window.__STORE_CART__ || []
  window.__STORE_CART__.push(item)
}
```

### ✅ Best Practice / Idiomatic

```typescript
// src/scripts/cartState.ts
// Idiomatic: Use browser-native persistence (localStorage/cookies) or Nanostores
const CART_KEY = 'store_cart_v1'

export function getCart(): Array<{ id: string; quantity: number }> {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(CART_KEY) || '[]')
  } catch {
    return []
  }
}

export function addToCart(item: { id: string; quantity: number }) {
  const current = getCart()
  const updated = [...current, item]
  localStorage.setItem(CART_KEY, JSON.stringify(updated))
  window.dispatchEvent(new CustomEvent('cart:updated', { detail: updated }))
}
```

## 4. Verification & Audit

Audit memory across multi-page navigation using Chrome DevTools:

1. Open Chrome DevTools -> **Memory** tab -> Select **Allocation instrumentation on timeline**.
2. Navigate between 5–10 pages of your Astro site.
3. Observe that after each page navigation, the JS heap drops back to near-zero baseline bytes, confirming no retained detached trees.

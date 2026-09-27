# Read Nanostores With .get() in Event Handlers

> **Context:** Islands & Hydration | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

The `useStore(store)` hook in `@nanostores/react`, `@nanostores/vue`, and `@nanostores/preact` subscribes the component to store updates, forcing a component re-render every time the store changes value. When a component only needs to read store data inside an event handler, callback, or submission function (and does not display that value in its UI template), calling `useStore` creates wasteful re-renders. Reading directly with `store.get()` avoids unnecessary subscriptions and re-renders.

## 2. How It Differs From Classic React / Next.js

In standard React with `useState` or context, values are accessed via hook state variables that inherently re-render the component. Nanostores stores are decoupled from the React lifecycle: `.get()` is an instantaneous, synchronous accessor that operates outside the React rendering loop.

## 3. Common Mistakes & Anti-Patterns

Subscribing an "Add to Cart" button or search bar to an entire items store with `useStore` merely to append a new item on submit, causing the button to re-render whenever _any_ item is added elsewhere.

### ❌ Bad Practice / Anti-Pattern

```jsx
// src/components/AddToCartButton.jsx - Wasteful re-renders on every store change
import { useStore } from '@nanostores/react'
import { cartItems, addCartItem } from '../stores/cart'

export default function AddToCartButton({ product }) {
  // Re-renders AddToCartButton every time cartItems changes!
  const $cartItems = useStore(cartItems)

  function handleClick() {
    addCartItem(product)
  }

  return <button onClick={handleClick}>Add to Cart</button>
}
```

### ✅ Best Practice / Idiomatic

```jsx
// src/components/AddToCartButton.jsx - Zero re-renders on store updates
import { cartItems, addCartItem } from '../stores/cart'

export default function AddToCartButton({ product }) {
  function handleClick() {
    // Read directly when the event fires, without subscribing to re-renders
    const current = cartItems.get()
    addCartItem(product)
  }

  return <button onClick={handleClick}>Add to Cart</button>
}
```

## 4. Verification & Audit

Use React DevTools "Highlight updates when components render":
Trigger cart actions from another island and confirm that `AddToCartButton` does NOT flash or re-render when other items are added.

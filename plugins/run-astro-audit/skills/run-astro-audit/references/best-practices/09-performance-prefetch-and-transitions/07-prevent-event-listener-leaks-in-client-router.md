# Prevent Memory Leaks and Duplicate Listeners Under ClientRouter

> **Context:** Performance & Prefetch | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

When `<ClientRouter />` is active, Astro swaps the DOM during page navigation without refreshing the global JavaScript execution context. Traditional `DOMContentLoaded` events do not re-fire on page transitions. Conversely, registering global event listeners inside `astro:page-load` without idempotency attaches duplicate listeners on every navigation, leaking memory and multiplying callback executions.

## 2. How It Differs From Classic React / Next.js

In React/Next.js, `useEffect` cleanups (`return () => ...`) automatically detach listeners on unmount. In Astro vanilla client scripts, there is no automatic unmount cycle. Developers must manually handle lifecycle idempotency using `astro:page-load` and clean up global listeners on `astro:before-swap`.

## 3. Common Mistakes & Anti-Patterns

Stacking duplicate window listeners on every navigation, or expecting `DOMContentLoaded` to initialize interactive elements after page transition.

### ❌ Bad Practice / Anti-Pattern

```html
<!-- src/components/NavDrawer.astro -->
<button id="drawer-toggle">Menu</button>

<script>
  // LEAK: Adds a new listener to window on EVERY page transition!
  document.addEventListener('astro:page-load', () => {
    window.addEventListener('resize', () => {
      console.log('Resize handler called') // Multiplies N times after N navigations
    })

    // BROKEN: Elements on navigated pages will not respond if using DOMContentLoaded
  })
</script>
```

### ✅ Best Practice / Idiomatic

```html
<!-- src/components/NavDrawer.astro -->
<button id="drawer-toggle">Menu</button>

<script>
  function setupDrawer() {
    const btn = document.getElementById('drawer-toggle')
    if (!btn || btn.dataset.initialized) return
    btn.dataset.initialized = 'true'

    const onToggle = () => btn.classList.toggle('active')
    btn.addEventListener('click', onToggle)
  }

  // Idempotent initialization on every page visit
  document.addEventListener('astro:page-load', setupDrawer)
</script>
```

## 4. Verification & Audit

In Chrome DevTools Console, navigate between pages 5 times, then inspect attached listeners on the element:

```javascript
getEventListeners(document.getElementById('drawer-toggle'))
```

Confirm that the `click` listener count is exactly 1, not 5.

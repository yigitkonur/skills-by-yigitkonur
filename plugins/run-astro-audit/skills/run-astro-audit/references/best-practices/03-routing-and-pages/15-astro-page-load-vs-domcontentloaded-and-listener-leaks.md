# Replace DOMContentLoaded and Prevent Event Listener Memory Leaks

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Under `<ClientRouter />`, `DOMContentLoaded` only fires on the very first page visit, leaving scripts inert on subsequent client navigations. Switching to `astro:page-load` fixes this because it fires on initial load and every navigation. However, blindly attaching window listeners or intervals inside `astro:page-load` causes duplicate callbacks to accumulate, leaking memory and slowing down the browser.

## 2. How It Differs From Classic React / Next.js

In React, `useEffect(() => { ... return () => cleanup(); }, [])` automatically provides a cleanup return function when unmounting. In Astro vanilla client scripts, there is no automatic unmount hook. You must manually clean up timers, observers, and window listeners on `astro:before-swap` or use an `AbortController`.

## 3. Common Mistakes & Anti-Patterns

Using `DOMContentLoaded` (broken navigation) or registering persistent window event listeners inside `astro:page-load` without cleanup, multiplying listeners by 10x after 10 page navigations.

### ❌ Bad Practice / Anti-Pattern

```html
<script>
  // Trap 1: DOMContentLoaded never fires on client navigation
  document.addEventListener('DOMContentLoaded', () => {
    initWidget()
  })

  // Trap 2: Memory leak! Stacks an extra listener on every page navigation
  document.addEventListener('astro:page-load', () => {
    window.addEventListener('scroll', () => {
      console.log('Scrolled!') // Fires N times after N navigations!
    })
    setInterval(() => updateClock(), 1000) // Orphaned timers accumulate!
  })
</script>
```

### ✅ Best Practice / Idiomatic

```html
<script>
  // Clean, leak-free pattern using AbortController
  let pageAbortController

  document.addEventListener('astro:page-load', () => {
    // Abort previous page listeners if any remain
    pageAbortController?.abort()
    pageAbortController = new AbortController()
    const { signal } = pageAbortController

    // Attach listeners bound to the signal
    window.addEventListener('scroll', handleScroll, { signal })
    window.addEventListener('keydown', handleKeydown, { signal })

    const timer = setInterval(updateData, 5000)

    // Clean up timers and observers right before DOM swap
    document.addEventListener(
      'astro:before-swap',
      () => {
        clearInterval(timer)
        pageAbortController?.abort()
      },
      { once: true },
    )
  })

  function handleScroll() {
    /* ... */
  }
  function handleKeydown() {
    /* ... */
  }
  function updateData() {
    /* ... */
  }
</script>
```

## 4. Verification & Audit

In Chrome DevTools Console, inspect listener counts before and after 5 page transitions:

```javascript
getEventListeners(window).scroll?.length
```

Verify that the count remains 1 and does not increment with each navigation.

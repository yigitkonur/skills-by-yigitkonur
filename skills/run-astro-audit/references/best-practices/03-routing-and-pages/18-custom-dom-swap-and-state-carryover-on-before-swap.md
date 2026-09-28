# Intercept DOM Swap to Carry State and Prevent Flash in before-swap

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

During client-side navigation, the incoming page is parsed as an off-screen `Document` object (`event.newDocument`). Hooking into `astro:before-swap` allows developers to mutate the incoming document attributes (such as theme classes or authentication flags) **before** it is painted to screen, completely eliminating theme flashing (FOUC) and visual jitter.

## 2. How It Differs From Classic React / Next.js

In SPA frameworks, theme context providers re-evaluate state in memory and update the root DOM element during re-render. In Astro's `<ClientRouter />`, the server returns a static HTML page with default attributes (e.g. `data-theme="light"`). If the user selected dark mode in `localStorage`, `astro:before-swap` lets you mutate `event.newDocument` before the swap occurs.

## 3. Common Mistakes & Anti-Patterns

Setting theme classes inside `astro:page-load`. By the time `astro:page-load` fires, the browser has already painted the new page with the server default theme, resulting in an unpleasant white flash for dark mode users.

### ❌ Bad Practice / Anti-Pattern

```html
<script>
  // FLASH OF UNSTYLED CONTENT (FOUC):
  // Fires AFTER the new page is already visible on screen!
  document.addEventListener('astro:page-load', () => {
    if (localStorage.getItem('theme') === 'dark') {
      document.documentElement.classList.add('dark')
    }
  })
</script>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/ThemeSynchronizer.astro
---
<script>
  import { swapFunctions } from "astro:transitions/client";

  document.addEventListener("astro:before-swap", (event) => {
    // 1. Sync theme to incoming document before it is inserted
    const storedTheme = localStorage.getItem("theme") || "system";
    const isDark = storedTheme === "dark" ||
      (storedTheme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

    if (isDark) {
      event.newDocument.documentElement.classList.add("dark");
    } else {
      event.newDocument.documentElement.classList.remove("dark");
    }

    // 2. Custom swap logic (optional): preserve custom form inputs or focus
    // event.swap = () => {
    //   swapFunctions.swapRootAttributes(event.newDocument);
    //   swapFunctions.swapHeadElements(event.newDocument);
    //   swapFunctions.swapBodyElement(event.newDocument.body, document.body);
    // };
  });
</script>
```

## 4. Verification & Audit

Switch to dark mode in your application. Rapidly click through multiple pages.
Verify with high-speed video or visual inspection that zero light flashes occur between route transitions.

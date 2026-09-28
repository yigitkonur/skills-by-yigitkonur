# Manage Programmatic Navigation and Scroll Restoration with navigate()

> **Context:** Routing & Pages | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

While standard navigation uses `<a>` tags, interactive interfaces (such as drop-down jump menus, multi-step wizards, or post-action redirects) require programmatic navigation. The `navigate()` function from `astro:transitions/client` invokes client routing programmatically while preserving view transitions and lifecycle events.

## 2. How It Differs From Classic React / Next.js

In Next.js, programmatic routing uses `useRouter().push('/path')`. In Astro, `navigate('/path', options)` can be called from any client script, Web Component, or React/Vue island. It accepts `{ history: 'push' | 'replace' }` and triggers the same preparation and swap lifecycle as link clicks.

## 3. Common Mistakes & Anti-Patterns

Calling `window.location.href = url` inside an app that uses `<ClientRouter />`. This forces an abrupt full-page browser reload, completely bypassing the View Transitions animation and resetting persistent islands.

### ❌ Bad Practice / Anti-Pattern

```html
<script>
  // BAD: Full browser refresh destroys view transitions and resets player state!
  function onFilterChange(category) {
    window.location.href = `/catalog?category=${category}`
  }
</script>
```

### ✅ Best Practice / Idiomatic

```html
<select id="category-picker">
  <option value="/catalog?category=all">All</option>
  <option value="/catalog?category=shoes">Shoes</option>
  <option value="/catalog?category=hats">Hats</option>
</select>

<script>
  import { navigate } from "astro:transitions/client";

  document.addEventListener("astro:page-load", () => {
    const select = document.getElementById("category-picker");

    select?.addEventListener("change", (e) => {
      const targetUrl = (e.target as HTMLSelectElement).value;

      // Programmatic SPA navigation with custom history option
      navigate(targetUrl, {
        history: "push",
      });
    });
  });

  // Custom scroll restoration override if desired
  document.addEventListener("astro:after-swap", () => {
    // Ensures page instantly scrolls to top on navigation
    window.scrollTo({ left: 0, top: 0, behavior: "instant" });
  });
</script>
```

## 4. Verification & Audit

In your browser, trigger programmatic navigation via the select input. Check DevTools to confirm that page transitions animate smoothly without a full browser reload, and that the scroll position resets cleanly.

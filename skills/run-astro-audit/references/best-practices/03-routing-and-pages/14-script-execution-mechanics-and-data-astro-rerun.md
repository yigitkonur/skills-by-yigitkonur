# Differentiate Bundled Module Scripts from is:inline and data-astro-rerun

> **Context:** Routing & Pages | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

By default, Astro processes `<script>` tags as ES modules: they are bundled, deduplicated, and executed **once per session**. Under `<ClientRouter />`, navigating to a new page does **not** re-run bundled module scripts. Understanding how Astro processes scripts prevents broken client interactivity on secondary navigations.

## 2. How It Differs From Classic React / Next.js

In React/Next.js, components run their body on every render and mount effects via `useEffect`. In Astro, `.astro` components are server-only. A `<script>` tag inside an `.astro` component is extracted into a client-side bundle that evaluates once upon download. To re-run script logic across page transitions, you must hook into `astro:page-load` or use `is:inline data-astro-rerun`.

## 3. Common Mistakes & Anti-Patterns

Writing top-level DOM queries directly in a bundled `<script>` tag and expecting them to re-execute when the user clicks to another page. The script runs on the initial page, but subsequent pages never attach the event listeners.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Menu.astro
---
<button id="toggle-btn">Menu</button>

<script>
  // FAILS ON SUBSEQUENT PAGES:
  // This module executes once when first imported.
  // After navigating with ClientRouter, this code does NOT re-run!
  const btn = document.getElementById("toggle-btn");
  btn?.addEventListener("click", () => alert("Clicked!"));
</script>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/Menu.astro
interface Props {
  initialOpen?: boolean;
}
const { initialOpen = false } = Astro.props;
---
<!-- Pass server props to client via data-* attributes -->
<div id="menu-container" data-initial-open={String(initialOpen)}>
  <button id="toggle-btn">Menu</button>
</div>

<script>
  // Idiomatic pattern 1: Listen to astro:page-load in bundled scripts
  document.addEventListener("astro:page-load", () => {
    const container = document.getElementById("menu-container");
    const btn = document.getElementById("toggle-btn");

    btn?.addEventListener("click", () => {
      console.log("Toggle menu, initial was:", container?.dataset.initialOpen);
    });
  });
</script>

<!-- Idiomatic pattern 2: Force raw script re-execution using data-astro-rerun -->
<script is:inline data-astro-rerun>
  // Runs every time this page is visited via client-side routing
  console.log("Page visited, running tracking beacon");
</script>
```

## 4. Verification & Audit

In browser, navigate between pages. Check console logs to verify that page setup logic runs on every transition rather than only on hard refresh.

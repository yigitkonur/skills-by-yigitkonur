# Treat Astro Templates as Pure HTML Compilers Without Virtual DOM or Reactive State Hooks

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro components are templating functions that execute once per render pass to produce an HTML string or stream. There is no client-side Virtual DOM, no component instance in browser memory, and no reactive re-rendering engine. Eliminating the Virtual DOM removes runtime diffing costs, state reconciliation loops, and memory bloat entirely.

## 2. How It Differs From Classic React / Next.js

React components continuously re-render whenever state or props change, requiring hooks (`useState`, `useEffect`, `useCallback`) to manage lifecycle. In Astro, the component script runs strictly once on the server. Frontmatter variables are evaluated at generation time; changing a variable afterward has zero effect on the browser DOM.

## 3. Common Mistakes & Anti-Patterns

React developers often write inline JSX event handlers like `onClick={...}` or try to declare reactive state variables in frontmatter, expecting client-side interactivity without a client island or native script.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/components/Counter.astro
// Anti-pattern: Treating an Astro template like a reactive React component
let count = 0;

function increment() {
  // BROKEN: This function only exists on the server during build/render!
  count++;
}
---
<div>
  <!-- BROKEN: onClick is not an Astro prop; this will not fire in the browser -->
  <button onClick={increment}>Clicked {count} times</button>
</div>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/components/Counter.astro
// Idiomatic: Use native HTML + bundled <script> or a Custom Element
interface Props {
  initialCount?: number;
}
const { initialCount = 0 } = Astro.props;
---
<counter-widget data-count={initialCount}>
  <button type="button">Clicked <span>{initialCount}</span> times</button>
</counter-widget>

<script>
  class CounterWidget extends HTMLElement {
    connectedCallback() {
      let count = Number(this.dataset.count) || 0;
      const btn = this.querySelector('button');
      const span = this.querySelector('span');

      btn?.addEventListener('click', () => {
        count++;
        if (span) span.textContent = String(count);
      });
    }
  }
  customElements.define('counter-widget', CounterWidget);
</script>
```

## 4. Verification & Audit

Audit template attributes using the Astro linter and compiler:

```bash
npx astro check
# Flag invalid client event handlers like onClick or onChange on native HTML tags
```

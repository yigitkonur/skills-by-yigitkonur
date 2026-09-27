# Enforce Strict Framework Isolation and Avoid Direct Cross-Framework Imports

> **Context:** Architecture & Philosophy | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro’s Bring Your Own Framework (BYOF) architecture allows React, Svelte, Vue, Preact, and Solid to run side-by-side on the same page. Each framework runs inside its own isolated island container. Maintaining a clean boundary ensures that framework runtimes do not pollute each other's execution context, and prevents incompatible AST transforms from breaking compiler passes.

## 2. How It Differs From Classic React / Next.js

Next.js enforces a single framework paradigm (React only). In Astro, multiple UI runtimes can coexist on a single route, but they cannot import each other directly inside framework files (e.g. `.jsx` cannot import `.svelte`). Composition must happen in an `.astro` component.

## 3. Common Mistakes & Anti-Patterns

Attempting to import a Svelte or Vue component directly inside a React JSX file causes compilation failures because the React Vite plugin cannot process foreign template syntax or component lifecycle hooks.

### ❌ Bad Practice / Anti-Pattern

```jsx
// src/components/react/ProductConfigurator.jsx
// Anti-pattern: Direct cross-framework import inside a React component
import SveltePriceCalculator from '../svelte/PriceCalculator.svelte' // FATAL COMPILER ERROR

export default function ProductConfigurator({ basePrice }) {
  return (
    <div className="configurator">
      <h2>Configure Product</h2>
      {/* React cannot instantiate or hydrate a Svelte component */}
      <SveltePriceCalculator price={basePrice} />
    </div>
  )
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/product/[id].astro
// Idiomatic: Compose cross-framework islands inside an Astro template using slots
import ProductConfigurator from '../../components/react/ProductConfigurator.jsx';
import SveltePriceCalculator from '../../components/svelte/PriceCalculator.svelte';

const { id } = Astro.params;
const basePrice = 499;
---
<main>
  <!-- Astro orchestrates both islands safely -->
  <ProductConfigurator client:load basePrice={basePrice}>
    <div slot="calculator">
      <SveltePriceCalculator client:idle price={basePrice} />
    </div>
  </ProductConfigurator>
</main>
```

```jsx
// src/components/react/ProductConfigurator.jsx
// React component accepts slotted content via props.calculator or props.children
export default function ProductConfigurator({ basePrice, calculator }) {
  return (
    <div className="configurator">
      <h2>Configure Product</h2>
      {calculator}
    </div>
  )
}
```

## 4. Verification & Audit

Run type checking and project diagnostics to verify island boundary integrity:

```bash
npx astro check
# Ensure zero JSX syntax errors or unrecognized loader errors across integrations
```

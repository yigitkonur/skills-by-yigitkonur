# Pass Static Markup via Astro Slots Instead of Dynamic Render Props to Framework Islands

> **Context:** Architecture & Philosophy | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro components render to static HTML strings either at build time or on-demand on the server. Because Astro has no client-side runtime, it cannot serialize and transfer executable JavaScript functions from an `.astro` component to a hydrated client island. Passing markup through Astro slots provides a clean serialization boundary.

## 2. How It Differs From Classic React / Next.js

In React/Next.js applications, passing functions as props or using "render props" (e.g., `renderItem={(item) => <div>{item}</div>}`) is common. In Astro, attempting to pass a render function from frontmatter or template to a hydrated island will silently fail or throw a serialization error.

## 3. Common Mistakes & Anti-Patterns

Passing dynamic callbacks or render props from an Astro component into a hydrated React island leads to broken interactivity, as functions cannot cross the server-client boundary.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/catalog.astro
// Anti-pattern: Attempting to pass a render prop from an Astro file to a React island
import ProductTable from '../components/react/ProductTable.jsx';
const products = [{ id: '1', name: 'Running Shoes', price: 90 }];
---
<main>
  <!-- BROKEN: Astro cannot serialize the renderRow callback to the browser -->
  <ProductTable
    client:visible
    items={products}
    renderRow={(product) => <tr><td>{product.name}</td></tr>}
  />
</main>
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/catalog.astro
// Idiomatic: Pass serializable data as props, or use slots for static markup
import ProductTable from '../components/react/ProductTable.jsx';
const products = [{ id: '1', name: 'Running Shoes', price: 90 }];
---
<main>
  <ProductTable client:visible items={products}>
    <!-- Slot markup is rendered on the server and passed as props.children or named slots -->
    <caption slot="caption">Seasonal Product Catalog 2026</caption>
  </ProductTable>
</main>
```

```jsx
// src/components/react/ProductTable.jsx
// React island handles its own internal item rendering or consumes slotted children
export default function ProductTable({ items, caption }) {
  return (
    <table>
      {caption}
      <tbody>
        {items.map((item) => (
          <tr key={item.id}>
            <td>{item.name}</td>
            <td>${item.price}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

## 4. Verification & Audit

Audit props passed to hydrated components during build:

```bash
npx astro build
# Check browser console for hydration errors:
# "Functions cannot be passed directly to Client Components unless they are Server Actions"
```

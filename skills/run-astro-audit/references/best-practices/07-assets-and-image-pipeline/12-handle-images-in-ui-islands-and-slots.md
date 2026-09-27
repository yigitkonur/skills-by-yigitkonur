# Bridge Optimized Images Across UI Framework Islands via Slots

> **Context:** Assets & Image Pipeline | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro components such as `<Image />` and `<Picture />` cannot be imported or executed inside React, Vue, or Svelte client islands because an island bundle must contain strictly valid code for its own target framework. Attempting to import `astro:assets` inside React components throws a Vite compilation error. To deliver optimized images inside interactive UI widgets without shipping image processing logic to the client, developers must pass pre-rendered Astro components via children/slots or pass metadata properties.

## 2. How It Differs From Classic React / Next.js

In Next.js, `next/image` is a universal React component that works seamlessly anywhere in the JSX component tree. In Astro, Astro components live exclusively on the server, requiring a clean architectural seam between the server-rendered container and the hydrated client island.

## 3. Common Mistakes & Anti-Patterns

Importing `import { Image } from 'astro:assets'` directly inside a `.tsx` or `.jsx` React island component, causing build crashes. Another pitfall is converting images to raw unoptimized strings rather than using slots.

### ❌ Bad Practice / Anti-Pattern

Importing Astro server components inside client framework islands:

```tsx
// src/components/CartDrawer.tsx (React Island)
// ❌ Fatal Error: astro:assets cannot be imported inside React client files
import { Image } from 'astro:assets'

export default function CartDrawer({ item }) {
  return (
    <aside className="drawer">
      <Image src={item.image} alt={item.title} />
      <h3>{item.title}</h3>
    </aside>
  )
}
```

### ✅ Best Practice / Idiomatic

Pass the optimized `<Image />` component into the React island as a server-rendered slot from the parent `.astro` file:

```astro
---
// src/pages/cart.astro
import CartDrawer from '../components/CartDrawer.jsx';
import { Image } from 'astro:assets';
import productThumb from '../assets/products/shoes.jpg';
---
<!-- ✅ Renders static optimized Image on server; passes as children to React island -->
<CartDrawer client:idle>
  <Image
    src={productThumb}
    alt="Ultra-light Trail Runners"
    width={120}
    height={120}
    slot="product-image"
  />
</CartDrawer>
```

In the React component, render the slot as standard React children or named props:

```tsx
// src/components/CartDrawer.tsx
export default function CartDrawer({ children }: { children?: React.ReactNode }) {
  return <aside className="drawer">{children}</aside>
}
```

## 4. Verification & Audit

Verify your client bundle size: confirm no image processing libraries or Astro asset runtime code leaked into the client JS bundle in `dist/_astro/*.js`.

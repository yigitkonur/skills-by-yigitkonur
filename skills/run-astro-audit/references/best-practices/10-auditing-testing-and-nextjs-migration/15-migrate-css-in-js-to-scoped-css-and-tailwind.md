# Migrate Runtime CSS-in-JS to Native Scoped CSS or Zero-Runtime Tailwind

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Runtime CSS-in-JS libraries (Emotion, styled-components) inject `<style>` tags dynamically into the DOM during client-side JavaScript execution. In Astro's server-rendered and static architecture, runtime style injection fails during SSR, causes `styled.div is not a function` errors, produces Flash of Unstyled Content (FOUC), and forces hundreds of kilobytes of runtime CSS parsers into client bundles. Migrating to Astro's native scoped `<style>` or Tailwind CSS eliminates runtime overhead completely.

## 2. How It Differs From Classic React / Next.js

Next.js supports runtime CSS-in-JS via custom document registry wrappers (`StyleSheetManager` / `ServerStyleSheet`). In Astro, there is no root React document to inject dynamic style sheets into. Astro components feature built-in, build-time CSS scoping via automated `data-astro-cid-*` attributes, generating zero runtime JS.

## 3. Common Mistakes & Anti-Patterns

Using `client:only="react"` on components purely to circumvent SSR crashes caused by Emotion or styled-components. This forces the browser to download React and the CSS-in-JS engine before painting the element, hurting Cumulative Layout Shift (CLS) and LCP.

### ❌ Bad Practice / Anti-Pattern

```tsx
// Next.js styled-components pattern: Fails in Astro SSR; causes FOUC
import styled from 'styled-components'

const CalloutBox = styled.aside`
  background-color: #f0fdf4;
  border-left: 4px solid #16a34a;
  padding: 1.5rem;
`

export default function Callout({ children }: { children: React.ReactNode }) {
  return <CalloutBox>{children}</CalloutBox>
}
```

### ✅ Best Practice / Idiomatic

```astro
---
// Astro: Native Scoped CSS (Zero runtime JS, pure build-time CSS extraction)
interface Props {
  variant?: 'success' | 'warning';
}
const { variant = 'success' } = Astro.props;
---
<aside class:list={['callout', variant]}>
  <slot />
</aside>

<style>
  .callout {
    padding: 1.5rem;
    border-radius: 4px;
  }
  .callout.success {
    background-color: #f0fdf4;
    border-left: 4px solid #16a34a;
  }
</style>
```

## 4. Verification & Audit

Verify that styles are extracted into static `.css` files rather than dynamic `<style>` DOM tags:

```bash
# Verify no runtime css-in-js libraries remain in package.json
grep -E "(styled-components|@emotion)" package.json && \
  echo "FAIL: Runtime CSS-in-JS dependency found" || \
  echo "PASS: Zero-runtime styling enforced"
```

# Use client:only With Fallback for Pure Browser Widgets

> **Context:** Islands & Hydration | **Impact:** High | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Certain components rely strictly on browser APIs (`window`, `document`, WebGL, Canvas, Chart.js, Monaco Editor, rich text editors). Running them through server-side rendering (SSR) triggers `window is not defined` or heavy server-side shim overhead. `client:only="{framework}"` completely skips SSR compilation and renders strictly in the browser. Pairing it with `<div slot="fallback">` prevents layout shifts while the script loads.

## 2. How It Differs From Classic React / Next.js

In Next.js, skipping SSR requires `dynamic(() => import(...), { ssr: false })`. In Astro, you specify `client:only="react"` directly on the component tag in `.astro` templates, explicitly declaring the target framework runtime since Astro does not inspect it during SSR.

## 3. Common Mistakes & Anti-Patterns

Forgetting to specify the framework name (`client:only` without `="react"` throws an error), or using `client:only` on SEO-critical content (headings, product descriptions) which empties the initial HTML.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/analytics.astro - Missing framework name and leaving layout shift gap
import AnalyticsChart from '../components/AnalyticsChart.jsx';
---
<!-- Error: Astro cannot deduce framework without explicit argument -->
<!-- Also leaves blank layout shift while Chart.js downloads -->
<AnalyticsChart client:only />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/analytics.astro - Explicit framework with fallback skeleton placeholder
import AnalyticsChart from '../components/AnalyticsChart.jsx';
import ChartSkeleton from '../components/ChartSkeleton.astro';
---
<AnalyticsChart client:only="react">
  <!-- slot="fallback" renders static HTML immediately until the client island mounts -->
  <ChartSkeleton slot="fallback" />
</AnalyticsChart>
```

## 4. Verification & Audit

Curl the page from the terminal to inspect the raw static HTML emitted by the server:

```bash
curl -s http://localhost:4321/analytics | grep -i "ChartSkeleton"
```

Verify that the `ChartSkeleton` fallback HTML is present in the initial response and no `window is not defined` errors occur during build:

```bash
npx astro build
```

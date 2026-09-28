# Verify Zero Client-Side JavaScript in Emitted HTML Output for Static Pages

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Astro's primary architectural advantage is delivering zero client-side JavaScript by default. Marketing, editorial, and documentation pages should emit pristine HTML without hydration scripts. Unchecked imports, rogue `<script>` tags, or unnecessary hydration directives (`client:load`) can silently inject client bundles into static pages, degrading mobile First Input Delay (FID), Interaction to Next Paint (INP), and Lighthouse performance. Auditing emitted `dist/*.html` guarantees that static pages remain truly script-free.

## 2. How It Differs From Classic React / Next.js

In Next.js (both Pages and App Router), every page—even one marked as static or using React Server Components (RSC)—renders with client-side React hydration bundles (`_next/static/chunks/main.js`, framework scripts, and React runtime). Zero client-side JS is impossible in Next.js without custom headless workarounds. In Astro, an `.astro` component compiles into pure HTML; client scripts are only emitted if explicitly commanded.

## 3. Common Mistakes & Anti-Patterns

Developers migrating from Next.js frequently attach `client:load` or `client:idle` to presentational components (headers, cards, footers) out of habit, or place plain `<script>` tags that Vite hoists and bundles as ES module chunks into the page `<head>`.

### ❌ Bad Practice / Anti-Pattern

```astro
---
// src/pages/blog/post.astro
import Header from '../../components/Header.jsx';
import ArticleContent from '../../components/ArticleContent.astro';
import Footer from '../../components/Footer.jsx';
---
<!-- Unnecessary client directive on static presentational component -->
<Header client:load />
<ArticleContent />
<!-- Inadvertently hydrates pure display footer, shipping React runtime -->
<Footer client:idle />
```

### ✅ Best Practice / Idiomatic

```astro
---
// src/pages/blog/post.astro
import Header from '../../components/Header.astro';
import ArticleContent from '../../components/ArticleContent.astro';
import Footer from '../../components/Footer.astro';
---
<!-- Zero-JS: Components render at build-time to clean HTML without client scripts -->
<Header />
<ArticleContent />
<Footer />
```

## 4. Verification & Audit

Run an automated CI assertion against the emitted `dist/` directory to ensure static routes contain zero `<script type="module">` tags:

```bash
# Verify no client module scripts exist in static marketing page HTML
grep -E '<script\b[^>]*\btype=["'\'']module["'\'']' dist/blog/post/index.html && \
  { echo "FAIL: Client JavaScript leaked into static route"; exit 1; } || \
  echo "PASS: Zero client JS verified in static route"
```

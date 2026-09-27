# Thematic Audit Layers & Inspection Taxonomy

This document outlines the 7 architectural audit layers for full-codebase audits in Astro and Cloudflare edge web applications, organizing all 70 canonical workload briefs.

---

## The 7 Thematic Layers Overview

```
                                  [ Full Repository Astro 7 Architecture ]
                                                     │
         ┌───────────────────┬───────────────────────┼───────────────────────┬───────────────────┐
         ▼                   ▼                       ▼                       ▼                   ▼
  Layer 1: Routing    Layer 2: Zero-JS        Layer 3: Visual         Layer 4: Content    Layer 5: Edge
   & Core Hubs         & Hydration             & Layout 120fps         & Multilingual      & Runtime
  (Workloads 01-10)   (Workloads 11-20)       (Workloads 21-30)       (Workloads 31-40)   (Workloads 41-50)
                                                     │
                                     ┌───────────────┴───────────────┐
                                     ▼                               ▼
                              Layer 6: Future AI              Layer 7: Contracts
                               & Edge Negotiation              & Security
                              (Workloads 51-60)               (Workloads 61-70)
```

---

## 1. Layer 1: Core Marketing, Hubs & Dynamic Routing (`01-templates-routing/`)

- **Scope**: Workloads 01 – 10.
- **Focus**: Route enumeration, commercial funnel, tier-1/tier-2/tier-3 services hierarchy, resources hub, proof case studies, interactive tool matrices, academy LMS, community events SSR, and glossary listing pages.
- **Key Invariants**:
  - Astro Multi-Page Architecture (MPA) static path enumeration via `getStaticPaths()`.
  - Slashless canonical URLs (Contract C5): never emit trailing slashes.
  - Zero duplicate routes across locales (`en`, `tr`, `ar`).
- **Inspection Command**:
  ```bash
  pnpm exec vitest run tests/int/routes* tests/int/services*
  ```

---

## 2. Layer 2: Zero-JS Defaults, Hydration Stripping & Island Performance (`02-zero-js-hydration/`)

- **Scope**: Workloads 11 – 20.
- **Focus**: Eradication of unnecessary client JS, downgrading eager `client:load` to `client:idle` or `client:visible`, media query responsive gating (`client:media`), migrating interactive widgets to native Web Components (`<custom-element>`), shrinking island props payloads, Nano Stores cross-island state, tree-shaking client bundles, WebMCP browser agent tools, third-party analytics deferral, and forms rate limiting.
- **Key Invariants**:
  - Static presentation cards must render as pure HTML in `.astro` files; never wrap static cards in React islands.
  - Interactive leaf triggers (e.g. video modals) must be isolated into lightweight client islands using event delegation.
  - Total client JavaScript bundle on landing pages must stay strictly under performance budgets.
- **Inspection Command**:
  ```bash
  pnpm exec vitest run tests/int/hydration* tests/int/island*
  ```

---

## 3. Layer 3: Visual Pipeline, Vector Identity, R2 & Layout Stability (`03-media-pipeline-lqip/`)

- **Scope**: Workloads 21 – 30.
- **Focus**: Inline base64 WebP LQIP placeholders, separating moving ticker logos from lazy content imagery, customer reference brand logo silhouettes (dark/light pairs), team roster 17-angle cursor-tracking headshots, video thumbnail Variant 05 canvas wipe, dynamic Satori OG cards, Cloudflare R2 media manifests, Cumulative Layout Shift (CLS) 120fps stabilization, Swiss typography font preloading, and dark-mode theme flicker prevention.
- **Key Invariants**:
  - All raster illustrations must have base64 WebP LQIP in `src/data/assets/image-placeholders.json`.
  - Continuous marquees must remain eager (`loading="eager"`).
  - Explicit aspect ratios and dimensions on all images to prevent layout shift.
- **Inspection Command**:
  ```bash
  pnpm assets:placeholders:check
  pnpm exec vitest run tests/int/lqip* tests/int/cls*
  ```

---

## 4. Layer 4: Content Layer, SEO Architecture & Multilingual Parity (`04-content-and-seo/`)

- **Scope**: Workloads 31 – 40.
- **Focus**: Satteri Rust mdast/hast parsing pipeline, automated glossary autolinking engine, outbound link rel hardening (`rel="noopener noreferrer"`), multilingual commercial parity (`en`, `tr`, `ar`), bidirectional hreflang cluster return tags, central redirect loop/chain elimination, thin/retired categories SEO policy, JSON-LD Schema.org structured data, and bilingual vector search index.
- **Key Invariants**:
  - Hreflang tags must form complete circular return clusters across all translated locales.
  - Zero redirect chains or self-referential redirect loops in the edge redirect table.
  - JSON-LD schemas must be valid Schema.org entities (`Organization`, `Service`, `Article`, `Course`).
- **Inspection Command**:
  ```bash
  pnpm exec vitest run tests/int/hreflang* tests/int/redirects* tests/int/schema*
  ```

---

## 5. Layer 5: Cloudflare Edge Workers, Security & Runtime Purity (`05-edge-workers-and-qa/`)

- **Scope**: Workloads 41 – 50.
- **Focus**: Pure Cloudflare Workers runtime compliance (`compatibility_date: 2026-09-02`, zero `node:` runtime imports in emitted worker bundles), edge caching with `stale-while-revalidate` (SWR), sharded build engine RAM-disk tuning, incremental build hash stamping, Content Security Policy (CSP) Level 3 headers, WCAG 2.2 AAA accessibility, Swiss design tokens purity, Playwright visual regression suite, adversarial edge attack probing, and architectural wiki registry synchronization.
- **Key Invariants**:
  - `edge/policy/*.mjs` and `src/worker.ts` must remain pure Web Platform standards.
  - Zero synthetic pulsing dots, generic SaaS badges, or monospace fonts on marketing surfaces.
  - All documentation links and script names must pass `pnpm check:doc-integrity`.
- **Inspection Command**:
  ```bash
  pnpm test:edge
  pnpm check:doc-integrity
  pnpm premerge:runner:prepush
  ```

---

## 6. Layer 6: Future Edge, AI Crawlers, Markdown Negotiation & UX Resilience (`06-future-edge-ai-analytics/`)

- **Scope**: Workloads 51 – 60.
- **Focus**: `llms.txt` and `llms-full.txt` AI crawler aggregations, edge markdown content negotiation (`Accept: text/markdown` with `Vary: Accept`), View Transitions BFCache lifecycle coordination, Interaction to Next Paint (INP) main-thread yielding (`scheduler.yield()`), deep-link fragment anchor normalization (`scroll-margin-top`), non-blocking edge Geo-IP regional routing, editorial print/PDF mode stylesheets (`@media print`), Speculative Rules API instant prerender, form draft auto-save session persistence (`sessionStorage` with `transition:persist`), and SPA soft-navigation analytics tracking parity.
- **Key Invariants**:
  - Negotiated responses must unconditionally emit `Vary: Accept` to prevent edge CDN cache poisoning.
  - `robots.txt` must declare AI discovery without blocking human web indexes.
  - Zero data loss mandate for long user input forms across client navigations.
- **Inspection Command**:
  ```bash
  pnpm exec vitest run tests/int/llms* tests/int/edge-markdown* tests/int/view-transitions*
  ```

---

## 7. Layer 7: Migration Safety, Zod Contracts, Memory Deferral & Security Boundaries (`07-migration-and-core-contracts/`)

- **Scope**: Workloads 61 – 70.
- **Focus**: Next.js ghost import and `'use client'` directive elimination, hoisting React `useEffect()` data fetching waterfalls to server frontmatter `await`, enforcing Content Layer `entry.id` contracts (replacing direct `node:fs` in pages), Zod schema date coercion (`z.coerce.date` and `dateLike`), Content Collection build-time memory deferral (eliminating concurrent `render()` loops on overview hubs), middleware static asset bypass fast-paths (`/_astro/` zero-regex exit), middleware stream lock prevention and `context.locals` typing (`App.Locals`), frontmatter security boundaries (isolating gated download URLs and CRM UUIDs from client props), ClientRouter event listener leak guards, and Server Islands (`server:defer`) URL limits with `ASTRO_KEY` encryption contracts.
- **Key Invariants**:
  - Static asset requests (`/_astro/*`, `/assets/*`) must bypass middleware regex evaluation.
  - Gated asset URLs and private CRM identifiers must never be serialized into `<astro-island props="...">`.
  - Collections must defer markdown AST compilation to detail routes; never compile hundreds of entries concurrently on listing pages.
- **Inspection Command**:
  ```bash
  pnpm exec vitest run tests/int/nextjs* tests/int/zod* tests/int/server-islands* tests/int/middleware-static*
  ```

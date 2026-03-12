# Migration Strategy Patterns

> Battle-tested strategies for migrating Vue applications to React/Next.js, drawn from 8 real-world case studies and community consensus.

---

## Strategy Comparison

| Strategy | Best For | Timeline | Risk | Team Size |
|---|---|---|---|---|
| **Big Bang Rewrite** | Small apps, strong React team, clean break | 2–8 weeks | 🔴 High | 2–5 devs |
| **Incremental / Strangler Fig** | Production apps, continuous delivery needed | 3–12 months | 🟢 Low | 2–10 devs |
| **Micro-Frontend** | Very large apps, multiple independent teams | 6–18 months | 🟡 Medium | 5+ devs |
| **Page-by-Page** | Clear page boundaries, Nuxt → Next.js | 2–6 months | 🟢 Low | 2–5 devs |

---

## Big Bang Rewrite

### When It Works

- **Small apps** (< 30 components, < 20 pages)
- **Strong React team** that can rebuild quickly
- **Major redesign** planned anyway (new UI, new architecture)
- **No active users** (internal tools, pre-launch apps)

### When It Fails

- **Large apps** (100+ components) — scope creep is inevitable
- **Active users** expecting continuous feature delivery
- **Evolving requirements** — new features get blocked during rewrite

> **u/domdommdommmm:** *"I've tried on 3 separate occasions to migrate a large application to no success."*

### Execution Steps

1. Set up new Next.js project with TypeScript, Tailwind, Zustand
2. Recreate routing structure (`app/` directory mirrors Vue Router config)
3. Convert state management (Pinia → Zustand)
4. Rebuild components bottom-up (leaf → composite → pages)
5. Migrate tests (VTU → RTL), deploy, decommission Vue app

### Risk Mitigations

- Keep the old app running as a fallback
- Set a hard deadline — migrations without timelines never finish
- Deploy incrementally using feature flags or canary releases

---

## Incremental / Strangler Fig (Recommended)

Gradually replace the old system while keeping it running. Used in the most successful case studies.

### Architecture

```
                    ┌─────────────────┐
    User traffic →  │  Reverse Proxy  │
                    │  (nginx/Vercel) │
                    └──┬──────────┬───┘
                       │          │
              ┌────────▼──┐  ┌───▼────────┐
              │  Next.js  │  │  Vue/Nuxt  │
              │  (new)    │  │  (legacy)  │
              └───────────┘  └────────────┘
                    │              │
                    └──────┬───────┘
                    ┌──────▼──────┐
                    │ Shared Auth │
                    │ Shared API  │
                    └─────────────┘
```

### Step-by-Step Process

**Phase 1: Foundation (Week 1–2)**
- Set up Next.js project alongside Vue app
- Configure reverse proxy (all traffic → Vue by default)
- Implement shared authentication (same-domain cookies or JWT)
- Create shared design token package

**Phase 2: First Page (Week 3–4)**
- Pick the **simplest, lowest-traffic page** for first migration
- Rebuild in Next.js, update proxy to route that path to Next.js
- Validate: auth works, styles match, functionality identical

**Phase 3: Accelerate (Ongoing)**
- Migrate pages one at a time, increasing complexity
- Convert shared components into a common package
- Update proxy routing after each page

**Phase 4: Cleanup**
- All traffic routed to Next.js; remove Vue app and proxy

### Proxy Routing Config

**Nginx:**
```nginx
upstream vue_app  { server localhost:3000; }
upstream next_app { server localhost:3001; }

server {
  # Migrated pages → Next.js
  location /dashboard { proxy_pass http://next_app; }
  location /profile   { proxy_pass http://next_app; }
  # Everything else → Vue (legacy)
  location / { proxy_pass http://vue_app; }
}
```

### Shared Auth

Both apps must share authentication. Same-domain cookies work automatically. For JWT:

```ts
// packages/shared-auth/index.ts
export function getAuthToken(): string | null {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('auth-token='))
    ?.split('=')[1] ?? null;
}

export function isAuthenticated(): boolean {
  const token = getAuthToken();
  if (!token) return false;
  const payload = JSON.parse(atob(token.split('.')[1]));
  return payload.exp * 1000 > Date.now();
}
```

### Real-World Results

| Case Study | Scale | Timeline | Downtime |
|---|---|---|---|
| Navid Barsalari (SaaS dashboard) | 4 zones | 3 months | **0 hours** |
| Hakan Aktaş (internal app) | Company-wide | 8 months | **0 hours** |
| Better Programming (large app) | Major tech debt | 15+ months | **0 hours** |

---

## Micro-Frontend Approach

### When to Use

- **Very large apps** with 200+ components and multiple independent teams
- **Long-term coexistence** of both frameworks is acceptable

### Implementation Options

| Tool | Approach | Complexity |
|---|---|---|
| **Module Federation** | Share modules at runtime | 🟡 Medium |
| **single-spa** | Framework-agnostic orchestrator | 🔴 High |
| **Astro.js** | Container for both Vue and React | 🟡 Medium |

> **Warning:** *"Deploying Module Federation without version-locking shared deps → runtime conflicts."* Always pin shared dependency versions.

- Adds infrastructure complexity — only justified for large organizations
- Shared state between micro-frontends is challenging
- Bundle size increases (two framework runtimes)

---

## Page-by-Page Migration

Use subdomain or path-based routing to serve different pages from different apps. Start with **least complex, lowest-risk pages**:

1. Static pages (about, terms, FAQ) — simplest
2. Auth pages (login, register) — isolated
3. Settings pages — usually CRUD
4. Dashboard pages — data-heavy
5. Core feature pages — highest complexity, migrate last

### Shared Components via Package

```
packages/shared-ui/     # npm package with shared design tokens
apps/next-app/           # Imports React components
apps/nuxt-app/           # Imports Vue components
```

---

## ReactWrapper Bridge Component

For component-level coexistence — mount React components inside Vue:

```vue
<!-- ReactWrapper.vue -->
<template>
  <div ref="reactRoot" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, toRaw } from 'vue'
import { createRoot } from 'react-dom/client'
import React from 'react'

const props = defineProps({
  component: { type: [Object, Function], required: true },
  componentProps: { type: Object, default: () => ({}) }
})

const reactRoot = ref(null)
let root = null

function render() {
  if (!root || !reactRoot.value) return
  root.render(React.createElement(toRaw(props.component), toRaw(props.componentProps)))
}

onMounted(() => { root = createRoot(reactRoot.value); render() })
watch(() => props.componentProps, render, { deep: true })
onBeforeUnmount(() => { root?.unmount(); root = null })
</script>
```

**Usage:**
```vue
<ReactWrapper :component="ReactChart" :componentProps="{ data: chartData }" />
```

**Use when:** Migrating individual components within a Vue page, testing React components before full page migration. **Remove** once the entire page is migrated.

**Limitations:** Two runtimes in bundle, no shared reactive context, prop-drilling at scale.

---

## Component Migration Order (6 Phases per Route)

Within each route, migrate components in this order — it minimizes the number of moving parts you have to reason about at the same time:

| Phase | What to Migrate | Why This Order |
|---|---|---|
| 1 | **Presentational leaf components** (Button, Card, Avatar, Badge, Icon) | Pure props-in/render-out — no state, no side effects |
| 2 | **Input & form field components** (TextField, Select, DatePicker) | Introduces `v-model` → controlled component conversion |
| 3 | **Overlays & behavior-heavy UI** (modals, popovers, tooltips, drawers) | Portals, focus traps, animation — complex but self-contained |
| 4 | **Container components** (compose children, manage state, store/route access) | Depend on layers 1–3 being stable |
| 5 | **Route components & layouts** (Vue Router → App Router structure) | Structural migration — reshapes the page boundary |
| 6 | **Global state & data fetching** (Pinia, route guards, API layer) | Cross-cutting — touch last to avoid cascading changes |

---

## 12-Step Practical Project Order

For a medium-to-large Vue 3 app, follow this end-to-end sequence:

1. Create the Next.js app shell and root layout
2. Pick one **non-critical route** (settings, profile, about)
3. Create the route in `app/` — keep it `"use client"` heavy at first
4. Port the route's leaf UI components (Phase 1 above)
5. Port form controls and `v-model` contracts (Phase 2)
6. Port overlays — modals, dropdowns, tooltips (Phase 3)
7. Port composables into custom hooks
8. Port route/container logic (Phase 4–5)
9. Move fetches to the server where appropriate
10. Move persistent shells (sidebar, navbar) into layouts
11. Migrate Pinia stores by category: local UI → shared client → server state
12. **Only then** optimize `"use client"` boundaries into more Server Components

> Steps 1–8 are about **parity**. Steps 9–12 are about **leverage**.

---

## Behavior Freeze Before Migration

Before migrating any route, capture its current behavior as a baseline:

- **Screenshots** of major states (populated, empty, loading, error)
- **Key interaction flows** (click paths, form submissions, drag/drop)
- **Keyboard & focus behavior** (tab order, focus traps, shortcuts)
- **Route transitions** and URL/query-string behavior
- **Responsive breakpoints** (mobile, tablet, desktop renders)
- **Store-driven behavior** (how Pinia state affects the UI)

> *"This is not ceremony. It is how you avoid the classic migration problem where 'the component renders' but no longer behaves the same."*

---

## The Two-Phase Mindset

Every migrated route goes through two distinct phases:

**Phase 1 — Contract Preservation (ship this):**
- Does it still look the same?
- Do interactions behave identically?
- Does state sync correctly?
- Does navigation work?

**Phase 2 — Architectural Refinement (optimize after):**
- Which components should stay client-side?
- Which can become Server Components?
- Which Pinia store responsibilities should move to layouts, Context, or server fetching?

> *"That two-phase mindset is why component-by-component migration works."* Never combine both phases — ship parity first, refine second.

---

## CSS / UI Parity Rule

For the first pass of every component, preserve:

- Same HTML structure and wrapper elements
- Same CSS classes and breakpoint logic
- Same portal/teleport targets
- Same animation timing and transitions

> *"Do not combine a framework migration with a design-system rewrite."* Visual changes introduce ambiguity — you can't tell if a bug is from the migration or the redesign. Redesign **after** parity is proven.

---

## Testing During Migration

- **Keep both test suites running:** `test:vue` and `test:react` scripts
- **E2E tests are framework-agnostic:** Playwright/Cypress tests work regardless of framework
- **Smoke test each migrated page** before moving to the next

```ts
// Playwright smoke test for migrated pages
const migratedPages = ['/dashboard', '/profile', '/settings'];
for (const page of migratedPages) {
  test(`${page} loads`, async ({ page: p }) => {
    await p.goto(page);
    await expect(p.locator('body')).not.toBeEmpty();
  });
}
```

---

## Real-World Lessons

### Timeline Reality

| Estimate | Actual | Why |
|---|---|---|
| "2 months" | 4–6 months | Third-party deps take 2–3× longer |
| "Same as Vue 2→3" | 3–5× more | Framework switch ≠ version upgrade |

> **u/budd222:** *"Half the team thinks it will be the same amount of time... Half the team doesn't know what they are talking about."*

### What Works

- **Dedicated migration team** (2–3 devs) for fast timelines
- **Rotation** (1 week/month per dev) for sustainability
- **New features go in React** — build forward, fix backward
- **Never pause feature delivery** — every successful migration kept shipping

> **Hakan Aktaş:** *"Avoid long isolated rewrites — keep shipping."*

### When to Stop and Reassess

- ⚠️ At 50% done but 80% of estimated time used
- ⚠️ Critical deps have no React equivalent
- ⚠️ Team morale dropping; migration feels like a death march

**Recovery:** Scale down scope, switch to micro-frontend, or pause and revisit.

---

## Migration Checklist

- [ ] Next.js project initialized with TypeScript + Tailwind
- [ ] Reverse proxy or routing layer configured
- [ ] Shared auth working across both apps
- [ ] State management converted (Pinia → Zustand)
- [ ] Leaf components migrated and tested
- [ ] Pages migrated in priority order
- [ ] All proxy routes point to Next.js
- [ ] Vue app decommissioned; bridge components removed
- [ ] Final performance audit completed

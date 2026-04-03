# Pre-Migration Assessment Checklist

> Evaluate your Vue application's complexity, dependencies, and team readiness before committing to a React/Next.js migration.

---

## App Complexity Assessment

### Component Inventory Matrix

Rate each dimension of your application:

| Dimension | Simple (1 pt) | Moderate (2 pts) | Complex (3 pts) |
|---|---|---|---|
| **Component count** | < 30 components | 30–150 components | 150+ components |
| **Nesting depth** | Max 3 levels | 4–6 levels | 7+ levels or recursive |
| **Custom directives** | None | 1–5 custom directives | 6+ or heavily used |
| **Mixins/composables** | < 5 | 5–20 | 20+ shared composables |
| **Dynamic components** | None | Occasional `<component :is>` | Heavy dynamic rendering |
| **Renderless components** | None | A few | Core architecture pattern |

### State Management Complexity

| Level | Description | Migration Impact |
|---|---|---|
| **Local only** | `ref()` / `reactive()` within components | 🟢 Low — direct `useState` mapping |
| **Prop drilling** | Props passed 3+ levels deep | 🟡 Medium — consider Context or Zustand |
| **Single store** | One Pinia/Vuex store | 🟡 Medium — straightforward Zustand conversion |
| **Multi-store** | Multiple Pinia stores with cross-references | 🟡 Medium — map each store to Zustand slice |
| **Complex flows** | Vuex modules + actions + plugins + subscriptions | 🔴 High — requires architectural redesign |

### Routing Complexity

| Level | Description | Migration Impact |
|---|---|---|
| **Static routes** | Flat list of pages, no params | 🟢 Low — simple file structure |
| **Dynamic routes** | URL params (`:id`, `:slug`) | 🟢 Low — `[id]`, `[slug]` folders |
| **Nested routes** | Parent/child layouts with `<router-view>` | 🟡 Medium — nested `layout.tsx` files |
| **Route guards** | `beforeEach`, per-route guards, meta fields | 🟡 Medium — `middleware.ts` + conventions |
| **Complex routing** | Programmatic navigation, route-based code splitting, scroll behavior | 🔴 High — significant rearchitecture |

### SSR/SSG Assessment

| Current Setup | Migration Path | Effort |
|---|---|---|
| **SPA only** (no SSR) | Client Components with `'use client'` | 🟢 Low |
| **Nuxt SSR** (universal) | Server Components (default in Next.js) | 🟡 Medium |
| **Nuxt SSG** (`generate`) | `generateStaticParams()` + static export | 🟡 Medium |
| **Nuxt ISR** (`routeRules`) | `revalidate` config in route segments | 🟡 Medium |
| **Nuxt hybrid** (mixed modes) | Per-route rendering config in Next.js | 🔴 High |

---

## Conversion Effort Estimator

Score each factor and multiply by its weight:

| Factor | Low (1×) | Medium (2×) | High (3×) | Weight |
|---|---|---|---|---|
| **Component count** | < 30 | 30–150 | 150+ | ×3 |
| **State complexity** | Local only | Single store | Multi-store + plugins | ×3 |
| **Routing complexity** | Static | Dynamic + guards | Nested + programmatic | ×2 |
| **Third-party Vue deps** | 0–3 | 4–10 | 10+ Vue-specific deps | ×3 |
| **Custom directives** | None | 1–5 | 6+ | ×1 |
| **Test coverage** | No tests | Some tests | Comprehensive suite | ×2 |
| **SSR usage** | SPA only | Basic SSR | Hybrid SSR/SSG/ISR | ×2 |
| **Team React experience** | Strong React skills | Some React knowledge | No React experience | ×2 |

**Scoring guide:**
- **18–30 points**: Small migration, 2–6 weeks estimated
- **31–45 points**: Medium migration, 2–4 months estimated
- **46–54 points**: Large migration, 4–8 months estimated

> Multiply timeline by 1.5× for realistic planning — migrations consistently take longer than estimated.

---

## Dependency Audit Checklist

### Step 1: Inventory All Vue-Specific Dependencies

Run this in your project root:

```bash
# List all dependencies containing 'vue' in the name
cat package.json | grep -E '"(vue|@vue|nuxt|@nuxt|vuelidate|vee-validate|pinia|vuex|vuetify|quasar|element-plus|naive-ui|primevue)' 
```

### Step 2: Categorize Each Dependency

| Category | Action | Example |
|---|---|---|
| **Direct equivalent** | Swap package | PrimeVue → PrimeReact |
| **Alternative available** | Evaluate and choose | Pinia → Zustand |
| **Framework-agnostic** | Keep as-is | Axios, date-fns, Lodash |
| **Must rebuild** | Reimplement in React | Custom Vue directives |
| **Blocker** | No React equivalent; critical feature | Evaluate workarounds |

### Step 3: Identify Blockers

Common blockers (dependencies with no React equivalent):
- Custom Vue directives used throughout the codebase
- Vue-specific plugins (`app.use()`) with deep framework integration
- Quasar cross-platform features (mobile/desktop from single codebase)
- BootstrapVue components (no maintained React port)

---

## Risk Assessment Matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Timeline overrun** | 🔴 High | 🔴 High | Add 50% buffer; use incremental strategy; track weekly |
| **Skill gaps** | 🟡 Medium | 🔴 High | Allocate 1–2 weeks for React training before starting |
| **Feature freeze pressure** | 🔴 High | 🟡 Medium | Use incremental migration; keep shipping features in Vue |
| **Data loss during migration** | 🟢 Low | 🔴 High | Shared auth/session management; database untouched |
| **Downtime** | 🟢 Low | 🔴 High | Reverse proxy routing; canary deployment |
| **Feature parity gaps** | 🟡 Medium | 🟡 Medium | Audit all features before starting; prioritize critical paths |
| **Performance regression** | 🟡 Medium | 🟡 Medium | Lighthouse baseline before migration; compare after each phase |
| **Third-party dep incompatibility** | 🟡 Medium | 🔴 High | Full dependency audit before committing; identify blockers early |
| **Team burnout** | 🟡 Medium | 🟡 Medium | Celebrate milestones; limit migration to 50% of sprint capacity |
| **Rollback needed** | 🟢 Low | 🟡 Medium | Keep Vue app running; proxy routing enables instant rollback |

---

## Prerequisites Checklist

### Team Readiness

- [ ] At least one team member has React/Next.js production experience
- [ ] Team has completed React fundamentals training (hooks, JSX, component model)
- [ ] Team understands key mental model shifts (immutable state, dependency arrays, one-way data flow)
- [ ] Team has read [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect) (official React docs)
- [ ] React coding conventions documented (folder structure, naming, state management choice)

### Infrastructure

- [ ] CI/CD pipeline can build both Vue and Next.js apps (if using incremental strategy)
- [ ] Reverse proxy or routing layer available for parallel deployment
- [ ] Shared authentication mechanism identified (cookies, JWT, session tokens)
- [ ] Deployment platform supports Next.js (Vercel, AWS, Docker, etc.)
- [ ] Monitoring/error tracking works with React (Sentry, Datadog, etc.)

### Testing Infrastructure

- [ ] Decision made: keep Vitest or switch to Jest
- [ ] React Testing Library configured
- [ ] E2E tests (Playwright/Cypress) are framework-agnostic and will work post-migration
- [ ] Performance baseline captured (Lighthouse scores, Core Web Vitals)

### Design System

- [ ] UI component library replacement chosen (see package-mapping.md)
- [ ] Design tokens (colors, spacing, typography) extracted and documented
- [ ] Shared component package planned (if running both apps simultaneously)

---

## Decision Framework

### ✅ Migrate to React/Next.js When:

- **Hiring:** React developer pool is 3–5× larger; hiring Vue devs is a bottleneck
- **Ecosystem:** You need React-only libraries (Framer Motion, Radix, react-aria, React Native)
- **AI tooling:** AI assistants generate significantly better React code (larger training data)
- **Team preference:** Your team already knows and prefers React
- **Major rewrite:** You're rebuilding the architecture anyway — framework switch adds marginal cost
- **SSR maturity:** Next.js offers ISR, RSC, and streaming that Nuxt can't match yet

### ⛔ Stay on Vue When:

- **Team is productive:** Vue devs are happy, shipping fast, no pain points
- **Only need Vue 2 → 3:** Upgrading within Vue is significantly less effort than switching frameworks
- **"Performance" is the reason:** Framework differences are negligible; optimize your code, not your framework
- **Tight timeline:** Multi-month migration isn't feasible given business constraints
- **Vue ecosystem suffices:** Radix Vue, shadcn-vue, Pinia, VueUse cover your needs
- **Laravel backend:** Vue + Laravel ecosystem is mature and well-integrated

### 🔄 Consider Incremental Migration When:

- **Production app with real users:** Can't afford downtime or feature freezes
- **Clear page boundaries:** App has distinct sections that can be migrated independently
- **Mixed team skills:** Some devs know React, others know Vue — both can contribute
- **Risk tolerance is low:** Need the ability to pause or rollback at any point
- **Large codebase (100+ components):** Full rewrite is too risky; strangler pattern is safer

---

## Migration Order (Recommended)

Once you've decided to migrate, follow this order:

1. **Foundation first:** Auth, routing infrastructure, shared design tokens
2. **State management:** Convert Pinia/Vuex stores to Zustand
3. **Leaf components:** Buttons, inputs, cards — isolated, low-risk
4. **Composite components:** Forms, lists, tables — medium complexity
5. **Pages:** One at a time, starting with lowest traffic
6. **Data fetching:** Convert `useFetch`/`useAsyncData` to Server Components or TanStack Query
7. **Advanced patterns:** Transitions, portals, error boundaries
8. **Testing:** Migrate test suite alongside each component
9. **Cleanup:** Remove Vue app, proxy routing, bridge components

> **From u/tengusheath (100K LOC migration):** *"Once the foundational stuff was migrated over, the component to component migration was pretty painless."*

---

## Per-Component Migration Worksheet

> That worksheet is more valuable than blindly translating lines of code.

Before migrating **any** component, copy this template and fill it out completely. It forces you to understand the component's full contract before writing a single line of React.

```markdown
## Component Migration Worksheet: [ComponentName]

### Public API
- [ ] Props and defaults: ___
- [ ] Emitted events: ___
- [ ] v-model bindings: ___

### Composition
- [ ] Default slot used: yes/no
- [ ] Named slots: ___
- [ ] Scoped slots: ___
- [ ] Fallthrough attributes ($attrs): ___

### Internal State
- [ ] Refs / exposed methods (defineExpose): ___
- [ ] Local reactive state (ref, reactive): ___
- [ ] Computed values: ___
- [ ] Watchers: ___

### Dependencies
- [ ] Router usage (params, query, push): ___
- [ ] Store usage (which stores, what state): ___
- [ ] Composables used: ___

### Special Features
- [ ] Directives used: ___
- [ ] Teleport: ___
- [ ] Transition/TransitionGroup: ___
- [ ] KeepAlive: ___

### UI Contract
- [ ] CSS dependencies and class names: ___
- [ ] Accessibility attributes: ___
- [ ] Test IDs: ___
```

**How to use this:**
1. Print or copy for each component before migration
2. Components with many unknowns (`___`) need investigation first — don't migrate what you don't understand
3. The "Special Features" section flags patterns that need React-specific solutions (e.g., Teleport → `createPortal`, KeepAlive → custom caching)
4. Archive completed worksheets — they become documentation for the React version

### TypeScript Component Contract Stubs

Vue components have a "hidden API" — slots and emitted events are often undocumented. Before migrating a component, formalize its contract so both the Vue and React versions satisfy the same interface:

```ts
// component-contracts/Button.contract.ts
export type ButtonVariant = "primary" | "secondary" | "danger";

export interface ButtonContract {
  props: {
    variant?: ButtonVariant;
    disabled?: boolean;
    ariaLabel?: string;
  };
  events: {
    onClick: () => void;
  };
  slots: {
    default: "label content";
    icon?: "optional icon content";
  };
}
```

**Why contracts matter:**
- Vue recommends `defineEmits` — but many codebases skip it. Contracts force you to document **all** emitted events before migration.
- Slots translate to React `children` or render props. Naming them explicitly prevents missed functionality.
- Both Vue and React implementations must satisfy the same contract interface — it's your behavioral parity guarantee.

**Use contracts as migration gates:** don't deploy the React version of a component until it satisfies every field in the contract. If the contract can't be satisfied, the component isn't ready.

### Contract Validation Tooling

- **Usage graphs:** Scan `.vue` imports with the TypeScript compiler API (AST-based) to generate a dependency graph of who consumes each component and which props/events/slots they use.
- **Visual parity:** Stand up Storybook for both Vue (`@storybook/vue3`) and React (`@storybook/react`) — write identical stories per contract and compare side-by-side.
- **Test fixture generation:** Use the contract type to auto-generate test fixtures — every prop combination, every event handler assertion, every slot rendering permutation.

---

## Behavior Freeze Checklist (Pre-Migration per Route)

Before migrating a route, capture its **exact** current behavior. This is your acceptance criteria — the React version must match every item.

### Visual State Capture
- [ ] Screenshots of all major UI states
- [ ] Empty state appearance
- [ ] Loading state appearance
- [ ] Error state appearance
- [ ] Responsive breakpoints verified (mobile, tablet, desktop)

### Interaction Behavior
- [ ] Key interaction flows documented (click paths, form submissions)
- [ ] Keyboard behavior documented (tab order, shortcuts, escape handling)
- [ ] Focus management behavior (where focus goes after modals, deletions, navigations)
- [ ] Route transitions (animations, scroll position restoration)

### Data & State Behavior
- [ ] Store-driven behavior documented (what state triggers what UI changes)
- [ ] URL/query-string behavior documented (filters, pagination, deep links)
- [ ] Optimistic updates or real-time data flows

> **Tip:** Record a short screen capture of each route's key flows. It's faster than writing and catches details you'd miss in a written spec.

---

## Pinia Store Categorization Audit

Not all Pinia stores migrate the same way. Categorize each store **before** you start converting, then choose the right React target.

### Store Category Reference

| Category | What It Holds | React Migration Target |
|---|---|---|
| **Local UI state** | Toggles, form state, modals, panel visibility | `useState` / `useReducer` in the consuming component |
| **Shared client state** | Theme, sidebar state, user preferences | React Context or Zustand (lightweight global) |
| **Server-cached data** | API responses, lists, entities, pagination | Server Component `fetch` / TanStack Query |

### Store Audit Table

Fill in one row per Pinia store in your application:

| Store | Category | Key State | Subscribers | Migration Target |
|---|---|---|---|---|
| ___ | Local UI / Shared / Server | ___ | ___ components | ___ |

### Decision Rules

- **Only 1–2 components read it?** → Inline as `useState`. No global store needed.
- **Many components read it, rarely writes?** → React Context with `useMemo` provider value.
- **Frequent reads AND writes across the tree?** → Zustand store (avoids Context re-render issues).
- **Holds API response data?** → TanStack Query or Server Component fetch — don't put server data in client stores.
- **Store has actions with side effects (API calls)?** → Those become TanStack Query mutations or Server Actions.

### SSR Sensitivity Audit

Add this column to your component inventory. Components with high SSR sensitivity need `'use client'` directives or conditional imports in Next.js.

| Component | Uses `window`/`document`? | `onMounted` data fetch? | Vue Router coupled? | SSR Sensitivity |
|---|---|---|---|---|
| ___ | yes / no | yes / no | params / guards / no | None / Low / High |

**Rating guide:**
- **None:** Pure presentational, no browser APIs, no lifecycle data fetching
- **Low:** Uses `onMounted` but only for DOM measurement or animation setup
- **High:** Calls `window`/`document` at module scope, fetches data in `onMounted`, or reads route params/guards directly — these require `'use client'` or refactoring to Server Components

> **Common mistake:** Migrating every Pinia store to Zustand 1:1. Many stores exist in Vue only because Vue lacks a built-in data-fetching primitive — React Server Components and TanStack Query eliminate the need.

---

## Baseline Metrics to Capture

Before starting migration, record:

| Metric | Tool | Why |
|---|---|---|
| Lighthouse scores | Chrome DevTools | Compare performance pre/post |
| Bundle size | `npx vite-bundle-visualizer` | Ensure React version isn't larger |
| Core Web Vitals | PageSpeed Insights | Track LCP, FID, CLS |
| Component count | `find src -name '*.vue' \| wc -l` | Track migration progress |
| Test count & coverage | `vitest --coverage` | Ensure tests are ported |
| Build time | CI pipeline logs | Compare build performance |
| Error rate | Sentry / error tracking | Detect regression post-migration |

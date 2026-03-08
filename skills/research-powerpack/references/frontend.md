# Frontend-Specific Research Guide

## Quick Reference: Which Tools For Which Frontend Problem

| Use Case | Primary Tool | Secondary Tool | Key Signal |
|---|---|---|---|
| 01. Framework Migration Planning | `deep_research` | `web_search` | Phased plan with effort estimates and risk matrix |
| 02. SSR vs SSG vs SPA Decision | `deep_research` | `web_search` | Multi-factor decision matrix, cost modeling |
| 03. Accessibility Compliance | `deep_research` | `web_search` | Prioritized remediation plan, testing strategy |
| 04. Responsive Design Debugging | `deep_research` | `web_search` | Decision framework, mobile Safari bug catalog |
| 05. Animation & Rendering Performance | `deep_research` | `web_search` | Rendering pipeline mastery, profiling methodology |

---

## 01. Framework Migration Planning

### Recommended Tools
- **deep_research**: Phased migration plans with dependencies, milestones, effort estimates, and risk matrices. Decision frameworks for rewrite vs incremental migration.
- **web_search**: Official migration guides, codemods, compatibility modes, and breaking change lists from framework teams.
- **search_reddit**: Real migration timelines, unexpected obstacles, and "we switched back" cautionary tales.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Migration plan for 300-component React codebase from class components to hooks with
concurrent feature development. Migration order (shared components first? pages first?)?
Codemod handling of complex patterns (HOCs, render props)? Effort for 300 components with
2 developers? Redux connect() -> useSelector migration alongside hooks? Testing strategy?"
"Q2: Decision framework for incremental migration vs full rewrite: jQuery to modern framework.
50K lines, no module system. Strangler fig pattern for frontend (iframe? micro-frontends?
shared DOM)? Realistic timelines? State sharing between jQuery and React during transition?"

# web_search
keywords = ["react class components to hooks migration guide 2025",
            "react codemod class to function component automatic",
            "jquery to react migration strategy large codebase"]
```

### Best Practices
- Include **component count and pattern details** ("300 components using HOCs and Redux connect()").
- Mention your constraints: "cannot freeze feature development" or "only 2 developers."
- Attach a **representative component** showing your most complex patterns.
- Ask about testing strategy explicitly -- migration without testing is the most common regression source.
- Separate the **decision** (whether to migrate) from the **plan** (how to migrate).
- Search for "codemod" in web queries -- automated tools save massive manual work.
- Look for compatibility modes: Vue's `@vue/compat`, Angular schematics, React StrictMode.

---

## 02. SSR vs SSG vs SPA Decision

### Recommended Tools
- **deep_research**: Multi-factor decision matrix weighing SEO, performance, cost, complexity, and team expertise for your specific project. Hybrid architecture recommendations when no single approach fits.
- **web_search**: Framework documentation, Core Web Vitals benchmarks, SEO evidence, and deployment cost analyses.
- **search_reddit**: Real-world experiences with SSR cold starts, SSG build time scaling, and SPA SEO limitations.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Decision framework for Next.js SSR vs Astro SSG vs React SPA for B2B SaaS with
marketing pages + app dashboard. One framework for both or separate? Does SSR add value
for dashboard (no SEO)? Hosting cost differences at our scale? React Server Components
impact? Developer experience tradeoffs?"
"Q2: When SSG breaks down for content-heavy sites (15K pages, daily updates, 45-minute builds).
Page count threshold where SSG becomes impractical? Next.js ISR at 15K pages -- stale content
risk? SSG-first frameworks for large-scale content? SSR caching strategy approaching SSG
performance?"

# web_search
keywords = ["SSR vs SSG vs SPA comparison 2025 when to use each",
            "next.js app router server components vs client components"]
```

### Best Practices
- Describe your **project type** -- "B2B SaaS", "e-commerce", "content site" each point toward different strategies.
- Specify **which pages need SEO** -- the answer is almost always "some do, some don't" leading to hybrid recommendations.
- Include **scale expectations**: page count, traffic volume, update frequency all affect the decision.
- Ask about **cost explicitly** -- hosting cost is often the deciding factor between SSR and SSG.
- Include "2025" in queries -- the landscape changes rapidly with React Server Components and Astro improvements.
- Key insight: most projects benefit from **hybrid** architectures (SSG for marketing, SPA/SSR for app).

---

## 03. Accessibility Compliance

### Recommended Tools
- **deep_research**: Prioritized remediation plan ranked by user impact and legal risk. Replace vs retrofit analysis for custom components. Integrated automated + manual testing methodology.
- **web_search**: WCAG specifications, ARIA Authoring Practices Guide (APG) reference implementations, and audit tool documentation.
- **search_reddit**: Teams sharing their compliance journeys, tool recommendations, and screen reader testing experiences.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: WCAG 2.1 AA compliance plan for React SPA with 50+ components (forms, data tables,
modals, custom dropdowns). Most commonly violated criteria? Priority order for fixes (user
impact + legal risk)? Replace custom components with Radix/React Aria vs retrofit? Automated
vs manual testing limits? Focus management for SPA route changes?"
"Q2: Screen reader testing guide for frontend developers who have never used one. Minimum
browser + screen reader combinations for coverage? Practical testing checklist per PR? Key
shortcuts for NVDA and VoiceOver? Most common screen reader issues developers miss?"

# web_search
keywords = ["WCAG 2.1 AA compliance checklist frontend developer 2025",
            "ARIA design patterns APG modal dialog combobox",
            "axe-core accessibility testing automation CI pipeline"]
```

### Best Practices
- List your **component types** (forms, data tables, modals, dropdowns) -- each has specific accessibility requirements.
- Mention your **timeline** -- a 6-month deadline produces a very different plan than gradual improvement.
- Search for APG patterns by name: "APG dialog pattern" or "APG combobox pattern" for reference implementations.
- Target accessibility-focused sites: `site:w3.org`, `site:dequeuniversity.com`, `site:a11yproject.com`.
- Key automation insight: axe-core catches roughly **30-40% of accessibility issues**. The rest require manual testing (screen readers, keyboard navigation, cognitive review).
- Separate the compliance plan from the testing guide -- different research domains.

---

## 04. Responsive Design Debugging

### Recommended Tools
- **deep_research**: Structured decision framework for container queries vs media queries vs fluid values. Complete mobile Safari bug catalog with canonical fixes.
- **web_search**: CSS specification references (MDN), browser compatibility data (Can I Use), and DevTools debugging guides.
- **search_reddit**: Real-world container query experiences at scale, mobile Safari workaround discussions, and design system responsive strategies.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: When to use container queries vs media queries vs CSS clamp() in a component-based
React design system. Decision rule for each? Container query performance at 100+ components?
Fluid typography/spacing pattern? Testing container queries in Storybook? Gotchas (sizing
context, nesting, circular refs)?"
"Q2: Systematic debugging of mobile Safari viewport and layout issues. Complete list of known
issues with canonical fixes. 100vh overflow, fixed position jumps on keyboard, safe area inset.
Dev environment setup for mobile Safari testing. Preventive CSS patterns."

# web_search
keywords = ["container queries vs media queries when to use 2025",
            "CSS viewport units dvh svh lvh mobile Safari iOS",
            "responsive design debugging techniques Chrome DevTools"]
```

### Best Practices
- Describe your **architecture**: "design system with 100+ components" vs "single marketing page" leads to different strategies.
- List **specific bugs** when debugging mobile Safari for focused research.
- Mention your **CSS approach** (utility classes, CSS modules, styled-components) since patterns differ.
- Search for "caniuse" with feature names for quick browser support data.
- Include "mobile Safari" or "iOS" in queries -- Safari has the most responsive design quirks.
- Container query decision rule: use **container queries** when a component should adapt to its parent width (reusable components in different layouts); use **media queries** when responding to the viewport.

---

## 05. Animation & Rendering Performance

### Recommended Tools
- **deep_research**: Connects browser rendering pipeline (layout, paint, composite), React's rendering model, and GPU layer management into actionable optimization strategies.
- **web_search**: Chrome team articles (web.dev), rendering pipeline documentation, and DevTools profiling guides.
- **search_reddit**: Real jank debugging stories, Framer Motion performance tips, and mobile device optimization experiences.

### Query Templates
```python
# deep_research (use 2 questions)
"Q1: Achieving 60fps animations in React with page transitions, scroll-driven animations,
and interactive elements. CSS properties animatable on compositor thread? React rendering
model interaction with animations (concurrent mode, state updates during frames)? CSS
transitions vs Web Animations API vs requestAnimationFrame? Profiling jank with DevTools?
Scroll-driven animation patterns for 60fps?"
"Q2: CSS compositor layers, will-change, and GPU memory management. How browser decides
layer promotion? GPU memory cost per layer and how to measure? When will-change helps vs
hurts? Chrome DevTools Layers panel audit methodology?"

# web_search
keywords = ["CSS compositor layer will-change transform GPU acceleration",
            "layout thrashing forced reflow prevention JavaScript",
            "Chrome rendering pipeline composite paint layout explained"]
```

### Best Practices
- Describe your **animation types** -- page transitions, scroll-driven, hover effects, and loading animations have different optimization strategies.
- Include **target devices** -- "mid-range Android phones" shapes optimization priorities significantly.
- Attach janky animation code for dramatically more specific research.
- Ask about **profiling separately from optimization** -- diagnosing is a prerequisite for fixing.
- Three compositor-only CSS properties (no layout/paint): `transform`, `opacity`, `filter`.
- Key rendering pipeline: **Layout** (geometry) -> **Paint** (pixels) -> **Composite** (GPU layers). Animate only at the composite level for 60fps.
- Search for "layout thrashing" and "forced reflow" -- the most common JavaScript animation killers.
- Web Animations API is underused and often the best solution for complex animations needing JavaScript control with CSS-level performance.

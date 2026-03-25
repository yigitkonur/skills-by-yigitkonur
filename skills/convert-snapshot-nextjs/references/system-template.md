# Wave 3: Design System Foundation & Next.js Scaffold Template

This template defines what Wave 3 produces: a complete Next.js project scaffold with a design system grounded entirely on extracted CSS values. Every token, every component, every breakpoint comes from real source data via Waves 0–2.

**Grounding rule:** No value is invented. Every token traces to a CSS rule, CSS custom property, or inline style discovered during Wave 0 exploration and cataloged in Wave 1/2 deliverables.

## When to Use

The Wave 3 orchestrator follows this template to build the project foundation. Wave 4 agents then use this foundation to build individual pages. This template is the contract between Waves 2 and 4 — it specifies every file, every type, every naming convention that downstream agents depend on.

## Prerequisites

Before Wave 3 begins, the following must exist:
- **Wave 0:** Exploration docs, deobfuscated CSS, downloaded assets (fonts, images, icons)
- **Wave 1:** `token-values.json`, `component-inventory.md`, foundation analysis docs
- **Wave 2:** Per-page manifests with section briefs, shared component specs, page routing map

---

## 1. Next.js Project Structure

The scaffold creates a standard Next.js App Router project. Every folder and file class has a specific purpose. The scaffold shape is fixed, but individual shared component files are created only when Wave 1/2 evidence proves they exist or a minimal unstyled wrapper is required to express extracted layout.

```
nextjs-project/
├── app/
│   ├── layout.tsx                     # Root layout: fonts, globals, metadata
│   ├── page.tsx                       # Homepage (stub, built in Wave 4)
│   ├── pricing/page.tsx               # Pricing (stub, built in Wave 4)
│   ├── features/page.tsx              # Features (stub, built in Wave 4)
│   ├── about/page.tsx                 # About (stub, built in Wave 4)
│   └── [additional routes]/page.tsx   # One per page from Wave 2 routing map
│
├── components/
│   ├── shared/                        # Shared components from Wave 1 inventory
│   │   ├── Button.tsx                 # Only if a button primitive is grounded in source
│   │   ├── NavLink.tsx                # Only if nav links are shared
│   │   ├── SectionWrapper.tsx         # Allowed as an unstyled layout wrapper when needed
│   │   ├── Header.tsx                 # Shared header (marked SHARED in Wave 2)
│   │   ├── Footer.tsx                 # Shared footer (if present in source)
│   │   ├── Badge.tsx                  # Only if badge/tag treatment exists
│   │   ├── Card.tsx                   # Only if card shell is a real repeated primitive
│   │   ├── Container.tsx              # Allowed as an unstyled max-width wrapper when needed
│   │   ├── GradientText.tsx           # Only if gradient text is grounded in source
│   │   ├── Icon.tsx                   # Only if icon wrapper semantics are needed
│   │   └── index.ts                   # Export only the files that actually exist
│   └── pages/                         # Page-specific components (built in Wave 4)
│       ├── homepage/
│       ├── pricing/
│       ├── features/
│       └── ...
│
├── lib/
│   ├── tokens.ts                      # Design tokens (typed TypeScript)
│   ├── animations.ts                  # Animation utilities + IntersectionObserver helpers
│   └── utils.ts                       # cn() helper, other utilities
│
├── styles/
│   ├── globals.css                    # @font-face + CSS custom properties + @tailwind
│   └── animations.css                 # @keyframes definitions
│
├── public/
│   └── assets/                        # All self-hosted assets
│       ├── fonts/                     # Local font files (.woff2)
│       ├── images/                    # Per-page image folders
│       │   ├── homepage/
│       │   ├── pricing/
│       │   └── shared/
│       └── icons/                     # SVG icons
│
├── tailwind.config.ts                 # Extended with REAL extracted values
├── postcss.config.js                  # Standard: tailwindcss + autoprefixer
├── tsconfig.json                      # strict: true
├── package.json                       # ONLY allowed deps
└── next.config.js                     # Minimal config
```

### Route Stubs

Every page from the Wave 2 routing map gets a stub file. The stub is a valid React component that renders a placeholder:

```typescript
// app/pricing/page.tsx — Route stub (Wave 4 replaces this)
export default function PricingPage() {
  return (
    <main className="min-h-screen bg-bg-primary text-text-primary">
      <p className="p-8 text-text-secondary">Pricing — Wave 4 builds this page.</p>
    </main>
  );
}
```

Every stub MUST use tokens from the design system so `npm run build` validates token wiring.

### Package.json Dependencies (HARD LIMIT)

Use one internally compatible version set. Do not independently pin every package to `latest`. The safest path is to start from one fresh Next.js App Router scaffold for the chosen Next major, then prune every package outside the allowlist below.

```json
{
  "dependencies": {
    "next": "<current-compatible-next>",
    "react": "<matching-react>",
    "react-dom": "<matching-react-dom>"
  },
  "devDependencies": {
    "typescript": "<next-compatible-typescript>",
    "tailwindcss": "<current-tailwind-3-compatible>",
    "@types/react": "<matching-react-types>",
    "@types/react-dom": "<matching-react-dom-types>",
    "@types/node": "<current-node-types>",
    "postcss": "<current-compatible-postcss>",
    "autoprefixer": "<current-compatible-autoprefixer>"
  }
}
```

**NO other packages.** No UI libraries (no shadcn, no radix, no headless-ui). No animation libraries (no framer-motion, no gsap). No icon packages (no lucide-react, no heroicons). No font packages (no @fontsource). No utility packages (no clsx — we write our own cn()). If a feature requires a library, implement it with vanilla CSS/JS instead.

If `npx tsc --noEmit` fails because the installed TypeScript version requires an `ignoreDeprecations` setting, add the exact compiler-requested value to `tsconfig.json`. Do not guess a value and do not downgrade the grounding requirements just to silence the compiler.

---

## 2. Design Tokens (lib/tokens.ts)

Every value extracted from Wave 1 `token-values.json`, typed in TypeScript. This file is the single source of truth for all visual values in the project.

### Structure

```typescript
// lib/tokens.ts — Auto-generated from extracted CSS values
// Every value traces to source CSS via Wave 0 exploration docs
// Format: value is the resolved CSS value, comment is the source variable name

// ─── Colors ─────────────────────────────────────────────────────────────────

export const colors = {
  brand: {
    DEFAULT: '#5e6ad2',        // --color-brand
    light: '#7c85e0',          // --color-brand-light
    dark: '#4850b8',           // --color-brand-dark
  },
  bg: {
    primary: '#0a0a0f',        // --color-bg-primary (page background)
    secondary: '#1a1a2e',      // --color-bg-secondary (section alt)
    elevated: '#252540',       // --color-bg-elevated (cards, modals)
    overlay: 'rgba(0,0,0,0.6)',// --color-bg-overlay (modal backdrop)
    card: '#16162a',           // --color-bg-card (card surface)
  },
  text: {
    primary: '#f7f8f8',        // --color-text-primary (headings, strong)
    secondary: '#b4b5c0',      // --color-text-secondary (body text)
    tertiary: '#8a8b9a',       // --color-text-tertiary (captions, labels)
    quaternary: '#5f6070',     // --color-text-quaternary (disabled, placeholders)
    onBrand: '#ffffff',        // --color-text-on-brand (text on brand bg)
  },
  border: {
    DEFAULT: 'rgba(255,255,255,0.08)', // --color-border
    strong: 'rgba(255,255,255,0.15)',  // --color-border-strong
  },
  semantic: {
    success: '#4ade80',        // --color-success
    error: '#ef4444',          // --color-error
    warning: '#f59e0b',        // --color-warning
    info: '#3b82f6',           // --color-info
  },
  gradient: {
    brand: 'linear-gradient(135deg, #5e6ad2, #8b5cf6)', // --gradient-brand
    hero: 'linear-gradient(180deg, transparent, #0a0a0f)', // --gradient-hero-fade
    // ... all extracted gradients from Wave 1
  },
  // ... all remaining colors from token-values.json
} as const;

// ─── Typography ─────────────────────────────────────────────────────────────

export const typography = {
  fontFamily: {
    display: "'Inter', sans-serif",       // --font-display
    body: "'Inter', sans-serif",          // --font-body
    mono: "'JetBrains Mono', monospace",  // --font-mono
  },
  fontSize: {
    // Type scale from Wave 1 — [size, { lineHeight, letterSpacing, fontWeight }]
    'display-2xl': ['80px', { lineHeight: '1.0', letterSpacing: '-0.03em', fontWeight: '700' }],
    'display-xl': ['72px', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '700' }],
    'display-lg': ['56px', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '600' }],
    'heading-1': ['48px', { lineHeight: '1.15', letterSpacing: '-0.01em', fontWeight: '600' }],
    'heading-2': ['40px', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
    'heading-3': ['32px', { lineHeight: '1.25', letterSpacing: '-0.005em', fontWeight: '600' }],
    'heading-4': ['24px', { lineHeight: '1.3', letterSpacing: '0em', fontWeight: '600' }],
    'heading-5': ['20px', { lineHeight: '1.4', letterSpacing: '0em', fontWeight: '600' }],
    'body-lg': ['18px', { lineHeight: '1.6', letterSpacing: '0em', fontWeight: '400' }],
    'body': ['16px', { lineHeight: '1.6', letterSpacing: '0em', fontWeight: '400' }],
    'body-sm': ['14px', { lineHeight: '1.5', letterSpacing: '0em', fontWeight: '400' }],
    'caption': ['12px', { lineHeight: '1.4', letterSpacing: '0.02em', fontWeight: '500' }],
    'eyebrow': ['13px', { lineHeight: '1.2', letterSpacing: '0.08em', fontWeight: '600' }],
    // ... all type levels from token-values.json
  },
} as const;

// ─── Spacing ────────────────────────────────────────────────────────────────

export const spacing = {
  section: {
    xl: '160px',    // Hero-level section padding
    lg: '120px',    // Large section padding
    md: '80px',     // Standard section padding
    sm: '48px',     // Compact section padding
    xs: '32px',     // Tight section padding
  },
  container: {
    maxWidth: '1200px',    // Main container max-width
    narrow: '800px',       // Narrow content max-width (blog, legal)
    wide: '1400px',        // Wide container (full-bleed sections)
    padding: '24px',       // Horizontal padding at edges
    paddingMobile: '16px', // Mobile horizontal padding
  },
  component: {
    // Spacing within components, from Wave 1 analysis
    cardPadding: '24px',
    cardGap: '16px',
    buttonPaddingX: '24px',
    buttonPaddingY: '12px',
    inputPaddingX: '16px',
    inputPaddingY: '12px',
  },
  // ... spacing scale from token-values.json
} as const;

// ─── Animation ──────────────────────────────────────────────────────────────

export const animation = {
  easing: {
    default: 'cubic-bezier(0.16, 1, 0.3, 1)',    // --ease-out (primary)
    gentle: 'cubic-bezier(0.4, 0, 0.2, 1)',       // --ease-gentle
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',  // --ease-spring
    inOut: 'cubic-bezier(0.65, 0, 0.35, 1)',       // --ease-in-out
    linear: 'linear',                               // --ease-linear
  },
  duration: {
    instant: '100ms',     // Micro-interactions (focus ring)
    fast: '150ms',        // Hover states, toggles
    normal: '300ms',      // Standard transitions
    slow: '500ms',        // Section reveals, complex transitions
    entrance: '600ms',    // Scroll-triggered entrance animations
    ambient: '3000ms',    // Floating, pulse, background loops
  },
} as const;

// ─── Breakpoints ────────────────────────────────────────────────────────────

export const breakpoints = {
  sm: '640px',       // Small phones → landscape phones
  md: '768px',       // Landscape phones → tablets
  lg: '1024px',      // Tablets → small desktops
  xl: '1280px',      // Small desktops → large desktops
  '2xl': '1536px',   // Large desktops → ultra-wide
  // THESE MUST MATCH REAL @media queries found in Wave 0 CSS
} as const;

// ─── Border Radius ──────────────────────────────────────────────────────────

export const radius = {
  xs: '2px',        // --radius-xs (subtle rounding)
  sm: '4px',        // --radius-sm (buttons, inputs)
  md: '8px',        // --radius-md (cards, panels)
  lg: '12px',       // --radius-lg (modals, containers)
  xl: '16px',       // --radius-xl (large cards)
  '2xl': '24px',    // --radius-2xl (hero cards)
  full: '9999px',   // --radius-full (pills, avatars)
} as const;

// ─── Shadows ────────────────────────────────────────────────────────────────

export const shadows = {
  xs: '0 1px 2px rgba(0,0,0,0.05)',                            // --shadow-xs
  sm: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',// --shadow-sm
  md: '0 4px 12px rgba(0,0,0,0.15)',                           // --shadow-md
  lg: '0 8px 24px rgba(0,0,0,0.2)',                            // --shadow-lg
  xl: '0 16px 48px rgba(0,0,0,0.25)',                          // --shadow-xl
  glow: '0 0 24px rgba(94,106,210,0.3)',                       // --shadow-glow (brand glow)
  inner: 'inset 0 1px 2px rgba(0,0,0,0.1)',                   // --shadow-inner
} as const;

// ─── Z-Index Layers ─────────────────────────────────────────────────────────

export const zIndex = {
  base: 0,           // Default content
  dropdown: 10,      // Dropdowns, tooltips
  sticky: 20,        // Sticky header, floating nav
  overlay: 30,       // Backdrop behind modals
  modal: 40,         // Modal dialogs
  toast: 50,         // Notification toasts (topmost)
} as const;
```

### Token Rules

1. Every value in `tokens.ts` MUST trace back to a CSS rule found in Wave 0 deobfuscated CSS.
2. If a value was inferred (not directly extracted), mark it with `// INFERRED: [reason]` in the comment.
3. If a value could not be verified, mark it with `// UNVERIFIED: [what was expected]` and investigate.
4. The `as const` assertion on every export ensures TypeScript narrows the types to literal values.
5. Do NOT use enums. Use plain objects with `as const`.
6. Do NOT nest deeper than 3 levels. Flat is better than nested.

---

## 3. Tailwind Configuration (tailwind.config.ts)

Extend Tailwind with REAL extracted values. Do NOT use Tailwind defaults if they don't match the source site. Every color, every breakpoint, every spacing value must be overridden with extracted values.

```typescript
// tailwind.config.ts — Extended with real extracted values from Wave 1
import type { Config } from 'tailwindcss'
import {
  colors,
  typography,
  spacing,
  animation,
  breakpoints,
  radius,
  shadows,
} from './lib/tokens'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    // OVERRIDE defaults with real values where they differ
    screens: {
      sm: breakpoints.sm,
      md: breakpoints.md,
      lg: breakpoints.lg,
      xl: breakpoints.xl,
      '2xl': breakpoints['2xl'],
    },
    extend: {
      // ─── Colors ────────────────────────────────────────────────
      colors: {
        brand: colors.brand,
        bg: colors.bg,
        text: colors.text,
        border: colors.border,
        semantic: colors.semantic,
        // Flatten additional colors as needed for Tailwind classes:
        // bg-brand → colors.brand.DEFAULT
        // text-text-primary → colors.text.primary
        // bg-bg-primary → colors.bg.primary
      },

      // ─── Typography ───────────────────────────────────────────
      fontFamily: {
        display: [typography.fontFamily.display],
        body: [typography.fontFamily.body],
        mono: [typography.fontFamily.mono],
      },
      fontSize: {
        // Map token fontSize entries to Tailwind format
        // text-display-xl → typography.fontSize['display-xl']
        'display-2xl': typography.fontSize['display-2xl'],
        'display-xl': typography.fontSize['display-xl'],
        'display-lg': typography.fontSize['display-lg'],
        'heading-1': typography.fontSize['heading-1'],
        'heading-2': typography.fontSize['heading-2'],
        'heading-3': typography.fontSize['heading-3'],
        'heading-4': typography.fontSize['heading-4'],
        'heading-5': typography.fontSize['heading-5'],
        'body-lg': typography.fontSize['body-lg'],
        'body': typography.fontSize['body'],
        'body-sm': typography.fontSize['body-sm'],
        'caption': typography.fontSize['caption'],
        'eyebrow': typography.fontSize['eyebrow'],
      },

      // ─── Spacing ──────────────────────────────────────────────
      spacing: {
        'section-xl': spacing.section.xl,
        'section-lg': spacing.section.lg,
        'section-md': spacing.section.md,
        'section-sm': spacing.section.sm,
        'section-xs': spacing.section.xs,
      },
      maxWidth: {
        container: spacing.container.maxWidth,
        narrow: spacing.container.narrow,
        wide: spacing.container.wide,
      },
      padding: {
        container: spacing.container.padding,
        'container-mobile': spacing.container.paddingMobile,
      },

      // ─── Shape ────────────────────────────────────────────────
      borderRadius: {
        xs: radius.xs,
        sm: radius.sm,
        md: radius.md,
        lg: radius.lg,
        xl: radius.xl,
        '2xl': radius['2xl'],
        full: radius.full,
      },
      boxShadow: {
        xs: shadows.xs,
        sm: shadows.sm,
        md: shadows.md,
        lg: shadows.lg,
        xl: shadows.xl,
        glow: shadows.glow,
        inner: shadows.inner,
      },

      // ─── Animation ────────────────────────────────────────────
      transitionTimingFunction: {
        DEFAULT: animation.easing.default,
        gentle: animation.easing.gentle,
        spring: animation.easing.spring,
        'in-out': animation.easing.inOut,
      },
      transitionDuration: {
        instant: animation.duration.instant,
        fast: animation.duration.fast,
        normal: animation.duration.normal,
        slow: animation.duration.slow,
        entrance: animation.duration.entrance,
      },
    },
  },
  plugins: [],
}

export default config
```

### CRITICAL RULES:
- These breakpoints, colors, and spacing MUST come from real extracted CSS values, NOT Tailwind defaults.
- If Tailwind's default `blue-500` happens to match a brand color, use the extracted value anyway — naming must match the design system, not Tailwind conventions.
- The `content` array must cover all directories where Tailwind classes appear.
- Do NOT add any Tailwind plugins. CSS-only implementations for all patterns.

---

## 4. Global Styles (styles/globals.css)

This file combines Tailwind directives, font-face declarations, and CSS custom properties. All values are extracted from Wave 0 source CSS.

```css
/* styles/globals.css */

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ─── Font Loading — self-hosted, NO CDN ─────────────────────────────────── */

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url('/assets/fonts/inter-var.woff2') format('woff2');
}

@font-face {
  font-family: 'Inter';
  font-style: italic;
  font-weight: 100 900;
  font-display: swap;
  src: url('/assets/fonts/inter-var-italic.woff2') format('woff2');
}

@font-face {
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/assets/fonts/jetbrains-mono-var.woff2') format('woff2');
}

/* Add ALL @font-face declarations found in Wave 0 CSS. */
/* Each must reference a local file in /assets/fonts/ — never a CDN URL. */

/* ─── CSS Custom Properties (from extracted :root) ────────────────────────── */

:root {
  /* Brand */
  --color-brand: #5e6ad2;
  --color-brand-light: #7c85e0;
  --color-brand-dark: #4850b8;

  /* Backgrounds */
  --color-bg-primary: #0a0a0f;
  --color-bg-secondary: #1a1a2e;
  --color-bg-elevated: #252540;
  --color-bg-overlay: rgba(0,0,0,0.6);
  --color-bg-card: #16162a;

  /* Text */
  --color-text-primary: #f7f8f8;
  --color-text-secondary: #b4b5c0;
  --color-text-tertiary: #8a8b9a;
  --color-text-quaternary: #5f6070;

  /* Borders */
  --color-border: rgba(255,255,255,0.08);
  --color-border-strong: rgba(255,255,255,0.15);

  /* Typography */
  --font-display: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Animation */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-gentle: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-entrance: 600ms;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.2);

  /* ... ALL extracted CSS variables from Wave 0 :root ... */
}

/* ─── Dark Mode Overrides (if extracted) ──────────────────────────────────── */

[data-theme="dark"] {
  /* Override variables for dark theme if the source site has theme switching. */
  /* If the source is dark-only, this block is empty or omitted. */
}

/* ─── Base Resets (grounded on source CSS) ────────────────────────────────── */

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-body);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  line-height: 1.6;
}

a {
  color: inherit;
  text-decoration: none;
}

img {
  max-width: 100%;
  height: auto;
  display: block;
}
```

---

## 5. Animation System

Two files work together: `lib/animations.ts` for JavaScript-driven scroll animations, and `styles/animations.css` for pure CSS keyframes and utility classes.

### lib/animations.ts

```typescript
// lib/animations.ts — Scroll-triggered animation utilities
// Uses IntersectionObserver (no external libraries)
// Respects prefers-reduced-motion at the OS level

import { useEffect, useRef, type RefObject } from 'react';

/**
 * Hook: Adds 'animate-in' class when element enters viewport.
 * Respects prefers-reduced-motion — skips animation if user prefers reduced motion.
 *
 * Usage:
 *   const ref = useScrollAnimation();
 *   <div ref={ref} className="opacity-0 translate-y-6">...</div>
 *   // Element gets 'animate-in' class when scrolled into view
 */
export function useScrollAnimation(
  options: IntersectionObserverInit = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
): RefObject<HTMLDivElement | null> {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Respect user's motion preference
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      el.classList.add('animate-in');
      return;
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        el.classList.add('animate-in');
        observer.unobserve(el);
      }
    }, options);

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return ref;
}

/**
 * Hook: Staggers 'animate-in' class across child elements.
 * Each child receives the class with an incremental delay.
 *
 * Usage:
 *   const ref = useStaggerAnimation(100);
 *   <div ref={ref}>
 *     <div className="opacity-0 translate-y-4">Child 1</div>
 *     <div className="opacity-0 translate-y-4">Child 2</div>
 *   </div>
 */
export function useStaggerAnimation(
  staggerMs: number = 100,
  options: IntersectionObserverInit = { threshold: 0.1 }
): RefObject<HTMLDivElement | null> {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const children = Array.from(container.children) as HTMLElement[];

    if (prefersReduced) {
      children.forEach((child) => child.classList.add('animate-in'));
      return;
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        children.forEach((child, i) => {
          child.style.transitionDelay = `${i * staggerMs}ms`;
          child.classList.add('animate-in');
        });
        observer.unobserve(container);
      }
    }, options);

    observer.observe(container);
    return () => observer.disconnect();
  }, [staggerMs]);

  return ref;
}
```

### styles/animations.css

```css
/* styles/animations.css — @keyframes from extracted source CSS */

/* ─── Entrance Animations ────────────────────────────────────────────────── */

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-24px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(24px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* ─── Ambient / Looping Animations ────────────────────────────────────────── */

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes shimmer {
  from { background-position: -200% 0; }
  to { background-position: 200% 0; }
}

/* ... add ALL @keyframes blocks found in Wave 0 deobfuscated CSS ... */

/* ─── Utility Classes ────────────────────────────────────────────────────── */

/* Default scroll-triggered entrance: fade + slide up */
.animate-in {
  animation: fadeInUp var(--duration-entrance, 600ms) var(--ease-out, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
}

/* Variant entrances — apply via additional classes */
.animate-fade { animation-name: fadeIn; }
.animate-slide-down { animation-name: fadeInDown; }
.animate-slide-left { animation-name: fadeInLeft; }
.animate-slide-right { animation-name: fadeInRight; }
.animate-scale { animation-name: scaleIn; }

/* Ambient animations — opt-in via class */
.animate-float { animation: float 3s var(--ease-gentle) infinite; }
.animate-pulse { animation: pulse 2s var(--ease-gentle) infinite; }

/* ─── Reduced Motion ─────────────────────────────────────────────────────── */

@media (prefers-reduced-motion: reduce) {
  .animate-in,
  .animate-fade,
  .animate-slide-down,
  .animate-slide-left,
  .animate-slide-right,
  .animate-scale {
    animation: none;
    opacity: 1;
    transform: none;
  }

  .animate-float,
  .animate-pulse {
    animation: none;
  }
}
```

---

## 6. Shared Component Library

Every component tagged `SHARED` in Wave 2 manifests must be built in Wave 3. These are the building blocks that Wave 4 page agents import.

### Component Design Rules

1. **Props are explicit.** No `...rest` spreading, no `any` types. Every prop is named and typed.
2. **Styles use only tokens.** No hardcoded hex colors, no magic pixel values. Everything maps to a Tailwind class backed by `tokens.ts`.
3. **No external dependencies.** No component libraries, no animation libraries. Pure React + Tailwind.
4. **Accessibility by default.** Semantic HTML, ARIA attributes where needed, keyboard navigation for interactive elements.
5. **Server Components by default.** Only add `'use client'` if the component requires browser APIs (event handlers, refs, hooks).

### lib/utils.ts — Shared Utilities

```typescript
// lib/utils.ts — Utility functions used across all components

/**
 * Conditional class name helper.
 * Merges class strings, filtering out falsy values.
 * Replaces clsx/classnames — no external package needed.
 *
 * Usage: cn('base-class', isActive && 'active', variant === 'primary' && 'bg-brand')
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}
```

### Component Template

Every shared component follows this pattern:

```typescript
// components/shared/Button.tsx
import { cn } from '@/lib/utils';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  href?: string;
  className?: string;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-brand text-text-onBrand hover:bg-brand-light active:bg-brand-dark transition-colors duration-fast',
  secondary: 'bg-bg-elevated text-text-primary border border-border hover:bg-bg-card transition-colors duration-fast',
  ghost: 'bg-transparent text-text-secondary hover:text-text-primary transition-colors duration-fast',
} as const;

const sizeStyles = {
  sm: 'px-4 py-2 text-body-sm rounded-sm',
  md: 'px-6 py-3 text-body rounded-md',
  lg: 'px-8 py-4 text-body-lg rounded-md font-semibold',
} as const;

export function Button({
  variant = 'primary',
  size = 'md',
  href,
  className,
  children,
}: ButtonProps) {
  const classes = cn(
    'inline-flex items-center justify-center font-medium',
    variantStyles[variant],
    sizeStyles[size],
    className,
  );

  if (href) {
    return <a href={href} className={classes}>{children}</a>;
  }

  return <button className={classes}>{children}</button>;
}
```

### Shared Component Decision Table

Only implement the components below when the Wave 1 inventory or Wave 2 manifests prove they exist, or when a wrapper is explicitly allowed as a zero-style structural helper. If a listed component is absent from the source, omit the file and record that omission in the Wave 3 traceability matrix instead of inventing visuals.

| Component | File | Props | Variants | Source |
|-----------|------|-------|----------|--------|
| Button | `Button.tsx` | variant, size, href, className, children | primary / secondary / ghost × sm / md / lg | Create only if buttons are a shared primitive in Wave 1 inventory |
| Header | `Header.tsx` | transparent?: boolean | standard / transparent | Create only if Wave 2 marks header as SHARED |
| Footer | `Footer.tsx` | — | — | Create only if footer is grounded in source |
| NavLink | `NavLink.tsx` | href, active?: boolean, children | — | Create only if shared nav links exist |
| SectionWrapper | `SectionWrapper.tsx` | maxWidth?: string, padding?: string, bg?: string, className?, children | — | Allowed structural helper; must stay unstyled except for grounded layout values |
| Container | `Container.tsx` | size?: 'default' / 'narrow' / 'wide', className?, children | default / narrow / wide | Allowed structural helper; must stay unstyled except for grounded layout values |
| Badge | `Badge.tsx` | variant?: 'default' / 'brand' / 'success', children | color variants | Create only if badges/tags exist in inventory |
| Card | `Card.tsx` | hover?: boolean, className?, children | with/without hover effect | Create only if a reusable card shell is grounded in source |
| GradientText | `GradientText.tsx` | gradient?: string, as?: keyof JSX.IntrinsicElements, children | — | Create only if gradient text exists in source |
| Icon | `Icon.tsx` | name: string, size?: 'sm' / 'md' / 'lg', className? | size variants | Create only if icon wrapper semantics are needed |

### Barrel Export

```typescript
// components/shared/index.ts
export { Button } from './Button';
export { Header } from './Header';
export { Footer } from './Footer';
export { NavLink } from './NavLink';
export { SectionWrapper } from './SectionWrapper';
export { Container } from './Container';
export { Badge } from './Badge';
export { Card } from './Card';
export { GradientText } from './GradientText';
export { Icon } from './Icon';
```

Only export files that were actually created. Do not add empty stubs just to satisfy the table above.

---

## 7. Root Layout (app/layout.tsx)

The root layout wires up fonts, global styles, metadata, and any optional shared chrome that truly applies across pages.

```typescript
// app/layout.tsx
import type { Metadata } from 'next';
import '@/styles/globals.css';
import '@/styles/animations.css';
// Import shared chrome only if Wave 2 marked it SHARED:
// import { Header } from '@/components/shared/Header';
// import { Footer } from '@/components/shared/Footer';

export const metadata: Metadata = {
  title: '[Site Name] — [Tagline]',       // From Wave 0 <title> extraction
  description: '[Site description]',        // From Wave 0 <meta name="description">
  // ... additional metadata from Wave 0 <head>
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-body bg-bg-primary text-text-primary antialiased">
        {/* Optional shared chrome: render only when those components exist in Wave 3. */}
        {/* <Header /> */}
        {children}
        {/* <Footer /> */}
      </body>
    </html>
  );
}
```

### Layout Rules:
- `globals.css` is imported FIRST — it contains @tailwind directives and @font-face.
- `animations.css` is imported SECOND — it contains @keyframes referenced by animation utilities.
- Header and Footer wrap page content only when Wave 2 proves they are SHARED. Do not invent global chrome when the snapshot has page-specific shells or no persistent header/footer.
- The `<html>` element gets `lang="en"` (or whatever `lang` attribute was found in Wave 0 HTML).
- The `<body>` element gets base typography and color classes from the design system.
- Metadata is extracted from Wave 0 HTML `<head>` — title, description, Open Graph tags.

---

## 8. Foundation Quality Gate

Wave 3 is NOT complete until ALL checks pass. The orchestrator must verify every item below before writing the `foundation-ready.signal` file. This signal file is what authorizes Wave 4 to begin.

### Token Coverage

- [ ] Every color from Wave 1 `token-values.json` exists in `tokens.ts` under the appropriate category
- [ ] Every font family from Wave 1 exists in `tokens.ts` AND has a matching `@font-face` in `globals.css`
- [ ] Every font weight used in Wave 1 type scale is covered by the `@font-face` weight range
- [ ] Every spacing value from Wave 1 exists in `tokens.ts` (section, container, component)
- [ ] Every breakpoint from Wave 1 exists in `tokens.ts` AND is wired into `tailwind.config.ts` screens
- [ ] Every animation easing/duration from Wave 1 exists in `tokens.ts`
- [ ] Every border-radius value from Wave 1 exists in `tokens.ts`
- [ ] Every shadow value from Wave 1 exists in `tokens.ts`
- [ ] Every gradient from Wave 1 is documented in `tokens.ts` (at minimum as a comment with the CSS value)

### Component Coverage

- [ ] Every component marked `SHARED` in Wave 2 manifests has an implementation in `components/shared/`
- [ ] Every shared component's props match the Wave 2 specification (same variant names, same prop types)
- [ ] Every component uses ONLY `tokens.ts` values via Tailwind classes (no hardcoded `#hex` or `12px` in components)
- [ ] The barrel export (`components/shared/index.ts`) exports every shared component
- [ ] Every component is a valid TypeScript file with no type errors

### Build Check

- [ ] `npm install` succeeds with zero warnings about missing peer deps
- [ ] `npx tsc --noEmit` produces zero errors across all `.ts` and `.tsx` files
- [ ] `npm run build` produces zero errors (all route stubs must be valid React components)
- [ ] `package.json` has ONLY the allowed dependencies listed in Section 1 (no extras)

### Asset Check

- [ ] All font files from Wave 0 `assets/` are copied to `public/assets/fonts/`
- [ ] Every `@font-face` declaration in `globals.css` references a file that exists in `public/assets/fonts/`
- [ ] Font loading works — the `font-display: swap` property is set on every `@font-face`
- [ ] All images referenced in Wave 2 manifests exist in `public/assets/images/[page]/`
- [ ] All SVG icons from Wave 0 exist in `public/assets/icons/`

### Zero External Dependencies

- [ ] `grep -r "http://" --include="*.ts" --include="*.tsx" --include="*.css" .` — zero results
- [ ] `grep -r "https://" --include="*.ts" --include="*.tsx" --include="*.css" .` — zero results (except `next.config.js` if needed)
- [ ] No `<link>` tags pointing to CDNs in any component or layout
- [ ] No Google Fonts links, no unpkg, no cdnjs, no jsdelivr — everything is local

### Route Coverage

- [ ] Every page from Wave 2 routing map has a stub file under `app/`
- [ ] Every stub file exports a default React component
- [ ] Every stub uses at least one design system class (validates token wiring)

### Traceability

- [ ] `traceability-matrix.md` exists and maps every token to its Wave 2 brief section AND Wave 0 CSS source
- [ ] No token exists in `tokens.ts` without a source citation (either inline comment or matrix entry)
- [ ] The matrix covers: colors, typography, spacing, breakpoints, animation, shadows, radius

### Signal File

Only after ALL checks above pass, write:

```
foundation-ready.signal
```

`foundation-ready.signal` is an empty file. If you need a human-readable completion summary, keep it in `foundation-brief.md` or `traceability-matrix.md`, not in the signal file.

---

## 9. Foundation Brief for Wave 4 (foundation-brief.md)

This file is the handoff document that every Wave 4 page agent reads before building their page. It must contain everything a page agent needs to know.

### Required Sections in foundation-brief.md:

**1. Import Guide**
```typescript
// How to import tokens (for reference, not direct use — prefer Tailwind classes)
import { colors, typography, spacing } from '@/lib/tokens';

// Import only the shared components Wave 3 actually created.
// Example:
// import { Button, SectionWrapper, Container, Badge } from '@/components/shared';

// How to import animation utilities
import { useScrollAnimation, useStaggerAnimation } from '@/lib/animations';

// How to import utility functions
import { cn } from '@/lib/utils';
```

**2. Tailwind Class Reference**
A mapping of design tokens to their Tailwind utility classes:
```
Background:   bg-bg-primary, bg-bg-secondary, bg-bg-elevated, bg-bg-card
Text:         text-text-primary, text-text-secondary, text-text-tertiary
Brand:        bg-brand, text-brand, hover:bg-brand-light
Border:       border-border, border-border-strong
Radius:       rounded-sm, rounded-md, rounded-lg, rounded-xl, rounded-full
Shadow:       shadow-sm, shadow-md, shadow-lg, shadow-glow
Spacing:      py-section-lg, py-section-md, py-section-sm
Container:    max-w-container, max-w-narrow, max-w-wide
Font:         font-display, font-body, font-mono
Size:         text-display-xl, text-heading-1, text-body, text-caption
Animation:    duration-fast, duration-normal, ease-DEFAULT, ease-spring
```

**3. Shared Component API**
For each shared component: name, import path, all props with types, example usage snippet.

**4. Animation Patterns**
How to apply scroll-triggered animations:
```typescript
// Basic fade-in on scroll
const ref = useScrollAnimation();
<div ref={ref} className="opacity-0 translate-y-6">Content fades in</div>

// Staggered children
const ref = useStaggerAnimation(100);
<div ref={ref}>
  <div className="opacity-0 translate-y-4">Item 1</div>
  <div className="opacity-0 translate-y-4">Item 2</div>
</div>
```

**5. Image Strategy**
- All images go in `public/assets/images/[page-name]/`
- Reference as `/assets/images/[page-name]/filename.ext`
- Use Next.js `<Image>` for raster assets by default; fall back to plain `<img>` only when the brief explicitly requires it, and keep icons as inline SVG or local SVG assets
- Provide `width`, `height`, and `alt` on every image

**6. Page Structure Convention**
Every page follows this skeleton:
```typescript
export default function PageName() {
  return (
    <main>
      {/* Use SectionWrapper only if Wave 3 created it. Otherwise put the grounded classes directly on the section. */}
      <section className="bg-bg-primary py-section-lg">
        <div className="mx-auto max-w-container px-container">
          {/* Section content */}
        </div>
      </section>
      <section className="bg-bg-secondary py-section-md">
        <div className="mx-auto max-w-container px-container">
          {/* Next section */}
        </div>
      </section>
    </main>
  );
}
```

**7. Route Map**
Table listing every page, its route, the Wave 2 manifest file, and the stub file location.

---

## 10. Traceability Matrix Format

Every token in the design system must trace to its origin. The traceability matrix is a Markdown table that maps tokens → Wave 2 brief references → Wave 0 source CSS.

### Matrix Structure

```markdown
# Traceability Matrix

## Colors

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| colors.brand.DEFAULT | #5e6ad2 | homepage/Hero.colors.brand | wave0/homepage/deobfuscated.css → :root → --color-brand |
| colors.brand.light | #7c85e0 | homepage/Hero.colors.brandHover | wave0/homepage/deobfuscated.css → :root → --color-brand-light |
| colors.bg.primary | #0a0a0f | global/background | wave0/homepage/deobfuscated.css → :root → --color-bg-primary |
| colors.text.primary | #f7f8f8 | global/typography.color | wave0/homepage/deobfuscated.css → :root → --color-text-primary |

## Typography

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| typography.fontFamily.display | 'Inter', sans-serif | global/fonts.display | wave0/homepage/deobfuscated.css → :root → --font-display |
| typography.fontSize.heading-1 | 48px / 1.15 / -0.01em | homepage/Hero.typography.H1 | wave0/homepage/deobfuscated.css → .hero-heading |
| typography.fontSize.display-xl | 72px / 1.05 / -0.02em | homepage/Hero.typography.display | wave0/homepage/deobfuscated.css → .hero-title |

## Spacing

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| spacing.section.lg | 120px | global/layout.sectionPadding | wave0/homepage/deobfuscated.css → .section → padding-block |
| spacing.container.maxWidth | 1200px | global/layout.containerWidth | wave0/homepage/deobfuscated.css → .container → max-width |

## Breakpoints

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| breakpoints.sm | 640px | global/responsive.mobile | wave0/homepage/deobfuscated.css → @media (min-width: 640px) |
| breakpoints.lg | 1024px | global/responsive.desktop | wave0/homepage/deobfuscated.css → @media (min-width: 1024px) |

## Animation

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| animation.easing.default | cubic-bezier(0.16, 1, 0.3, 1) | global/motion.easeOut | wave0/homepage/deobfuscated.css → :root → --ease-out |
| animation.duration.entrance | 600ms | global/motion.entranceDuration | wave0/homepage/deobfuscated.css → .animate-in → animation-duration |

## Shadows

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| shadows.md | 0 4px 12px rgba(0,0,0,0.15) | global/elevation.card | wave0/homepage/deobfuscated.css → .card → box-shadow |
| shadows.glow | 0 0 24px rgba(94,106,210,0.3) | homepage/CTA.glowEffect | wave0/homepage/deobfuscated.css → .cta-glow → box-shadow |

## Radius

| Token Path | Value | Wave 2 Brief Reference | Wave 0 CSS Source |
|-----------|-------|----------------------|------------------|
| radius.sm | 4px | global/shape.buttonRadius | wave0/homepage/deobfuscated.css → .button → border-radius |
| radius.md | 8px | global/shape.cardRadius | wave0/homepage/deobfuscated.css → .card → border-radius |
```

### Matrix Rules

1. **Every row must have all four columns filled.** No empty cells.
2. **Wave 0 CSS Source must be specific:** file path → selector → property. Not just "found in CSS."
3. **If a token was inferred** (not directly extracted), the Wave 0 column should say `INFERRED: [reason]`.
4. **If a token is unverified**, the Wave 0 column should say `UNVERIFIED: [what was expected]`.
5. **The matrix must be complete** — every token in `tokens.ts` must appear in the matrix.

---

## 11. File Delivery Checklist

When Wave 3 completes, these files MUST exist. No exceptions.

### Required Files

| File | Purpose | Template Section |
|------|---------|-----------------|
| `lib/tokens.ts` | All design tokens, typed | Section 2 |
| `lib/animations.ts` | Scroll animation hooks | Section 5 |
| `lib/utils.ts` | cn() helper | Section 6 |
| `tailwind.config.ts` | Extended Tailwind config | Section 3 |
| `postcss.config.js` | PostCSS with Tailwind + autoprefixer | Section 1 |
| `styles/globals.css` | Font-face + CSS vars + Tailwind directives | Section 4 |
| `styles/animations.css` | @keyframes + animation utilities | Section 5 |
| `app/layout.tsx` | Root layout with globals + optional shared chrome | Section 7 |
| `app/page.tsx` | Homepage route stub | Section 1 |
| `app/[route]/page.tsx` | One stub per Wave 2 page | Section 1 |
| `components/shared/*.tsx` | All grounded shared components | Section 6 |
| `components/shared/index.ts` | Barrel export for created shared components | Section 6 |
| `package.json` | Only allowed deps | Section 1 |
| `tsconfig.json` | strict: true, path aliases | Section 1 |
| `next.config.js` | Minimal Next.js config | Section 1 |
| `foundation-brief.md` | Wave 4 handoff document | Section 9 |
| `traceability-matrix.md` | Token → source mapping | Section 10 |
| `foundation-ready.signal` | Gate signal (written last) | Section 8 |

### File Sizes (Approximate Expectations)

| File | Expected Lines | If Under, Likely Missing |
|------|---------------|------------------------|
| `tokens.ts` | 150–300 | Colors, spacing, or typography incomplete |
| `tailwind.config.ts` | 80–150 | Token wiring incomplete |
| `globals.css` | 80–150 | Missing @font-face or CSS variables |
| `animations.css` | 50–100 | Missing @keyframes from source |
| `animations.ts` | 60–100 | Missing stagger or reduced motion |
| `layout.tsx` | 25–40 | Missing metadata or structure |
| Each shared component | 30–80 | Missing variants or accessibility |
| `foundation-brief.md` | 100–200 | Missing import guide or class reference |
| `traceability-matrix.md` | 80–200 | Incomplete token coverage |

---

## Appendix A: postcss.config.js

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

No other PostCSS plugins. No nesting plugin (use Tailwind's built-in support if needed).

## Appendix B: tsconfig.json

```json
{
  "compilerOptions": {
    "target": "es2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

The `@/*` path alias is mandatory — all imports use it (`@/lib/tokens`, `@/components/shared`).

If the installed TypeScript version requires `ignoreDeprecations`, add only the exact value requested by the compiler. Keep the rest of the config minimal.

## Appendix C: next.config.js

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Minimal config — add only what's needed
  reactStrictMode: true,
};

module.exports = nextConfig;
```

No image domains (all assets are local). No rewrites. No headers. Keep it minimal.

## Appendix D: SectionWrapper Pattern

`SectionWrapper` is an optional structural helper. Use it only when Wave 3 intentionally creates it to express grounded section spacing and containment. Do not force every section through it if the page is clearer without the wrapper.

```typescript
// components/shared/SectionWrapper.tsx
import { cn } from '@/lib/utils';

interface SectionWrapperProps {
  bg?: string;           // Tailwind bg class: 'bg-bg-primary', 'bg-bg-secondary'
  padding?: string;      // Tailwind py class: 'py-section-lg', 'py-section-md'
  maxWidth?: string;     // Tailwind max-w class: 'max-w-container', 'max-w-narrow'
  className?: string;
  children: React.ReactNode;
}

export function SectionWrapper({
  bg = 'bg-bg-primary',
  padding = 'py-section-md',
  maxWidth = 'max-w-container',
  className,
  children,
}: SectionWrapperProps) {
  return (
    <section className={cn(bg, padding, className)}>
      <div className={cn('mx-auto px-container', maxWidth)}>
        {children}
      </div>
    </section>
  );
}
```

Wave 4 may use `SectionWrapper` when it matches the extracted layout. Otherwise, place the same grounded classes directly on the section markup. Keep the defaults above only when those values are genuinely shared across the snapshot; if not, require explicit props.

## Appendix E: Header / Footer Pattern

Use these patterns only when the source proves a shared header, footer, or nav primitive exists. If the snapshot uses page-specific chrome, keep those pieces page-local instead of creating global shared components.

### Header

```typescript
// components/shared/Header.tsx
'use client';

import { cn } from '@/lib/utils';
import { NavLink } from './NavLink';
import { Button } from './Button';

interface HeaderProps {
  transparent?: boolean;
}

export function Header({ transparent = false }: HeaderProps) {
  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-sticky',
        'flex items-center justify-between',
        'px-container py-4',
        transparent
          ? 'bg-transparent'
          : 'bg-bg-primary/80 backdrop-blur-md border-b border-border',
      )}
    >
      <div className="flex items-center gap-8">
        {/* Logo — use extracted SVG or image */}
        <a href="/" className="font-display text-heading-5 font-bold text-text-primary">
          [Logo]
        </a>

        {/* Navigation links — from Wave 2 manifest */}
        <nav className="hidden md:flex items-center gap-6">
          {/* <NavLink href="/route-from-wave2">Label from source</NavLink> */}
          {/* Repeat only for links proven by Wave 2 route/navigation docs */}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Optional action buttons from the source header */}
        {/* <Button variant="ghost" size="sm" href="/source-action">Action</Button> */}
        {/* <Button variant="primary" size="sm" href="/source-action">Primary Action</Button> */}
      </div>
    </header>
  );
}
```

### Footer

```typescript
// components/shared/Footer.tsx
import { cn } from '@/lib/utils';
import { NavLink } from './NavLink';

export function Footer() {
  return (
    <footer className="bg-bg-secondary border-t border-border py-section-sm">
      <div className="mx-auto max-w-container px-container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Column groups — from Wave 2 footer manifest */}
          <div>
            <h4 className="text-caption font-semibold text-text-primary uppercase tracking-wider mb-4">
              [Column Heading]
            </h4>
            <ul className="space-y-2">
              {/* <li><NavLink href="/route-from-wave2">Link label from source</NavLink></li> */}
              {/* Repeat for grounded footer links only */}
            </ul>
          </div>
          {/* ... additional columns ... */}
        </div>

        <div className="mt-12 pt-8 border-t border-border flex items-center justify-between">
          <p className="text-body-sm text-text-tertiary">
            © {new Date().getFullYear()} [Company Name]. All rights reserved.
          </p>
          {/* Social links, legal links */}
        </div>
      </div>
    </footer>
  );
}
```

### NavLink

```typescript
// components/shared/NavLink.tsx
import { cn } from '@/lib/utils';

interface NavLinkProps {
  href: string;
  active?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function NavLink({ href, active = false, className, children }: NavLinkProps) {
  return (
    <a
      href={href}
      className={cn(
        'text-body-sm transition-colors duration-fast',
        active
          ? 'text-text-primary'
          : 'text-text-secondary hover:text-text-primary',
        className,
      )}
    >
      {children}
    </a>
  );
}
```

---

*End of Wave 3: Design System Foundation & Next.js Scaffold Template*

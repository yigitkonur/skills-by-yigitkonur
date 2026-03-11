# Token Naming Conventions

How to name, organize, and document design tokens extracted from a codebase.

---

## Naming Strategies

### 1. Semantic Naming (Recommended)

Names describe **purpose**, not appearance. This is the dominant pattern in modern design systems.

```
--background           (NOT --white)
--foreground           (NOT --black)
--primary              (NOT --blue)
--destructive          (NOT --red)
--muted-foreground     (NOT --gray-500)
```

**Why semantic**: When dark mode flips values, `--background` still makes sense. `--white` would be misleading.

### 2. Scale Naming

Names describe **position on a scale**. Common for primitive tokens.

```
--gray-50    --gray-100    --gray-200    ... --gray-950
--blue-50    --blue-100    --blue-200    ... --blue-950
--spacing-0  --spacing-1   --spacing-2   ... --spacing-12
```

### 3. Component Naming

Names describe **where the token is used**. Common for component-level tokens.

```
--button-primary-bg
--input-border-default
--sidebar-background
--card-shadow
```

---

## Common Naming Patterns in the Wild

### shadcn/ui Pattern (Most Common in Modern React)

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0.006 285.885);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.965 0.001 286.375);
  --secondary-foreground: oklch(0.205 0.006 285.885);
  --muted: oklch(0.965 0.001 286.375);
  --muted-foreground: oklch(0.556 0.005 286.286);
  --accent: oklch(0.965 0.001 286.375);
  --accent-foreground: oklch(0.205 0.006 285.885);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0.004 286.32);
  --input: oklch(0.922 0.004 286.32);
  --ring: oklch(0.708 0.005 286.286);
}
```

Pattern: `{purpose}` or `{purpose}-{variant}` (e.g., `card-foreground`)

### Material Design Pattern

```
--md-sys-color-primary
--md-sys-color-on-primary
--md-sys-color-surface
--md-sys-color-on-surface
--md-ref-palette-primary-40
```

Pattern: `{namespace}-{layer}-{category}-{variant}`

### Tailwind/Utility Pattern

```
--color-gray-950
--color-blue-500
--spacing-4
--font-size-sm
```

Pattern: `{category}-{scale-position}`

---


### shadcn/ui Naming Convention (Dominant in Modern React)

| Pattern | Example | Rule |
|---------|---------|------|
| `--{purpose}` | `--background`, `--foreground` | Single-word semantic name |
| `--{purpose}-{variant}` | `--primary-foreground`, `--card-foreground` | Purpose + variant suffix |
| `--{scope}-{purpose}` | `--sidebar-background`, `--sidebar-ring` | Scoped tokens for sub-systems |
| `--chart-{N}` | `--chart-1`, `--chart-2` | Indexed series for data visualization |

**Key rules:**
1. Every `--{color}` token has a matching `--{color}-foreground` for text-on-that-color
2. Sidebar tokens are prefixed `--sidebar-*` (separate scope)
3. Chart tokens are indexed `--chart-1` through `--chart-5`
4. `--radius` is the base; derived radii use `calc(var(--radius) - Npx)`
5. Token names describe PURPOSE not APPEARANCE

---

## Naming Rules for Extraction Output

When documenting tokens from any codebase, follow these rules:

### 1. Preserve Original Names

Always document tokens with their ORIGINAL names from the codebase. Don't rename.

```
GOOD: --primary: oklch(0.205 0.006 285.885)   ← actual name
BAD:  --brand-blue: oklch(0.205 0.006 285.885)  ← renamed by you
```

### 2. Add Semantic Context

After the original name, explain what it's FOR:

| Token | Value (Light) | Value (Dark) | Purpose |
|-------|---------------|--------------|---------|
| --primary | oklch(0.21 ...) | oklch(0.92 ...) | Primary buttons, active nav items, accent links |
| --muted-foreground | oklch(0.56 ...) | oklch(0.71 ...) | Descriptions, timestamps, placeholder text |

### 3. Group by Function

Organize into these groups (in this order):

1. **Surface tokens** — backgrounds for pages, cards, popovers
2. **Text tokens** — foreground colors for text
3. **Interactive tokens** — primary, secondary, accent, destructive
4. **Border & control tokens** — borders, input borders, focus rings
5. **Status tokens** — success, warning, error, info
6. **Chart tokens** — data visualization palette
7. **Sidebar tokens** — sidebar-specific overrides (if any)

### 4. Document Opacity Modifiers Separately

```
Token opacity modifiers:
/5   = 5%  opacity → ghost button hover
/10  = 10% opacity → dark mode subtle borders
/30  = 30% opacity → dark mode input backgrounds
/50  = 50% opacity → focus rings, disabled overlays
```

---

## Token Hierarchy Documentation

### How to Determine the Hierarchy

1. **Read CSS variable definitions** — find `var()` references
2. **Trace the chain** — which variables reference other variables
3. **Identify tiers**:
   - Variables with literal values = **primitives**
   - Variables referencing primitives = **semantic**
   - Variables scoped to components = **component-level**

### Example Resolution Chain

```css
/* Primitive tier */
--gray-100: oklch(0.965 0.001 286.375);

/* Semantic tier */
--muted: var(--gray-100);            /* references primitive */
--secondary: var(--gray-100);         /* same primitive, different purpose */

/* Component tier (if present) */
--sidebar-background: var(--muted);   /* references semantic */
```

Document this as:

```
--gray-100 (primitive)
  └── --muted (semantic: muted backgrounds)
  │     └── --sidebar-background (component: sidebar canvas)
  └── --secondary (semantic: secondary button background)
```

---

## Dark Mode Naming

Dark mode tokens use the SAME names but different values. Document them side by side:

```css
:root {
  --background: oklch(1 0 0);         /* white */
  --foreground: oklch(0.145 0 0);     /* near-black */
}

.dark {
  --background: oklch(0.145 0 0);     /* near-black */
  --foreground: oklch(0.985 0 0);     /* near-white */
}
```

The naming DOESN'T change. The VALUES flip. This is why semantic naming matters — `--background` is always "the page background" regardless of mode.

---

## Handling Inconsistencies

When extracting tokens from real codebases, you'll find inconsistencies. Document them:

### Hardcoded Values

```tsx
// INCONSISTENCY: hardcoded color bypassing token system
<div className="bg-[#f0f0f0]">  {/* should be bg-muted */}
```

Flag these:
```
⚠️ Hardcoded colors found:
  src/components/legacy-card.tsx:42  →  #f0f0f0 (should be --muted)
  src/pages/settings.tsx:18          →  rgb(0,0,0,0.5) (should be --foreground/50)
```

### Near-Duplicates

```
⚠️ Near-duplicate tokens:
  --gray-200: oklch(0.922 ...) and --border: oklch(0.922 ...)
  → These resolve to the same value. --border is the semantic alias.
```

---

## Output Checklist

- [ ] Original token names preserved (not renamed)
- [ ] Every token has a purpose/usage description
- [ ] Tokens grouped by function (surface, text, interactive, border, status, chart)
- [ ] Token hierarchy documented (primitive → semantic → component)
- [ ] Dark mode values shown alongside light values
- [ ] Opacity modifiers cataloged with semantic meaning
- [ ] Inconsistencies flagged (hardcoded values, near-duplicates)

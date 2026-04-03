# Typography Extraction Methodology

Extract font families, size scales, weight scales, line heights, letter spacing, and special typographic patterns from a codebase.

---

## Step 1: Font Families

### Locate Font Declarations

```bash
# CSS @font-face and font-family declarations
grep -rn '@font-face\|font-family' --include="*.css" --include="*.scss" src/

# Tailwind font config
grep -A 10 'fontFamily' tailwind.config.*

# Google Fonts / CDN imports
grep -rn 'fonts.googleapis\|fonts.gstatic\|font.*cdn' --include="*.html" --include="*.css" src/

# Next.js font imports
grep -rn 'next/font\|@next/font' --include="*.ts" --include="*.tsx" src/
```

### Document Each Family

| Role | Family | Source | Fallback Stack | Usage |
|------|--------|--------|----------------|-------|
| Sans | Inter | next/font/google | system-ui, -apple-system, sans-serif | App body text |
| Mono | JetBrains Mono | next/font/google | ui-monospace, monospace | Code blocks, data IDs |
| Serif | (none) | — | — | N/A for this app |

---


### Tailwind v4 Font Configuration

In Tailwind v4, fonts are configured in `@theme` blocks, not `tailwind.config.js`:

```bash
grep -A 10 '@theme' --include="*.css" src/ . | grep -i 'font'
```

### Next.js Font Optimization

Next.js projects use `next/font` for optimized font loading:

```bash
grep -rn 'from.*next/font' --include="*.ts" --include="*.tsx" src/ app/
```

Document: font name, CSS variable name (`--font-sans`), subsets loaded, where the variable is applied.

### Font Smoothing

Check for antialiased rendering (common in dashboards):

```bash
grep -rn 'antialiased' --include="*.css" --include="*.tsx" src/ app/
```

---

## Step 2: Size Scale

### Extract All Font Sizes

```bash
# Tailwind text-* classes with frequency
grep -roh 'text-\(xs\|sm\|base\|lg\|xl\|2xl\|3xl\|4xl\|5xl\)' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn

# Custom text sizes
grep -roh 'text-\[[0-9]*px\]' --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn

# CSS font-size declarations
grep -rn 'font-size:' --include="*.css" --include="*.scss" src/
```

### Size-to-CSS Conversion Table

| Tailwind | CSS | Line Height | Frequency | Context |
|----------|-----|-------------|-----------|---------|
| text-[10px] | 10px | 14px | Nx | Micro badges, annotations |
| text-xs | 12px / 0.75rem | 16px / 1rem | Nx | Labels, captions, meta |
| text-sm | 14px / 0.875rem | 20px / 1.25rem | Nx | Body text, table cells, descriptions |
| text-base | 16px / 1rem | 24px / 1.5rem | Nx | Input text, comfortable body |
| text-lg | 18px / 1.125rem | 28px / 1.75rem | Nx | Card/dialog titles |
| text-xl | 20px / 1.25rem | 28px / 1.75rem | Nx | Section headers |
| text-2xl | 24px / 1.5rem | 32px / 2rem | Nx | Page headings |
| text-3xl | 30px / 1.875rem | 36px / 2.25rem | Nx | Hero metrics, dashboard numbers |
| text-4xl | 36px / 2.25rem | 40px / 2.5rem | Nx | Large display numbers |

---

## Step 3: Weight Scale

```bash
# Tailwind font-weight classes
grep -roh 'font-\(thin\|extralight\|light\|normal\|medium\|semibold\|bold\|extrabold\|black\)' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn

# CSS font-weight declarations
grep -rn 'font-weight:' --include="*.css" --include="*.scss" src/
```

### Weight-to-CSS Mapping

| Tailwind | CSS | Frequency | Context |
|----------|-----|-----------|---------|
| font-normal | 400 | Nx | Body text, descriptions |
| font-medium | 500 | Nx | Buttons, labels, badges, nav items |
| font-semibold | 600 | Nx | Card titles, headings, active items |
| font-bold | 700 | Nx | Page titles, emphasis, hero numbers |

---

## Step 4: Line Height & Letter Spacing

### Line Heights

```bash
grep -roh 'leading-\(none\|tight\|snug\|normal\|relaxed\|loose\|[0-9]\+\)' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

| Tailwind | CSS | Frequency | Context |
|----------|-----|-----------|---------|
| leading-none | 1 | Nx | Metric numbers, button text |
| leading-tight | 1.25 | Nx | Card titles, compact headings |
| leading-snug | 1.375 | Nx | Form labels |
| leading-normal | 1.5 | Nx | Body text (default) |
| leading-relaxed | 1.625 | Nx | Long-form content |

### Letter Spacing

```bash
grep -roh 'tracking-\(tighter\|tight\|normal\|wide\|wider\|widest\)' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

| Tailwind | CSS | Frequency | Context |
|----------|-----|-----------|---------|
| tracking-tight | -0.025em | Nx | Headings, hero numbers |
| tracking-normal | 0 | Nx | Body text (default) |
| tracking-wide | 0.025em | Nx | — |
| tracking-wider | 0.05em | Nx | Uppercase labels, badge text |
| tracking-widest | 0.1em | Nx | — |

---

## Step 5: Special Typography Patterns

### Tabular Numbers

```bash
grep -rn 'tabular-nums\|font-variant-numeric' --include="*.tsx" --include="*.jsx" --include="*.css" src/
```

Used for: data tables (numbers align vertically), timestamps, metric cards, pricing.

### Truncation Strategies

```bash
grep -roh 'truncate\|line-clamp-[0-9]\+\|text-ellipsis\|overflow-hidden' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

| Pattern | CSS | Context |
|---------|-----|---------|
| `truncate` | `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` | Sidebar labels, table cells, breadcrumbs |
| `line-clamp-1` | `-webkit-line-clamp: 1` | Card titles |
| `line-clamp-2` | `-webkit-line-clamp: 2` | Card descriptions |
| `line-clamp-3` | `-webkit-line-clamp: 3` | Long descriptions |

### Uppercase + Tracking

```bash
grep -rn 'uppercase.*tracking\|tracking.*uppercase' --include="*.tsx" --include="*.jsx" src/
```

Combined pattern: `uppercase tracking-wider text-xs font-medium` — used for section labels, badge text, table headers in some designs.

### Monospace for Data

```bash
grep -rn 'font-mono\|font-family.*mono' --include="*.tsx" --include="*.jsx" --include="*.css" src/
```

Used for: code snippets, commit SHAs, API keys, terminal output, timestamps in some apps.

---

## Step 6: Heading Hierarchy

Map actual heading usage to establish the typographic hierarchy:

```bash
# Find heading elements and their classes
grep -rn '<h[1-6]\|<Heading' --include="*.tsx" --include="*.jsx" src/ | head -30
```

### Expected Hierarchy

| Level | Element | Size | Weight | Tracking | Context |
|-------|---------|------|--------|----------|---------|
| h1 | `<h1>` | text-2xl (24px) | font-bold (700) | tracking-tight | Page title |
| h2 | `<h2>` | text-xl (20px) | font-semibold (600) | normal | Section header |
| h3 | `<h3>` | text-lg (18px) | font-semibold (600) | normal | Card/dialog title |
| h4 | `<h4>` | text-base (16px) | font-medium (500) | normal | Subsection |
| Label | `<label>` | text-sm (14px) | font-medium (500) | normal | Form labels |
| Body | `<p>` | text-sm (14px) | font-normal (400) | normal | Body text |
| Caption | `<span>` | text-xs (12px) | font-normal (400) | normal | Meta, timestamps |

---

## Output Checklist

- [ ] All font families documented with source and fallback stack
- [ ] Complete size scale with frequency counts and contexts
- [ ] Complete weight scale with frequency counts and contexts
- [ ] Line height values documented
- [ ] Letter spacing values documented
- [ ] Tabular-nums usage identified and documented
- [ ] Truncation strategies cataloged
- [ ] Uppercase+tracking patterns documented
- [ ] Monospace usage contexts listed
- [ ] Heading hierarchy mapped with actual usage

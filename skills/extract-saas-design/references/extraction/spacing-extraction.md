# Spacing Extraction Methodology

Extract every spacing value (padding, margin, gap) from the codebase, count frequency, and build a spacing scale with semantic context.

---

## Step 1: Extract All Spacing Values

### Padding

```bash
# Tailwind padding classes
grep -roh 'p-[0-9.]*\|px-[0-9.]*\|py-[0-9.]*\|pt-[0-9.]*\|pb-[0-9.]*\|pl-[0-9.]*\|pr-[0-9.]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn

# Custom padding values
grep -roh 'p-\[[0-9]*px\]\|px-\[[0-9]*px\]\|py-\[[0-9]*px\]' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

### Margin

```bash
grep -roh 'm-[0-9.]*\|mx-[0-9.]*\|my-[0-9.]*\|mt-[0-9.]*\|mb-[0-9.]*\|ml-[0-9.]*\|mr-[0-9.]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

### Gap

```bash
grep -roh 'gap-[0-9.]*\|gap-x-[0-9.]*\|gap-y-[0-9.]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

### Space-between

```bash
grep -roh 'space-x-[0-9.]*\|space-y-[0-9.]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

---

## Step 2: Build Frequency Table

Combine all results into a unified frequency table. Convert Tailwind units to pixels (1 unit = 4px).

### Tailwind-to-Pixel Conversion

| Tailwind | Pixels | Rem |
|----------|--------|-----|
| 0 | 0px | 0 |
| px | 1px | 0.0625rem |
| 0.5 | 2px | 0.125rem |
| 1 | 4px | 0.25rem |
| 1.5 | 6px | 0.375rem |
| 2 | 8px | 0.5rem |
| 2.5 | 10px | 0.625rem |
| 3 | 12px | 0.75rem |
| 3.5 | 14px | 0.875rem |
| 4 | 16px | 1rem |
| 5 | 20px | 1.25rem |
| 6 | 24px | 1.5rem |
| 7 | 28px | 1.75rem |
| 8 | 32px | 2rem |
| 10 | 40px | 2.5rem |
| 12 | 48px | 3rem |
| 16 | 64px | 4rem |
| 20 | 80px | 5rem |

### Example Frequency Output

```
Spacing scale (combined padding + margin + gap):
  2px  (0.5):   42 occurrences  — micro: badge padding, indicator gaps
  4px  (1):     57 occurrences  — tight: icon gaps, inline elements
  6px  (1.5):   67 occurrences  — compact: small button padding
  8px  (2):    193 occurrences  — PRIMARY: content gaps, card internal
  12px (3):     60 occurrences  — standard: input horizontal padding
  16px (4):     48 occurrences  — generous: card padding, dialog padding
  24px (6):     26 occurrences  — spacious: section padding
  32px (8):     13 occurrences  — major: section separation
  40px (10):     5 occurrences  — page-level spacing
```

---

## Step 3: Identify the Base Unit

The base unit is the GCD (greatest common divisor) of the most-used values. For most design systems: **4px**.

**Verification:** Check if all common values are multiples of the base:
- 2px = 0.5 × base ✓
- 4px = 1 × base ✓
- 6px = 1.5 × base ✓
- 8px = 2 × base ✓
- 12px = 3 × base ✓
- 16px = 4 × base ✓

If values like 10px, 14px, or 5px appear frequently, the system may use a non-standard base or be inconsistent.

---

## Step 4: Map Spacing to Components

Document WHERE each spacing value is used. This is the semantic layer.

### Density Zones

Dashboards have varying density. Document the zones:

| Zone | Spacing Values Used | Where |
|------|---------------------|-------|
| Data-dense | 2px, 4px, 6px, 8px | Table cells, sidebar items, metric cards, data grids |
| Standard | 8px, 12px, 16px | Forms, settings pages, content areas |
| Spacious | 16px, 24px, 32px | Empty states, onboarding, hero sections |

### Common Spacing Combos

Look for recurring padding patterns:

```bash
# Find common padding combos
grep -roh 'px-[0-9.]* py-[0-9.]*\|px-[0-9.]*\s*py-[0-9.]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

| Combo | CSS | Component Pattern |
|-------|-----|-------------------|
| `px-3 py-1` | 12px 4px | Badge, small tag |
| `px-3 py-1.5` | 12px 6px | Compact button, menu item |
| `px-4 py-2` | 16px 8px | Standard button, input |
| `px-4 py-3` | 16px 12px | Large input, select trigger |
| `px-6 py-4` | 24px 16px | Card padding, dialog padding |
| `p-4` | 16px all | Card content area |
| `p-6` | 24px all | Dialog content, generous card |

---

## Step 5: Layout Strategy

### Flexbox vs Grid

```bash
# Count layout approaches
grep -c 'flex\|inline-flex' --include="*.tsx" --include="*.jsx" -r src/
grep -c 'grid\|grid-cols' --include="*.tsx" --include="*.jsx" -r src/
```

### Gap-based vs Margin-based

```bash
# Gap usage (modern)
grep -c 'gap-' --include="*.tsx" --include="*.jsx" -r src/

# Margin-based spacing (legacy)
grep -c 'space-x-\|space-y-' --include="*.tsx" --include="*.jsx" -r src/

# Direct margin
grep -c ' m[trblxy]-' --include="*.tsx" --include="*.jsx" -r src/
```

**Gap-dominant** = modern system (flex + gap)
**Margin-dominant** = older system or framework constraints

---

## Step 6: Component Spacing Map

Build a reference of spacing per component type:

| Component | Outer Spacing | Inner Padding | Child Gap | Example |
|-----------|---------------|---------------|-----------|---------|
| Button (sm) | — | 6px 12px | 6px | `py-1.5 px-3 gap-1.5` |
| Button (md) | — | 8px 16px | 8px | `py-2 px-4 gap-2` |
| Input | — | 8px 12px | — | `py-2 px-3` |
| Card | 0 | 24px | — | `p-6` |
| Card content | — | 24px (h) 0 | 8px | `px-6 gap-2` |
| Table cell | — | 8px 16px | — | `py-2 px-4` |
| Sidebar item | — | 8px 12px | 8px | `py-2 px-3 gap-2` |
| Dialog | — | 24px | 16px | `p-6 gap-4` |
| Badge | — | 4px 10px | — | `py-1 px-2.5` |

---

## Output Checklist

- [ ] Complete spacing scale documented with pixel values
- [ ] Frequency count for every spacing value
- [ ] Base unit identified and verified
- [ ] Each scale step mapped to component usage (semantic meaning)
- [ ] Density zones identified and documented
- [ ] Common spacing combos documented (e.g., px-3 py-1.5)
- [ ] Layout strategy identified (gap-based vs margin-based)
- [ ] Component spacing map created
- [ ] Padding symmetry patterns noted (symmetric vs asymmetric)

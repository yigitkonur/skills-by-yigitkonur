# Icons & Assets Extraction Methodology

Extract icon libraries, sizing conventions, asset patterns, and visual decoration systems.

---

## Step 1: Identify the Icon Library

```bash
# Check package.json for icon packages
grep -i 'lucide\|heroicons\|phosphor\|feather\|tabler\|radix.*icons\|@iconify\|react-icons' package.json

# Find icon imports in components
grep -rn 'from.*lucide\|from.*heroicons\|from.*phosphor\|from.*@radix-ui/react-icons' \
  --include="*.tsx" --include="*.jsx" src/ | head -20

# Find custom SVG icons
find src -name "*.svg" -type f | head -20
```

### Common Icon Libraries

| Library | Package | Style | Stroke Width |
|---------|---------|-------|-------------|
| Lucide | lucide-react | Outline (stroke-based) | 2px default |
| Heroicons | @heroicons/react | Outline + Solid variants | 1.5px default |
| Phosphor | @phosphor-icons/react | 6 weights (thin→bold) | Variable |
| Radix Icons | @radix-ui/react-icons | 15px fixed, 1.5px stroke | Fixed |
| Tabler | @tabler/icons-react | Outline | 2px default |

---

## Step 2: Icon Sizing Convention

```bash
# Find icon size patterns
grep -roh 'size-[0-9]*\|w-[0-9]* h-[0-9]*\|className=".*size-\|size={[0-9]*}' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn

# Find size prop patterns
grep -roh 'size=["{][0-9]*["}]' --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

### Standard Icon Sizes

| Context | Tailwind | Pixels | When Used |
|---------|----------|--------|-----------|
| Inline micro | size-3 | 12px | Badge icons, status indicators |
| Inline small | size-3.5 | 14px | Menu item icons, breadcrumb separators |
| Standard | size-4 | 16px | Button icons, input icons, nav items |
| Medium | size-5 | 20px | Card header icons, alert icons |
| Large | size-6 | 24px | Empty state icons, feature icons |
| Hero | size-8 | 32px | Page header icons, onboarding |
| Display | size-10+ | 40px+ | Splash screens, illustrations |

### Button Icon Sizing Rule

Buttons typically auto-size icons with a nested rule:

```tsx
// Common pattern in shadcn/ui
<Button>
  <Icon className="size-4" />  {/* 16px for default buttons */}
  Label
</Button>

// Icon-only button (square)
<Button variant="ghost" size="icon">
  <Icon className="size-4" />
</Button>
```

Document the size-per-button-size mapping:

| Button Size | Icon Size | Total Button Height |
|-------------|-----------|-------------------|
| sm | size-3.5 (14px) | 32px |
| default | size-4 (16px) | 36px |
| lg | size-5 (20px) | 40px |
| icon | size-4 (16px) | 36px × 36px square |

---

## Step 3: SVG Styling Patterns

```bash
# How SVGs are styled
grep -rn 'stroke-current\|fill-current\|stroke="\|fill="' \
  --include="*.tsx" --include="*.jsx" --include="*.svg" src/ | head -20

# Stroke width overrides
grep -rn 'strokeWidth\|stroke-width' --include="*.tsx" --include="*.jsx" src/ | head -10
```

### Common SVG Patterns

| Pattern | CSS/Tailwind | Meaning |
|---------|-------------|---------|
| `stroke="currentColor"` | Inherits text color | Standard for outline icons |
| `fill="currentColor"` | Inherits text color | Filled/solid icons |
| `fill="none"` | No fill | Outline-only icons |
| `strokeWidth={1.5}` | Custom stroke | Thinner than library default |
| `className="shrink-0"` | flex-shrink: 0 | Prevents icon from shrinking in flex |
| `aria-hidden="true"` | Hidden from SR | Decorative icons |

---

## Step 4: Image & Illustration Patterns

```bash
# Find image patterns
grep -rn '<img\|<Image\|<Avatar\|backgroundImage' \
  --include="*.tsx" --include="*.jsx" src/ | head -20

# Find placeholder/fallback patterns
grep -rn 'fallback\|placeholder\|onError' \
  --include="*.tsx" --include="*.jsx" src/ | head -10
```

### Avatar System

| Size | Dimensions | Radius | Fallback | Context |
|------|-----------|--------|----------|---------|
| xs | 24px | full | Initials | Inline mentions |
| sm | 32px | full | Initials | Comment threads, lists |
| md | 40px | full | Initials | User menu, profiles |
| lg | 64px | full | Initials | Profile pages |
| xl | 96px | full | Initials | Settings page |

### Avatar Group

```
[avatar][avatar][avatar][+3]
     ←overlap→
```

- Overlap: typically -8px to -12px margin-left
- Border: 2px solid background color (creates separation)
- Counter badge: "+N" with muted background

---

## Step 5: Logo & Brand Assets

```bash
# Find logo files
find src public -name "*logo*" -o -name "*brand*" | head -10

# Find logo usage
grep -rn 'logo\|Logo\|brand\|Brand' --include="*.tsx" --include="*.jsx" src/ | head -10
```

Document:
- Logo variants: full, icon-only, monochrome
- Logo placement: sidebar header, login page, favicon
- Logo dimensions at each placement

---

## Output Checklist

- [ ] Icon library identified with package name
- [ ] Icon sizing scale documented with contexts
- [ ] Button-to-icon size mapping documented
- [ ] SVG styling patterns (stroke vs fill, currentColor)
- [ ] Stroke width convention documented
- [ ] `shrink-0` and `aria-hidden` patterns noted
- [ ] Avatar system documented (sizes, fallback, groups)
- [ ] Image/illustration patterns documented
- [ ] Logo variants and placements documented

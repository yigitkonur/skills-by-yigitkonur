# UI Consistency Audit Checklist

Systematic checklist for auditing a SaaS dashboard's visual consistency. Run this after extraction to identify inconsistencies, missing patterns, and accessibility gaps.

---

## Phase 1: Token Consistency

### Color Audit

- [ ] **No hardcoded colors** — every color in components uses a CSS variable or Tailwind token
- [ ] **No near-duplicates** — no two tokens resolve to visually identical values
- [ ] **Semantic naming** — tokens describe purpose, not appearance (--primary, not --blue)
- [ ] **Dark mode coverage** — every token has both light and dark values
- [ ] **Chart palette separate** — data visualization colors are distinct from UI colors
- [ ] **Opacity consistent** — same opacity modifier means the same thing everywhere

```bash
# Find hardcoded colors in components
grep -rn '#[0-9a-fA-F]\{3,8\}' --include="*.tsx" --include="*.jsx" src/components/
grep -rn 'rgb(\|rgba(\|hsl(' --include="*.tsx" --include="*.jsx" src/components/

# Find color inconsistencies
grep -roh 'bg-\[#[0-9a-f]*\]\|text-\[#[0-9a-f]*\]' --include="*.tsx" src/ | sort | uniq -c
```

### Spacing Audit

- [ ] **Consistent base unit** — all spacing values are multiples of the base (usually 4px)
- [ ] **No magic numbers** — no spacing values that don't fit the scale (e.g., 10px, 14px, 22px)
- [ ] **Same component, same spacing** — all Buttons use the same padding, all Cards the same internal spacing
- [ ] **Density zones consistent** — data-dense areas use tight spacing uniformly

```bash
# Find non-standard spacing values
grep -roh 'p-\[[0-9]*px\]\|m-\[[0-9]*px\]\|gap-\[[0-9]*px\]' \
  --include="*.tsx" src/ | sort | uniq -c | sort -rn

# Verify buttons use consistent padding
grep -A 2 'btn\|Button' --include="*.tsx" src/components/ui/button.tsx | grep 'p-\|px-\|py-'
```

### Typography Audit

- [ ] **Size scale respected** — only sizes from the defined scale appear in components
- [ ] **Weight scale respected** — only weights from the defined scale
- [ ] **No inline font-size** — components use tokens/classes, not inline styles
- [ ] **Heading hierarchy** — h1 > h2 > h3 in visual size (not just semantic)
- [ ] **Monospace for data** — numbers in tables use tabular-nums or font-mono

### Border Radius Audit

- [ ] **Consistent scale** — all radii come from the defined scale (sm, md, lg, full)
- [ ] **Same category, same radius** — all buttons share a radius, all cards share a radius
- [ ] **No arbitrary values** — no `rounded-[7px]` or `rounded-[3px]` that bypass the scale

### Shadow Audit

- [ ] **Consistent depth** — shadows correspond to elevation levels
- [ ] **Dark mode shadows** — shadows may need adjustment in dark mode (opacity changes)
- [ ] **No shadow soup** — no mixed shadow strategies (border-based + heavy shadows)

---

## Phase 2: Component Consistency

### Interactive States

For EVERY interactive component, verify:

- [ ] **Hover state exists** — visible change on mouse hover
- [ ] **Focus-visible state** — keyboard focus indicator (ring, outline, or border change)
- [ ] **Active/pressed state** — visual feedback on click/press
- [ ] **Disabled state** — reduced opacity + pointer-events: none + cursor changes
- [ ] **Loading state** — spinner or skeleton (or explicitly "not implemented")
- [ ] **Error state** — for form inputs: red border/ring + error message
- [ ] **Selected state** — for toggleable components (tabs, checkboxes, radio)

### State Consistency Across Components

| State | Button | Input | Select | Checkbox | Toggle | Sidebar Item |
|-------|--------|-------|--------|----------|--------|-------------|
| Hover | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Focus-visible | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Disabled | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Loading | ✓/✗ | N/A | N/A | N/A | N/A | N/A |
| Error | N/A | ✓/✗ | ✓/✗ | ✓/✗ | N/A | N/A |

### Transition Timing

- [ ] **Consistent hover timing** — all hover transitions use the same duration (typically 150ms)
- [ ] **Consistent focus timing** — focus rings appear instantly or with consistent timing
- [ ] **Exit faster than enter** — floating elements dismiss faster than they appear
- [ ] **No `transition: all`** — use explicit properties to avoid transitioning layout changes

```bash
# Find transition values
grep -roh 'transition-\[.*\]\|transition-all\|duration-[0-9]*' \
  --include="*.tsx" --include="*.jsx" src/ | sort | uniq -c | sort -rn
```

---

## Phase 3: Layout Consistency

### Sidebar

- [ ] **Width matches spec** — expanded and collapsed widths are correct
- [ ] **Active indicator** — currently active nav item has a visible indicator
- [ ] **Collapse transition** — smooth transition, content shifts correctly
- [ ] **Mobile behavior** — sidebar converts to sheet/drawer on small screens
- [ ] **Scroll behavior** — sidebar scrolls independently of main content

### Content Area

- [ ] **Consistent padding** — all pages use the same content area padding
- [ ] **Max-width applied** — content doesn't stretch infinitely on wide screens
- [ ] **Grid consistency** — metric cards, chart grids use the same column patterns

### Responsive

- [ ] **No content overflow** — no horizontal scrollbars on any viewport size
- [ ] **Breakpoints match** — Tailwind breakpoints used consistently
- [ ] **Mobile navigation** — clear navigation pattern for small screens
- [ ] **Touch targets** — interactive elements are at least 44×44px on mobile

---

## Phase 4: Accessibility Audit

### Keyboard Navigation

- [ ] **Tab order logical** — focus moves through the page in reading order
- [ ] **Skip navigation** — "Skip to content" link available
- [ ] **Escape closes overlays** — modals, popovers, dropdowns close on Escape
- [ ] **Arrow keys in lists** — menu items, radio groups navigable with arrows
- [ ] **Enter/Space activates** — buttons, links, toggles respond to keyboard

### Screen Reader

- [ ] **All images have alt text** — or `aria-hidden="true"` for decorative icons
- [ ] **ARIA labels on icon buttons** — buttons with only icons need `aria-label`
- [ ] **Form inputs have labels** — every input associated with a `<label>` or `aria-label`
- [ ] **Live regions for toast** — toast notifications use `aria-live` or `role="alert"`
- [ ] **Modal focus trap** — focus stays within open modals

### Color Contrast

- [ ] **Text contrast** — body text meets WCAG AA (4.5:1 ratio)
- [ ] **Interactive contrast** — buttons, links meet AA (3:1 for large text)
- [ ] **Focus indicator contrast** — focus ring visible against all backgrounds
- [ ] **Disabled state** — disabled elements still readable (just dimmed, not invisible)

```bash
# Find potential contrast issues
grep -rn 'text-muted\|opacity-50\|opacity-30' \
  --include="*.tsx" --include="*.jsx" src/ | head -20
```

### Motion & Animation

- [ ] **Respects prefers-reduced-motion** — animations disabled when user preference set
- [ ] **No essential motion** — no information conveyed only through animation
- [ ] **Duration reasonable** — no animations longer than 500ms for UI transitions

```bash
# Check for prefers-reduced-motion
grep -rn 'prefers-reduced-motion\|motion-reduce' \
  --include="*.css" --include="*.tsx" src/
```

---

## Phase 5: Cross-Reference Verification

### Token Usage

- [ ] Every color token referenced in component docs exists in color-tokens.md
- [ ] Every spacing value in component docs exists in spacing-scale.md
- [ ] Every shadow value in component docs matches shadow-depth.md
- [ ] Every animation in component docs matches animation-system.md
- [ ] Every radius in component docs matches radius-scale.md

### Component Coverage

- [ ] Every component in the codebase has a documentation file
- [ ] Every component doc has a CSS recreation block
- [ ] Every component doc has an ASCII anatomy diagram
- [ ] Every interactive component doc has state transition documentation
- [ ] Every component doc has dark mode differences section

---

## Severity Classification

| Severity | Description | Action |
|----------|-------------|--------|
| 🔴 Critical | Blocks recreation — missing token, missing component | Document immediately |
| 🟡 Warning | Inconsistency — hardcoded value, missing state | Flag in docs |
| 🟢 Note | Minor — near-duplicate token, edge case | Note in docs |

### Example Audit Findings

```markdown
## Audit Findings

### 🔴 Critical
- Missing: No loading state for any button variant
- Missing: No error state for Select component

### 🟡 Warning
- Inconsistency: 3 hardcoded #f0f0f0 values (should use --muted)
- Inconsistency: Button uses rounded-md but Card uses rounded-lg (expected: both use --radius)
- Missing: No focus-visible ring on sidebar menu items

### 🟢 Note
- Near-duplicate: --gray-200 and --border resolve to same value
- Edge case: Custom scrollbar styles only apply in WebKit browsers
```

---

## The Ultimate Test

> Could a developer who has NEVER seen the original codebase
> recreate a pixel-perfect version using ONLY these documents?

If yes → audit passes.
If "mostly, but they'd need to guess at X" → document X.

---

## Output Checklist

- [ ] Token consistency verified (colors, spacing, typography, radius, shadows)
- [ ] Component state consistency matrix completed
- [ ] Layout consistency verified (sidebar, content, responsive)
- [ ] Accessibility audit completed (keyboard, screen reader, contrast, motion)
- [ ] Cross-reference verification done (tokens ↔ components)
- [ ] Findings classified by severity
- [ ] All critical gaps documented or flagged

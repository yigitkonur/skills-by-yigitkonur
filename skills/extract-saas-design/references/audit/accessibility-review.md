# Accessibility Review for Design Extraction

How to audit and document accessibility patterns when extracting a SaaS dashboard's design system.

---

## WCAG Compliance Levels

| Level | Requirements | Target for Most SaaS |
|-------|-------------|---------------------|
| A | Minimum — keyboard access, alt text, no seizure triggers | Baseline |
| AA | Standard — color contrast 4.5:1, resize to 200%, error identification | **Target** |
| AAA | Enhanced — contrast 7:1, sign language, simple language | Aspirational |

---

## Color Contrast Verification

### Text Contrast Requirements

| Element Type | Minimum Ratio | WCAG Level | How to Check |
|-------------|--------------|------------|-------------|
| Normal text (< 18px / < 14px bold) | 4.5:1 | AA | Foreground vs background |
| Large text (≥ 18px / ≥ 14px bold) | 3:1 | AA | Heading/title vs background |
| Non-text UI (borders, icons) | 3:1 | AA | Icon color vs background |
| Disabled elements | No requirement | — | May have lower contrast |

### Common Contrast Issues in Dashboards

| Issue | Where Found | Fix |
|-------|------------|-----|
| Muted text too light | `--muted-foreground` on `--background` | Ensure 4.5:1 ratio |
| Placeholder text | Input placeholder on white/dark bg | Often fails — check specifically |
| Disabled buttons | 0.5 opacity reduces contrast below 3:1 | Acceptable per WCAG |
| Badge text | Small colored badge on card | Verify each badge variant |
| Chart labels | Axis labels on chart background | Often low contrast |
| Sidebar items | Inactive item on sidebar background | Verify in both modes |

### Verification Process

```bash
# Extract foreground/background pairs to check
# 1. Read --background and --foreground values from CSS
# 2. Calculate contrast ratio: (L1 + 0.05) / (L2 + 0.05) where L = relative luminance
# 3. Document each pair with pass/fail

# Common tools: WebAIM contrast checker, axe DevTools, Lighthouse
```

### Contrast Documentation Template

| Pair | Foreground | Background | Ratio | Pass (AA) |
|------|-----------|------------|-------|-----------|
| Body text | --foreground | --background | [N]:1 | ✓/✗ |
| Muted text | --muted-foreground | --background | [N]:1 | ✓/✗ |
| Card text | --card-foreground | --card | [N]:1 | ✓/✗ |
| Primary button text | --primary-foreground | --primary | [N]:1 | ✓/✗ |
| Destructive button | --destructive-foreground | --destructive | [N]:1 | ✓/✗ |
| Sidebar text | --sidebar-foreground | --sidebar-background | [N]:1 | ✓/✗ |

---

## Keyboard Navigation Patterns

### Focus Management

```bash
# Find focus management patterns
grep -rn 'focus\|tabIndex\|tab-index\|autoFocus\|FocusTrap\|FocusScope' \
  --include="*.tsx" --include="*.jsx" src/ | head -20

# Find focus ring styles
grep -rn 'focus-visible\|focus-within\|:focus' \
  --include="*.css" --include="*.tsx" src/ | head -20
```

### Standard Keyboard Patterns

| Component | Keys | Behavior |
|-----------|------|----------|
| Button | Enter, Space | Activate |
| Link | Enter | Navigate |
| Input | Tab | Focus |
| Checkbox | Space | Toggle |
| Radio | Arrow Up/Down | Move selection |
| Select | Arrow Up/Down, Enter | Navigate options |
| Dialog | Escape | Close |
| Tab panel | Arrow Left/Right | Switch tabs |
| Menu | Arrow Up/Down, Enter, Escape | Navigate, select, close |
| Sidebar | Cmd/Ctrl+B | Toggle collapse |
| Command palette | Cmd/Ctrl+K | Open |

### Focus Trap Documentation

Document for each overlay component:

| Overlay | Focus Trap | Initial Focus | Return Focus |
|---------|-----------|---------------|-------------|
| Dialog | Yes | First focusable or close button | Trigger element |
| Sheet | Yes | First focusable | Trigger element |
| Dropdown | Yes | First item | Trigger element |
| Popover | Optional | Content | Trigger element |
| Tooltip | No | N/A | N/A |
| Toast | No | N/A | N/A |

---

## ARIA Patterns

### Common ARIA Attributes in SaaS Components

| Component | Role | ARIA Attributes | Purpose |
|-----------|------|-----------------|---------|
| Sidebar | navigation | `aria-label="Main navigation"` | Landmark |
| Nav item | link | `aria-current="page"` (active) | Current page |
| Dialog | dialog | `aria-modal="true"`, `aria-labelledby` | Modal identification |
| Alert | alert | `aria-live="assertive"` | Announce to SR |
| Toast | status | `aria-live="polite"` | Non-urgent announce |
| Tab list | tablist | `aria-orientation` | Tab container |
| Tab | tab | `aria-selected`, `aria-controls` | Tab state |
| Tab panel | tabpanel | `aria-labelledby` | Panel for tab |
| Accordion | — | `aria-expanded` on trigger | Expand state |
| Toggle | switch | `aria-checked` | On/off state |
| Badge count | — | `aria-label="3 notifications"` | Describe count |
| Icon button | button | `aria-label="Close"` | Describe action |
| Loading | status | `aria-busy="true"` | Loading state |
| Progress | progressbar | `aria-valuenow`, `aria-valuemax` | Progress state |

### Screen Reader Text

```bash
# Find sr-only patterns
grep -rn 'sr-only\|visually-hidden\|VisuallyHidden' \
  --include="*.tsx" --include="*.jsx" src/ | head -10
```

Document hidden text that provides context to screen readers:

| Component | SR Text | Purpose |
|-----------|---------|---------|
| Search input | "Search" label | Identifies search function |
| Close button | "Close" | Describes icon-only button |
| External link | "Opens in new tab" | Warns about navigation |
| Required field | "Required" | Indicates requirement |
| Sort column | "Sort ascending" | Describes sort state |

---

## Motion & Animation Accessibility

### prefers-reduced-motion

```bash
# Check implementation
grep -rn 'prefers-reduced-motion\|motion-reduce\|motion-safe' \
  --include="*.css" --include="*.tsx" --include="*.ts" src/
```

### Documentation Template

| Animation | Default | Reduced Motion | Implementation |
|-----------|---------|---------------|----------------|
| Modal enter | fade + zoom (200ms) | Instant appear | `motion-reduce:animate-none` |
| Sidebar collapse | Width transition (300ms) | Instant | `motion-reduce:transition-none` |
| Loading spinner | Continuous rotation | Static indicator | Alternative UI |
| Skeleton shimmer | Pulse animation | Static placeholder | `motion-reduce:animate-none` |
| Toast slide-in | Slide + fade (200ms) | Instant appear | `motion-reduce:animate-none` |

---

## Form Accessibility

### Error Handling

| Pattern | Implementation | ARIA |
|---------|---------------|------|
| Inline error | Red text below input | `aria-invalid="true"` + `aria-describedby` |
| Error summary | List at top of form | Focus on first error, `role="alert"` |
| Required field | Asterisk or text | `aria-required="true"` or `required` |
| Help text | Below input | `aria-describedby` linking to help text |

### Form Association

```html
<!-- Correct: label associated with input -->
<label for="email">Email</label>
<input id="email" type="email" aria-describedby="email-help email-error" />
<span id="email-help">We'll never share your email</span>
<span id="email-error" role="alert">Invalid email format</span>
```

---

## Data Table Accessibility

| Feature | ARIA/HTML | Implementation |
|---------|----------|----------------|
| Table structure | `<table>`, `<thead>`, `<tbody>` | Semantic HTML |
| Column headers | `<th scope="col">` | Screen reader announces column |
| Row headers | `<th scope="row">` | Screen reader announces row |
| Sort indicator | `aria-sort="ascending"` | Announces sort state |
| Pagination | `nav aria-label="Pagination"` | Identifies pagination |
| Selection | `aria-selected`, checkbox label | Announces selection state |
| Empty state | `role="status"` or visible message | Announces no results |

---

## Output Checklist

- [ ] Color contrast ratios verified for all text/background pairs
- [ ] Keyboard navigation patterns documented for all interactive components
- [ ] Focus trap behavior documented for all overlays
- [ ] ARIA roles and attributes documented per component
- [ ] Screen reader text (sr-only) cataloged
- [ ] prefers-reduced-motion implementation verified
- [ ] Form error handling patterns documented
- [ ] Data table accessibility verified
- [ ] Touch target sizes verified (44×44px minimum)

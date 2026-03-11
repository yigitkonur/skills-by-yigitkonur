# Component Documentation Template

Every component document follows this structure. Skip sections that genuinely don't apply, but err on the side of including them — "Not implemented" is better than silence.

> **Every section below matters.** Skip a section only if it genuinely does not apply (e.g., "Responsive Behavior" for a component that truly doesn't change at any breakpoint). When a feature is absent, write "Not implemented" — never leave a silent gap. The person recreating this needs to know what's missing, not just what's present.

---

```markdown
# [ComponentName]

> [One sentence: what this looks like and what it's for]

Source: `[relative path to source file]`
Library: [shadcn/ui + Radix | MUI | Ant Design | custom | headless-ui | Vaul | etc.]
Depends on: [other components if composition-based]

---

## Anatomy

[ASCII diagram showing the visual structure with actual dimensions]

```
+-- [container] ----------------------------------------+
|                                                        |
|  +--[icon]--+  [primary text]      +--[action]--+    |
|  |  16x16   |   14px medium       |  chevron    |    |
|  +----------+                      +------------+    |
|               [secondary text]                        |
|                12px muted                             |
|                                                        |
+--------------------------------------------------------+
```

### Elements
- **Container**: [display, layout, overflow]

> **How to Measure**: Use the Tailwind-to-CSS tables at the bottom of this template. `p-3` = 12px, `h-9` = 36px, `gap-2` = 8px. `size-4` on an icon = 16x16px. `text-sm` = 14px/20px.
- **[Element 1]**: [what it is, optional?]
- **[Element 2]**: [what it is, optional?]

---

## Variants

### default
| Property | Value | Tailwind |
|----------|-------|----------|
| Background | [CSS var -> computed value, e.g. var(--primary) -> oklch(0.21 0.006 285.88)] | [tailwind class] |
| Text | [resolved CSS value] | [tailwind class] |
| Border | [width style color] | [tailwind class] |
| Shadow | [shadow value or "none"] | [tailwind class] |
| Radius | [px value] | [tailwind class] |

Hover: [what changes]
Active: [what changes]

### [variant-name]
| Property | Value | Tailwind |
|----------|-------|----------|
| Background | [resolved CSS value] | [tailwind class] |
| Text | [resolved CSS value] | [tailwind class] |
| Border | [width style color] | [tailwind class] |
| Shadow | [shadow value or "none"] | [tailwind class] |

Hover: [what changes]
Active: [what changes]

[...repeat for EVERY variant]

---

## Sizes

| Size | Height | Padding (h/v) | Text | Icon | Gap | Tailwind classes |
|------|--------|---------------|------|------|-----|-----------------|
| xs | [N]px | [h]px [v]px | [N]px | [N]px | [N]px | [classes] |
| sm | [N]px | [h]px [v]px | [N]px | [N]px | [N]px | [classes] |
| default | [N]px | [h]px [v]px | [N]px | [N]px | [N]px | [classes] |
| lg | [N]px | [h]px [v]px | [N]px | [N]px | [N]px | [classes] |

---

## States

### Default (resting)
- Background: [value]
- Border: [value]
- Text: [value]
- Shadow: [value]
- Cursor: [value]

### Hover
| Change | From -> To | Transition |
|--------|-----------|------------|
| [property] | [from] -> [to] | [property duration easing] |

### Focus-visible
| Change | From -> To | Transition |
|--------|-----------|------------|
| Border color | [from] -> [to] | instant |
| Ring | none -> [ring value] | instant |
| Outline | none -> [outline value] | instant |

### Active / Pressed
[Document changes or "Not implemented"]

### Disabled
| Change | Value |
|--------|-------|
| Opacity | [value] |
| Pointer events | [value] |
| Cursor | [value] |

### Loading
[Document spinner/skeleton behavior or "Not implemented"]

### Error / aria-invalid
[Document border/ring changes or "Not implemented"]

### Selected / data-[state=active]
[Document for toggleable components or "N/A for this component"]

---

## State Transitions

Document the state flow for this component. Show what CSS properties change at each transition.

### Mouse Interaction Flow
```
IDLE ──hover──▶ HOVER ──mousedown──▶ ACTIVE ──mouseup──▶ HOVER ──mouseleave──▶ IDLE
```

### Keyboard Interaction Flow
```
IDLE ──tab──▶ FOCUS-VISIBLE ──enter/space──▶ ACTIVE ──release──▶ FOCUS-VISIBLE ──tab──▶ IDLE
```

### Async Interaction Flow (if applicable)
```
IDLE ──click──▶ LOADING ──success──▶ SUCCESS ──timeout──▶ IDLE
                        ──failure──▶ ERROR ──retry──▶ LOADING
```

### Transition Properties

| From → To | Properties Changed | Duration | Easing |
|-----------|-------------------|----------|--------|
| Idle → Hover | background, color, box-shadow | 150ms | ease |
| Hover → Active | background (darken), transform (scale 0.98) | 50ms | ease |
| Idle → Focus | outline, ring, border-color | instant | — |
| Idle → Disabled | opacity (0.5), pointer-events (none) | — | — |

---

## Animations

| Trigger | Property | Duration | Easing | From | To |
|---------|----------|----------|--------|------|-----|
| [trigger] | [property] | [N]ms | [easing] | [value] | [value] |
| [trigger] | [property] | [N]ms | [easing] | [value] | [value] |

### Micro-Interaction Detail

| Trigger | Feedback Type | Timing | Visual Change | Why |
|---------|--------------|--------|---------------|-----|
| Mouse enter | Background shift | 150ms ease | bg-primary → bg-primary/90 | Instant acknowledgment of hover |
| Mouse press | Scale + darken | 50ms ease | transform: scale(0.98), bg darkens | Physical "click" feedback |
| Focus (keyboard) | Ring appear | instant | 3px ring at 50% opacity | Immediate keyboard navigation cue |
| Loading start | Spinner replace | 0ms | Icon → spinner animation | Immediate state feedback |
| Error | Ring change | 150ms ease | ring-ring → ring-destructive | Visual urgency shift |

### Opacity Scale (Document what each opacity value means)

| Opacity | Semantic Meaning | Where Used |
|---------|-----------------|------------|
| 1.0 | Full presence | Default/resting state |
| 0.9 | Hover darkening | Primary button hover |
| 0.8 | Secondary hover | Secondary button hover |
| 0.5 | Disabled / background | Disabled state, table footer, row hover |
| 0.35 | Ambient presence | Muted text, labels |
| 0 | Hidden | Collapsed, removed |

---

## Internal Spacing

[Pixel-level spacing diagram showing padding, gaps, and element positions]

```
+----------------------------------------------+
|<-16px-> [icon 16x16] <-8px-> [text] <-16px->|
|         ^ centered vertically                 |
|<-------------- 36px tall ------------------->|
+----------------------------------------------+
```

- Container padding: [top] [right] [bottom] [left]
- Icon-to-text gap: [N]px
- Text-to-action gap: [N]px or auto
- Minimum width: [value or none]

---

## Dark Mode Differences

| Property | Light | Dark |
|----------|-------|------|
| Background | [value] | [value] |
| Text | [value] | [value] |
| Border | [value] | [value] |
| Shadow | [value] | [value] |
| [other] | [value] | [value] |

---

## Responsive Behavior

| Breakpoint | Change |
|------------|--------|
| < [N]px | [description or "no responsive changes"] |
| [N]px | [description] |

---

## Accessibility

- **Role:** [ARIA role or native element role]
- **Keyboard:** [Space/Enter activates, Tab focuses, Escape closes, Arrow keys navigate]
- **Screen reader:** [aria-label patterns, sr-only text]
- **Focus visible:** [standard ring pattern or custom]
- **Contrast:** [meets WCAG AA / AAA / unknown]

---

## Composition Patterns

Show how this component is typically used WITH other components. Don't document in isolation.

### Common Pairings

| Context | Composition | Example |
|---------|------------|---------|
| Card footer | Button pair (cancel + confirm) | `<CardFooter><Button variant="outline">Cancel</Button><Button>Save</Button></CardFooter>` |
| Dialog actions | Button group with alignment | `<DialogFooter className="flex justify-end gap-2">...</DialogFooter>` |
| Table row action | Ghost icon button | `<Button variant="ghost" size="icon"><MoreHorizontal /></Button>` |
| Form field | Label + Input + Error message | `<FormField><Label /><Input /><FormMessage /></FormField>` |

### Inline Usage

[How this component appears alongside others in real usage]

```jsx
<Card>
  <CardHeader>
    <CardTitle />
    <CardDescription />
  </CardHeader>
  <CardContent>
    <Input placeholder="Search..." />
  </CardContent>
  <CardFooter>
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

### Mega-Component Decomposition (if applicable)

If this component has 5+ sub-components, document the hierarchy:

```
ComponentName
├── ComponentHeader
│   ├── ComponentTitle
│   └── ComponentDescription
├── ComponentContent
│   └── [children]
└── ComponentFooter
    └── [action buttons]
```

For each sub-component, show: its role, its CSS, and how it relates to siblings.

---

## CSS Recreation Specification

The exact CSS to recreate this component's default appearance. No JS logic — pure visual spec.

```css
/* Container */
.component {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 8px 16px;
  gap: 8px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--background);
  color: var(--foreground);
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  cursor: pointer;
  transition: all 150ms ease;
  user-select: none;
}

/* Hover */
.component:hover {
  background: var(--accent);
  color: var(--accent-foreground);
}

/* Focus */
.component:focus-visible {
  border-color: var(--ring);
  outline: 1px solid var(--ring);
  box-shadow: 0 0 0 3px rgba(var(--ring-rgb), 0.5);
}

/* Disabled */
.component:disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Variant: destructive */
.component--destructive {
  background: var(--destructive);
  color: var(--destructive-foreground);
  border-color: transparent;
}

/* Size: sm */
.component--sm {
  height: 32px;
  padding: 0 12px;
  gap: 6px;
}
```
```

---

## Anti-Patterns to Avoid

Document patterns that should NOT be used with this component, and common mistakes implementers make.

### Don't Skip These
- [ ] Disabled state with visual feedback (opacity + pointer-events)
- [ ] Focus-visible ring (not just :focus, but :focus-visible specifically)
- [ ] Loading state — even if "Not implemented", say so explicitly
- [ ] Error/invalid state — `aria-invalid`, destructive ring variant
- [ ] Selected/active state for toggleable components
- [ ] Empty/zero-data state for data components

### Common Mistakes
| Mistake | Why It's Wrong | Correct Approach |
|---------|---------------|------------------|
| Using `:focus` instead of `:focus-visible` | Shows focus ring on mouse click | Use `:focus-visible` for keyboard-only ring |
| Animating layout properties (width, height) | Causes reflow, janky on low-end devices | Use `transform: scale()` or `opacity` |
| Hardcoding colors instead of tokens | Breaks dark mode and theming | Always use `var(--color-*)` |
| Forgetting `pointer-events: none` on disabled | Disabled elements still receive clicks | Always pair opacity with pointer-events |
| Missing `white-space: nowrap` on buttons | Button text wraps at narrow widths | Add nowrap for inline controls |

---

## Reading Component Source Files

When reading a component file, look for these patterns:

### CVA (Class Variance Authority)
```tsx
const variants = cva("base-classes", {
  variants: {
    variant: { default: "...", destructive: "..." },
    size: { sm: "...", default: "...", lg: "..." }
  },
  defaultVariants: { variant: "default", size: "default" }
})
```
Extract EVERY variant, EVERY size, the base classes, and the defaults.

### Tailwind className strings
```tsx
className={cn("class1 class2 class3", className)}
```
Parse every class. Convert to CSS properties using the conversion tables below.

### Conditional classes
```tsx
data-[state=active]:bg-background
data-[state=checked]:translate-x-[calc(100%-2px)]
dark:bg-input/30
hover:bg-accent
```
Each conditional is a state change. Document the trigger and the visual change.

### Radix/Headless UI data attributes
```tsx
data-[state=open]:animate-in
data-[side=bottom]:slide-in-from-top-2
```
These drive animations. Document which animation fires on which state transition.

---


---

## Required vs Conditional Sections

**REQUIRED** (must appear in every component doc):
1. Header (name, source, library)
2. Anatomy (ASCII diagram)
3. Variants (every variant fully specified)
4. States (all states, including "Not implemented")
5. CSS Recreation (complete CSS block)

**CONDITIONAL** (include when applicable):
1. Sizes (when component has size variants)
2. State Transitions (interactive components)
3. Animations (when transitions/animations exist)
4. Internal Spacing (complex layouts)
5. Dark Mode Differences (when dark mode exists)

---

## CVA Extraction Checklist

When a component uses `cva()` (class-variance-authority), extract ALL of these:

1. **Base classes** -- the first argument to `cva()`. Apply to ALL variants.
2. **Each variant key** -- e.g., `variant`, `size`, `color`.
3. **Each variant value** -- e.g., `variant.default`, `variant.destructive`. Full class list.
4. **Default variants** -- which variant/size applies when no props are passed.
5. **Compound variants** -- overrides when two variant values combine.

---

## cn() Class Merging

shadcn components merge classes with `cn()`:

```tsx
className={cn(buttonVariants({ variant, size }), className)}
```

**Resolution order** (last wins):
1. Base classes from `cva()` first argument
2. Variant-specific classes from the matched variant
3. User-provided `className` (overrides everything above)

## Tailwind-to-CSS Conversion

### Spacing (1 unit = 4px)
| Tailwind | CSS |
|----------|-----|
| p-0 | padding: 0 |
| p-0.5 | padding: 2px |
| p-1 | padding: 4px |
| p-1.5 | padding: 6px |
| p-2 | padding: 8px |
| p-3 | padding: 12px |
| p-4 | padding: 16px |
| p-5 | padding: 20px |
| p-6 | padding: 24px |
| p-8 | padding: 32px |

### Sizing
| Tailwind | CSS |
|----------|-----|
| h-7 | height: 28px |
| h-8 | height: 32px |
| h-9 | height: 36px |
| h-10 | height: 40px |
| w-full | width: 100% |
| size-4 | width: 16px; height: 16px |

### Border Radius
| Tailwind | CSS |
|----------|-----|
| rounded-sm | border-radius: calc(var(--radius) - 4px) |
| rounded | border-radius: 4px |
| rounded-md | border-radius: calc(var(--radius) - 2px) |
| rounded-lg | border-radius: var(--radius) |
| rounded-xl | border-radius: calc(var(--radius) + 4px) |
| rounded-full | border-radius: 9999px |

### Typography
| Tailwind | CSS |
|----------|-----|
| text-xs | font-size: 12px; line-height: 16px |
| text-sm | font-size: 14px; line-height: 20px |
| text-base | font-size: 16px; line-height: 24px |
| text-lg | font-size: 18px; line-height: 28px |
| font-medium | font-weight: 500 |
| font-semibold | font-weight: 600 |
| tracking-wider | letter-spacing: 0.05em |
| leading-none | line-height: 1 |

### Common Patterns
| Tailwind | CSS |
|----------|-----|
| transition-all | transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1) |
| transition-[color,box-shadow] | transition: color 150ms, box-shadow 150ms |
| duration-200 | transition-duration: 200ms |
| shrink-0 | flex-shrink: 0 |
| whitespace-nowrap | white-space: nowrap |
| select-none | user-select: none |
| pointer-events-none | pointer-events: none |
| tabular-nums | font-variant-numeric: tabular-nums |
| truncate | overflow: hidden; text-overflow: ellipsis; white-space: nowrap |

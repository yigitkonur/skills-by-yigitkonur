# Styling Patterns

> Summarizes the styling conventions used across components and pages. Consult this when you want new UI to feel native to the rest of the codebase.

## Common patterns

- semantic Tailwind token classes (`bg-card`, `text-foreground/60`, `border-border`)
- `cn(...)` for conditional class names
- mobile-first layouts (`flex-col` before `md:flex-row`)
- rounded card surfaces and subtle borders

## Representative code

```tsx
<div className={cn("rounded-lg border p-4", active && "border-primary bg-primary/5", className)}>
  ...
</div>
```

From shared dashboard layout styling:

```tsx
<main className="py-6 bg-card px-4 md:p-8 min-h-full w-full border-t md:border-t-0 md:border-l">
```

## Practical rule

Prefer extending the existing token-driven styles over introducing one-off utility combinations that ignore the theme system.

---

**Related references:**
- `references/ui/theme-tokens.md` — Source of semantic color/radius values
- `references/conventions/component-patterns.md` — How styling appears inside component files
- `references/marketing/home-page-components.md` — Marketing-side composition examples

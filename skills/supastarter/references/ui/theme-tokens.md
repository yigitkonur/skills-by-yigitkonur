# Theme Tokens

> Documents the shared Tailwind/CSS token system defined in `tooling/tailwind/theme.css`. Consult this when changing colors, radii, or dark-mode behavior.
>
> The project maps semantic CSS variables to Tailwind tokens so components can use classes like `bg-primary` and `text-muted-foreground` without hardcoding palette values.

## Token Mapping

```css
@theme {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-secondary: var(--secondary);
  --color-success: var(--success);
  --color-destructive: var(--destructive);
  --radius-lg: var(--radius);
  --radius-md: calc(var(--radius) - 2px);
  --radius-sm: calc(var(--radius) - 4px);
}
```

## Light / Dark Palettes

`theme.css` defines values twice:

- `:root` — light mode defaults
- `.dark` — dark mode overrides

Examples:

- `--background`
- `--foreground`
- `--card`
- `--border`
- `--ring`
- `--primary`

## Why This Matters

UI components in `@repo/ui` consume these semantic tokens instead of raw colors, which keeps theme changes centralized.

---

**Related references:**
- `references/ui/components.md` — Components that consume these tokens
- `references/setup/next-config.md` — App-level configuration that participates in shared UI behavior
- `references/setup/config-feature-flags.md` — Theme-related app config flags

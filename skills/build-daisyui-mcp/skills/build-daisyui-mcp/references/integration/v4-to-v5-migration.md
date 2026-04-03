# daisyUI v4 → v5 Migration Guide

> **Purpose**: Complete migration reference for upgrading from daisyUI 4 (Tailwind CSS v3) to daisyUI 5 (Tailwind CSS v4). Every class rename, removal, default change, and config migration.

---

## Configuration Migration

### Before (v4 — tailwind.config.js)

```js
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{html,js,jsx,ts,tsx}"],
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark", "cupcake"],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
    logs: true,
    themeRoot: ":root",
  },
};
```

### After (v5 — CSS only)

```css
/* app.css */
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, cupcake;
}
```

### Config Option Changes

| v4 Option | v5 Equivalent | Notes |
|-----------|---------------|-------|
| `plugins: [require("daisyui")]` | `@plugin "daisyui"` | CSS `@plugin` syntax |
| `themes: ["light", "dark"]` | `themes: light, dark` | Comma-separated, no quotes |
| `darkTheme: "dark"` | `themes: dark --prefersdark` | Flag on theme name |
| First theme = default | `themes: light --default` | Explicit flag |
| `base: false` | `exclude: base` | Include/exclude syntax |
| `styled: false` | Removed | Use `include:`/`exclude:` |
| `utils: false` | Removed | Use `include:`/`exclude:` |
| `logs: true` | Removed | No console output |
| `themeRoot: ":root"` | `root: :root` | Renamed |

---

## Theme Variable Migration

### Color Variable Renames

| v4 Variable | v5 Variable |
|-------------|-------------|
| `--p` | `--color-primary` |
| `--pf` | Removed (auto-calculated) |
| `--pc` | `--color-primary-content` |
| `--s` | `--color-secondary` |
| `--sf` | Removed |
| `--sc` | `--color-secondary-content` |
| `--a` | `--color-accent` |
| `--af` | Removed |
| `--ac` | `--color-accent-content` |
| `--n` | `--color-neutral` |
| `--nf` | Removed |
| `--nc` | `--color-neutral-content` |
| `--b1` | `--color-base-100` |
| `--b2` | `--color-base-200` |
| `--b3` | `--color-base-300` |
| `--bc` | `--color-base-content` |
| `--in` | `--color-info` |
| `--inc` | `--color-info-content` |
| `--su` | `--color-success` |
| `--suc` | `--color-success-content` |
| `--wa` | `--color-warning` |
| `--wac` | `--color-warning-content` |
| `--er` | `--color-error` |
| `--erc` | `--color-error-content` |

### Color Format Change

| v4 | v5 |
|----|-----|
| HSL: `hsl(210, 50%, 50%)` | oklch: `oklch(55% 0.2 240)` |

### Shape Variable Renames

| v4 Variable | v5 Variable |
|-------------|-------------|
| `--rounded-box` | `--radius-box` |
| `--rounded-btn` | `--radius-field` |
| `--rounded-badge` | `--radius-selector` |
| `--animation-btn` | Removed |
| `--animation-input` | Removed |
| `--btn-focus-scale` | Removed |
| N/A | `--size-selector` (new) |
| N/A | `--size-field` (new) |
| N/A | `--border` (new) |
| N/A | `--depth` (new) |
| N/A | `--noise` (new) |

### Custom Theme Migration

**v4:**
```js
// tailwind.config.js
daisyui: {
  themes: [{
    mytheme: {
      "primary": "#570df8",
      "secondary": "#f000b8",
      "accent": "#37cdbe",
      "neutral": "#3d4451",
      "base-100": "#ffffff",
    },
  }],
}
```

**v5:**
```css
@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;
  color-scheme: light;
  --color-primary: oklch(55% 0.3 280);
  --color-primary-content: oklch(98% 0.01 280);
  --color-secondary: oklch(60% 0.25 330);
  --color-secondary-content: oklch(98% 0.01 330);
  --color-accent: oklch(70% 0.15 180);
  --color-accent-content: oklch(20% 0.02 180);
  --color-neutral: oklch(40% 0.05 260);
  --color-neutral-content: oklch(95% 0.01 260);
  --color-base-100: oklch(100% 0 0);
  --color-base-200: oklch(96% 0.01 260);
  --color-base-300: oklch(92% 0.02 260);
  --color-base-content: oklch(20% 0.03 260);
  --color-info: oklch(70% 0.15 220);
  --color-info-content: oklch(98% 0.01 220);
  --color-success: oklch(65% 0.2 145);
  --color-success-content: oklch(98% 0.01 145);
  --color-warning: oklch(80% 0.2 80);
  --color-warning-content: oklch(20% 0.03 80);
  --color-error: oklch(60% 0.25 25);
  --color-error-content: oklch(98% 0.01 25);
  --radius-selector: 1rem;
  --radius-field: 0.25rem;
  --radius-box: 0.5rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

---

## Class Name Changes

### Removed Components

| v4 Class | v5 Replacement |
|----------|----------------|
| `form-control` | `<fieldset class="fieldset">` |
| `label-text` | `<legend class="fieldset-legend">` |
| `label-text-alt` | `<label class="fieldset-label">` |
| `btn-group` | `join` with `join-item` on each child |
| `input-group` | `join` with `join-item` on each child |
| `artboard` | Tailwind utilities: `w-[320px] h-[568px]` |
| `artboard-demo` | Removed |
| `phone-1` through `phone-6` | Tailwind width/height utilities |
| `btm-nav` | `dock` |
| `btm-nav-xs/sm/md/lg` | `dock-xs/sm/md/lg` |
| `btm-nav-active` | `dock-active` |
| `btm-nav-label` | `dock-label` |
| `mask-parallelogram` (all) | Removed entirely |

### Renamed Classes

| v4 Class | v5 Class |
|----------|----------|
| `card-bordered` | `card-border` |
| `card-compact` | `card-sm` |
| `tabs-lifted` | `tabs-lift` |
| `tabs-bordered` | `tabs-border` |
| `tabs-boxed` | `tabs-box` |
| `avatar online` | `avatar avatar-online` |
| `avatar offline` | `avatar avatar-offline` |
| `avatar placeholder` | `avatar avatar-placeholder` |
| `menu` + `disabled` | `menu-disabled` |
| `menu` + `active` | `menu-active` |
| `menu` + `focus` | `menu-focus` |
| `camera` (mockup-phone) | `mockup-phone-camera` |
| `display` (mockup-phone) | `mockup-phone-display` |

### Removed Classes (Default Behavior Changed)

| v4 Class | v5 Behavior | Use This Instead |
|----------|-------------|------------------|
| `input-bordered` | Borders are default in v5 | Use `input-ghost` for borderless |
| `select-bordered` | Borders are default in v5 | Use `select-ghost` for borderless |
| `file-input-bordered` | Borders are default in v5 | Use `file-input-ghost` for borderless |
| `textarea-bordered` | Borders are default in v5 | Use `textarea-ghost` for borderless |
| `table hover` | No built-in hover class | Use `hover:bg-base-300` on `<tr>` |

### Default Changes

| Component | v4 Default | v5 Default |
|-----------|-----------|------------|
| Input/Select width | No default width | `20rem` default width |
| Footer layout | Horizontal | Vertical (use `footer-horizontal` for horizontal) |
| Menu width | `w-full` | Auto width (add `w-full` manually) |
| Chat bubble color | `neutral` | `base-300` (use `chat-bubble-neutral` for v4 look) |
| Stat background | Colored | Transparent (add `bg-base-100` if needed) |
| Button height | Taller | Reduced (customize via `--size-field`) |

---

## New Components in v5

| Component | Class | Purpose |
|-----------|-------|---------|
| Fieldset | `fieldset` | Form field grouping (replaces `form-control`) |
| Label | `label` | Input labels with floating variant |
| Floating Label | `floating-label` | CSS-only floating label effect |
| Validator | `validator` | CSS-only validation styling |
| Validator Hint | `validator-hint` | Shows/hides based on input validity |
| Filter | `filter` | Radio button filter group with reset |
| Dock | `dock` | Bottom navigation bar |
| List | `list` | Vertical data rows |
| Status | `status` | Small status indicator icon |
| Calendar | `calendar` | Datepicker styling (for Cally, Pikaday, etc.) |
| Hover 3D | `hover-3d` | 3D card hover effect |
| Text Rotate | `text-rotate` | Rotating text animation |
| Hover Gallery | `hover-gallery` | Image gallery hover effect |
| FAB | `fab` | Floating action button + speed dial |
| Skeleton Text | `skeleton-text` | Animated text placeholder |

---

## New Variants in v5

| Variant | Usage | Purpose |
|---------|-------|---------|
| `is-drawer-open:` | `is-drawer-open:w-64` | Applied when drawer is open |
| `is-drawer-close:` | `is-drawer-close:w-14` | Applied when drawer is closed |
| `user-invalid:` | `user-invalid:input-error` | Applied after user interaction + invalid |

---

## New Size: XL

Many components gained an `xl` size in v5:

```html
<button class="btn btn-xl">Extra Large Button</button>
<input class="input input-xl" />
<span class="badge badge-xl">XL Badge</span>
<input type="checkbox" class="checkbox checkbox-xl" />
<input type="checkbox" class="toggle toggle-xl" />
<input type="radio" class="radio radio-xl" />
<kbd class="kbd kbd-xl">XL</kbd>
<span class="loading loading-xl"></span>
```

---

## Migration Checklist

- [ ] Update CSS entry point: `@import "tailwindcss"` + `@plugin "daisyui"`
- [ ] Remove `tailwind.config.js` daisyUI plugin (or convert to CSS `@plugin`)
- [ ] Search & replace `form-control` → `fieldset`
- [ ] Search & replace `label-text` → `fieldset-legend`
- [ ] Remove `input-bordered`, `select-bordered`, `file-input-bordered`, `textarea-bordered`
- [ ] Replace `btn-group` / `input-group` → `join` + `join-item`
- [ ] Replace `btm-nav` → `dock`
- [ ] Replace `card-bordered` → `card-border`
- [ ] Replace `card-compact` → `card-sm`
- [ ] Replace `tabs-lifted` → `tabs-lift`
- [ ] Replace `tabs-bordered` → `tabs-border`
- [ ] Replace `tabs-boxed` → `tabs-box`
- [ ] Update avatar state classes: `online` → `avatar-online`, etc.
- [ ] Update menu state classes: `active` → `menu-active`, etc.
- [ ] Convert custom themes from JS config to CSS `@plugin "daisyui/theme"`
- [ ] Convert HSL colors to oklch
- [ ] Add `w-full` to inputs/selects if needed (v5 defaults to `20rem`)
- [ ] Add `footer-horizontal` if horizontal footer was expected
- [ ] Test all form layouts with new `fieldset` structure
- [ ] Remove `artboard` classes, use Tailwind width/height utilities

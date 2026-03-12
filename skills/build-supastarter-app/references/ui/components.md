# UI Components

> Overview of the shared `@repo/ui` component library. Consult this when choosing an existing primitive before building custom UI.
>
> The package is a Shadcn/Radix-style library with Tailwind token classes and a barrel export in `packages/ui/index.ts`.

## Barrel Export

```ts
// packages/ui/index.ts
export * from "./components/button";
export * from "./components/card";
export * from "./components/dialog";
export * from "./components/form";
export * from "./components/toast";
export * from "./lib";
```

The library currently exports components such as accordion, alert, avatar, badge, button, card, dialog, form, input, select, sheet, table, tabs, textarea, toast, tooltip, and the shared `cn()` utility.

## Import Pattern

Prefer deep imports for components:

```ts
import { Button } from "@repo/ui/components/button";
import { Dialog, DialogContent } from "@repo/ui/components/dialog";
import { cn } from "@repo/ui";
```

## When To Use The Barrel

Use `@repo/ui` for utilities and broad re-exports, but the existing conventions docs prefer deep component imports for day-to-day feature work.

---

**Related references:**
- `references/ui/forms.md` — Form primitives built on top of the UI package
- `references/ui/styling-patterns.md` — Shared visual conventions and token usage
- `references/ui/feedback-overlays.md` — Dialog and toast primitives
- `references/setup/import-conventions.md` — Import rules for UI deep imports
- `references/ui/theme-tokens.md` — Theme token system

# Inline Vector Graphics Using Native Astro SVG Components

> **Context:** Assets & Image Pipeline | **Impact:** Medium | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Loading vector icons and badges via HTML `<img src="/icon.svg">` tags triggers independent HTTP network roundtrips, prevents dynamic CSS styling with `currentColor`, and disables dark-mode stroke/fill theming. Astro 5.7+ natively imports `.svg` files as Astro components, inlining clean SVG markup into the static document while passing attributes (`width`, `height`, `fill`, `stroke`) and enforcing type safety via `SvgComponent`.

## 2. How It Differs From Classic React / Next.js

React applications require external plugins like `@svgr/webpack` or custom JSX wrappers (e.g. Lucide React) to turn SVGs into components, inflating client JavaScript bundles. Astro compiles SVGs into zero-JS inline HTML components at build time without runtime packages.

## 3. Common Mistakes & Anti-Patterns

Using heavy third-party React icon libraries in marketing templates or referencing SVGs via `<img>` tags, which blocks CSS color inheritance and creates flash of unstyled icons.

### ❌ Bad Practice / Anti-Pattern

Loading SVGs as external images or embedding multi-kilobyte React icon packages:

```astro
---
// ❌ Anti-Pattern: External <img> prevents CSS currentColor inheritance
---
<a href="/docs" class="flex items-center text-blue-600">
  <span>Documentation</span>
  <img src="/icons/arrow-right.svg" class="icon" alt="" />
</a>
```

### ✅ Best Practice / Idiomatic

Import local `.svg` files directly as native Astro components with type safety:

```astro
---
import ArrowRight from '../assets/icons/arrow-right.svg';
import type { SvgComponent } from 'astro/types';

interface ActionLink {
  label: string;
  href: string;
  icon: SvgComponent;
}

const link: ActionLink = {
  label: "Documentation",
  href: "/docs",
  icon: ArrowRight
};

const IconComponent = link.icon;
---
<!-- ✅ Inlines SVG, inherits text color via currentColor, zero JS runtime -->
<a href={link.href} class="flex items-center text-blue-600 hover:text-blue-800">
  <span>{link.label}</span>
  <IconComponent width={18} height={18} fill="currentColor" class="ml-1" />
</a>
```

## 4. Verification & Audit

Inspect generated HTML in `dist/`: confirm SVG code is inlined (`<svg ...>`) without external `/icons/*.svg` HTTP requests:

```bash
grep -n '<svg' dist/index.html && echo "Pass: SVG inlined cleanly"
```

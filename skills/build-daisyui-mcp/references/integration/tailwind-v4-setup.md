# Tailwind CSS v4 + daisyUI 5 — Setup Guide

> **Purpose**: Complete setup instructions for daisyUI 5 with Tailwind CSS v4 across all major frameworks, CDN, and PostCSS configurations.

---

## Minimal Setup (Any Framework)

### 1. Install

```bash
npm i tailwindcss daisyui@latest
```

### 2. CSS Entry File

```css
/* app.css or src/input.css */
@import "tailwindcss";
@plugin "daisyui";
```

That's it. No `tailwind.config.js` required for basic usage.

### 3. Theme Selection (Optional)

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, cupcake;
}
```

- `--default` → applied on page load
- `--prefersdark` → applied when `prefers-color-scheme: dark`
- Omit the block entirely → only `light` theme enabled

### 4. Enable All 35 Themes

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: all;
}
```

### 5. Include / Exclude Components

```css
@plugin "daisyui" {
  include: button, card, modal;
}
/* or */
@plugin "daisyui" {
  exclude: carousel, countdown;
}
```

---

## Framework-Specific Setup

### React + Vite

```bash
npm create vite@latest my-app -- --template react
cd my-app
npm i tailwindcss @tailwindcss/vite daisyui@latest
```

```js
// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

```css
/* src/index.css */
@import "tailwindcss";
@plugin "daisyui";
```

```jsx
// src/App.jsx
export default function App() {
  return (
    <div className="min-h-screen bg-base-200 flex items-center justify-center">
      <div className="card bg-base-100 shadow-lg">
        <div className="card-body">
          <h2 className="card-title">Hello daisyUI 5</h2>
          <p>Built with Tailwind CSS v4</p>
          <div className="card-actions justify-end">
            <button className="btn btn-primary">Get Started</button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Next.js (v15+)

```bash
npx create-next-app@latest my-app
cd my-app
npm i daisyui@latest
```

Next.js 15 includes Tailwind CSS v4 by default. Add daisyUI to your CSS:

```css
/* app/globals.css */
@import "tailwindcss";
@plugin "daisyui";
```

### SvelteKit

```bash
npx sv create my-app
cd my-app
npm i daisyui@latest
```

```css
/* src/app.css */
@import "tailwindcss";
@plugin "daisyui";
```

### Nuxt 3

```bash
npx nuxi@latest init my-app
cd my-app
npm i daisyui@latest @nuxtjs/tailwindcss
```

```css
/* assets/css/main.css */
@import "tailwindcss";
@plugin "daisyui";
```

### Astro

```bash
npm create astro@latest my-app
cd my-app
npx astro add tailwind
npm i daisyui@latest
```

```css
/* src/styles/global.css */
@import "tailwindcss";
@plugin "daisyui";
```

---

## PostCSS Setup (Non-Vite Bundlers)

For webpack, Parcel, or other PostCSS-based setups:

```bash
npm i tailwindcss @tailwindcss/postcss postcss autoprefixer daisyui@latest
```

```js
// postcss.config.js
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

```css
/* src/input.css */
@import "tailwindcss";
@plugin "daisyui";
```

Build:
```bash
npx @tailwindcss/cli -i src/input.css -o dist/output.css --watch
```

---

## CDN (No Build Step)

For prototyping or static HTML:

```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/themes/light.css" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/full.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
```

Individual component CDN (tree-shaking):
```html
<!-- Only load button + card -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/components/button.css" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/daisyui@5/components/card.css" rel="stylesheet" />
```

---

## MCP Blueprint Server Setup

The official daisyUI Blueprint MCP server. Package: `daisyui-blueprint`.

### VS Code / Cursor

Add to `.vscode/mcp.json` or user MCP settings:

```json
{
  "servers": {
    "daisyui-blueprint": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "daisyui-blueprint@latest"],
      "env": {
        "LICENSE": "YOUR_LICENSE_KEY",
        "EMAIL": "YOUR_EMAIL"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add daisyui-blueprint \
  --env LICENSE=YOUR_LICENSE_KEY \
  --env EMAIL=YOUR_EMAIL \
  --env FIGMA=YOUR_FIGMA_API_KEY \
  -- npx -y daisyui-blueprint@latest
```

### Manual (Any MCP Host)

```json
{
  "daisyui-blueprint": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "daisyui-blueprint@latest"],
    "env": {
      "LICENSE": "YOUR_LICENSE_KEY",
      "EMAIL": "YOUR_EMAIL",
      "FIGMA": "YOUR_FIGMA_API_KEY"
    }
  }
}
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `LICENSE` | Yes | License key for Blueprint |
| `EMAIL` | Yes | Associated email |
| `FIGMA` | No | Figma personal access token (for Figma-to-daisyUI tool) |

---

## v4 vs v5 Configuration Comparison

| Setting | v4 (tailwind.config.js) | v5 (CSS @plugin) |
|---------|------------------------|-------------------|
| Plugin registration | `plugins: [require("daisyui")]` | `@plugin "daisyui"` |
| Theme list | `daisyui: { themes: ["light", "dark"] }` | `themes: light, dark` |
| Dark theme | `daisyui: { darkTheme: "dark" }` | `themes: dark --prefersdark` |
| Default theme | First in array | `themes: light --default` |
| Theme root | `daisyui: { themeRoot: ":root" }` | `root: :root` |
| Disable styling | `daisyui: { styled: false }` | Use `include:`/`exclude:` |
| Disable base | `daisyui: { base: false }` | Use `exclude:` |
| Log output | `daisyui: { logs: false }` | Removed (no logs) |
| Config file | Required (`tailwind.config.js`) | Not needed (CSS only) |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Unknown at rule @plugin` | IDE doesn't recognize Tailwind v4 syntax | Install Tailwind CSS IntelliSense extension; add `"css.lint.unknownAtRules": "ignore"` to VS Code settings |
| Components unstyled | Missing `@plugin "daisyui"` | Ensure CSS file has both `@import "tailwindcss"` and `@plugin "daisyui"` |
| Theme not applying | `data-theme` not set | Add `data-theme="light"` to `<html>` element |
| Only light theme works | Didn't enable themes | Use `@plugin "daisyui" { themes: light, dark; }` |
| Huge CSS output | All themes enabled | Use specific themes: `themes: light, dark` instead of `themes: all` |
| `daisyui` not found | Wrong package version | Use `npm i daisyui@latest` (v5+) |
| PostCSS build fails | Missing PostCSS plugin | Install `@tailwindcss/postcss` for PostCSS setups |

---

## Verified Minimal HTML

```html
<!DOCTYPE html>
<html data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="/dist/output.css" rel="stylesheet" />
</head>
<body class="min-h-screen bg-base-200">
  <div class="hero min-h-screen">
    <div class="hero-content text-center">
      <div class="max-w-md">
        <h1 class="text-5xl font-bold">Hello daisyUI 5</h1>
        <p class="py-6">Built with Tailwind CSS v4 and daisyUI 5.</p>
        <button class="btn btn-primary">Get Started</button>
      </div>
    </div>
  </div>
</body>
</html>
```

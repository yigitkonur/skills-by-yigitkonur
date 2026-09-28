# Modern ESLint, Prettier & Quality Tooling Architecture for Astro

Authoritative guide for configuring modern, high-speed, zero-conflict static analysis, formatting, and linting pipelines across Astro 5/7+ applications and React/TypeScript islands.

---

## 1. Tooling Hierarchy & Separation of Concerns

A robust Astro engineering pipeline partitions static analysis into 4 distinct, non-overlapping layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Astro Sentinel (AST & Contract Engine)                              │
│    - 170 authoritative rule cards                                      │
│    - Fast AST template parsing via @astrojs/compiler (374 files in ~3s) │
│    - Cross-file Content Layer, Zod coercion & Edge runtime closures    │
├────────────────────────────────────────────────────────────────────────┤
│ 2. ESLint Flat Config (Daily Developer & In-Editor Feedback)          │
│    - eslint-plugin-astro (Core rules + 26 JSX-a11y rules)             │
│    - eslint-plugin-better-tailwindcss (Class ordering & duplicate tags)│
│    - Local rule zeo-astro/no-nextjs-ghost-imports                     │
│    - Scoped React hooks & compiler rules on JSX/TSX islands only      │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Compiler-Level Type Safety (@astrojs/check & tsgo)                  │
│    - astro check: Template JSX expressions, Props & slot types        │
│    - tsgo: Microsoft TypeScript Go native compiler for scripts        │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Prettier AST Formatting & Tailwind v4 Class Ordering               │
│    - prettier-plugin-astro: AST-level template formatting             │
│    - prettier-plugin-tailwindcss: Tailwind CSS class ordering         │
│    - Tailwind v4 stylesheet resolution (tailwindStylesheet)           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Production ESLint Flat Config (`eslint.config.mjs`)

Below is the battle-tested, zero-conflict ESLint Flat Config template designed for hybrid Astro and React islands codebases:

```javascript
// eslint.config.mjs
import { defineConfig } from 'eslint/config'
import astroPlugin from 'eslint-plugin-astro'
import betterTailwind from 'eslint-plugin-better-tailwindcss'
import eslintPluginJsxA11y from 'eslint-plugin-jsx-a11y'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default defineConfig([
  // ─── 1. Global Ignores ────────────────────────────────────────────────────────
  {
    ignores: ['dist/**', '.astro/**', 'node_modules/**', '.worktrees/**'],
  },

  // ─── 2. Local In-Editor Plugin: Prevent Residual Framework Imports ───────────
  {
    plugins: {
      'local-astro': {
        rules: {
          'no-nextjs-ghost-imports': {
            meta: {
              type: 'problem',
              docs: { description: 'Disallow legacy Next.js package imports in Astro.' },
            },
            create(context) {
              return {
                ImportDeclaration(node) {
                  const src = node.source?.value
                  if (typeof src === 'string' && (src.startsWith('next/') || src === 'next')) {
                    context.report({
                      node,
                      message: `Legacy Next.js import "${src}" detected. Migrate to native Astro APIs.`,
                    })
                  }
                },
              }
            },
          },
        },
      },
    },
    rules: {
      'local-astro/no-nextjs-ghost-imports': 'error',
    },
  },

  // ─── 3. TypeScript & React Islands Scoping (Non-Astro Files) ──────────────────
  {
    files: ['src/**/*.{ts,tsx,js,jsx}'],
    ignores: ['**/*.astro', '**/*.astro/**'],
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      'react-hooks': reactHooks,
      'jsx-a11y': eslintPluginJsxA11y,
    },
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: './tsconfig.json',
      },
    },
    rules: {
      // React Hooks Invariants
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // TypeScript Bug Prevention
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },

  // ─── 4. Astro Templates & Accessibility (A11y) Suite ──────────────────────────
  ...astroPlugin.configs['flat/recommended'].map((config) => ({
    ...config,
    files: config.files ?? ['**/*.astro'],
    languageOptions: {
      ...config.languageOptions,
      parserOptions: { ...config.languageOptions?.parserOptions, parser: tseslint.parser },
    },
  })),
  {
    files: ['**/*.astro'],
    processor: 'astro/client-side-ts',
    plugins: {
      'better-tailwindcss': betterTailwind,
    },
    settings: {
      'better-tailwindcss': {
        entryPoint: './src/styles/globals.css',
        tsconfig: './tsconfig.json',
        callees: ['cn', 'clsx', 'twMerge', 'classnames'],
      },
    },
    rules: {
      // ── WCAG 2.2 Accessibility (A11y) Suite ──
      'astro/jsx-a11y/alt-text': 'warn',
      'astro/jsx-a11y/anchor-has-content': 'warn',
      'astro/jsx-a11y/anchor-is-valid': 'warn',
      'astro/jsx-a11y/aria-activedescendant-has-tabindex': 'warn',
      'astro/jsx-a11y/aria-props': 'warn',
      'astro/jsx-a11y/aria-proptypes': 'warn',
      'astro/jsx-a11y/aria-role': 'warn',
      'astro/jsx-a11y/aria-unsupported-elements': 'warn',
      'astro/jsx-a11y/autocomplete-valid': 'warn',
      'astro/jsx-a11y/click-events-have-key-events': 'warn',
      'astro/jsx-a11y/heading-has-content': 'warn',
      'astro/jsx-a11y/html-has-lang': 'warn',
      'astro/jsx-a11y/iframe-has-title': 'warn',
      'astro/jsx-a11y/img-redundant-alt': 'warn',
      'astro/jsx-a11y/interactive-supports-focus': 'warn',
      'astro/jsx-a11y/label-has-associated-control': 'warn',
      'astro/jsx-a11y/media-has-caption': 'warn',
      'astro/jsx-a11y/mouse-events-have-key-events': 'warn',
      'astro/jsx-a11y/no-access-key': 'warn',
      'astro/jsx-a11y/no-autofocus': 'warn',
      'astro/jsx-a11y/no-distracting-elements': 'warn',
      'astro/jsx-a11y/no-redundant-roles': 'warn',
      'astro/jsx-a11y/role-has-required-aria-props': 'warn',
      'astro/jsx-a11y/role-supports-aria-props': 'warn',
      'astro/jsx-a11y/scope': 'warn',
      'astro/jsx-a11y/tabindex-no-positive': 'warn',

      // ── Astro Architectural & Code Quality Rules ──
      'astro/no-unused-css-selector': 'warn',
      'astro/prefer-class-list-directive': 'warn',
      'astro/prefer-object-class-list': 'warn',
      'astro/no-set-html-directive': 'warn',
      'astro/no-unsafe-inline-scripts': 'warn',
      'astro/no-deprecated-getentrybyslug': 'error',
      'astro/no-exports-from-components': 'error',
      'astro/no-prerender-export-outside-pages': 'error',

      // ── Tailwind Class Order & Duplicate Detection in Astro Templates ──
      'better-tailwindcss/enforce-consistent-class-order': 'warn',
      'better-tailwindcss/no-conflicting-classes': 'warn',
      'better-tailwindcss/no-duplicate-classes': 'warn',
    },
  },

  // ─── 5. Astro Client-Side Scripts (<script> tags in .astro) ───────────────────
  {
    files: ['**/*.astro/*.{js,ts}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { project: null, projectService: false },
    },
  },
])
```

---

## 3. Prettier & Tailwind CSS v4 Configuration (`.prettierrc.json`)

When formatting Astro templates alongside Tailwind CSS, two non-negotiable rules apply:

1. **The Plugin Ordering Law**: `prettier-plugin-tailwindcss` **MUST** be loaded last in the plugins array so that it can inspect and re-order classes after `prettier-plugin-astro` parses and structures the AST:
   ```json
   "plugins": [
     "prettier-plugin-astro",
     "@ianvs/prettier-plugin-sort-imports",
     "prettier-plugin-tailwindcss"
   ]
   ```
2. **Tailwind v4 Stylesheet Path**: Tailwind CSS v4 replaces `tailwind.config.js` with CSS-first configuration (`@theme`, `@import "tailwindcss"`). Prettier requires the `tailwindStylesheet` option to resolve theme tokens and utility classes:
   ```json
   "tailwindStylesheet": "./src/styles/globals.css"
   ```

### Authoritative `.prettierrc.json`:

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "semi": false,
  "plugins": [
    "prettier-plugin-astro",
    "prettier-plugin-tailwindcss"
  ],
  "tailwindStylesheet": "./src/styles/globals.css",
  "overrides": [
    {
      "files": "*.astro",
      "options": {
        "parser": "astro"
      }
    }
  ]
}
```

---

## 4. Ecosystem Quality & Diagnostic Tooling Matrix

| Tool | Focus & Scope | Command / Usage | Primary Advantage |
| :--- | :--- | :--- | :--- |
| **Astro Sentinel** | 170 Astro best practices AST & contracts | `pnpm check:astro-sentinel` | Sub-4s full repository AST scanning across all 374 `.astro` components. |
| **@astrojs/check** | Compiler-level type checker | `pnpm astro:check` | Validates TypeScript types inside frontmatter and template expressions. |
| **react-doctor** | React islands health & performance | `npx react-doctor@latest --verbose` | Generates 0–100 health score; detects re-render cascades and DOM listener leaks. |
| **astro-doctor** | Astro anti-pattern scanner | `@santi020k/eslint-plugin-astro-doctor` | 13 proprietary rules catching `client:load` overuse, missing image dimensions, and env leaks. |
| **diagnost** | Holistic Astro diagnostic toolkit | `npx diagnost@latest --diff main` | Git-aware 0–100 quality score for SEO, a11y, routing, and island weights. |

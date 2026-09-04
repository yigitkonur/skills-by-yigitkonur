# Knip Configuration Catalog

Comprehensive reference for configuring Knip (v5+) across standalone applications, multi-package monorepos, heterogeneous frameworks, custom AST compilers, and granular quality rulesets.

---

## 1. Knip Configuration File Formats & Precedence

Knip resolves configuration from root configuration files or `package.json`. Knip checks candidate locations in the following resolution order:

1. `knip.json`
2. `knip.jsonc`
3. `.knip.json`
4. `.knip.jsonc`
5. `knip.ts`
6. `knip.js`
7. `knip.config.ts`
8. `knip.config.js`
9. `package.json` (under the `"knip"` property)

### Complete Knip v5 TypeScript Configuration Schema

```typescript
// knip.ts
import type { KnipConfig } from 'knip';

const config: KnipConfig = {
  // Schema reference for IDE intellisense in JSON/JSONC variants
  // $schema: 'https://unpkg.com/knip@5/overview/schema.json',

  // Entry points defining the root of the dependency graph
  // Use the '!' suffix to denote public APIs where unused exports are intentionally permitted
  entry: ['src/index.ts!', 'src/cli.ts!'],

  // Files included in the analysis graph
  project: ['src/**/*.{ts,tsx}', '!src/**/*.generated.ts'],

  // Paths excluded from dependency analysis (use with extreme caution; see Section 8)
  ignore: ['**/*.d.ts'],

  // Ignored dependencies and binaries from manifest validation
  ignoreDependencies: [
    '@types/*',
    'autoprefixer',
    '/^@babel/preset-/',
    'sharp',
  ],
  ignoreBinaries: ['docker', 'docker-compose', 'which', 'cat', 'sed'],

  // Granular export ignore settings for self-referencing modules
  ignoreExportsUsedInFile: {
    interface: true,
    type: true,
    variable: false,
    function: false,
    class: false,
  },

  // Ignored member identifiers for classes, interfaces, and enums
  ignoreMembers: [
    'displayName',
    'defaultProps',
    'propTypes',
    'toJSON',
    'beforeCreate',
    'mounted',
  ],

  // Knip v5: Control whether exports from entry files are analyzed
  // Default is false (entry exports are considered public). Setting to true checks entry exports
  // unless the entry pattern includes the '!' suffix.
  includeEntryExports: false,

  // Knip v5: JSDoc/TSDoc tag-based export filtering
  // Prefix with '-' to exclude from report, or '+' to exclusively report
  tags: ['-@internal', '-@beta'],

  // Rules classification with strict enterprise defaults
  rules: {
    files: 'error',
    dependencies: 'error',
    devDependencies: 'error',
    unlisted: 'error',
    binaries: 'error',
    unresolved: 'error',
    exports: 'error',
    types: 'error',
    nsExports: 'error',
    nsTypes: 'error',
    duplicateExports: 'error',
    enumMembers: 'warn',
    classMembers: 'off',
  },

  // File compilers for non-TS/JS extensions (Astro, MDX, Vue, Svelte)
  compilers: {
    vue: (text: string) => text,
    mdx: (text: string) => text,
    astro: (text: string) => text,
    svelte: (text: string) => text,
  },

  // Monorepo workspaces definition
  workspaces: {
    '.': {
      entry: ['scripts/*.ts'],
      project: ['scripts/*.ts'],
    },
    'packages/*': {
      entry: ['src/index.ts!'],
      project: ['src/**/*.ts'],
    },
    'apps/*': {
      entry: ['src/main.tsx!'],
      project: ['src/**/*.{ts,tsx}'],
    },
  },
};

export default config;
```

---

## 2. Knip v5 Schema Nuances & Architecture Shifts

Knip v5 introduces key architectural refinements that differentiate it from earlier major versions. Understanding these nuances avoids configuration drift, false-positive reports, and broken CI pipelines.

### 1. The `!` Public API Entry Suffix vs. `includeEntryExports`
In Knip v5, entry files defined in `entry` are treated as public interfaces by default.
- **Without `!`**: If `includeEntryExports: true` is configured, Knip will report unused exports in entry files.
- **With `!` (e.g., `src/index.ts!`)**: The exclamation mark explicitly designates the entry file as a **published public library API**. Even if `includeEntryExports: true` is active, Knip strictly exempts exports in `!`-suffixed files from being reported as dead exports.
- **CLI Override**: Running `knip --include-entry-exports` toggles entry export analysis globally across all non-`!` entries.

### 2. Production Mode Scoping (`--production` / `--prod`)
Running Knip in production mode changes graph boundaries:
- Ignores all `devDependencies`.
- Excludes test files (`**/*.test.ts`, `**/*.spec.ts`), Storybook stories, and development scripts from `project`.
- Only checks that `dependencies` satisfy imports in production source files.
- Useful for Docker build container pruning and lean production image validation.

### 3. Granular `ignoreExportsUsedInFile`
Earlier versions supported only a boolean flag. Knip v5 supports a granular object schema allowing fine-grained policy:
```jsonc
{
  "ignoreExportsUsedInFile": {
    "interface": true, // Allow exporting interfaces used only in the declaring file
    "type": true,      // Allow exporting type aliases used only in the declaring file
    "variable": false, // Flag variables exported but only consumed locally
    "function": false, // Flag helper functions exported but only consumed locally
    "class": false     // Flag classes exported but only consumed locally
  }
}
```

### 4. TSDoc / JSDoc Tag-Based Filtering (`tags`)
Knip v5 parses AST JSDoc/TSDoc docblocks on exported symbols:
- `tags: ["-@internal"]`: Ignores unused export warnings if the symbol is tagged with `/** @internal */`. This allows internal utility exports across packages without triggering dead code alarms.
- `tags: ["+@public"]`: Only report unused exports that are explicitly marked with `/** @public */`.

### 5. Negation Globs in `project` and `entry`
Knip v5 natively honors leading `!` in glob patterns to carve out generated or excluded files without using the destructive top-level `ignore` array:
```jsonc
{
  "project": [
    "src/**/*.{ts,tsx}",
    "!src/**/*.generated.ts",
    "!src/vendor/**"
  ]
}
```

---

## 3. Monorepo Workspace Isolation Patterns

In multi-package repositories (pnpm workspaces, Turborepo, Nx, Lerna, Yarn, npm workspaces), dead-code analysis faces distinct boundary hazards:
1. **Dependency Leakage**: Workspace A imports package `lodash` declared only in root `package.json` or Workspace B's `package.json`.
2. **Phantom Workspace References**: Workspace A imports `@repo/utils` using internal file paths (`@repo/utils/src/internal.ts`) bypassing the package export map.
3. **Cross-Package Transitive Masking**: A symbol exported by package `A` appears "used" because package `B` imports it in a dead file that is never imported by any application.

### Architecture A: Centralized Root Configuration (`knip.jsonc`)

Recommended for Turborepo and standard pnpm monorepos where a single configuration file coordinates all workspace packages.

```jsonc
// knip.jsonc (root)
{
  "$schema": "https://unpkg.com/knip@5/overview/schema.json",
  "workspaces": {
    // 1. Root Workspace (Tooling, Orchestration, CI scripts)
    ".": {
      "entry": [
        "scripts/**/*.{js,ts}",
        ".github/workflows/*.{yml,yaml}"
      ],
      "project": ["scripts/**/*.{js,ts}"],
      "ignoreDependencies": [
        "turbo",
        "typescript",
        "@types/node"
      ]
    },

    // 2. Shared UI Library Package (Public API)
    "packages/ui": {
      "entry": ["src/index.ts!"],
      "project": ["src/**/*.{ts,tsx}"],
      "storybook": true,
      "tailwind": true
    },

    // 3. Shared Database / ORM Package
    "packages/database": {
      "entry": ["src/index.ts!", "src/seed.ts!"],
      "project": ["src/**/*.ts"],
      "prisma": true
    },

    // 4. Client Application (Next.js)
    "apps/web": {
      "next": true
    },

    // 5. Documentation Application (Astro)
    "apps/docs": {
      "astro": true
    },

    // 6. Generic wildcard for internal tool packages
    "tools/*": {
      "entry": ["src/cli.ts!"],
      "project": ["src/**/*.ts"]
    }
  }
}
```

### Architecture B: Distributed Per-Package Configuration

Recommended for large enterprise monorepos (Nx or Lerna) where individual teams own distinct workspace directories and maintain autonomy over their Knip entries.

1. **Root Configuration (`knip.jsonc`)**:
   ```jsonc
   {
     "$schema": "https://unpkg.com/knip@5/overview/schema.json",
     "rules": {
       "unlisted": "error",
       "dependencies": "error",
       "devDependencies": "error"
     }
   }
   ```
2. **Leaf Package Configuration (`apps/web/knip.jsonc`)**:
   ```jsonc
   {
     "$schema": "https://unpkg.com/knip@5/overview/schema.json",
     "next": true,
     "ignoreDependencies": ["sharp"]
   }
   ```
3. **Library Package Configuration (`packages/core/knip.jsonc`)**:
   ```jsonc
   {
     "$schema": "https://unpkg.com/knip@5/overview/schema.json",
     "entry": ["src/index.ts!"],
     "project": ["src/**/*.ts"]
   }
   ```

### Workspace Isolation Safety Matrix

| Monorepo Challenge | Root Cause | Knip v5 Defense / Configuration |
|---|---|---|
| **Root Dependency Bleed** | Workspace imports dependency installed in root `node_modules` without listing it in its own `package.json`. | Enable `"unlisted": "error"` in root rules. Knip validates imports against the local package manifest, flagging root-hoisted packages as unlisted. |
| **Bypassing Package `exports`** | Consuming package directly imports private internal files of a sibling library (`@repo/ui/src/button.ts`). | Restrict library package `entry` strictly to public barrel entries (`src/index.ts!`) and align `package.json#exports`. Knip flags internal files not reached from entry. |
| **Phantom Workspace Links** | `"@repo/pkg": "workspace:*"` declared in `package.json`, but no symbols are imported. | Knip flags `@repo/pkg` in `dependencies` as an unused dependency. |
| **Mismatched tsconfig paths** | Root `tsconfig.json` paths alias packages differently from package `package.json` package names. | Ensure each workspace specifies its local `project` and `tsconfig` or runs Knip with workspace-aware resolution. |

---

## 4. Advanced Compilers Configuration (MDX, Astro, Vue, Svelte)

Knip parses TypeScript and JavaScript Abstract Syntax Trees. Non-JS/TS files (MDX, Astro, Vue, Svelte) require a compiler function to extract valid JS/TS script content, imports, and exports before AST walking.

Knip compiler signatures support synchronous or asynchronous functions:
```typescript
type Compiler = (text: string, path: string) => string | Promise<string>;
```

### 1. MDX (Markdown + JSX) Compiler

#### Regex-Based Fast Extractor (Zero Dependencies)
Extracts ESM imports, exports, and JSX tag references:
```typescript
// knip.ts
import type { KnipConfig } from 'knip';

export const mdxCompiler = (text: string): string => {
  // 1. Extract import statements
  const imports = text.match(/^import\s+[\s\S]*?from\s+['"][^'"]+['"];?/gm) ?? [];
  // 2. Extract export statements
  const exports = text.match(/^export\s+[\s\S]*?;?/gm) ?? [];
  // 3. Extract JSX component names to detect component imports used in markup
  const jsxComponents = (text.match(/<([A-Z][A-Za-z0-9_]*)/g) ?? [])
    .map(tag => tag.slice(1))
    .filter((value, index, self) => self.indexOf(value) === index)
    .map(comp => `void ${comp};`);

  return [...imports, ...exports, ...jsxComponents].join('\n');
};
```

#### AST-Based Full Extractor (`@mdx-js/mdx`)
Converts MDX into full JavaScript code representation:
```javascript
// knip.config.js
import { compileSync } from '@mdx-js/mdx';

export default {
  compilers: {
    mdx: (text) => {
      try {
        const compiled = compileSync(text, { jsx: true });
        return String(compiled);
      } catch {
        return ''; // Gracefully degrade on syntax error in docs
      }
    },
  },
};
```

### 2. Astro (`.astro`) Compiler

Astro components feature a frontmatter code fence (`---`) containing TypeScript imports and logic, followed by template markup with component usages and client directives.

#### Regex-Based Fast Extractor
```typescript
// knip.ts
export const astroCompiler = (text: string): string => {
  // Extract frontmatter block between initial --- markers
  const frontmatterMatch = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

  // Extract <script> tags within the template
  const scriptMatches = text.match(/<script[\s\S]*?>([\s\S]*?)<\/script>/gi) ?? [];
  const scripts = scriptMatches.map(tag => tag.replace(/<\/?script[^>]*>/gi, ''));

  // Extract custom component tags used in template to preserve component imports
  const componentTags = (text.match(/<([A-Z][A-Za-z0-9_.]*)/g) ?? [])
    .map(tag => tag.slice(1).split('.')[0])
    .filter((value, index, self) => self.indexOf(value) === index)
    .map(comp => `void ${comp};`);

  return [frontmatter, ...scripts, ...componentTags].join('\n');
};
```

#### AST-Based Extractor (`@astrojs/compiler`)
```javascript
// knip.config.js
import { parse } from '@astrojs/compiler';

export default {
  compilers: {
    astro: async (text) => {
      try {
        const { ast } = await parse(text);
        // Extract frontmatter node
        const frontmatter = ast.children.find(node => node.type === 'frontmatter');
        return frontmatter ? frontmatter.value : '';
      } catch {
        return '';
      }
    },
  },
};
```

### 3. Vue Single File Components (`.vue`)

Vue SFCs combine `<script>`, `<script setup lang="ts">`, and `<template>` blocks.

#### Regex-Based Fast Extractor
```typescript
// knip.ts
export const vueCompiler = (text: string): string => {
  // Extract standard <script> and <script setup>
  const scripts = text.match(/<script[^>]*>([\s\S]*?)<\/script>/gi) ?? [];
  const scriptContent = scripts.map(s => s.replace(/<\/?script[^>]*>/gi, ''));

  // Extract component tags from template (PascalCase or kebab-case)
  const templateMatch = text.match(/<template>([\s\S]*?)<\/template>/i);
  const template = templateMatch ? templateMatch[1] : '';
  const components = (template.match(/<([A-Z][A-Za-z0-9]*)/g) ?? [])
    .map(tag => tag.slice(1))
    .filter((value, index, self) => self.indexOf(value) === index)
    .map(comp => `void ${comp};`);

  return [...scriptContent, ...components].join('\n');
};
```

#### AST-Based Extractor (`@vue/compiler-sfc`)
```javascript
// knip.config.js
import { parse } from '@vue/compiler-sfc';

export default {
  compilers: {
    vue: (text) => {
      const { descriptor, errors } = parse(text);
      if (errors.length > 0) return '';
      const script = descriptor.script?.content ?? '';
      const scriptSetup = descriptor.scriptSetup?.content ?? '';
      return `${script}\n${scriptSetup}`;
    },
  },
};
```

### 4. Svelte Single File Components (`.svelte`)

Svelte components support `<script>`, `<script context="module">` (Svelte 4), and runes in Svelte 5 (`$state`, `$derived`, `<script module>`).

#### Regex-Based Fast Extractor
```typescript
// knip.ts
export const svelteCompiler = (text: string): string => {
  // Extract all script blocks (both standard and module context)
  const scripts = text.match(/<script[^>]*>([\s\S]*?)<\/script>/gi) ?? [];
  const scriptContent = scripts.map(s => s.replace(/<\/?script[^>]*>/gi, ''));

  // Extract component tags from template
  const componentTags = (text.match(/<([A-Z][A-Za-z0-9]*)/g) ?? [])
    .map(tag => tag.slice(1))
    .filter((value, index, self) => self.indexOf(value) === index)
    .map(comp => `void ${comp};`);

  return [...scriptContent, ...components].join('\n');
};
```

---

## 5. Exact Configuration for Linter & Formatter Plugins

Knip features dedicated plugins for code quality engines. Misconfiguration causes phantom "unused dependency" warnings for plugins and rulesets, or masks unlisted linters.

### 1. ESLint Plugin (`eslint`)

Knip detects both legacy (`.eslintrc.*`) and modern Flat Config (`eslint.config.{js,mjs,cjs,ts}`).

#### What Knip Resolves Automatically:
- Plugins (`eslint-plugin-*`, `@scope/eslint-plugin`, `@scope/eslint-plugin-*`)
- Custom parsers (`@typescript-eslint/parser`, `vue-eslint-parser`, `@babel/eslint-parser`)
- Extends configurations (`eslint-config-*`, `@scope/eslint-config`)

#### Exact Configuration Patterns:
```jsonc
// knip.jsonc
{
  // 1. Default auto-detection (enabled by default)
  "eslint": true,

  // 2. Custom flat config path (when located outside root)
  "eslint": {
    "config": ["config/eslint.config.mjs"]
  },

  // 3. Explicit entry patterns for custom rule definitions
  "eslint": {
    "config": ["eslint.config.ts"],
    "entry": ["tools/eslint-rules/**/*.ts"]
  }
}
```

#### Gotchas & Troubleshooting:
- **Flat Config Parser Plugins**: When importing parser packages directly inside `eslint.config.js` (`import tsParser from '@typescript-eslint/parser'`), Knip traces them directly via JS imports. If loaded dynamically as string identifiers, ensure Knip's ESLint plugin is enabled.
- **Dynamic Configs**: If your ESLint configuration imports helpers from a utility directory, ensure those utility files are covered by `eslint.entry` or `project`.

---

### 2. Prettier Plugin (`prettier`)

Knip parses Prettier configuration to discover formatting plugins.

#### What Knip Resolves Automatically:
- Config files: `.prettierrc`, `.prettierrc.json`, `.prettierrc.yml`, `.prettierrc.js`, `prettier.config.js`, `prettier.config.mjs`
- Plugin dependencies declared in the `"plugins"` array:
  - `prettier-plugin-tailwindcss`
  - `@trivago/prettier-plugin-sort-imports`
  - `@prettier/plugin-xml`

#### Exact Configuration Patterns:
```jsonc
// knip.jsonc
{
  // 1. Default auto-detection
  "prettier": true,

  // 2. Custom configuration location
  "prettier": {
    "config": [".config/prettier.config.js"]
  },

  // 3. Disable if Prettier is run via another tool (e.g. Biome)
  "prettier": false
}
```

#### Gotchas & Troubleshooting:
- **Autoloaded Plugins**: In Prettier v3+, plugins installed in `node_modules` are no longer autoloaded automatically and must be listed in `plugins: [...]`. Knip inspects this array to mark plugins as used dependencies.

---

### 3. Biome Plugin (`biome`)

Knip detects Biome configurations, binary invocations, and extended base configurations.

#### What Knip Resolves Automatically:
- Config files: `biome.json`, `biome.jsonc`
- Dependencies: `@biomejs/biome`
- Extended configurations referenced in `"extends": ["./biome.base.json", "@repo/biome-config"]`

#### Exact Configuration Patterns:
```jsonc
// knip.jsonc
{
  // 1. Default auto-detection
  "biome": true,

  // 2. Custom config location
  "biome": {
    "config": ["tools/biome/biome.json"]
  }
}
```

#### Gotchas & Troubleshooting:
- **Biome replacing ESLint + Prettier**: When migrating from ESLint to Biome, disable ESLint and Prettier plugins explicitly in Knip (`"eslint": false`, `"prettier": false`) to prevent Knip from scanning stale configuration files left in the repo.

---

### 4. Oxlint Plugin (`oxlint`)

Knip detects Oxlint configuration and CLI binary execution.

#### What Knip Resolves Automatically:
- Config files: `.oxlintrc.json`
- Dependencies: `oxlint`
- Plugins enabled under `"plugins": ["react", "unicorn", "typescript", "oxc"]`

#### Exact Configuration Patterns:
```jsonc
// knip.jsonc
{
  // 1. Default auto-detection
  "oxlint": true,

  // 2. Custom config location
  "oxlint": {
    "config": ["config/.oxlintrc.json"]
  }
}
```

#### Multi-Tool Coexistence Matrix (Oxlint + Biome + ESLint)
In modern high-performance toolchains, projects often run Oxlint or Biome for high-speed checks alongside ESLint for specialized type-aware rules:
```jsonc
// knip.jsonc - Hybrid Toolchain Configuration
{
  "eslint": {
    "config": ["eslint.config.mjs"]
  },
  "oxlint": {
    "config": [".oxlintrc.json"]
  },
  "prettier": false, // Formatter handled by Biome
  "biome": {
    "config": ["biome.json"]
  }
}
```

---

## 6. Plugins Catalog (80+ Tools & Frameworks)

Knip provides built-in plugins that automatically detect configuration files, entry points, dependencies, and binaries. Every plugin can be set to `true`, `false` (to disable), or configured with an object containing custom `config`, `entry`, or `project` paths.

### Web & Application Frameworks

| Plugin Name | Key / Identifier | Default Config Patterns | Default Entry / Discovered Files | Common Gotchas & Overrides |
|---|---|---|---|---|
| Next.js | `next` | `next.config.{js,mjs,ts}`, `next-env.d.ts` | `app/**/{page,layout,loading,error,not-found,route,default,template}.{js,jsx,ts,tsx}`, `pages/**/*.{js,jsx,ts,tsx}`, `middleware.{js,ts}` | Dynamic route params or custom server entry points require explicit `entry` overrides. |
| Remix | `remix` | `remix.config.{js,cjs,mjs}`, `vite.config.{js,ts}` | `app/root.{jsx,tsx}`, `app/routes/**/*.{jsx,tsx}`, `app/entry.{client,server}.{jsx,tsx}` | Route modules with `loader`, `action`, `headers` exports. |
| Astro | `astro` | `astro.config.{js,mjs,ts}` | `src/pages/**/*.{astro,md,mdx,html,js,ts}`, `src/content/config.ts` | Requires MDX compiler when importing `.mdx` files. |
| Nuxt | `nuxt` | `nuxt.config.{js,ts,mjs}` | `app.vue`, `pages/**/*.{vue,js,ts}`, `server/**/*.{js,ts}`, `middleware/**/*.{js,ts}`, `plugins/**/*.{js,ts}` | Auto-imported components and composables can trigger false positive unused export reports. |
| SvelteKit | `sveltekit` | `svelte.config.{js,cjs}` | `src/routes/**/+{page,layout,error,server}.{svelte,js,ts}`, `src/hooks.{client,server}.{js,ts}` | Dynamic `$lib` imports require tsconfig path mapping parity. |
| Vite | `vite` | `vite.config.{js,mjs,ts,cjs}` | `index.html` (scripts extracted), `vite.config.*` | Inline HTML script tags parsed as entry files. |
| Gatsby | `gatsby` | `gatsby-config.{js,ts}`, `gatsby-node.{js,ts}`, `gatsby-browser.{js,ts}`, `gatsby-ssr.{js,ts}` | `src/pages/**/*.{js,jsx,ts,tsx}`, `src/templates/**/*.{js,jsx,ts,tsx}` | Lifecycle hook files must be preserved in root. |
| Angular | `angular` | `angular.json` | `src/main.ts`, `src/polyfills.ts` | Decorator-based metadata (`@Component`, `@NgModule`) requires AST parsing preservation. |
| NestJS | `nest` | `nest-cli.json` | `src/main.ts` | Decorator reflection parameters must be accounted for in compilation. |
| Fastify | `fastify` | Embedded or programmatic | Fastify plugin files registered via `fastify.register` | Autoloaded directory plugins require explicit entry globs. |
| Express | `express` | Programmatic | Server entry files (`src/app.ts`, `src/server.ts`) | Controller routing declarations require entry tracking. |
| Eleventy | `eleventy` | `.eleventy.js`, `eleventy.config.{js,cjs}` | Templates, shortcodes, filter registrations | Dynamic shortcode imports in config must be tracked. |
| Docusaurus | `docusaurus` | `docusaurus.config.{js,ts}` | `src/pages/**/*.{js,jsx,ts,tsx}`, `sidebars.{js,ts}` | Presets bundle plugins implicitly. |
| SolidStart | `solid` | `app.config.{js,ts}` | `src/app.tsx`, `src/routes/**/*.{tsx,jsx}` | Route actions and RPC exports. |
| Waku | `waku` | `waku.config.{js,ts}` | `src/entries.tsx`, `src/routes/**/*.{tsx,jsx}` | React Server Component boundaries. |
| RedwoodJS | `redwood` | `redwood.toml` | `web/src/Routes.{tsx,jsx}`, `api/src/functions/**/*.{ts,js}` | Multi-workspace full-stack architecture. |
| React Router v7 | `react-router` | `react-router.config.{js,ts}` | `app/routes/**/*.{tsx,jsx}`, `app/root.tsx` | Replaces Remix configuration schema. |

### Testing & Verification Tools

| Plugin Name | Identifier | Default Config Patterns | Default Entry Files |
|---|---|---|---|
| Vitest | `vitest` | `vitest.config.{js,mjs,ts,cjs}`, `vite.config.{js,mjs,ts,cjs}` | `**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}`, `**/__tests__/**/*.{js,ts}` |
| Jest | `jest` | `jest.config.{js,ts,mjs,cjs,json}`, `package.json` | `**/*.{spec,test}.{js,jsx,ts,tsx}`, `**/__tests__/**/*.{js,jsx,ts,tsx}` |
| Playwright | `playwright` | `playwright.config.{js,ts,mjs}` | Tests defined in test directory or `**/*.@(spec\|test).?(c\|m)[jt]s?(x)` |
| Cypress | `cypress` | `cypress.config.{js,ts,mjs,cjs}` | `cypress/e2e/**/*.{js,jsx,ts,tsx}`, `cypress/support/**/*.{js,ts}` |
| Storybook | `storybook` | `.storybook/main.{js,ts,cjs,mjs}` | `.storybook/preview.{js,ts,jsx,tsx}`, `**/*.stories.{js,jsx,ts,tsx}` |
| Mocha | `mocha` | `.mocharc.{js,cjs,json,yaml,yml}` | `test/**/*.{js,cjs,mjs}` |
| AVA | `ava` | `ava.config.{js,cjs,mjs}`, `package.json` | `test/**/*.{js,cjs,mjs,ts}` |
| Jasmine | `jasmine` | `spec/support/jasmine.json` | `spec/**/*[sS]pec.{js,ts}` |
| WebdriverIO | `webdriverio` | `wdio.conf.{js,ts}` | `test/specs/**/*.js` |
| Cucumber | `cucumber` | `cucumber.{json,yaml,yml,js,cjs,mjs}` | Step definitions and world parameters |
| MSW | `msw` | Programmatic | Mock service worker definitions (`src/mocks/browser.ts`, `src/mocks/handlers.ts`) |
| Testing Library | `testing-library` | Programmatic | Referenced within test suite runners |
| Node Test Runner | `node-test-runner` | Programmatic (`node --test`) | `**/*.test.{js,mjs,cjs,ts}` |

### CSS, Styling & Asset Processors

| Plugin Name | Identifier | Default Config Patterns | Discovered Dependencies |
|---|---|---|---|
| Tailwind CSS | `tailwind` | `tailwind.config.{js,cjs,mjs,ts}` | Discovers Tailwind plugins (`@tailwindcss/*`), content extractors |
| PostCSS | `postcss` | `postcss.config.{js,cjs,mjs,ts}`, `.postcssrc.{json,yaml,js,cjs}` | Discovers PostCSS plugins (`autoprefixer`, `postcss-preset-env`, etc.) |
| Sass | `sass` | Programmatic | Discovers compiler binaries (`sass`, `node-sass`) |
| Panda CSS | `panda-css` | `panda.config.{ts,js,mjs}` | `@pandacss/dev` codegen and preset dependencies |
| Vanilla Extract | `vanilla-extract`| Programmatic | `@vanilla-extract/css` compilation plugins |
| Linaria | `linaria` | `.linariarc`, `linaria.config.{js,cjs}` | Discovers Babel/Vite Linaria loaders |
| UnoCSS | `unocss` | `uno.config.{js,ts,mjs}` | UnoCSS presets, extractors, transformers |
| PostHTML | `posthtml` | `.posthtmlrc.{js,json}`, `posthtml.config.{js,cjs}` | Discovers PostHTML plugins |

### Bundlers, Compilers & Transpilers

| Plugin Name | Identifier | Default Config Patterns | Entry / Plugins Parsed |
|---|---|---|---|
| Webpack | `webpack` | `webpack.config.{js,ts,mjs,cjs}` | Resolves entrypoints, loaders, and plugins |
| Rollup | `rollup` | `rollup.config.{js,mjs,ts}` | Input configs, output plugins, rollup plugins |
| esbuild | `esbuild` | Programmatic | Entrypoints passed in build scripts |
| Parcel | `parcel` | `.parcelrc` | Parcel plugins, reporters, transformers |
| Tsup | `tsup` | `tsup.config.{ts,js,cjs,json}` | Entry arrays and export targets |
| SWC | `swc` | `.swcrc` | Plugins registered under `jsc.experimental.plugins` |
| Babel | `babel` | `babel.config.{json,js,cjs,mjs}`, `.babelrc.{json,js}` | Discovers `@babel/preset-*`, `@babel/plugin-*` |
| Unbuild | `unbuild` | `build.config.{ts,js,mjs}` | Entries and bundle configurations |
| Microbundle | `microbundle`| Programmatic (`package.json`) | `source` field entry files |
| Rspack | `rspack` | `rspack.config.{js,ts,mjs,cjs}` | Resolves loaders, plugins, entries |
| Bun | `bun` | `bunfig.toml` | Discovers preload scripts and plugins |

---

## 7. Rules Configuration & CI Severities

Violations detected by Knip are classified by rule. Each rule accepts `"error"`, `"warn"`, or `"off"`.

### Rules Reference Matrix

| Rule Name | Target Violation Description | Recommended CI Severity | Recommended Triage Severity |
|---|---|---|---|
| `files` | Unused or unreferenced source files | `error` | `error` |
| `dependencies` | Unused production dependencies (`dependencies` in `package.json`) | `error` | `error` |
| `devDependencies` | Unused developer dependencies (`devDependencies` in `package.json`) | `error` | `error` |
| `unlisted` | Dependencies imported in source code but missing from `package.json` | `error` | `error` |
| `binaries` | CLI tools invoked in scripts but missing from dependencies | `error` | `warn` |
| `unresolved` | Unresolvable module specifiers or broken imports | `error` | `error` |
| `exports` | Exported functions, constants, or variables unused across the codebase | `error` | `warn` |
| `types` | Exported TypeScript types or interfaces unused across the codebase | `error` | `warn` |
| `nsExports` | Unused exports inside namespace objects (`import * as Foo`) | `warn` | `off` |
| `nsTypes` | Unused type exports inside namespace objects | `warn` | `off` |
| `duplicateExports` | Identical identifier exported multiple times | `error` | `error` |
| `enumMembers` | Unreferenced enum members | `warn` | `off` |
| `classMembers` | Unreferenced class properties or methods | `warn` | `off` |

---

## 8. Specific Ignore Patterns vs Harmful Broad Ignores

Knip provides targeted ignore arrays to eliminate false positives without disabling transitive graph analysis.

### `ignoreDependencies`
Accepts exact package strings, package subpaths, or regular expressions (enclosed in `/.../`):
```json
{
  "ignoreDependencies": [
    "react-dom/client",
    "@types/*",
    "sharp",
    "/^@babel/preset-/"
  ]
}
```

### `ignoreBinaries`
Accepts binary names executed via package scripts or child processes that do not exist as direct dependencies:
```json
{
  "ignoreBinaries": [
    "docker",
    "docker-compose",
    "cat",
    "sed",
    "awk",
    "find",
    "gh"
  ]
}
```

### Anti-Pattern: Why Broad `"ignore": [...]` Is Harmful (The Webpro Rule)

> **Never use top-level `"ignore"` as a quick bypass to silence unwanted warnings.**

In Knip's architecture, specifying a glob pattern in top-level `"ignore"` completely excises those files from Knip's internal file walker and dependency graph.

#### Severe Downstream Consequences of Broad `"ignore"`:
1. **Transitive Graph Blindness**: If file `A.ts` imports `B.ts`, and `B.ts` imports `lodash`, adding `B.ts` to `"ignore"` breaks the chain. Knip stops walking through `B.ts`. As a result, Knip now flags `lodash` as an **unused dependency** in `package.json`, causing false positives elsewhere.
2. **False Dead File Chains**: If `B.ts` also imports `C.ts`, and `C.ts` is only imported by `B.ts`, Knip cannot see the import edge from `B.ts` to `C.ts`. Knip will falsely report `C.ts` as an **unused file**, causing accidental deletion of active code.
3. **Silent Drift**: Excluded files deteriorate. Dead imports and broken specifiers accumulate inside ignored files without CI reporting.

### Resolution Protocol: Targeted Ignores vs Broad Ignores

| Scenario | Incorrect (Harmful) Configuration | Correct (Targeted) Configuration |
|---|---|---|
| Auto-generated GraphQL client code has unused types | `"ignore": ["src/generated/**"]` | `"entry": ["src/generated/graphql.ts!"]` (marking as public entry) |
| Test helper exports are flagged as unused outside tests | `"ignore": ["test/helpers/**"]` | Add test helpers to `entry` or project test glob: `"project": ["src/**", "test/**"]` |
| External CSS / Tailwind tools trigger unused dependency warnings | `"ignore": ["tailwind.config.js"]` | `"ignoreDependencies": ["autoprefixer", "postcss"]` or `"tailwind": true` |
| Type exports are used inside their defining files | `"ignore": ["src/types/**"]` | `"ignoreExportsUsedInFile": { "interface": true, "type": true }` |
| A file is truly dead and will not be restored | `"ignore": ["src/legacy/old-feature.ts"]` | Physically delete `src/legacy/old-feature.ts` from disk |

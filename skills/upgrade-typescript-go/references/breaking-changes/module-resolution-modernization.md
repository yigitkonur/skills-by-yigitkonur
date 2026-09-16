# Module Resolution Modernization

## Overview

In TypeScript 7.0, the legacy `node10` (previously known as `"node"`) module resolution strategy has been completely removed. Modern TypeScript projects must choose between two distinct resolution paradigms:

1. **`"moduleResolution": "bundler"`**: For applications and libraries built via a modern bundler (Vite, Next.js, Turbopack, Webpack 5, Rollup, esbuild, Rolldown).
2. **`"moduleResolution": "nodenext"`** (or `"node16"`): For Node.js packages and libraries that execute directly in Node.js using standard Node ESM package resolution.

## Decision Matrix

```
Is the project bundled by Vite / Next.js / Turbopack / Webpack?
  ├── YES → Use "moduleResolution": "bundler"
  │         "module": "ESNext"
  │         (Supports extensionless imports, package.json "exports" subpaths)
  │
  └── NO (Pure Node.js library / CLI package)
            ├── Uses ESM ("type": "module" in package.json)
            │     → Use "moduleResolution": "nodenext"
            │       "module": "nodenext"
            │       (Requires explicit file extensions in imports: './utils.js')
            │
            └── Uses CommonJS
                  → Use "moduleResolution": "node16"
                    "module": "commonjs"
```

## Migrating from `node10` to `bundler`

### 1. Update `tsconfig.json`
```json
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false
  }
}
```

### 2. Common Gotchas
* **`package.json` Exports Resolution**: `bundler` mode honors conditional exports in `node_modules` packages (e.g. `"exports": { "import": "...", "types": "..." }`).
* **Extensionless Relative Imports**: Allowed in `bundler` mode for `.ts`, `.tsx`, `.js`, `.jsx`.
* **JSON Imports**: Ensure `"resolveJsonModule": true` is set when importing `.json` files.

## Migrating from `node10` to `nodenext`

If building an npm library or CLI executed directly by Node:
```json
{
  "compilerOptions": {
    "module": "NodeNext",
    "moduleResolution": "NodeNext"
  }
}
```
* **Mandatory Extensions**: Relative imports must include `.js` extensions even when referring to TypeScript files (e.g., `import { helper } from './helper.js';`).
* **Declaration Emit**: Ensure declaration files (`.d.ts`) match the module format.

# Removed & Deprecated Compiler Options in TypeScript 7.0

## Overview

TypeScript 7.0 eliminates legacy compiler options that were deprecated in TypeScript 5.x and 6.x. The Go-native compiler rejects unknown or removed flags with an error.

## Complete Matrix of Removed / Changed Flags

| Compiler Option | Status in 7.0 | Replacement / Migration |
| :--- | :--- | :--- |
| `target: "es5"` / `"es3"` | **REMOVED** | Set `"target": "ES2020"` or `"ESNext"`. For legacy browser support, rely on Babel / SWC / esbuild post-processing. |
| `moduleResolution: "node10"` / `"node"` | **REMOVED** | Set `"moduleResolution": "bundler"` (for apps/bundlers) or `"nodenext"` / `"node16"` (for Node.js packages). |
| `baseUrl` | **DEPRECATED/REMOVED** | Remove `baseUrl`. Define root-relative paths directly in `paths` (e.g. `"@/*": ["./src/*"]`). |
| `module: "amd"` / `"umd"` / `"system"` | **REMOVED** | Set `"module": "esnext"` or `"nodenext"`. |
| `noImplicitUseStrict` | **REMOVED** | ESM output always implies strict mode. |
| `keyofStringsOnly` | **REMOVED** | Modern `keyof` rules (symbols and numbers included) are always active. |
| `suppressExcessPropertyErrors` | **REMOVED** | Excess property checks are always enforced. |
| `suppressImplicitAnyIndexErrors` | **REMOVED** | Use explicit index signatures or `Record<string, unknown>`. |
| `out` | **REMOVED** | Use `outFile` or modern bundlers. |
| `charset` | **REMOVED** | UTF-8 is the only supported character encoding. |

## Quick Cleanup Script

To scan and clean invalid flags across all `tsconfig*.json` files:

```bash
# Scan for deprecated compiler options
grep -E '"(baseUrl|noImplicitUseStrict|keyofStringsOnly|suppressExcessPropertyErrors|suppressImplicitAnyIndexErrors|charset)"' tsconfig*.json
```

## Valid Modern `tsconfig.json` Baseline

```json
{
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "target": "ESNext",
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noEmit": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

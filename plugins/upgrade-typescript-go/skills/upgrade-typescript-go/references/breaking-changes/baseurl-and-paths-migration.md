# `baseUrl` Deprecation & `paths` Migration

## Overview

In legacy TypeScript, `baseUrl` was used to resolve non-relative module names and as the root directory for `paths` mappings. In TypeScript 7.0, `baseUrl` has been deprecated and removed.

The native Go compiler resolves all `paths` mappings relative to the directory containing the `tsconfig.json` file (or the root `tsconfig` directory).

## The Problem With `baseUrl`

1. **Pollution of Module Resolution**: Setting `"baseUrl": "."` or `"baseUrl": "src"` caused TypeScript to treat every folder in `src` as an ambient top-level module (e.g. `import { foo } from "components/foo"`), which clashed with npm package names and caused silent resolution hijacking.
2. **Ambiguous Bundler Mappings**: Bundlers like Vite, Turbopack, and Webpack required duplicate alias configuration when `baseUrl` was present.

## How to Migrate

### Pattern 1: Absolute / Root-Relative Aliases (Standard)

```json
// BEFORE (Legacy with baseUrl)
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"]
    }
  }
}

// AFTER (Modern TS 7.0 Standard)
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"]
    }
  }
}
```

### Pattern 2: Monorepo Package Mappings

In monorepos with multiple packages:

```json
{
  "compilerOptions": {
    "paths": {
      "@myorg/core": ["./packages/core/src/index.ts"],
      "@myorg/core/*": ["./packages/core/src/*"],
      "@myorg/utils": ["./packages/utils/src/index.ts"],
      "@myorg/utils/*": ["./packages/utils/src/*"]
    }
  }
}
```

### Pattern 3: Bare Imports Without Aliases

If your codebase relied on bare imports like `import utils from "utils/format"` (via `"baseUrl": "./src"`):

1. Replace bare imports with explicit `@/` aliases:
   ```bash
   # Search for bare imports
   grep -rn "from 'utils/" src/
   ```
2. Or define an explicit wildcard path mapping:
   ```json
   {
     "compilerOptions": {
       "paths": {
         "utils/*": ["./src/utils/*"],
         "components/*": ["./src/components/*"]
       }
     }
   }
   ```

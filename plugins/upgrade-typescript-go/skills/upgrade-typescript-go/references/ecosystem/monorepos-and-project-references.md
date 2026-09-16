# Monorepos & Composite Project References

## Overview

In large monorepos (managed with pnpm workspaces, Turborepo, Nx, or Lerna), TypeScript 7.0 provides massive performance improvements when using **Project References** (`"composite": true`) and `tsc --build` (`tsc -b`).

Because Go handles multi-threading and cross-package dependency graphs in native memory, composite project builds that previously took minutes now complete in seconds.

## Monorepo Architecture Patterns

### Pattern A: Internal Package Resolution via `paths`

Best for unified application repositories where all packages are built together:

```json
// root tsconfig.json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "paths": {
      "@myorg/database": ["./packages/database/src/index.ts"],
      "@myorg/database/*": ["./packages/database/src/*"],
      "@myorg/ui": ["./packages/ui/src/index.ts"],
      "@myorg/ui/*": ["./packages/ui/src/*"]
    }
  }
}
```

### Pattern B: Composite Project References (`tsc -b`)

Best for publishing libraries or strict boundary enforcement between packages:

```json
// root tsconfig.json
{
  "files": [],
  "references": [
    { "path": "./packages/database" },
    { "path": "./packages/ui" },
    { "path": "./apps/web" }
  ]
}
```

```json
// packages/database/tsconfig.json
{
  "compilerOptions": {
    "composite": true,
    "declaration": true,
    "declarationMap": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
```

## Turborepo Integration

In `turbo.json`:
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "type-check": {
      "outputs": [".cache/tsbuildinfo/**"],
      "dependsOn": ["^type-check"]
    },
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    }
  }
}
```

## Incremental Build Caches

* Set `"tsBuildInfoFile": ".cache/tsc/package-name.tsbuildinfo"` in each package.
* Ensure `.cache/` is added to `.gitignore`.

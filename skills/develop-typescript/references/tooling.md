# Tooling

Build tools, linters, formatters, and runtime tools for TypeScript projects.

## Build Tool Comparison

| Tool | Use Case | Type Checking | Output Formats | Speed |
|------|----------|---------------|----------------|-------|
| `tsc` | Type check + emit | Full | JS + `.d.ts` | Baseline |
| `tsup` | Library publishing | Via `tsc` for `.d.ts` | ESM, CJS, IIFE | ~5x faster than tsc |
| `tsx` | Dev execution | None (transpile only) | ESM | Near-instant |
| `esbuild` | Bundling | None (transpile only) | ESM, CJS, IIFE | ~50x faster than tsc |
| `swc` | Transpilation | None | ESM, CJS | ~20x faster than tsc |
| `oxc` | Lint + transpile | Partial | ESM | ~100x faster than ESLint |

**Rule**: Always run `tsc --noEmit` separately for type checking. Build tools only transpile — they strip types without checking them.

---

## `tsc` — The TypeScript Compiler

```bash
# Type check only (no output)
tsc --noEmit

# Type check with extended diagnostics
tsc --noEmit --extendedDiagnostics

# Build with incremental compilation
tsc --build --incremental

# Watch mode
tsc --watch --incremental

# Generate declaration files only
tsc --declaration --emitDeclarationOnly
```

### Key flags

```bash
# Generate type trace for performance analysis
tsc --generateTrace ./trace --incremental false
npx @typescript/analyze-trace ./trace

# Increase heap for large projects
NODE_OPTIONS='--max-old-space-size=8192' tsc --noEmit
```

---

## `tsup` — Library Bundler

Zero-config bundler built on esbuild. Best for publishing npm packages.

```bash
npm install -D tsup

# Basic build
tsup src/index.ts

# Dual format with declarations
tsup src/index.ts --format esm,cjs --dts

# With minification
tsup src/index.ts --format esm,cjs --dts --minify
```

### Configuration file

```typescript
// tsup.config.ts
import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm', 'cjs'],
  dts: true,
  sourcemap: true,
  clean: true,
  splitting: false,
  target: 'es2022',
  outDir: 'dist',
  external: ['react', 'react-dom'],
});
```

### Package.json for dual publish

```json
{
  "name": "my-library",
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.js"
      },
      "require": {
        "types": "./dist/index.d.cts",
        "default": "./dist/index.cjs"
      }
    }
  },
  "files": ["dist"]
}
```

---

## `tsx` — TypeScript Execute

Run TypeScript files directly without compilation step.

```bash
npm install -D tsx

# Run a file
tsx src/index.ts

# Watch mode
tsx watch src/index.ts

# Use as Node.js loader
node --import tsx src/index.ts
```

### In package.json scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "start": "tsx src/index.ts",
    "seed": "tsx src/scripts/seed.ts"
  }
}
```

**Note**: `tsx` does not type-check. Use `tsc --noEmit` in CI or as a separate script.

---

## ESLint with `typescript-eslint` v8+

### Flat config setup

```bash
npm install -D eslint @eslint/js typescript-eslint
```

```typescript
// eslint.config.ts
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', '*.config.*'],
  },
);
```

### Recommended rules for strict TypeScript

```typescript
// eslint.config.ts — custom rules on top of strict preset
export default tseslint.config(
  // ...presets above
  {
    rules: {
      // Type safety
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',

      // Import hygiene
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports', fixStyle: 'inline-type-imports' },
      ],
      '@typescript-eslint/no-import-type-side-effects': 'error',

      // Code quality
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/require-await': 'error',

      // Unused variables (allow underscore prefix)
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
);
```

### Legacy `.eslintrc` migration

```bash
# Auto-migrate to flat config
npx @eslint/migrate-config .eslintrc.json
```

---

## Biome — All-in-One Alternative

Fast linter + formatter as an alternative to ESLint + Prettier.

```bash
npm install -D @biomejs/biome

# Initialize config
npx biome init

# Lint and format
npx biome check --write .

# CI check (no writes)
npx biome ci .
```

### Configuration

```json
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/1.9.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "suspicious": {
        "noExplicitAny": "error"
      },
      "style": {
        "useImportType": "error",
        "noNonNullAssertion": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  }
}
```

**Trade-offs**: Biome is 10-50x faster than ESLint but has fewer rules. Missing: type-aware rules (no `no-floating-promises`, `no-unsafe-assignment`). Use Biome for formatting + basic linting, or ESLint for full type-aware analysis.

---

## Prettier

```bash
npm install -D prettier

# Format
npx prettier --write .

# Check (CI)
npx prettier --check .
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

**With ESLint**: Use `eslint-config-prettier` to disable formatting rules in ESLint:

```bash
npm install -D eslint-config-prettier
```

```typescript
// eslint.config.ts
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  // ...other configs
  prettier, // Must be last — disables conflicting rules
);
```

---

## Development Workflow Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsup",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest",
    "ci": "npm run typecheck && npm run lint && npm run test -- --run && npm run build"
  }
}
```

### Pre-commit with lint-staged

```bash
npm install -D husky lint-staged
npx husky init
```

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,yml}": ["prettier --write"]
  }
}
```

---

## Monorepo Tools

### Turborepo

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "lint": {},
    "test": {}
  }
}
```

```bash
# Run build across all packages (respects dependencies)
turbo build

# Run type checking
turbo typecheck

# Run everything in CI
turbo build typecheck lint test
```

### With TypeScript project references

```json
// tsconfig.json (root)
{
  "files": [],
  "references": [
    { "path": "packages/shared" },
    { "path": "packages/api" },
    { "path": "packages/web" }
  ]
}

// packages/api/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "references": [{ "path": "../shared" }]
}
```

Build: `tsc --build` respects dependency order and only rebuilds changed packages.

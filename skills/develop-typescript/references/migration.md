# Migration

Strategies for migrating JavaScript to TypeScript, `any` to strict types, and CJS to ESM.

## JavaScript to TypeScript — Step by Step

### Phase 1: Setup (zero code changes)

```json
// tsconfig.json — start permissive
{
  "compilerOptions": {
    "allowJs": true,
    "checkJs": false,
    "strict": false,
    "noImplicitAny": false,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "rootDir": "src",
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

Install types for dependencies:
```bash
npm install -D typescript @types/node
# For each dependency
npm install -D @types/express @types/lodash
```

### Phase 2: Rename files

Rename `.js` → `.ts` one directory at a time. Start with leaf modules (no dependents).

```
Priority order:
1. Shared types / constants  (no dependencies)
2. Utility functions          (pure functions)
3. Data models                (interfaces/types)
4. Service layer              (business logic)
5. API routes / controllers   (entry points)
6. Tests                      (last — rename .test.js → .test.ts)
```

### Phase 3: Add types incrementally

```typescript
// Start with function signatures — annotate params and returns
// BEFORE (JavaScript)
function getUser(id) {
  return db.findOne({ id });
}

// AFTER (TypeScript — minimal annotations)
function getUser(id: string): Promise<User | null> {
  return db.findOne({ id });
}
```

### Phase 4: Tighten strictness progressively

```json
// Order of enabling flags (fix errors before next flag)
{ "noImplicitAny": true }       // Step 1: forces param annotations
{ "strictNullChecks": true }    // Step 2: catches null/undefined bugs
{ "strict": true }              // Step 3: enables all strict checks
{ "noUncheckedIndexedAccess": true }  // Step 4: array access safety
{ "exactOptionalPropertyTypes": true } // Step 5: strictest optional handling
```

Each flag surfaces errors. Fix them before enabling the next.

---

## `any` to `unknown` Migration

Systematic approach to eliminating `any` from an existing TypeScript codebase.

### Step 1: Find all `any` usage

```bash
# Count any usage
npx tsc --noEmit 2>&1 | grep -c "any"

# Or use ESLint
npx eslint --rule '{"@typescript-eslint/no-explicit-any": "warn"}' src/

# Type coverage report
npx type-coverage --detail --at-least 90
```

### Step 2: Categorize and prioritize

| Category | Example | Fix Strategy |
|----------|---------|-------------|
| Function params | `(data: any)` | Add specific type or `unknown` + guard |
| API responses | `res.data as any` | Add Zod schema validation |
| Third-party types | `(lib as any).method()` | Write `.d.ts` declaration or use `@ts-expect-error` |
| Generic defaults | `<T = any>` | Change to `<T = unknown>` or add constraint |
| Catch variables | `catch (e: any)` | Use `unknown` (default in strict mode) |
| Dynamic access | `obj[key] as any` | Use `Record<string, unknown>` or proper index type |

### Step 3: Fix patterns

```typescript
// API responses — before
async function fetchUser(id: string): Promise<any> {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
}

// API responses — after
interface User {
  id: string;
  name: string;
  email: string;
}

async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  const data: unknown = await res.json();
  return UserSchema.parse(data); // Zod validates at runtime
}
```

```typescript
// Dynamic objects — before
function processConfig(config: any) {
  return config.database.host;
}

// Dynamic objects — after
function processConfig(config: unknown): string {
  if (
    typeof config === 'object' &&
    config !== null &&
    'database' in config &&
    typeof (config as { database: unknown }).database === 'object' &&
    (config as { database: unknown }).database !== null &&
    'host' in (config as { database: object }).database
  ) {
    return (config as { database: { host: string } }).database.host;
  }
  throw new Error('Invalid config structure');
}

// Better — use Zod
const ConfigSchema = z.object({
  database: z.object({ host: z.string() }),
});

function processConfig(config: unknown): string {
  return ConfigSchema.parse(config).database.host;
}
```

---

## CommonJS to ESM Migration

### Step 1: Update package.json

```json
{
  "type": "module"
}
```

### Step 2: Update tsconfig.json

```json
{
  "compilerOptions": {
    "module": "node16",
    "moduleResolution": "node16",
    "verbatimModuleSyntax": true
  }
}
```

### Step 3: Update imports

```typescript
// BEFORE (CJS-style)
const fs = require('fs');
const { readFile } = require('fs/promises');
const config = require('./config');
module.exports = { start };

// AFTER (ESM)
import fs from 'node:fs';
import { readFile } from 'node:fs/promises';
import config from './config.js'; // Note: .js extension required
export { start };
```

### Step 4: Fix common issues

```typescript
// __dirname and __filename don't exist in ESM
// BEFORE
const configPath = path.join(__dirname, 'config.json');

// AFTER
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const configPath = join(__dirname, 'config.json');

// Or simpler with import.meta
const configPath = new URL('./config.json', import.meta.url);
```

```typescript
// require.resolve doesn't exist in ESM
// BEFORE
const modulePath = require.resolve('some-package');

// AFTER
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const modulePath = require.resolve('some-package');
```

```typescript
// JSON imports need import attributes
// BEFORE
const pkg = require('./package.json');

// AFTER
import pkg from './package.json' with { type: 'json' };
```

### File extensions in ESM

```typescript
// With moduleResolution: "node16" — extensions required
import { helper } from './utils.js';     // Even for .ts files
import type { Config } from './types.js'; // Even for .ts files

// With moduleResolution: "bundler" — extensions optional
import { helper } from './utils';
import type { Config } from './types';
```

---

## Declaration Files for Untyped Packages

When no `@types/package` exists, write a minimal declaration file.

```typescript
// src/types/untyped-lib.d.ts
declare module 'untyped-lib' {
  export interface Options {
    timeout?: number;
    retries?: number;
  }

  export function initialize(options?: Options): void;
  export function process(input: string): Promise<string>;

  export default class Client {
    constructor(apiKey: string);
    send(data: unknown): Promise<{ id: string; status: string }>;
    close(): void;
  }
}
```

### For modules with complex shapes

```typescript
// src/types/complex-lib.d.ts
declare module 'complex-lib' {
  namespace ComplexLib {
    interface Config {
      mode: 'development' | 'production';
      plugins: Plugin[];
    }

    interface Plugin {
      name: string;
      setup(api: PluginAPI): void;
    }

    interface PluginAPI {
      onBuild(callback: () => void): void;
      onError(callback: (error: Error) => void): void;
    }
  }

  function createApp(config: ComplexLib.Config): {
    start(): Promise<void>;
    stop(): Promise<void>;
  };

  export = createApp;
}
```

### Wildcard modules

```typescript
// For CSS modules, images, etc.
// src/types/assets.d.ts
declare module '*.css' {
  const classes: Record<string, string>;
  export default classes;
}

declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const src: string;
  export default src;
}
```

---

## Migration Checklist

```
□ Install TypeScript and @types packages
□ Create tsconfig.json with allowJs: true, strict: false
□ Rename files .js → .ts (leaf modules first)
□ Add type annotations to function signatures
□ Enable noImplicitAny → fix errors
□ Enable strictNullChecks → fix errors
□ Enable strict: true → fix errors
□ Replace any with unknown + type guards
□ Add Zod schemas at API boundaries
□ Enable noUncheckedIndexedAccess → fix errors
□ Verify type coverage > 95%
□ Set up ESLint with typescript-eslint
□ Add tsc --noEmit to CI pipeline
```


---

## Handling circular dependencies during migration

### Detection

```bash
# Install detection tools
npx madge --circular --extensions ts src/
# or
npx dpdm --circular --extensions ts src/
```

### Resolution patterns

1. **Extract shared types** — move shared interfaces to a separate `types.ts` file imported by both modules
2. **Dependency inversion** — depend on interfaces, not concrete implementations
3. **Barrel file splitting** — replace `index.ts` re-exports with direct imports to break cycles
4. **Lazy imports** — use dynamic `import()` for runtime-only dependencies

```typescript
// BEFORE — circular: a.ts imports b.ts, b.ts imports a.ts
// a.ts
import { B } from "./b";
export class A { constructor(public b: B) {} }

// AFTER — extract shared interface
// types.ts
export interface IB { name: string; }
// a.ts
import type { IB } from "./types";
export class A { constructor(public b: IB) {} }
```

---

## Automation tools for migration

| Tool | Purpose | Use when |
|---|---|---|
| `ts-migrate` (Airbnb) | Bulk JS-to-TS conversion | Large JS codebase, want automated first pass |
| `jscodeshift` | AST-based code transforms | Need custom codemods (rename, restructure) |
| `tsc --allowJs --checkJs` | Incremental type checking | Want to type-check JS files before renaming |
| `@ts-check` comment | Per-file JS type checking | Gradual migration, file by file |

```bash
# ts-migrate: automated first pass
npx ts-migrate-full ./src

# jscodeshift: custom transform
npx jscodeshift -t transform.ts --extensions=ts src/
```

---

## Test file migration

### Rename patterns

```bash
# Rename test files from .js to .ts
find test/ -name "*.test.js" -exec bash -c 'mv "$0" "${0%.js}.ts"' {} \;
find test/ -name "*.spec.js" -exec bash -c 'mv "$0" "${0%.js}.ts"' {} \;
```

### Mock typing

```typescript
// BEFORE — untyped mock
jest.mock("./api");
const mockFetch = api.fetch as jest.Mock;

// AFTER — typed mock with jest.Mocked
jest.mock("./api");
const mockedApi = jest.mocked(api); // fully typed
mockedApi.fetch.mockResolvedValue({ data: [] });
```

### Test utility typing

```typescript
// Type-safe test fixtures
function createTestUser(overrides?: Partial<User>): User {
  return {
    id: "test-1",
    name: "Test User",
    email: "test@example.com",
    ...overrides,
  };
}
```

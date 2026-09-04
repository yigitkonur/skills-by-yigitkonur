# Type Safety and Strictness Protocol

Engineering standards for eliminating untyped surfaces, executing incremental strict-mode migrations, and tidying structural type debt during TypeScript cleanup passes.

---

## 1. Type Safety Architecture

Dead-code removal and export pruning directly alter TypeScript symbol resolution. Stripping an `export` keyword from an unreferenced type or interface can break downstream declaration emit (`.d.ts`), destabilize monorepo project references (`tsc -b`), or mask creeping `any` types in newly private helper functions.

Type safety remediation proceeds under a defensive contract that balances dead-code elimination against compiler guarantees:

```
+-------------------------------------------------------------------------------+
|                       TYPE SAFETY & STRICTNESS PROTOCOL                       |
+-------------------------------------------------------------------------------+
| 1. ANY-CREEP ELIMINATION                                                      |
|    - Measure untyped surfaces; ratchet the score upward, never down           |
|    - Replace loose 'any' with 'unknown' or narrow inferred types              |
| 2. DECLARATION EMIT SAFETY                              -> declaration-emit.md|
|    - Guard public signatures against un-exported constituent types            |
| 3. INCREMENTAL STRICT MODE MIGRATION                                          |
|    - File-by-file ratchet: scoped tsconfig.strict.json whitelist              |
|    - Flag-by-flag progression: noImplicitAny -> strictNullChecks -> ...       |
| 4. TYPE TIDYING RULES                                                         |
|    - Convert overlapping unions into discriminated unions                     |
|    - Strip obsolete aliases, identity wrappers, dead interface extensions     |
+-------------------------------------------------------------------------------+
```

---

## 2. Eliminating Any-Creep

### The Mechanism of Any Contagion

The `any` type disables compile-time typechecking across all downstream call sites. An `any` parameter or return value infects every variable assigned from it, disables member-access checks, permits arbitrary property mutation, and silently bypasses function signature contracts.

Cleanup passes actively manufacture `any`. Internalizing a public export into a private function tempts developers and automated tools to degrade a specific parameter type to `any` to silence a local type mismatch. That converts static dead code into a runtime defect — a strictly worse outcome than leaving the export in place.

### Ratcheting the Type Coverage Score

Measure the percentage of typed identifiers before and after every cleanup wave. Use one canonical invocation:

```bash
npx type-coverage --at-least 95 --strict --detail
```

Apply the score as a one-way ratchet:

1. Record the pre-cleanup percentage as the floor before touching any file.
2. Fail the wave if the post-wave percentage drops below the floor — a decrease means the cleanup traded dead code for untyped code.
3. Raise `--at-least` to the new percentage after any wave that improves it. Never lower it to make CI green.
4. Pin the threshold in CI so the floor is enforced on every pull request, not only during cleanup work.

For install, flag surface, output parsing, and hotspot ranking, see [`../engines/analysis-engines.md`](../engines/analysis-engines.md).

### Replacing Loose `any` in Private Functions

Never accept `any` as a parameter type, return type, or variable annotation in private or newly internalized functions. Apply this replacement ladder in order and stop at the first match:

| # | Condition | Replacement |
|---|---|---|
| 1 | Type is inferable from the assignment or literal | Delete the annotation; let TypeScript infer the narrow type |
| 2 | Value is dynamic, untrusted external input (HTTP, JSON, DOM, storage) | `unknown` plus a narrowing guard before every consumption |
| 3 | Value is a generic dictionary or key-value lookup | `Record<string, unknown>` — never `Record<string, any>` |
| 4 | Value is a callback or function reference | `(...args: unknown[]) => unknown`, or an explicit call signature |
| 5 | None of the above | Define an explicit type alias or discriminated union |

#### Pattern 1: External Input (HTTP, JSON, LocalStorage)

**Anti-pattern (loose `any`):**
```typescript
function parseUserData(rawPayload: any) {
  return {
    id: rawPayload.id.toUpperCase(),          // Runtime crash if id is undefined
    email: rawPayload.email,
    roles: rawPayload.roles.map((r: any) => r.name), // Crash if roles is not an array
  };
}
```

**Remediation (narrowed `unknown` with guards):**
```typescript
interface UserData {
  id: string;
  email: string;
  roles: string[];
}

function isRecord(val: unknown): val is Record<string, unknown> {
  return typeof val === 'object' && val !== null && !Array.isArray(val);
}

function parseUserData(rawPayload: unknown): UserData {
  if (!isRecord(rawPayload) || typeof rawPayload.id !== 'string' || typeof rawPayload.email !== 'string') {
    throw new TypeError('Invalid user payload structure');
  }

  const roles = Array.isArray(rawPayload.roles)
    ? rawPayload.roles.filter((r): r is string => typeof r === 'string')
    : [];

  return { id: rawPayload.id.toUpperCase(), email: rawPayload.email, roles };
}
```

#### Pattern 2: Dictionary Indexing and Property Bags

`Record<string, any>` disables typechecking for every property of the bag. Switch the index signature to `unknown` and narrow at the point of use:

```typescript
// Anti-pattern: options: Record<string, any> -- every value is untyped
function applyConfig(target: HTMLElement, options: Record<string, unknown>) {
  for (const [key, value] of Object.entries(options)) {
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      target.setAttribute(key, String(value));
    }
  }
}
```

#### Pattern 3: Catch Variables and Unknown Errors

Under `"useUnknownInCatchVariables": true` (implied by `"strict": true` in TS 4.4+), caught exceptions are typed `unknown`. Never widen them back with `catch (e: any)` or `(e as any).message`.

```typescript
try {
  executeTask();
} catch (e: unknown) {
  // Anti-pattern: catch (e: any) then read e.message / e.stack directly
  const message = e instanceof Error ? e.message : String(e);
  const stack = e instanceof Error ? e.stack : undefined;
  logger.error(message, { stack });
}
```

---

Before stripping any `export` keyword, clear the declaration emit gate in [`./declaration-emit.md`](./declaration-emit.md) — a type that is private in the module body can still be illegal in the emitted `.d.ts`.

---

## 3. Incremental Strict Mode Migration

Migrating a large legacy repository to full strictness (`"strict": true`) cannot land in a single commit. Enabling strict mode at once produces hundreds or thousands of compiler errors and halts active development.

Choose one of two structured models — never mix them in the same package:

| Attribute | File-by-File Ratchet | Flag-by-Flag Progression |
|---|---|---|
| **Migration axis** | Vertical: file-by-file, module-by-module | Horizontal: compiler flag by compiler flag |
| **Active flags** | All strict flags enabled at once, on migrated files only | One flag enabled at once, across all files |
| **Configuration** | Dual config: `tsconfig.json` + `tsconfig.strict.json` | Single `tsconfig.json` plus a suppression baseline |
| **Regression defense** | Whitelist in `tsconfig.strict.json` only ever grows | CI error/suppression count ceiling that only ever shrinks |
| **Best for** | Monorepos, large apps with active feature teams, legacy code | Compact codebases, shared utility libraries, core modules |

---

### Model A: The File-by-File Ratchet

Partition the repository into legacy non-strict code and strictly typed code. A secondary configuration applies maximum strictness to a whitelisted set of files. CI guarantees that once a file enters the whitelist it can never regress, and that all newly created files pass strict checks immediately.

#### Step 1: Create `tsconfig.strict.json`

Inherit the base configuration, activate full strictness, and declare an explicit `include` array:

```jsonc
// tsconfig.strict.json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  },
  "include": [
    // Monotonically increasing whitelist of strict-compliant files
    "src/utils/**/*.ts",
    "src/types/**/*.ts",
    "src/features/auth/**/*.ts"
  ]
}
```

#### Step 2: Run Both Configurations in CI

```bash
# 1. Verify the legacy baseline still passes
npx tsc --project tsconfig.json --noEmit

# 2. Verify every migrated file passes strict rules
npx tsc --project tsconfig.strict.json --noEmit
```

#### Step 3: Enforce New Files Into the Whitelist

```bash
#!/usr/bin/env bash
# scripts/verify-strict-ratchet.sh
set -euo pipefail

# Newly added TypeScript files relative to the default branch
NEW_FILES=$(git diff --name-only --diff-filter=A origin/main...HEAD | grep -E '\.(ts|tsx)$' || true)

if [ -n "$NEW_FILES" ]; then
  echo "Checking new files against tsconfig.strict.json..."
  for FILE in $NEW_FILES; do
    if ! grep -q "$FILE" tsconfig.strict.json; then
      echo "ERROR: New file '$FILE' must be included in tsconfig.strict.json and meet strict standards."
      exit 1
    fi
  done
fi

npx tsc --project tsconfig.strict.json --noEmit
echo "Strict ratchet verification passed."
```

Expand the whitelist with directory globs, not individual paths, once a directory is fully migrated. Move a directory into the whitelist in its own commit so a revert is surgical.

---

### Model B: The Flag-by-Flag Progression

Activate strict compiler flags horizontally across the entire codebase, one flag at a time, in an order that minimizes churn. Land each phase as an isolated commit.

| Phase | Flag(s) | What it surfaces |
|---|---|---|
| 1 | `noImplicitAny` | Untyped parameters, empty collection literals, unannotated callbacks |
| 2 | `strictNullChecks` | Unguarded access to nullable values; the largest error volume by far |
| 3 | `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`, `alwaysStrict` | Variance violations, uninitialized class fields, floating `this` |
| 4 | `noUncheckedIndexedAccess` | Array and record indexing that assumes presence |
| 5 | `exactOptionalPropertyTypes`, then `"strict": true` | Missing keys conflated with explicit `undefined` |

#### Phase 1 — `noImplicitAny`
- **Targets**: functions without parameter types, empty array initialization (`const list = []`), unannotated catch parameters.
- **Fixes**: add explicit parameter types; type empty collections (`const list: string[] = []`); replace un-inferred callback arguments with typed parameters or `unknown`.

#### Phase 2 — `strictNullChecks`
- **Targets**: object access on potentially undefined values (`user.profile.name`), `.find()` results consumed without a null guard.
- **Fixes**: optional chaining (`user?.profile?.name`); nullish coalescing for defaults (`options.timeout ?? 3000`); early return guards (`if (!user) return;`).
- Do not use non-null assertions (`!`) to silence errors unless the line is immediately preceded by an explicit invariant guard.

#### Phase 3 — core strict family
- **Targets**: contravariant parameter assignments, uninitialized class fields, unbound `this` in extracted methods.
- **Fixes**: narrow handler signatures; use definite assignment (`declare`/constructor init) rather than `!` on fields; bind or arrow-wrap detached methods.

#### Phase 4 — `noUncheckedIndexedAccess`
- **Targets**: dynamic lookups `record[key]` and numeric indexing `items[0]`, which now evaluate to `T | undefined` instead of `T`.
- **Fixes**: check existence before access, or use `Map.has()` / the `in` operator for dictionaries.

```typescript
// Before: assumes index 0 exists -- Error: 'first' is possibly 'undefined'
const first = items[0];
if (first !== undefined) {
  first.toLowerCase();
}

// Dictionaries: prove presence before consuming
if (key in record && record[key] !== undefined) {
  process(record[key]);
}
```

#### Baselining and Burn-Down

When enabling a flag produces more than 100 errors, do not abandon the flag. Baseline the existing errors with tagged `@ts-expect-error` suppressions so no new violation can enter:

```typescript
// @ts-expect-error [MIGRATION-STRICT-NULL]: Burn-down tracked in #1042
const user = users.find(u => u.id === id);
return user.name;
```

Every suppression carries a migration tag and links to a tracking issue. Untagged suppressions are indistinguishable from ordinary debt and never get removed.

Enforce a shrinking ceiling in CI:

```bash
# Count active migration suppressions
SUPPRESSION_COUNT=$(rg -c "@ts-expect-error \[MIGRATION-" src/ | awk -F: '{s+=$2} END {print s+0}')
echo "Current strict debt baseline: $SUPPRESSION_COUNT"

# Fail if new suppressions are introduced above the tracked ceiling
MAX_ALLOWED=42
if [ "$SUPPRESSION_COUNT" -gt "$MAX_ALLOWED" ]; then
  echo "ERROR: Strict debt increased ($SUPPRESSION_COUNT > $MAX_ALLOWED). Fix existing errors instead of adding suppressions."
  exit 1
fi
```

Lower `MAX_ALLOWED` in the same commit that removes suppressions. `@ts-expect-error` fails the build once the underlying error is fixed, which makes stale suppressions self-reporting.

---

## 4. Type Tidying Rules

Apply during Wave 5 (Unused Type Pruning): tidy residual type structures, eliminate redundant indirection, and convert ambiguous unions into discriminated types.

### Rule 1: Convert Overlapping Unions Into Discriminated Unions

Untagged object unions with overlapping optional properties create ambiguous inference, force runtime `in` checks, and permit invalid state combinations.

**Anti-pattern — ambiguous optional property bag:**
```typescript
// Permits invalid states, e.g. status: 'loading' carrying an error.
// Every consumer needs a non-null assertion: res.data!.id
type AsyncRequest = {
  status: 'idle' | 'loading' | 'success' | 'error';
  data?: Record<string, unknown>;
  error?: Error;
  startedAt?: number;
};
```

**Remediation — discriminated union with a single literal tag:**
```typescript
type AsyncRequest =
  | { status: 'idle' }
  | { status: 'loading'; startedAt: number }
  | { status: 'success'; data: Record<string, unknown> }
  | { status: 'error'; error: Error };

function handleResponse(res: AsyncRequest) {
  switch (res.status) {
    case 'idle':
      return;
    case 'loading':
      console.log(`Loading since ${res.startedAt}`);
      return;
    case 'success':
      console.log(res.data); // Narrowed, guaranteed present
      return;
    case 'error':
      console.error(res.error.message);
      return;
    default: {
      // Compile-time exhaustiveness: fails if a new state is added to AsyncRequest
      const _exhaustiveCheck: never = res;
      throw new Error(`Unhandled async state: ${JSON.stringify(_exhaustiveCheck)}`);
    }
  }
}
```

### Rule 2: Strip Obsolete Type Aliases

#### Case A — non-branded identity wrappers

Delete plain identity wrappers. They add zero type safety and obscure native methods. Keep only true nominal brands:

```typescript
// Obsolete
type StringId = string;
type Username = string;
type Timestamp = number;

// Keep only if genuinely nominal
type UserId = string & { readonly __brand: unique symbol };
function createUserId(id: string): UserId {
  return id as UserId;
}
```

#### Case B — re-exported third-party wrapper aliases

Delete any alias that exists solely to rename a third-party type without adding fields or constraints; import the upstream type directly at call sites.

```typescript
// Dead indirection
import type { RequestOptions as AxiosRequestOptions } from 'axios';
export type ApiRequestConfig = AxiosRequestOptions;
```

#### Case C — merging duplicate representations

Dismantle parallel structures left by half-finished refactors (`UserDTO`, `IUser`, `UserData`):

1. Compare the field schemas of every parallel representation.
2. If fields are identical or overlap ≥90%, designate one canonical domain type.
3. Rewrite call sites to the canonical type or a utility variation (`Pick<User, 'id' | 'email'>`, `Omit<User, 'passwordHash'>`).
4. Delete the duplicates.

### Rule 3: Clean Up Unused Interface Extensions

#### Case A — empty interface extensions

Empty interfaces (`interface Props extends BaseProps {}`) create dead AST nodes and trigger `@typescript-eslint/no-empty-interface` / `no-empty-object-type`. Delete the interface and repoint callers at the parent, or collapse it to an alias when the name carries semantics:

```typescript
// Before
interface PrimaryButtonProps extends ButtonBaseProps {}

// After
type PrimaryButtonProps = ButtonBaseProps;
```

#### Case B — dead multi-inheritance chains

When an interface extends a parent whose properties are never read, unwire the chain:

```typescript
interface Auditable { createdBy: string; createdAt: Date }

interface LegacyCacheable {
  cacheTtl: number;
  evictionPolicy: string; // Dead feature, never read
}

interface UserProfile extends Auditable, LegacyCacheable {
  name: string;
}
```

1. Confirm the unused-export report flags the parent's members as unreferenced.
2. Remove the parent from the `extends` clause.
3. Delete the parent interface once all consumers are disconnected.

#### Case C — redundant `Record<string, any>` extensions

Never let an interface extend `Record<string, any>`. It disables typechecking for the whole interface and lets any nonexistent property resolve silently.

```typescript
// Anti-pattern: every typo compiles
interface UserSettings extends Record<string, any> {
  theme: 'dark' | 'light';
  notifications: boolean;
}
console.log(settings.nonExistentKey); // Compiles; undefined at runtime

// Remediation: drop the index signature; isolate dynamic keys
interface UserSettings {
  theme: 'dark' | 'light';
  notifications: boolean;
  metadata?: Record<string, unknown>;
}
```

---

Run the canonical verification gate in [`../remediation/waves.md`](../remediation/waves.md) before committing any wave; run [`./declaration-emit.md`](./declaration-emit.md) §5 for the type-specific declaration emit checks it invokes.

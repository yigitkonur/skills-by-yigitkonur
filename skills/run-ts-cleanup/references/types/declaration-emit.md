# Declaration Emit Safety

Gate for un-exporting and pruning types without breaking `.d.ts` generation: the TS4023/TS4081/TS4082/TS4060/TS2742/TS2883 diagnostic matrix, emit-only verification commands, and the pre-un-export checklist.

---

## 1. When This Gate Applies

Run this gate before committing any change that strips an `export` keyword or deletes a type declaration — Wave 4 (Internalizing Exports) and Wave 5 (Unused Type Pruning) in [`../remediation/waves.md`](../remediation/waves.md).

Declaration emit risk activates when any of these conditions hold:

| Condition | tsconfig / package signal | Verification command |
|---|---|---|
| Project emits declaration files | `"declaration": true`, `"emitDeclarationOnly": true` | `tsc --declaration --emitDeclarationOnly --noEmit` |
| Package is a composite project reference | `"composite": true` | `tsc -b --noEmit` |
| Project enforces isolated declarations (TS 5.5+) | `"isolatedDeclarations": true` | `tsc --isolatedDeclarations --noEmit` |
| Package ships types to consumers | `package.json` `"types"`, `"typings"`, or `exports["."].types` | `tsc --declaration --emitDeclarationOnly --noEmit` |

Detect exposure before assuming the gate is optional:

```bash
# Any tsconfig that turns on declaration-graph checking, or package that ships .d.ts
rg -l '"(declaration|emitDeclarationOnly|composite|isolatedDeclarations)"\s*:\s*true' -g 'tsconfig*.json'
rg -l '"(types|typings)"\s*:' -g 'package.json'
```

Zero hits on both: treat this gate as advisory and rely on `tsc --noEmit`. Any hit: treat this gate as mandatory for every export-pruning commit.

---

## 2. The Un-Exported Dependency Crash Mechanism

`tsc --noEmit` typechecks the *implementation* graph. It never builds the *declaration* graph. A type can be simultaneously legal inside a module body and illegal in that module's emitted `.d.ts` public declaration table — the compiler only discovers the contradiction when asked to emit.

Unused-export analysis reports a type referenced only inside its defining module as an unused export:

```
Unused exports:
  src/services/user.ts: interface UserInternalConfig
```

Stripping the `export` keyword produces code that typechecks and crashes on emit:

```typescript
// src/services/user.ts
// 'export' stripped: no other file imports UserInternalConfig by name.
interface UserInternalConfig {
  retries: number;
}

// Still public -- and its signature now references a private symbol.
export function createUserService(config?: UserInternalConfig) {
  return { retries: config?.retries ?? 3 };
}
```

Failure surface:

- `tsc --noEmit` passes.
- `tsc --declaration --emitDeclarationOnly --noEmit` fails: `user.d.ts` cannot name `UserInternalConfig`.
- `tsc -b` fails for every downstream package in the project-reference graph, not just the edited one.
- `isolatedDeclarations` fails because a per-file emitter cannot resolve the symbol without whole-program inference.

Hold this invariant: **every type reachable from an exported signature is part of the public API, regardless of whether any file imports it by name.** Unused-export analysis measures name-level imports; declaration emit measures signature reachability. The two disagree, and the compiler wins.

---

## 3. Diagnostic Code Matrix

| Error Code | Official Diagnostic Message | Root Trigger During Cleanup | Deterministic Remediation |
|---|---|---|---|
| **TS4023** | `Exported variable '{0}' has or is using name '{1}' from external module '{2}' but cannot be named.` | Inferred variable type relies on a type from a dependency not exported or imported in public scope. | Annotate the exported variable explicitly with an exported type. |
| **TS4081** | `Exported type alias '{0}' has or is using private name '{1}'.` | `export` stripped from an interface/type referenced by an exported type alias. | Re-export `{1}`, or inline its structural definition into `{0}`. |
| **TS4082** | `Default export of the module has or is using private name '{0}'.` | `export` stripped from a type returned by or passed into `export default function`. | Export `{0}`, or annotate the default export with a public contract. |
| **TS4060** | `Return type of exported function has or is using private name '{0}'.` | `export` stripped from the return type of a public function. | Restore `export` on `{0}`, or narrow the function to return a primitive or public interface. |
| **TS2742** | `The inferred type of '{0}' cannot be named without a reference to '{1}'. This is likely not portable.` | Return type inferred from a transitive package or unexported local symbol under pnpm/monorepo node_modules layouts. | Add an explicit return type annotation to the public symbol; never rely on inference across package boundaries. |
| **TS2883** | `Type alias '{0}' refers to type '{1}' but is not exported.` | A private symbol leaks through an alias under `isolatedDeclarations: true`. | Export `{1}` directly, or rewrite `{0}` to avoid referencing private types. |

Map each code to its owner: TS4060/TS4081/TS4082 come from stripping `export` (Wave 4/5 regressions — revert or re-export). TS4023/TS2742 come from missing explicit annotations (annotate, do not re-export). TS2883 is `isolatedDeclarations`-only.

---

## 4. Failure Scenarios and Fixes

### Scenario 1: TS4060 / TS4081 — Internalized Return Type

**Breaking code (after a naive export strip):**
```typescript
// src/client.ts
// 'export' stripped because no other file imported ClientOptions directly:
interface ClientOptions { endpoint: string; timeoutMs: number }

// CRASH: TS4060: Return type of exported function has or is using private name 'ClientOptions'.
export function getDefaultOptions(): ClientOptions {
  return { endpoint: 'https://api.internal', timeoutMs: 5000 };
}
```

**Fix A — restore the export and declare it a public contract:**
```typescript
export interface ClientOptions { endpoint: string; timeoutMs: number }
```
Record `ClientOptions` as an intentional public export in the analysis engine's ignore list so the next pass does not re-flag it. See [`../engines/knip-configuration.md`](../engines/knip-configuration.md).

**Fix B — inline the structure when the named type is genuinely dead:**
```typescript
export function getDefaultOptions(): { endpoint: string; timeoutMs: number } {
  return { endpoint: 'https://api.internal', timeoutMs: 5000 };
}
```
Choose Fix B only when the shape is small (≤3 members) and referenced by exactly one signature; otherwise the inline literal duplicates on the next signature that needs it.

### Scenario 2: TS4082 — Private Name in a Default Export

**Breaking code:**
```typescript
// src/plugin.ts
interface PluginContext { logger: Console }

// CRASH: TS4082: Default export of the module has or is using private name 'PluginContext'.
export default function createPlugin(ctx: PluginContext) {
  return { name: 'plugin', ctx };
}
```

**Fix — export every constituent type and annotate the return value:**
```typescript
export interface PluginContext { logger: Console }
export interface Plugin { name: string; ctx: PluginContext }

export default function createPlugin(ctx: PluginContext): Plugin {
  return { name: 'plugin', ctx };
}
```

Default exports are the highest-risk surface: their inferred type has no name to fall back on, so both the parameter and the return type must resolve to exported symbols.

### Scenario 3: TS2742 — Transitive Inferred Types in Monorepos

Triggered by ORMs (Prisma, Drizzle), schema validators (Zod, Valibot), and router generators (tRPC) whose types resolve through a nested `node_modules` path that the consuming package cannot name.

**Breaking code:**
```typescript
// packages/api/src/router.ts
import { z } from 'zod';

export const userSchema = z.object({
  id: z.string().uuid(),
  displayName: z.string(),
});

// CRASH: TS2742: The inferred type of 'parseUser' cannot be named without a reference to
// 'packages/api/node_modules/zod/lib/types'. A type annotation is necessary.
export const parseUser = (input: unknown) => userSchema.parse(input);
```

**Fix — name the inferred type, then annotate the public symbol:**
```typescript
import { z } from 'zod';

export const userSchema = z.object({
  id: z.string().uuid(),
  displayName: z.string(),
});

export type User = z.infer<typeof userSchema>;

export const parseUser = (input: unknown): User => userSchema.parse(input);
```

Structural fixes when annotation is impractical: hoist the offending dependency to the workspace root so a single copy resolves (`pnpm.overrides`, `resolutions`), or add the package to `compilerOptions.paths` so the emitted path is nameable from the consumer.

### Scenario 4: TS2883 — Private Leak Under `isolatedDeclarations`

**Breaking code:**
```typescript
// src/config.ts
type InternalShape = { retries: number };

// CRASH: TS2883 under "isolatedDeclarations": true
export type PublicConfig = InternalShape & { name: string };
```

**Fix — export the constituent, or flatten the alias:**
```typescript
export type PublicConfig = { retries: number; name: string };
```

Under `isolatedDeclarations`, every exported symbol needs an explicit, locally-resolvable type. Add explicit return type annotations to all exported functions before enabling the flag, not after.

---

## 5. Declaration Emit Verification Workflow

`tsc --noEmit` does not check declaration emit unless combined with `--declaration` or `--isolatedDeclarations`. Execute declaration-specific verification before committing any export-pruning wave:

```bash
# 1. Single project: build the declaration graph without writing files to disk
npx tsc --declaration --emitDeclarationOnly --noEmit

# 2. Composite monorepo: rebuild the full project-reference graph from scratch
#    (--clean is mandatory; stale .tsbuildinfo masks fresh emit failures)
npx tsc -b --clean && npx tsc -b --noEmit

# 3. Isolated declarations (TypeScript 5.5+): verify swc/esbuild/oxc can emit .d.ts per file
npx tsc --isolatedDeclarations --noEmit
```

Diagnose a failure without hunting through build output:

```bash
# List only declaration-emit diagnostics, deduplicated by file
npx tsc --declaration --emitDeclarationOnly --noEmit 2>&1 \
  | rg 'TS(4023|4060|4081|4082|2742|2883)' \
  | sort -u
```

Install the checks as first-class scripts so CI and pre-commit hooks run them unconditionally:

```json
// package.json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "typecheck:emit": "tsc --declaration --emitDeclarationOnly --noEmit",
    "typecheck:build": "tsc -b --noEmit"
  }
}
```

---

## 6. Pre-Un-Export Checklist

Apply to every type symbol before stripping its `export`:

1. **Confirm no exported signature in the same module names the symbol.** Grep first as a cheap pre-filter; the compiler remains the authority.
   ```bash
   SYMBOL=UserInternalConfig
   rg -n --multiline "export[^\n]*\b${SYMBOL}\b" src/
   ```
2. **Confirm no exported symbol *infers* the type.** Un-annotated `export const` and `export function` leak inferred types that grep cannot see. Add an explicit annotation to any exported symbol whose type is inferred from the candidate, then re-check.
3. **Confirm the type is absent from `.d.ts` output.** Emit once and grep the artifact — the definitive test that a symbol is not part of the published surface.
   ```bash
   npx tsc --declaration --emitDeclarationOnly --outDir /tmp/dts-probe
   rg -n "\b${SYMBOL}\b" /tmp/dts-probe/
   ```
   Any hit: the symbol is public. Do not un-export it; register it as an intentional export instead.
4. **Strip the `export` keyword.**
5. **Re-run the full verification workflow from §5** — all three commands, not just `tsc --noEmit`.
6. **On failure, choose one remediation and never a suppression.** Restore the `export`, inline the structural type, or add an explicit annotation. `// @ts-ignore` and `// @ts-expect-error` cannot suppress declaration emit errors; they are emitted by the declaration emitter, not the checker.

Do not commit while any command in §5 fails. A green `tsc --noEmit` alongside a red `tsc -b` means the regression is already in the working tree and will surface in consumer packages, not this one.

Run these checks inside the canonical verification gate in [`../remediation/waves.md`](../remediation/waves.md); for any-creep elimination, strict-mode migration, and type tidying, see [`./strict-migration.md`](./strict-migration.md).

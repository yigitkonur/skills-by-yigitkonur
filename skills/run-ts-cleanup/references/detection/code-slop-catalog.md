# Code Slop and Bloat Taxonomy

The comprehensive catalog of removable bloat and agent anti-patterns this skill targets. Section 1 establishes **The 4 Pillars Mental Model** and **architectural origins**. Section 2 specifies **The Taxonomy of Agent Bloat (7 Patterns)** and code-level slop signatures with ripgrep detection and deterministic remediation. Section 3 is the executable audit sweep.

---

## 1. The 4 Pillars Mental Model & Architectural Origins

A true TypeScript cleanup is not merely running `knip` and deleting lines. A production-grade TypeScript cleanup operates across four architectural pillars that govern maintainability, compile-time soundness, and runtime stability:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE 4 PILLARS OF TYPESCRIPT CLEANUP                  │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 1. Reachability & Dead Code      │ 2. Encapsulation & Boundaries       │
│    (Graph Layer)                 │    (Interface & Visibility Layer)   │
│    • Unreferenced files          │    • Test-only leak containment     │
│    • Orphaned dependencies       │    • In-file private internalization│
│    • Abandoned zombie features   │    • Public API designation (!)     │
├──────────────────────────────────┼─────────────────────────────────────┤
│ 3. Type Rigor & Soundness        │ 4. Module & Graph Health            │
│    (Semantic & Inference Layer)  │    (Architecture & Build Layer)     │
│    • Ban type laundering (as any)│    • Eliminate barrel smog          │
│    • Schema-type single source   │    • Break import cycles (dpdm)     │
│    • Declaration emit safety     │    • Deterministic lockfile sync    │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Architectural Origins

Dead-code engines report symptoms: unused files, dead exports, orphaned dependencies. The origin determines the correct deletion unit. Pruning a single flagged export out of a zombie feature leaves the rest of the corpse in the tree; deleting the whole feature directory resolves dozens of findings at once.

| Origin | Typical Engine Report | Correct Deletion Unit |
|---|---|---|
| **A. Zombie feature / dead experiment** | Unreferenced files, unused exports, orphaned deps | The whole feature directory + its flag, fixtures, schema |
| **B. LLM generation without cross-file memory** | Duplicate unreferenced exports, single-file exports, type laundering | The duplicate implementation & anti-patterns (see §2) |
| **C. Barrel inflation & circular webs** | Nothing (transitive masking) — cycles found by `madge`/`dpdm` | The `export *` statement, not the module behind it |
| **D. Half-finished refactor / dual abstraction** | Unused dependency, unreferenced adapter files | The minority library and every call site that reaches it |

---

### Origin A: Zombie Features & Abandoned Experiments

Features shipped behind an A/B test or remote flag (LaunchDarkly, Statsig, Unleash, PostHog) get switched off in the dashboard. The code stays in the repository forever, because nothing in the build ever proves the branch is dead.

Indicators:
- Code paths guarded by a permanently disabled flag, whose only caller is the branch itself:
  ```typescript
  if (FLAGS.ENABLE_EXPERIMENTAL_DISCOUNT_ENGINE_V2) {
    return calculateExperimentalDiscount(cart); // sole call site in repo
  }
  ```
- The engine flags `calculateExperimentalDiscount` as an unused export, or the entire `src/features/experimental-discounts/` directory as unreferenced, once the flag is statically resolved or removed.
- Database models or migrations with zero references outside the migration folder.

Remediate:
1. Audit every flag against the production flag dashboard or analytics. Treat "disabled for > 1 release cycle" as dead.
2. Delete the conditional branch, then the feature directory outright (`git rm -r src/features/experimental-discounts`).
3. Delete the paired test fixtures, mocks, MSW handlers, and schema models.
4. Re-run the dead-code engine to sweep the sub-dependencies the feature was the last consumer of.

---

### Origin B: LLM Generation Without Cross-File Memory

A model generating a component or endpoint cannot see the rest of the repository. It re-derives helpers locally, wraps calls defensively, and narrates its own output in comments. This origin does not have its own remediation: **its code-level signature is the entire pattern list in Section 2**, and its highest-volume manifestation is Pattern 7 (Utility Duplication).

Suspect this origin when a diff shows any of: multiple `formatDate` definitions in unrelated directories, `try/catch` blocks that only re-throw, `as any` at internal boundaries, or a file whose comment-to-code ratio exceeds 1:3.

---

### Origin C: Barrel Inflation & Circular Webs

An `index.ts` in every directory, each glob re-exporting its siblings:

```typescript
// src/components/index.ts
export * from './Button';
export * from './Modal';
export * from './Card';
```

Consequences:
- **Tree-shaking defeat**: bundlers cannot prune re-exported modules once CommonJS interop or side effects are in play.
- **Cycles**: `Button` imports a helper from `index.ts`, `index.ts` exports `Button` — `Button -> index -> Button`, and the module initializes as `undefined` at runtime.
- **Transitive masking**: dead exports hidden behind `export *` look consumed to a graph scanner while still costing bundle size.

Detect:
```bash
npx madge --circular --extensions ts,tsx src/
npx dpdm --circular --warning=false ./src/index.ts
rg -n 'export \* from' src/
```

Remediate per the barrel and cycle protocols in [../remediation/structural-refactor.md](../remediation/structural-refactor.md). The short version: replace `export *` with explicit named re-exports, and ban modules from importing siblings through their own directory barrel.

---

### Origin D: Half-Finished Refactors & Dual Abstractions

A migration (Axios to Ky, Redux to Zustand, Moment to date-fns) stalls at 60%. Both libraries and both patterns then coexist for years, each keeping the other's adapter code alive.

Indicators:
- Competing libraries in one `package.json`: `axios` **and** `ky`; `lodash` **and** `lodash-es`; `date-fns` **and** `dayjs` **and** `moment`.
- Shadow directories: `src/components/v1/` beside `src/components/v2/`.
- An adapter or "compat" module whose only purpose is translating between the two.

Remediate:
```bash
# Rank call-site volume to pick the survivor
rg -c "from 'axios'" src/
rg -c "from 'ky'" src/
```
1. Convert the minority library's call sites to the survivor.
2. Remove the superseded package (`pnpm remove axios`) and delete the compat adapter.
3. Re-run the engine to catch stranded types and now-orphaned wrapper files.

---

### 2. The Taxonomy of Agent Bloat (7 Core Patterns)

When AI agents write and refactor TypeScript, they introduce systemic bloat resulting from bounded context windows, lack of cross-file memory, and optimization pressure to "make the compiler green" at all costs. These 7 patterns live in the seam between syntax checking and reachability analysis.

---

### Pattern 1: Type Laundering & Cast Cascades

At any difficult interface boundary — complex generics, third-party libraries, JSON deserialization — an agent reaches for `as any`, `as unknown as T`, or chained non-null assertions (`!`). This disables compiler checking across all downstream consumers, hides breaking upstream changes, and blinds dead-code analysis (which cannot follow graph reachability through `any`).

```bash
# Double casts and blind casts
rg -n '\bas\s+any\b' src/
rg -n '\bas\s+unknown\s+as\s+[A-Z]\w*' src/
rg -n '<\s*any\s*>' src/
# Chained non-null assertions
rg -n '(?:\w+!\.){2,}' src/
```

**Remediation:** Validate at the boundary using schemas (e.g. Zod) or `satisfies` for internal literals:

```diff
- const payload = JSON.parse(rawBody) as any;
- return { id: payload.id as string, eventName: payload.event_name as string };
+ const WebhookEventSchema = z.object({
+   id: z.string().uuid(),
+   event_name: z.string().min(1),
+ });
+ export type WebhookEvent = z.infer<typeof WebhookEventSchema>;
+ return WebhookEventSchema.parse(JSON.parse(rawBody));
```

```diff
- const theme = { primary: '#0070f3', accent: '#ff0080' } as any as ThemeConfig;
+ const theme = { primary: '#0070f3', accent: '#ff0080' } satisfies ThemeConfig;
```

---

### Pattern 2: Schema-Type Duplication & Drift

When defining data contracts, agents routinely declare both a runtime validator (Zod, Valibot, Yup, ArkType) and a standalone TypeScript `interface` or `type` with the identical fields. Over time, fields are added or modified in one but forgotten in the other, causing silent runtime type desynchronization.

```bash
# Grep for interface names that mirror schema definitions
rg -n 'export\s+interface\s+([A-Za-z0-9_$]+)\b' src/
rg -n 'export\s+const\s+([A-Za-z0-9_$]+)Schema\b' src/
```

**Remediation:** Enforce a Single Source of Truth via type inference from the schema:

```diff
  export const UserProfileSchema = z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    displayName: z.string().min(1),
  });
- export interface UserProfile {
-   id: string;
-   email: string;
-   displayName: string;
- }
+ export type UserProfile = z.infer<typeof UserProfileSchema>;
```

---

### Pattern 3: Defensive Null Paranoia & Optional Chaining Smog

Lacking whole-program context, an agent cannot be certain whether an upstream caller guaranteed non-nullability. It defensively decorates every property read with `?.` and `?? null`, nesting 4–5 levels deep, or adds conjunction checks (`if (user && user.profile && user.profile.settings)`). Under `strictNullChecks`, these branches are unreachable dead code that degrades performance and obscures domain invariants.

```bash
# Repeated conjunction guards: if (x && x.y)
rg -n 'if\s*\(\s*([a-zA-Z0-9_$]+)\s*&&\s*\1\.' src/

# Optional chains three or more links deep
rg -n '(?:\?\.[a-zA-Z0-9_$]+){3,}' src/
```

**Remediation:** Trust domain models and non-nullable types; eliminate impossible branches:

```diff
  export function formatCustomerTier(customer: Customer): string {
-   if (!customer) return 'Unknown';
-   if (customer && customer.profile && customer.profile.billing && customer.profile.billing.tier) {
-     return customer.profile.billing.tier.toUpperCase();
-   }
-   return 'Unknown';
+   return customer.profile.billing.tier.toUpperCase();
  }
```

```diff
- const postalCode = order?.shippingAddress?.postalCode ? order?.shippingAddress?.postalCode : '00000';
+ const postalCode = order?.shippingAddress?.postalCode ?? '00000';
```

Keep when: the value crossed an external boundary (`fetch`, WebSocket, raw SQL row) and has not been validated; the field is genuinely optional in the schema; or the value came from DOM traversal (`document.querySelector('button')?.focus()`).

---

### Pattern 4: Barrel Smog & Circular Dependency Loops

Agents love generating convenience index aggregators (`index.ts` with `export * from './...'`) in every subdirectory, and then importing siblings back through that barrel (`import { Button } from '../components'` inside `src/components/Modal.tsx`). This defeats tree-shaking, bloats production bundles, and causes non-deterministic module initialization where imported symbols are silently `undefined` at runtime.

```bash
# Detect cycles
npx madge --circular --extensions ts,tsx src/
# Or with dpdm
npx dpdm --circular --warning=false ./src/index.ts

# Detect wildcard barrel re-exports
rg -n 'export\s+\*\s+from' src/
```

**Remediation:**
1. Ban components and internal utilities from importing through their own directory barrels (use direct relative imports: `import { Button } from './Button'`).
2. Replace wildcard `export *` with explicit named re-exports of public symbols only.
3. Extract shared types or constants to leaf modules (e.g. `src/components/types.ts`) to sever cyclic links.

---

### Pattern 5: Mock & Test Utility Bleed

When agents write unit tests, they frequently export partial mocks, test doubles, test-only mutations, or fixture factories directly from production files instead of setting up a clean test harness. This bleeds test infrastructure into production bundles and bloats the public API surface.

```bash
# Grep for test-only terminology in non-test source files
rg -n 'export\s+(?:const|function|type|interface)\s+(?:mock|fixture|createMock|dummy|fake|testHelper)[A-Za-z0-9_$]*\b' --glob '!**/*.{test,spec,stories}.*' --glob '!**/test*/**' src/
```

**Remediation:** Relocate mock fixtures and test utilities to dedicated test directories (`test/helpers/`, `src/__mocks__/`) or colocate them in `*.test.ts`. Strip the `export` keyword from production files.

---

### Pattern 6: Phantom Interfaces & Speculative Generics

Agents often over-engineer simple logic by creating unneeded generic parameters (`function fetchItem<T = unknown, E = Error>()`), single-implementor interfaces (`interface IUserService`), or speculative enum variants "just in case" future requirements emerge. This introduces cognitive overhead, worsens compiler performance, and creates ghost types.

```bash
# Grep for interfaces named with I-prefix or generic abstractions with default types
rg -n 'export\s+interface\s+I[A-Z]\w*' src/
rg -n 'export\s+interface\s+[A-Za-z0-9_$]+<[A-Za-z0-9_$,\s=]+>' src/
```

**Remediation:** Inline single-use interfaces into concrete types or function parameters. Delete unconstrained or unused generic type parameters. Replace speculative enums with tight string unions (`'active' | 'inactive'`).

---

### Pattern 7: Anemic Type Guards & Unsound Narrowing

Agents often create custom type predicates (`val is User`) to silence type errors, but implement only shallow or vacuous checks inside the function body (`typeof val === 'object' && val !== null`), completely failing to verify required properties. Downstream consumers assume compile-time safety, leading to runtime `TypeError: Cannot read properties of undefined`.

```bash
# Find custom type guards
rg -n 'function\s+[A-Za-z0-9_$]+\s*\([^)]*\)\s*:\s*\w+\s+is\s+' src/
```

**Remediation:** Use genuine schema parsing (`zod.safeParse()`) or verify every mandatory field explicitly before asserting the type predicate:

```diff
- function isUser(val: unknown): val is User {
-   return typeof val === 'object' && val !== null;
- }
+ function isUser(val: unknown): val is User {
+   return UserSchema.safeParse(val).success;
+ }
```

---

## 2.1 Code-Level Syntax & Structural Slop Manifestations

Beyond the 7 core agent architectural patterns, models repeatedly generate four mechanical slop manifestations:

### Slop Manifestation A: Useless Try/Catch Wrappers
- **Passthrough re-throw** — `catch (e) { throw e; }`. Zero recovery, wasted stack frames, truncated async traces.
- **Blind swallow** — `catch (e) { console.error(e); return null; }`. Destroys root cause context.
- **Remediation:** Delete the wrapper or enrich with `new Error(..., { cause: e })`.

### Slop Manifestation B: Hallucinated & Obvious Comments
- Comments restating syntax: `// Set the user id`, `// Return result`, `// Imports`.
- **Remediation:** Delete comments describing *what* the code does; keep only architectural *why* comments.

### Slop Manifestation C: Verbose Ternaries & Boolean Theater
- `condition ? true : false`, `=== true`, `return !!isReady`.
- **Remediation:** Clean up with Biome (`noExtraBooleanCast`, `noUselessTernary`) or ESLint.

### Slop Manifestation D: Premature Micro-Abstractions & Utility Sprawl
- Single-use 1-line helpers (`const getUserId = (u: User) => u.id;`) that destroy locality without providing reuse.
- Repeated reimplementations of formatting, string manipulation, and styling helpers across disconnected directories:
  - Formatting: `formatDate`, `formatTimestamp`, `toIsoString`, `formatCurrency`
  - String transforms: `capitalize`, `slugify`, `truncate`, `sanitizeString`
  - Styling: `cn` / `clsx` / `twMerge` wrappers
  - Timing: `sleep`, `delay`, ad-hoc `new Promise(r => setTimeout(r, ms))`

```bash
# Exported duplicates across the workspace
rg -n 'export\s+(?:const|function)\s+(capitalize|slugify|formatDate|formatTime|formatCurrency|cn|sleep|delay|truncate|clamp|isEmpty|isNil|safeJsonParse)\b' src/

# Local unexported copies of the same names
rg -n '^(?:const|function)\s+(capitalize|slugify|formatDate|formatCurrency|cn|sleep|delay|isEmpty|safeJsonParse)\b' src/

# Ad-hoc sleep promises
rg -n 'new\s+Promise\(\s*\(?resolve\)?\s*=>\s*setTimeout\s*\(\s*resolve' src/
```

Consolidation protocol:
1. **Catalog** every call site of the duplicated helper.
2. **Pick one canonical module.** Never create a junk drawer: a `utils.ts` holding hundreds of unrelated exports creates circular webs. Target cohesive domain modules (`src/lib/format/`, `src/lib/http/`, `src/lib/async.ts`, `src/lib/utils.ts`).
3. **Superset the canonical implementation** so it satisfies all call sites cleanly.
4. **Redirect imports**, then delete every duplicate definition.
5. **Verify**: `npx tsc --noEmit && pnpm test && npx knip`.

---

## 3. Slop Audit Sweep

Run during any cleanup pass, and always after a heavy LLM generation cycle. Order matters: sweep for patterns, autofix mechanical syntax issues, restructure domain models, and then execute the wave protocol.

### Step 1: Pattern Sweep

```bash
#!/usr/bin/env bash
set -uo pipefail

echo "=== 1. Type Laundering (as any, as unknown as, non-null chains) ==="
rg -n '\bas\s+any\b|\bas\s+unknown\s+as\s+[A-Z]\w*|<\s*any\s*>|(?:\w+!\.){2,}' src/ || true

echo "=== 2. Defensive Null Paranoia & Optional Chaining Smog ==="
rg -n 'if\s*\(\s*([a-zA-Z0-9_$]+)\s*&&\s*\1\.' src/ || true
rg -n '(?:\?\.[a-zA-Z0-9_$]+){3,}' src/ || true

echo "=== 3. Barrel Smog & Circular Dependency Indicators ==="
rg -n 'export\s+\*\s+from' src/ || true

echo "=== 4. Mock & Test Utility Bleed into Production ==="
rg -n 'export\s+(?:const|function|type|interface)\s+(?:mock|fixture|createMock|dummy|fake|testHelper)[A-Za-z0-9_$]*\b' \
  --glob '!**/*.{test,spec,stories}.*' --glob '!**/test*/**' src/ || true

echo "=== 5. Phantom Interfaces & Speculative Generics ==="
rg -n 'export\s+interface\s+I[A-Z]\w*' src/ || true

echo "=== 6. Anemic Type Guards ==="
rg -n 'function\s+[A-Za-z0-9_$]+\s*\([^)]*\)\s*:\s*\w+\s+is\s+' src/ || true

echo "=== 7. Useless Try/Catch Wrappers ==="
rg -U -n 'catch\s*\((?:e|err|error)\)\s*\{\s*throw\s+(?:e|err|error);\s*\}' src/ || true
rg -U -n 'catch\s*\((?:e|err|error)?\)\s*\{\s*(?:console\.[a-z]+\([^)]*\);\s*)?return\s+(?:null|undefined|false);\s*\}' src/ || true

echo "=== 8. Boolean Theater & Obvious Comments ==="
rg -n '\?\s*(true\s*:\s*false|false\s*:\s*true)|(===|!==)\s*(true|false)' src/ || true
rg -i -n '^\s*//\s*(sets?|gets?|returns?|calls?|updates?|deletes?|fetches?|creates?)\s+(the|a|an)?\s*[a-zA-Z0-9_$]+' src/ || true

echo "=== 9. Duplicated Utilities ==="
rg -n 'export\s+(?:const|function)\s+(capitalize|slugify|formatDate|formatTime|cn|sleep|delay)\b' src/ || true
```

### Step 2: Linter Autofix

Patterns with deterministic mechanical fixes (useless try/catch, boolean casts, unneeded ternaries, unused locals) are cleared ahead of graph refactoring:

```bash
npx @biomejs/biome check --write src/     # noUselessCatch, noUselessTernary, noExtraBooleanCast, noUnusedImports
npx eslint --fix "src/**/*.{ts,tsx}"      # no-useless-catch, no-unneeded-ternary, no-useless-return
```

Engine detection order and per-engine rule tables live in [../engines/lint-engines.md](../engines/lint-engines.md).

### Step 3: Consolidate and Inline

Apply the consolidation protocol for duplicated utilities, inline single-use micro-abstractions, and extract shared types to sever barrel cycles per [../remediation/structural-refactor.md](../remediation/structural-refactor.md).

### Step 4: Engine Waves and Verification

Consolidation and inlining orphan the old exports. Sweep them with the wave protocol and its verification gate in [../remediation/waves.md](../remediation/waves.md):

```bash
npx knip --strict
```

For complexity budgets that decide which functions to attack first, see [../remediation/complexity-thresholds.md](../remediation/complexity-thresholds.md).

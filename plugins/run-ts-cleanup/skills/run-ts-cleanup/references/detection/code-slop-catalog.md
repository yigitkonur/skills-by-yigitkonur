# Code Slop and Bloat Taxonomy

The single catalog of removable code this skill targets. Section 1 covers **architectural origins** — why the bloat exists, and therefore what unit to delete. Section 2 covers **slop patterns** — what the bloat looks like in source, with ripgrep detection and deterministic remediation. Section 3 is the executable sweep.

---

## 1. Architectural Origins

Dead-code engines report symptoms: unused files, dead exports, orphaned dependencies. The origin determines the correct deletion unit. Pruning a single flagged export out of a zombie feature leaves the rest of the corpse in the tree; deleting the whole feature directory resolves dozens of findings at once.

| Origin | Typical Engine Report | Correct Deletion Unit |
|---|---|---|
| **A. Zombie feature / dead experiment** | Unreferenced files, unused exports, orphaned deps | The whole feature directory + its flag, fixtures, schema |
| **B. LLM generation without cross-file memory** | Duplicate unreferenced exports, single-file exports | The duplicate implementation (see every pattern in §2) |
| **C. Barrel inflation & circular webs** | Nothing (transitive masking) — cycles found by `madge` | The `export *` statement, not the module behind it |
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

## 2. Slop Patterns

Seven code-level signatures. Each compiles cleanly and passes shallow tests, which is exactly why linters and graph scanners miss them: they live in the seam between syntax checking and reachability analysis.

---

### Pattern 1: Useless Try/Catch Wrappers

Two destructive variants:
- **Passthrough re-throw** — `catch (e) { throw e; }`. Zero recovery, wasted frames, truncated async stack traces under transpilation.
- **Blind swallow** — `catch (e) { console.error(e); return null; }`. Converts network failures, schema drift, and auth errors into benign `null`, which detonates as `TypeError` far from the root cause.

```bash
# Passthrough re-throws
rg -U -n 'catch\s*\((?:e|err|error)\)\s*\{\s*throw\s+(?:e|err|error);\s*\}' src/

# Swallowed errors returning a sentinel
rg -U -n 'catch\s*\((?:e|err|error)?\)\s*\{\s*(?:console\.[a-z]+\([^)]*\);\s*)?return\s+(?:null|undefined|false);\s*\}' src/

# Empty catch blocks
rg -U -n 'catch\s*\([^)]*\)\s*\{\s*\}' src/
```

Delete the wrapper and let the error reach the nearest boundary. Where context genuinely helps, enrich instead of swallowing:

```diff
- export async function loadDashboardStats(orgId: string): Promise<Stats | null> {
-   try {
-     return await statsService.calculate(orgId);
-   } catch (err) {
-     console.error('Failed to load stats:', err);
-     return null; // UI renders blank, cause is lost
-   }
- }
+ export async function loadDashboardStats(orgId: string): Promise<Stats> {
+   try {
+     return await statsService.calculate(orgId);
+   } catch (err) {
+     throw new Error(`Failed to calculate dashboard stats for org ${orgId}`, { cause: err });
+   }
+ }
```

Keep when: the catch is a framework boundary converting exceptions to HTTP responses; a telemetry sink that reports then re-throws; or a documented, monitored fallback for a non-critical background task.

---

### Pattern 2: Blind Type Assertions

At any awkward boundary — complex generics, untyped SDKs, raw JSON — the model reaches for `as any`, `as unknown as T`, or a chain of `!`. Each one disables checking for every downstream consumer, hides breaking dependency upgrades, and blinds the export scanner, which cannot trace references through `any`.

```bash
rg -n '\bas\s+any\b' src/
rg -n '\bas\s+unknown\s+as\s+[A-Z]\w*' src/
rg -n '<\s*any\s*>' src/
rg -n '(?:\w+!\.){2,}' src/          # chained non-null assertions
```

Validate external input at the boundary with a schema, and use `satisfies` for internal literals:

```diff
- const payload = JSON.parse(rawBody) as any;
- return { id: payload.id as string, eventName: payload.event_name as string };
+ const WebhookEventSchema = z.object({
+   id: z.string().uuid(),
+   event_name: z.string().min(1),
+   data: z.record(z.unknown()).default({}),
+ });
+ export type WebhookEvent = z.infer<typeof WebhookEventSchema>;
+ const parsed: unknown = JSON.parse(rawBody);
+ return WebhookEventSchema.parse(parsed);
```

```diff
- const theme = { primary: '#0070f3', accent: '#ff0080' } as any as ThemeConfig;
+ const theme = { primary: '#0070f3', accent: '#ff0080' } satisfies ThemeConfig;
```

Keep when: an untyped CommonJS package has no `@types/*` and a `.d.ts` is not yet written; a test builds a partial mock (`as unknown as DeepDependency`) rather than 200 lines of irrelevant fixture; or a legacy global is being read (`(window as any).__PRERENDER_STATE__`).

---

### Pattern 3: Phantom Null/Undefined Checks

The model cannot track invariants established up the call stack, so it re-guards a parameter already typed non-nullable. Under `strictNullChecks` these branches can never be taken: they are unreachable code that depresses coverage and lies about the domain model.

```bash
# Repeated conjunction guards: if (x && x.y)
rg -n 'if\s*\(\s*([a-zA-Z0-9_$]+)\s*&&\s*\1\.' src/

# Optional chains three or more links deep
rg -n '(?:\?\.[a-zA-Z0-9_$]+){3,}' src/
```

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

### Pattern 4: Hallucinated / Obvious Comments

Comments that restate the next line in English: `// Set the user id`, `// Return the result`, `// Imports`, and JSDoc blocks echoing the parameter name back (`@param id The ID`). They inflate token cost, rot on the first refactor, and bury the two comments in the file that actually matter.

```bash
# Comments restating the verb and identifier below them
rg -i -n '^\s*//\s*(sets?|gets?|returns?|calls?|updates?|deletes?|fetches?|creates?|renders?|initializes?)\s+(the|a|an)?\s*[a-zA-Z0-9_$]+' src/

# Section divider noise
rg -i -n '^\s*//\s*(=|-){3,}\s*(imports?|constants?|types?|functions?|hooks?|helpers?|render|exports?)\s*(=|-){3,}' src/

# Tautological JSDoc params
rg -U -n '\*\s*@param\s+(\w+)\s+(?:The\s+)?\1' src/
```

Delete every comment describing *what* the syntax does. Preserve only the *why*:

```typescript
// Section 179: cap the equipment deduction at the IRS annual limit for the 2026 tax year
const cappedDeduction = Math.min(equipmentExpenses, IRS_SECTION_179_LIMIT_2026);

// Workaround for Safari 17.2 flexbox bug: container height collapses with aspect-ratio
element.style.minHeight = '0px';
```

Keep when: the JSDoc is on a published package's public API and drives consumer hover docs; the comment points at an ADR, RFC, or ticket; or it cites a formula or paper (`// Haversine distance for spherical coordinates`).

---

### Pattern 5: Verbose Ternaries & Boolean Theater

Boolean identity ternaries (`condition ? true : false`), explicit literal comparisons (`=== true`), `if/else` blocks returning `true`/`false`, and double negation on already-boolean values (`return !!isReady`).

```bash
rg -n '\?\s*(true\s*:\s*false|false\s*:\s*true)' src/
rg -n '(===|!==)\s*(true|false)' src/
rg -U -n 'if\s*\([^)]+\)\s*\{\s*return\s+true;\s*\}\s*else\s*\{\s*return\s+false;\s*\}' src/
rg -n 'return\s+!!(is[A-Z]\w*|has[A-Z]\w*|can[A-Z]\w*|should[A-Z]\w*)' src/
```

```diff
  export function isUserEligibleForPromo(user: User, hasPurchased: boolean): boolean {
-   const isMember = user.membershipStatus === 'active' ? true : false;
-   const isFirstTime = hasPurchased === false ? true : false;
-   if (isMember === true && isFirstTime === true) { return true; } else { return false; }
+   return user.membershipStatus === 'active' && !hasPurchased;
  }
```

Biome (`noExtraBooleanCast`, `noUselessTernary`) and ESLint (`no-unneeded-ternary`, `no-extra-boolean-cast`) autofix this pattern mechanically — do it before touching exports.

Keep when: discriminating tri-state `boolean | undefined` where `=== true` deliberately excludes `undefined`; or guarding JSX against rendering `0` (`{items.length > 0 && <ItemList />}`).

---

### Pattern 6: Premature Micro-Abstractions

One-line helpers used exactly once: `const getUserId = (user: User) => user.id;`. They provide no reuse and no seam, but destroy locality (five jumps to read a fifteen-line procedure), inflate the export surface, and generate "used only in file" findings.

```bash
# One-line arrow declarations
rg -n 'const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>\s*[^;{]+;' src/

# Rank them by repository-wide reference count
for name in $(rg -o -N 'const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>' -r '$1' src/); do
  count=$(rg -w "$name" src/ | wc -l)
  [ "$count" -le 2 ] && echo "single-use ($count refs): $name"
done
```

```diff
- const getFullName = (u: User) => `${u.firstName} ${u.lastName}`.trim();
- const getAvatar = (u: User) => u.avatarUrl ?? '/default.png';
-
  export function UserHeader({ user }: { user: User }) {
-   const fullName = getFullName(user);
-   const avatar = getAvatar(user);
+   const fullName = `${user.firstName} ${user.lastName}`.trim();
+   const avatar = user.avatarUrl ?? '/default.png';
    return <img src={avatar} alt={fullName} />;
  }
```

For multi-file wrappers and the full inlining protocol, see [../remediation/structural-refactor.md](../remediation/structural-refactor.md).

Keep when: the name carries intent into a callback (`posts.sort(byMostRecent)`); it is a custom React hook encapsulating state or effects; or it is a pure domain formula with its own edge-case tests.

---

### Pattern 7: Utility Duplication & Helper Sprawl

The highest-volume signature of Origin B. Lacking cross-file memory, the model re-implements the same trivial helper in every directory it touches. A mature repository accumulates five `formatDate`s (each with different `Intl` options), three `cn` wrappers (`src/utils/cn.ts`, `src/lib/utils.ts`, `src/components/ui/utils.ts`), and a `slugify` per feature, each with a different regex.

Recurring families:

| Family | Duplicated identifiers |
|---|---|
| Formatting | `formatDate`, `formatTimestamp`, `toIsoString`, `humanizeDate`, `formatCurrency` |
| String transforms | `capitalize`, `slugify`, `truncate`, `sanitizeString` |
| Guards and parsing | `isEmpty`, `isNil`, `hasKey`, `safeJsonParse` |
| Styling | `cn` / `clsx` / `twMerge` wrappers |
| Timing | `sleep`, `delay`, ad-hoc `new Promise(r => setTimeout(r, ms))` |

Costs: edge cases fixed in one copy stay broken in the other four; bundlers cannot deduplicate near-identical ASTs; every copy becomes an unreferenced export the moment one consumer is refactored.

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
2. **Pick one canonical module.** Never a junk drawer: a `utils.ts`, `helpers.ts`, or `common.ts` holding hundreds of unrelated exports is the failure mode this pattern creates. Target cohesive domain modules — `src/lib/format/`, `src/lib/http/`, `src/lib/async.ts` — not ten shallow files split across `src/utils/`, `src/helpers/`, and `src/lib/`.
3. **Superset the canonical implementation** so it satisfies every observed call site (empty strings, null input, timezones, Unicode).
4. **Redirect imports**, then delete every duplicate definition.
5. **Verify**: `npx tsc --noEmit && pnpm test && npx knip` — zero broken imports, zero orphaned duplicate exports.

```typescript
// src/lib/utils.ts — one canonical definition
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
```

Keep duplicates only when: the copies run in execution environments that cannot import each other (Edge runtime vs. Node server vs. browser script), or a zero-dependency published package in the monorepo may not depend on internal shared libraries.

---

## 3. Slop Audit Sweep

Run during any cleanup pass, and always after a heavy LLM generation cycle. Order matters: sweep, autofix the mechanical patterns, restructure, then let the engine collect the newly orphaned exports.

### Step 1: Pattern Sweep

```bash
#!/usr/bin/env bash
set -uo pipefail

echo "=== 1. Useless try/catch ==="
rg -U -n 'catch\s*\((?:e|err|error)\)\s*\{\s*throw\s+(?:e|err|error);\s*\}' src/ || true
rg -U -n 'catch\s*\((?:e|err|error)?\)\s*\{\s*(?:console\.[a-z]+\([^)]*\);\s*)?return\s+(?:null|undefined|false);\s*\}' src/ || true

echo "=== 2. Blind type assertions ==="
rg -n '\bas\s+any\b|\bas\s+unknown\s+as\s+[A-Z]\w*' src/ || true

echo "=== 3. Phantom null checks ==="
rg -n 'if\s*\(\s*([a-zA-Z0-9_$]+)\s*&&\s*\1\.' src/ || true

echo "=== 4. Obvious comments ==="
rg -i -n '^\s*//\s*(sets?|gets?|returns?|calls?|updates?|deletes?|fetches?|creates?)\s+(the|a|an)?\s*[a-zA-Z0-9_$]+' src/ || true

echo "=== 5. Boolean theater ==="
rg -n '\?\s*(true\s*:\s*false|false\s*:\s*true)|(===|!==)\s*(true|false)' src/ || true

echo "=== 6. Single-use micro-abstractions ==="
rg -n 'const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>\s*[^;{]+;' src/ || true

echo "=== 7. Duplicated utilities ==="
rg -n 'export\s+(?:const|function)\s+(capitalize|slugify|formatDate|formatTime|cn|sleep|delay)\b' src/ || true
```

### Step 2: Linter Autofix

Patterns 1, 5, and dead stores are mechanically fixable. Apply the autofix before touching exports, so the dead-code engine analyses a clean AST:

```bash
npx @biomejs/biome check --write src/     # noUselessCatch, noUselessTernary, noExtraBooleanCast
npx eslint --fix "src/**/*.{ts,tsx}"      # no-useless-catch, no-unneeded-ternary, no-useless-return
```

Engine detection order and per-engine rule tables live in [../engines/lint-engines.md](../engines/lint-engines.md).

### Step 3: Consolidate and Inline

Apply Pattern 7's consolidation protocol and Pattern 6's inlining, bounded to five files per batch, per [../remediation/structural-refactor.md](../remediation/structural-refactor.md).

### Step 4: Engine Waves and Verification

Consolidation and inlining orphan the old exports. Sweep them with the wave protocol and its verification gate in [../remediation/waves.md](../remediation/waves.md):

```bash
npx knip --strict
```

For complexity budgets that decide which functions to attack first, see [../remediation/complexity-thresholds.md](../remediation/complexity-thresholds.md).

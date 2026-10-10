# Lightweight Refactor Playbook

Tactical protocol for non-harmful structural refactoring during a cleanup pass: inlining unnecessary indirection, untangling module dependency cycles, dismantling barrel files, and co-locating single-consumer logic — all without altering runtime behaviour or rewriting business logic.

---

## 1. The Lightweight Boundary

Structural refactoring during dead-code remediation has one objective: **maximize navigability, compilation speed, and agent comprehension while strictly preserving runtime semantics.**

```
+-------------------------------------------------------------------------------+
|                 LIGHTWEIGHT REFACTORING BOUNDARY GUARANTEE                    |
+-------------------------------------------------------------------------------+
|  PRESERVED (ZERO MUTATION)            |  RESTRUCTURED (IMPROVED SURFACE)      |
|  - Business logic & algorithms        |  - Call indirection depth (inlining)  |
|  - Public API contract signatures     |  - Import graph edges (un-cycling)    |
|  - Runtime behavior & edge cases      |  - Bundler chunk footprint (barrels)  |
|  - Asynchronous execution timing      |  - Cognitive proximity (co-location)  |
|  - Existing test suite expectations   |  - Token consumption for AI agents    |
+---------------------------------------+---------------------------------------+
```

### Core Axioms

1. **Semantic invariance.** Every step must produce identical inputs, outputs, and side effects. If a change requires editing a test assertion, it is an architectural redesign, not a lightweight refactor — stop and escalate.
2. **Navigability over indirection.** Each forwarding layer, pass-through abstraction, and directory hop is cognitive debt paid by every future reader, human or agent.
3. **Bounded blast radius.** Apply changes in discrete batches. Never combine barrel decoupling, inlining, and cycle resolution in one un-audited step.
4. **Tool-verified, not eyeballed.** Gate every step on compiler diagnostics (`tsc --noEmit`), cycle analysis (`madge --circular`), and the existing test suite.

### Scope Discrimination

| Dimension | Lightweight Refactor (this file) | Heavy Architectural Rewrite |
|---|---|---|
| **Scope** | Single functions, import edges, leaf modules | Full subsystems, state layers, public APIs |
| **Logic modification** | None — pure relocation and inlining | Rewritten control flow and algorithms |
| **Risk profile** | Near-zero, compiler and test verified | High, regression risk across flows |
| **Verification** | `tsc`, dead-code engine, `madge`, unit tests | Integration suites, E2E, staging QA |
| **Beneficiary** | Agents, build tools, human maintainers | Product requirements, scale needs |

---

## 2. The Plan-First Rule

Never start multi-file structural changes without an explicit bounded plan. Unplanned refactors produce cascading import errors, accidental cycles, and unreviewable diffs.

```
+-------------------------------------------------------------------------------+
|                           THE PLAN-FIRST SEQUENCE                             |
+-------------------------------------------------------------------------------+
|  1. DIAGNOSE      --> Capture exact violations (engine, madge, compiler)      |
|  2. BOUND         --> Restrict the unit to <= 5 tightly coupled files         |
|  3. MAP EDGES     --> Document incoming/outgoing imports and consumer count   |
|  4. DRAFT PLAN    --> Write atomic transition steps and fallback criteria     |
|  5. EXECUTE       --> Apply structural edits step by step                     |
|  6. VERIFY & COMMIT-> Pass compiler and test gates, then commit atomically    |
+-------------------------------------------------------------------------------+
```

### Refactor Plan Specification

```markdown
### Refactor Plan: [Module / Subsystem Name]

1. Target Boundaries:
   - Source Files: `src/features/billing/service.ts`, `src/features/billing/wrapper.ts`
   - Affected Consumers: 3 modules in `src/features/checkout/`
   - File Budget: max 5 files per batch.

2. Diagnostic Finding:
   - Tool Output: `forwardBillingRequest` reported as a single-use export in `wrapper.ts`.
   - Structural Defect: pass-through wrapper adding one file hop and zero logic.

3. Step-by-Step Transformations:
   - Step 1: Inline `forwardBillingRequest` into `checkoutController.ts`.
   - Step 2: Remove the export from `wrapper.ts`.
   - Step 3: Re-run the engine; if `wrapper.ts` is now dead, delete the file.

4. Invariant Verification Checklist:
   - [ ] `npx tsc --noEmit` exits 0
   - [ ] `npm test -- checkout` passes with zero assertion edits
   - [ ] `npx madge --circular src/` reports no new cycles
```

### Abort Conditions

- **Test failures not fixable by import-path edits alone.** Revert immediately (`git checkout .`); the change was not semantics-preserving.
- **Plan exceeds 5 files.** Decompose into sequential batches before executing.
- **Symbol crosses a package boundary** in a library workspace. Stop and verify the `package.json` `exports` map first.

---

## 3. Inlining Single-Use Indirection

Two shapes qualify: the **pass-through wrapper** that forwards arguments to an underlying implementation unchanged, and the **single-expression builder** that wraps one template literal or arithmetic expression behind a name.

```
AVOID (Artificial Indirection):
  Consumer ---> [Pass-Through Wrapper] ---> [Core Implementation]
                (adds 0 logic, 1 file hop)

TARGET (Direct Resolution):
  Consumer --------------------------------> [Core Implementation]
```

### Inlining Criteria

Inline only when **all** hold:

1. **Single consumer.** The engine reports exactly one consuming file; confirm with `rg -w "symbolName" src/`.
2. **Zero transformation.** No validation, logging, telemetry, memoization, retry, or error handling.
3. **No hidden complexity.** The body is one `return targetFn(...args)`, one property read, or one expression — nothing a reader would need to test in isolation.
4. **No architectural seam.** The symbol is not a mock seam, plugin hook, or interface implementation.

```typescript
// src/utils/url.ts — single-expression builder, one call site
export const buildUserProfileRedirectUrl = (userId: string, orgId: string): string =>
  `/orgs/${orgId}/users/${userId}/profile?source=nav`;
```

```diff
// src/components/Navigation.tsx
- import { buildUserProfileRedirectUrl } from '@/utils/url';
- const redirectUrl = buildUserProfileRedirectUrl(user.id, org.id);
+ const redirectUrl = `/orgs/${org.id}/users/${user.id}/profile?source=nav`;
```

### Diagnostic Commands

```bash
# Single-expression arrow exports
rg -n --pcre2 "export const \w+ = \([^)]*\) => \w+\([^)]*\);" src/

# Single-statement forwarding functions
rg -n --pcre2 "export function \w+\([^)]*\)\s*\{\s*return \w+\([^)]*\);\s*\}" src/
```

### Inlining Protocol

#### Before (Fragile Indirection)

```typescript
// src/services/user/clientWrapper.ts
export async function fetchUserProfileById(userId: string): Promise<UserProfile> {
  return apiClient.get<UserProfile>(`/users/${userId}`);
}

// src/controllers/dashboard.ts
import { fetchUserProfileById } from '@/services/user/clientWrapper';

export async function loadDashboard(userId: string) {
  const profile = await fetchUserProfileById(userId);
  return { profile };
}
```

1. Replace the call with the direct expression at the single call site.
2. Add the direct imports (`apiClient`, `UserProfile`) to the consumer.
3. Delete the wrapper definition.
4. Re-run the dead-code engine (`npx knip --include exports`). If the wrapper file has zero remaining exports, delete the file.

#### After (Direct & Navigable)

```typescript
// src/controllers/dashboard.ts
import { apiClient } from '@/lib/apiClient';
import type { UserProfile } from '@/types/user';

export async function loadDashboard(userId: string) {
  const profile = await apiClient.get<UserProfile>(`/users/${userId}`);
  return { profile };
}
```

### When NOT to Inline

- The wrapper is an **anti-corruption layer** isolating third-party SDK types from domain models.
- The wrapper is a **mock seam** used by tests via dependency injection or module mocking.
- The wrapper satisfies an interface contract enforced by a framework or schema.

Related: deduplicating helpers is a different operation — consolidate to a canonical module per [../detection/code-slop-catalog.md](../detection/code-slop-catalog.md). Stripping `export` from an internal-only symbol belongs to Wave 3 in [waves.md](waves.md), not here.

---

## 4. Untangling Circular Dependencies

Cycles (`A -> B -> C -> A`) cause `ReferenceError: Cannot access 'X' before initialization` (temporal dead zone), broken tree-shaking, and silent `undefined` exports during bundle evaluation.

```
CIRCULAR (Deadly ESM Loop):        UNTANGLED (Acyclic via Leaf):
  A --> B --> C                      A --> B
  ^___________|                       \   /
                                       v v
                            [Leaf: types / pure contracts / leaf utils]
```

### Detection

```bash
npx madge --circular --extensions ts,tsx src/
npx dpdm --circular --warning=false ./src/index.ts

# CI-friendly JSON output
npx madge --circular --json src/ | jq '.[] | select(length > 0)'
```

### Strategy 1: Extract a Shared Leaf Module (default)

When two modules import each other for shared types or pure helpers, move the shared elements into a leaf module that imports neither.

```typescript
// BEFORE — src/domain/user.ts imports Order; src/domain/order.ts imports User. Cycle.
import { Order, calculateOrderTotal } from './order';
export interface User { id: string; orders: Order[] }

import { User } from './user';
export interface Order { id: string; userId: string; items: Array<{ price: number; quantity: number }> }
```

1. Create `src/domain/types.ts` holding `User` and `Order` — zero imports.
2. Point both modules at the leaf for type imports.
3. Leave the functions where they are; only one direction of value import survives.

```typescript
// AFTER — src/domain/types.ts (pure leaf, zero dependencies)
export interface User { id: string; orders: Order[] }
export interface Order { id: string; userId: string; items: Array<{ price: number; quantity: number }> }

// src/domain/order.ts — imports only the leaf
import type { Order } from './types';
export function calculateOrderTotal(order: Order): number {
  return order.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// src/domain/user.ts — leaf types plus a one-way value import
import type { User } from './types';
import { calculateOrderTotal } from './order';
export function getUserTotalSpent(user: User): number {
  return user.orders.reduce((sum, order) => sum + calculateOrderTotal(order), 0);
}
```

### Strategy 2: Type-Only Imports

Most runtime cycles are types imported with value syntax. Transpilers (Babel, SWC, esbuild) preserve the import statement unless it is marked type-only, so the bundler evaluates a graph edge that TypeScript would have erased.

```diff
- import { UserProfile, RoleDefinition } from './userProfile';
+ import type { UserProfile, RoleDefinition } from './userProfile';
```

Enforce repository-wide:

```json
{ "compilerOptions": { "verbatimModuleSyntax": true } }
```

### Strategy 3: Dependency Inversion

If A calls B and B must call back into A, pass the behaviour instead of importing the higher-level module:

```diff
- import { scheduleNextRun } from './scheduler';
- export function executeTask(task: Task) {
-   scheduleNextRun(task);
- }
+ export function executeTask(task: Task, onComplete?: (task: Task) => void) {
+   onComplete?.(task);
+ }
```

---

## 5. Barrel File Restructuring

Barrel files (`index.ts` with broad re-exports) degrade build and test performance across Vite, Next.js, Turbopack, and Jest. They force bundlers to parse hundreds of unneeded AST nodes, defeat tree-shaking, and manufacture cycles.

```
THE BARREL EXPLOSION:
  Consumer imports 1 icon:  import { ChevronRight } from '@/components/icons';

  icons/index.ts contains:
    export * from './ChevronRight';
    export * from './LucideSet';    <-- forces the bundler to parse 2,000 icons
    export * from './HeavyCharts';  <-- pulls D3 / Recharts into memory
```

| Toolchain | With Massive Barrels | With Direct Imports | Delta |
|---|---|---|---|
| **Vite dev server (HMR)** | 800ms - 2.5s cold reload | 50ms - 150ms | **5x - 15x faster** |
| **Next.js Turbopack** | Memory spikes, slow compile | Linear memory, fast compile | **~60% memory drop** |
| **Jest / Vitest startup** | High module evaluation overhead | Isolated leaf loading | **~3x faster runs** |
| **Production chunk size** | Side-effect leakage | Tree-shaken chunks | **20% - 40% smaller** |

### Audit

```bash
# Largest barrels first
find src -name "index.ts" -o -name "index.tsx" | xargs wc -l | sort -nr | head -n 25

# Wildcard re-exports
rg -n "export \* from" src/

# Consumers of a target barrel, before touching it
rg -l "from '@/components'" src/
```

### Restructuring Rules

1. **Ban internal barrel consumption.** A module must never reach a sibling through its own directory barrel.
   ```diff
   // Inside src/components/cards/UserProfileCard.tsx
   - import { Avatar } from '@/components';      // BANNED: cycle + full barrel pull
   - import { Avatar } from '../index';          // BANNED: internal barrel cycle
   + import { Avatar } from '../avatar/Avatar';  // REQUIRED: direct sibling path
   ```
2. **Dismantle kitchen-sink barrels** such as `src/index.ts` or `src/utils/index.ts` that aggregate unrelated modules.
3. **Convert wildcards to explicit named exports** wherever a public entry point is genuinely required.
   ```diff
   // src/components/index.ts
   - export * from './Button';
   - export * from './Charts';
   + export { Button, type ButtonProps } from './Button';
   ```
4. **Bypass the barrel entirely for heavy subsystems** (tables, charts, editors) in consumer files.
   ```diff
   - import { LineChart, BarChart } from '@/components';
   + import { LineChart } from '@/components/charts/LineChart';
   + import { BarChart } from '@/components/charts/BarChart';
   ```

Prune barrel entries with no consumers outside the folder as part of Wave 2 in [waves.md](waves.md).

---

## 6. Co-location and Directory Depth

Code that changes together must live together. Splitting a feature's helpers, types, and styles across `src/utils/`, `src/types/`, and `src/helpers/` raises discovery cost and strands orphans when the feature is deleted.

```
FRAGMENTED (high token spend):        CO-LOCATED POD (atomic, no graph sprawl):
  src/components/UserCard.tsx           src/features/user-card/
  src/hooks/useUserCardData.ts            UserCard.tsx
  src/types/userCard.ts                   UserCard.formatters.ts
  src/utils/userCardFormatters.ts         UserCard.test.tsx
  src/styles/userCard.module.css          useUserCardData.ts
```

### The 1-to-1 Rule

If a helper, constant, or type has **exactly one** consumer:

1. **Under ~25 lines and purely computational** — move it into the consumer file as a non-exported local declaration.
2. **Larger, or needing its own tests** — move it to a sibling file in the same directory (`orderSummary.ts` beside `orderSummary.calculator.ts`).

Do not create a separate `.types.ts` file for a three-line prop interface; declare it in the component file. Reserve dedicated type modules for contracts shared across a feature boundary.

### The Rule of Three

Do **not** promote a helper into a global `src/lib/` or `src/utils/` directory unless all three hold:
- Consumed by at least **three distinct domain features**.
- Fully domain-agnostic (array chunking, ISO date parsing, hashing).
- Covered by its own isolated tests.

### Directory Depth Ceiling

Generated scaffolding nests until a single button costs six directories:

```
src/features/billing/components/cards/subscription-card/components/
  subscription-card-button/SubscriptionCardButton.tsx
                          /SubscriptionCardButton.types.ts
                          /SubscriptionCardButton.styles.ts
                          /index.ts
```

Flatten any folder whose modules are exclusively coupled to their immediate parent:

```
src/features/billing/components/SubscriptionCard.tsx       <-- button inlined as a local component
src/features/billing/components/SubscriptionCard.test.tsx
```

Cap directory depth at **4 levels below `src/`**. A component rendered only by its parent belongs inside the parent file as a non-exported declaration, not in a directory of its own.

### Co-location Safety Checklist

- Strip the `export` keyword when a helper moves into its consuming file.
- Update test-file import paths to the new location.
- Use `git mv` so history follows the file, and confirm `git status` shows renames rather than delete/add pairs.
- Re-run the dead-code engine to confirm the old location has no dangling references.

---

## 7. Verifying a Structural Refactor

The canonical verification gate — typecheck, declaration emit, type coverage, tests, build, and post-flight reconciliation — lives in [waves.md](waves.md). Run it there; do not maintain a competing local gate.

Structural refactoring adds three checks a generic gate does not cover:

1. **Cycle non-regression.** Inlining and co-location can introduce new edges. Compare against the pre-refactor cycle count, not against zero:
   ```bash
   npx madge --circular --extensions ts,tsx src/ > .cycles-after.txt
   diff .cycles-before.txt .cycles-after.txt
   ```
2. **Behaviour preservation.** The test suite must pass **with zero assertion edits**. Any edited expectation means semantics changed — revert and reclassify the work as an architectural rewrite.
3. **Diff shape.** A lightweight refactor produces moved and deleted lines, not new logic. Inspect for unintended additions:
   ```bash
   git diff --stat
   git diff -U0 | rg '^\+[^+]' | rg '\b(if|for|while|catch)\b|\?\?|&&'
   ```
   New control-flow keywords in a structural diff are a red flag; justify each one or revert it.

### Commit Discipline

Commit each structural wave atomically with a scoped message:

- `refactor(inline): inline single-use wrapper fetchUserProfile`
- `refactor(cycles): untangle user-order cycle via leaf types`
- `refactor(barrels): replace wildcard re-exports with named exports`
- `refactor(colocate): co-locate checkout helpers into feature pod`

Never mix a functional bug fix into a structural commit — it destroys the revertability that makes these refactors safe.

---

### 8. Architectural Deepening (Matt Pocock Model)

Synthesizing Matt Pocock's `improve-codebase-architecture` and John Ousterhout's *Philosophy of Software Design* for TypeScript codebases, a cleanup operation must not merely delete dead lines — it must deepen existing modules and improve system leverage.

```
          SHALLOW MODULE (Agent Anti-Pattern)
         ┌───────────────────────────────────┐
         │ Interface: 15 exported functions  │
         │ Implementation: 2 lines each      │  ← Wide surface, shallow value,
         └───────────────────────────────────┘     high cognitive friction
                          vs.
            DEEP MODULE (High Architectural Leverage)
         ┌───────────────────────────────────┐
         │ Interface: 1 function / command   │  ← Tiny surface, deep value,
         ├───────────────────────────────────┤     hides complexity completely
         │ Implementation: state machine,    │
         │ caching, validation, persistence  │
         └───────────────────────────────────┘
```

When AI agents generate code or perform automated refactoring, they systematically introduce four categories of structural bloat:
1. **Shallow pass-through wrappers** (creating artificial call-stack hops with zero leverage).
2. **Test-only export leaks** (breaking encapsulation by exporting private helpers solely so unit tests can spy on internal state).
3. **Speculative seams / ghost interfaces** (introducing Java-style `IUserService` abstractions with exactly one implementation and no polymorphic variance).
4. **Context-fragmented micro-file sprawl** (scattering 5-line single-consumer helpers into disconnected global utility folders).

---

### Tenet 1: The Deletion Test

> **The Deletion Test:**  
> *"Imagine deleting the module:*  
> *- If removing it causes its complexity to vanish completely, it was a shallow module — inline it!*  
> *- If deleting it causes complexity to reappear and duplicate across N callers, it is a true deep module that must be preserved and deepened."*

Depth is not the ratio of implementation lines to interface lines. Depth is **leverage at the interface**: how much capability a caller gets per unit of API surface they have to learn.

#### Application 1: Pass-Through Wrapper vs. Deep Module

##### Anti-Pattern: Shallow Pass-Through Wrapper
An agent creates a wrapper to "abstract" an HTTP client:

```typescript
// src/services/userApi.ts (SHALLOW MODULE: AVOID)
import { apiClient } from '@/lib/apiClient';
import type { User } from '@/types/user';

// Interface: 1 function to learn
// Implementation: 1-line pass-through with 0 added value
export async function fetchUserById(id: string): Promise<User> {
  return apiClient.get<User>(`/users/${id}`);
}
```

*Applying the Deletion Test:*  
If we delete `fetchUserById`, what happens to callers?
```typescript
// Caller: src/features/profile/useProfile.ts
- const user = await fetchUserById(userId);
+ const user = await apiClient.get<User>(`/users/${userId}`);
```
The complexity did not reappear across callers; the complexity *vanished*. Callers already understand `apiClient.get`. The wrapper was pure indirection and cognitive drag.

##### Remediated: The True Deep Module
If `userApi.ts` is to earn its keep as a module, it must hide genuine complexity behind that small interface:

```typescript
// src/services/userApi.ts (DEEP MODULE: PRESERVE & ENHANCE)
import { apiClient } from '@/lib/apiClient';
import { userCache } from '@/lib/cache';
import { UserSchema, type User } from '@/schemas/user';

// Interface remains tiny: exactly 1 function, identical simple signature
export async function fetchUserById(id: string): Promise<User> {
  // Deep implementation hidden behind the seam:
  // 1. In-memory cache check
  const cached = userCache.get(id);
  if (cached && !cached.isStale()) return cached.data;

  // 2. Fetch with automatic retry and abort signal
  const raw = await apiClient.get(`/users/${id}`, { retry: 2 });

  // 3. Runtime boundary validation (Zod schema parse)
  const validated = UserSchema.parse(raw);

  // 4. Cache update
  userCache.set(id, validated);
  return validated;
}
```

*Applying the Deletion Test:*  
If we delete `fetchUserById` now, all N callers would have to re-implement caching, retry backoff, and runtime schema parsing. Real complexity reappears in N places. Therefore, this module passes the Deletion Test.

#### Application 2: Subsystem & Feature-Level Deletion Test (Horizontal Coupling)
- **Test:** Can you run `git rm -r src/features/referrals/` and have the rest of the repository compile cleanly (excluding explicit navigation links to referrals)?
- **Violation:** If deleting `src/features/referrals/` triggers 20 compiler errors in `src/features/billing/` and `src/utils/` because referrals exported its private referral bonus calculators or referral DTOs into global directories, the feature violated subsystem locality.
- **Remediation:** Colocate those internal symbols back into `src/features/referrals/`.

---

### Tenet 2: Interface as Test Surface

> **The Interface as Test Surface Principle:**  
> *"Callers and tests cross the exact same seam. If you need to test past the module's public interface, the module is the wrong shape or missing a clean internal seam. Never export private production symbols solely for unit tests."*

#### The Defect: Test-Only Export Leaks
When an agent writes unit tests, it frequently exports private helper functions to test them in isolation:

```typescript
// src/domain/pricing/calculator.ts (ENCAPSULATION LEAK: AVOID)
export interface OrderItem {
  id: string;
  price: number;
  quantity: number;
  category: 'standard' | 'clearance';
}

// LEAK 1: Exported ONLY for unit tests
export function _calculateItemDiscount(price: number, quantity: number, category: string): number {
  if (category === 'clearance') return price * quantity * 0.3;
  return quantity >= 10 ? price * quantity * 0.1 : 0;
}

// LEAK 2: Exported ONLY for unit tests
export function _computeTierTax(subtotal: number, state: string): number {
  const rates: Record<string, number> = { CA: 0.0825, NY: 0.08, TX: 0.0625 };
  return subtotal * (rates[state] ?? 0.05);
}

// The ONLY true public interface
export function calculateOrderTotal(items: OrderItem[], state: string): { subtotal: number; tax: number; total: number } {
  const subtotal = items.reduce((sum, item) => {
    const discount = _calculateItemDiscount(item.price, item.quantity, item.category);
    return sum + (item.price * item.quantity - discount);
  }, 0);
  const tax = _computeTierTax(subtotal, state);
  return { subtotal, tax, total: subtotal + tax };
}
```

```typescript
// src/domain/pricing/calculator.test.ts (FRAGILE PLUMBING TEST)
import { _calculateItemDiscount, _computeTierTax, calculateOrderTotal } from './calculator';

test('_calculateItemDiscount applies 30% for clearance', () => {
  expect(_calculateItemDiscount(100, 1, 'clearance')).toBe(30);
});
```

#### Why This Breaks Systems
1. **Knip Detection:** Knip flags `_calculateItemDiscount` and `_computeTierTax` as Batch 4 (Test-Only Leaks) or unused exports under `--production`.
2. **Refactoring Paralysis:** If the developer refactors the internal discount engine to use a strategy pattern or rule engine, the unit tests fail, even though `calculateOrderTotal` behaves identically!
3. **API Bloat:** Autocomplete in IDEs exposes `_calculateItemDiscount` to unrelated production consumers.

#### Remediation Protocol: "Replace, Don't Layer"
1. **Un-export the private helpers:** Remove `export` from `_calculateItemDiscount` and `_computeTierTax`.
2. **Re-target test suite at the public interface:** Test behavior through observable inputs and outputs of `calculateOrderTotal`.
3. **If internal logic is independently complex:** Extract a separate deep module (`DiscountPolicy`) with its own small interface and separate unit tests.

```typescript
// src/domain/pricing/calculator.ts (CLEAN ENCAPSULATION)
export interface OrderItem {
  id: string;
  price: number;
  quantity: number;
  category: 'standard' | 'clearance';
}

// Internal implementation details: strictly un-exported
function calculateItemDiscount(price: number, quantity: number, category: string): number {
  if (category === 'clearance') return price * quantity * 0.3;
  return quantity >= 10 ? price * quantity * 0.1 : 0;
}

function computeTierTax(subtotal: number, state: string): number {
  const rates: Record<string, number> = { CA: 0.0825, NY: 0.08, TX: 0.0625 };
  return subtotal * (rates[state] ?? 0.05);
}

// Public Interface
export function calculateOrderTotal(
  items: OrderItem[],
  state: string
): { subtotal: number; tax: number; total: number } {
  const subtotal = items.reduce((sum, item) => {
    const discount = calculateItemDiscount(item.price, item.quantity, item.category);
    return sum + (item.price * item.quantity - discount);
  }, 0);
  const tax = computeTierTax(subtotal, state);
  return { subtotal, tax, total: subtotal + tax };
}
```

```typescript
// src/domain/pricing/calculator.test.ts (RESILIENT TEST SURFACE)
import { calculateOrderTotal } from './calculator';

describe('calculateOrderTotal', () => {
  it('applies clearance discount through the public interface', () => {
    const result = calculateOrderTotal(
      [{ id: '1', price: 100, quantity: 1, category: 'clearance' }],
      'CA'
    );
    expect(result.subtotal).toBe(70);
    expect(result.tax).toBeCloseTo(5.775);
    expect(result.total).toBeCloseTo(75.775);
  });
});
```

---

### Tenet 3: The Seam Test

> **The Seam Test:**  
> *"One adapter = hypothetical seam (YAGNI & indirection). Two adapters = real seam.*  
> *Do not introduce an interface, abstract class, or port unless at least two concrete adapters exist in the repository (e.g. production + test in-memory fake, or multi-provider drivers)."*

#### The Defect: Ghost Interfaces & Speculative Polymorphism
AI agents habitually write Enterprise Java patterns in TypeScript:

```typescript
// src/services/user/IUserService.ts (GHOST INTERFACE: AVOID)
export interface IUserService {
  getUser(id: string): Promise<User>;
  updateUser(id: string, data: UpdateUserData): Promise<User>;
  deleteUser(id: string): Promise<void>;
}

// src/services/user/UserService.ts
import type { IUserService } from './IUserService';

export class UserService implements IUserService {
  async getUser(id: string): Promise<User> { /* ... */ }
  async updateUser(id: string, data: UpdateUserData): Promise<User> { /* ... */ }
  async deleteUser(id: string): Promise<void> { /* ... */ }
}
```

#### Why This is Toxic in TypeScript
- **Structural Typing:** TypeScript has structural typing. You do **not** need `implements IUserService` to mock or substitute `UserService` in tests! Any object matching the shape `{ getUser: ... }` satisfies consumers.
- **Maintenance Burden:** Adding a parameter requires updating both `IUserService.ts` and `UserService.ts`.
- **Zero Polymorphic Value:** There is only one implementation in the entire repo.

#### The Seam Decision Matrix
```
Is there more than 1 adapter in the codebase?
       │
       ├─► NO  ──► HYPOTHETICAL SEAM:
       │           Delete the interface. Export concrete functions/class directly.
       │
       └─► YES ──► REAL SEAM:
                   Where does the seam live?
                     ├─► Internal Seam: (e.g. PGLite stand-in for Postgres)
                     │   Keep interface private to module; do NOT leak to public exports.
                     │
                     └─► External Seam: (e.g. Stripe vs MockPaymentGateway)
                         Expose port at module boundary; accept dependencies via arguments.
```

#### Remediation Protocol
1. Search for interfaces implemented by exactly one class or function:
   ```bash
   rg -n 'export\s+interface\s+I[A-Z]\w*' src/
   rg -n 'class\s+\w+\s+implements\s+\w+' src/
   ```
2. Verify with `rg` that no second adapter (mock, in-memory fake, secondary vendor) implements the interface.
3. Delete `IUserService.ts`.
4. Remove `implements IUserService` from `UserService.ts` and export `UserService` directly.
5. If consumers imported `type { IUserService }`, update their type annotations to `type { UserService }` or infer from the implementation.

---

### Tenet 4: Locality & Anti-Fragmentation

> **Locality & Anti-Fragmentation Principle:**  
> *"Code that changes together must live together. Counter AI-agent context-window fragmentation by collocating single-consumer helpers in feature pods rather than scattering them into horizontal global layers."*

#### The Defect: Agent Micro-File Sprawl
When LLMs generate features, they have a strong cognitive bias toward micro-modularization across global directory layers:

```
SPRAWL ARCHITECTURE (High Token Cost & High Friction):
src/
├── components/
│   └── UserProfileCard.tsx            (25 lines)
├── hooks/
│   └── useUserProfileData.ts          (12 lines, 1 caller)
├── types/
│   └── userProfileCard.ts             (6 lines, 1 caller)
├── utils/
│   ├── formatUserInitials.ts          (4 lines, 1 caller)
│   └── formatMemberSince.ts           (5 lines, 1 caller)
└── styles/
    └── userProfileCard.module.css
```
Total: 6 files, 5 directory traversals, 5 roundtrips for any AI agent or human to understand one simple card component. When `UserProfileCard.tsx` is deleted, the other 4 files become zombie orphans.

#### The Rules of Locality

##### 1. The 1-to-1 Colocation Rule
If a helper, type, or hook has **exactly one consumer**:
- **Under ~25 LOC:** Move it into the consumer file as a non-exported private declaration.
- **Over 25 LOC or requires its own test file:** Keep it in the same directory as a sibling file (`UserProfileCard.helpers.ts`).

##### 2. The Rule of Three (Global Promotion Threshold)
Do **NOT** promote a utility to `src/utils/` or `src/lib/` unless **all three** criteria are met:
1. Consumed by **at least 3 distinct domain features** (not just 3 call sites in 1 feature).
2. Purely **domain-agnostic** (math, date formatting, string normalization, array operations).
3. Accompanied by **its own dedicated unit tests**.

##### 3. Directory Depth Ceiling
- Cap nesting at **4 levels below `src/`**.
- Ban single-child folders (e.g. `src/features/billing/components/cards/subscription-card/button/Button.tsx`). Flatten into feature pods.

##### Remediated: The Feature Pod Pattern
```
CO-LOCATED FEATURE POD (Atomic, Navigable, Zero Sprawl):
src/features/user-profile/
├── UserProfileCard.tsx            (contains inline formatters & prop types)
├── UserProfileCard.test.tsx       (tests component through public surface)
└── useUserProfileData.ts          (sibling hook, if complex enough to warrant extraction)
```

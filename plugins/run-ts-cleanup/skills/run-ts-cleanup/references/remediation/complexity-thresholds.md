# Complexity Thresholds and Code Smell Heuristics

Tool-agnostic cyclomatic and cognitive complexity budgets, plus the code-smell heuristics that predict where dead code hides. Use these thresholds to rank refactor targets: unreachable branches, ghost parameters, orphaned helpers, and unused types concentrate inside the functions that breach them.

---

## 1. Quantitative Complexity Diagnostics

Dead code survives inside overly complex functions, where branching depth hides unreferenced variables, dead conditionals, and unreachable returns. Bound complexity first; the dead code then becomes visible to both the compiler and the dead-code engine.

### Cyclomatic vs. Cognitive Complexity

Measure both. They diverge, and the divergence is the signal: a function with low cyclomatic and high cognitive complexity is deeply nested rather than broadly branched.

| Dimension | Cyclomatic Complexity (McCabe) | Cognitive Complexity |
|---|---|---|
| **What it measures** | Count of linearly independent execution paths through the function AST (`M = E - N + 2P`). | Mental effort required to follow the control flow. |
| **Increments on** | `if`, `while`, `for`, `case`, `catch`, `&&`, `\|\|`, `??`, ternary `? :`. | Breaks in linear flow, plus a **nesting penalty** per level of depth. |
| **Blind spot** | Treats a flat 10-branch `switch` as equal to 4 nested `if` blocks. | Ignores the test-permutation explosion of wide flat branching. |
| **Primary risk** | Untestable edge cases, unreachable branches, exponential test matrices. | Comprehension fatigue, high LLM hallucination rate, regression proneness. |

### Threshold Matrix

```
+-------------------------------------------------------------------------------+
|                       CYCLOMATIC COMPLEXITY THRESHOLDS                        |
+-------------------------------------------------------------------------------+
|  1 - 5    | Very Low Risk  | Simple, atomic, linear logic. Trivially testable. |
|  6 - 10   | Low Risk       | Well-structured branching. Leave alone.           |
|  11 - 15  | Warning Zone   | Inspect: nested ifs, mixed concerns, dead slop.   |
|  16 - 25  | High Risk      | Architectural defect. Split into focused          |
|           |                | functions or a table-driven dispatch map.         |
|  > 25     | Critical       | Untestable god function. Decompose into a state   |
|           |                | machine or dedicated domain handlers.             |
+-------------------------------------------------------------------------------+
```

Pair with a cognitive budget of **15** per function. Breaching either bound qualifies a function as a refactor target; breaching both makes it a priority.

### Detection Commands

Run whichever engine the repository already installs. Never add a new linter mid-cleanup; consult [../engines/lint-engines.md](../engines/lint-engines.md) for detection order.

```bash
# ESLint core: cyclomatic complexity (no plugin required)
npx eslint --rule 'complexity: ["error", 10]' src/

# ESLint core: structural shape limits that proxy for cognitive load
npx eslint --rule 'max-depth: ["error", 3]' --rule 'max-params: ["error", 3]' \
  --rule 'max-lines-per-function: ["error", 60]' src/
```

Biome measures cognitive complexity directly via `complexity/noExcessiveCognitiveComplexity` (threshold option `maxAllowedComplexity`, default `15`):

```json
{
  "linter": {
    "rules": {
      "complexity": {
        "noExcessiveCognitiveComplexity": {
          "level": "error",
          "options": { "maxAllowedComplexity": 15 }
        }
      }
    }
  }
}
```

```bash
npx @biomejs/biome lint src/
```

When no linter is configured, rank files by raw branching density as a first-pass heuristic:

```bash
# Count decision keywords per file, highest first
rg --count-matches '\b(if|else if|case|catch|while|for)\b' src/ | sort -t: -k2 -nr | head -n 20
```

---

## 2. Code Smell Heuristics

These smells are the structural precursors of dead-code findings: over-abstracted classes produce unused types, monolithic functions conceal dead internal branches, and leaky abstractions accumulate orphaned helpers. Fix the smell and the dead code surfaces on its own.

| Smell | Trigger Threshold | Dead-Code Correlate |
|---|---|---|
| **1. Brain Method / God Function** | > 60 LOC, cyclomatic > 10, cognitive > 15 | Dead internal branches and single-branch helpers |
| **2. Deep Control-Flow Nesting** | Indent depth > 3 inside logic | Unreachable error-handling paths |
| **3. Speculative Generality** | Interface or factory with <= 1 implementation | Unused types, interfaces, exports, enum members |
| **4. Long Parameter List** | >= 4 positional parameters | Ghost parameters, permanently-`undefined` arguments |
| **5. Boolean Flag Argument** | Any `boolean` parameter that forks the body | One branch with zero call sites |
| **6. Dead Store / Shadow Binding** | Value assigned then overwritten before read | Unreferenced local variables |
| **7. Feature Envy** | Function reads > 3 fields of a foreign module | Misplaced cross-module exports |
| **8. Shotgun Surgery** | One behaviour change touches > 5 files | Leaky barrels and sprawling re-export chains |

---

### Smell 1: Brain Methods / God Functions

A single function performing input validation, business logic, persistence, and response formatting in one body. Extract each concern into a named sub-function; the extraction immediately exposes which helpers and imports served only an unreachable branch.

```diff
- export async function processOrder(order: RawOrder) {
-   // 30 lines of validation...
-   // 40 lines of tax and currency conversion...
-   // 35 lines of database persistence...
-   // 20 lines of email notification...
- }
+ export async function processOrder(order: RawOrder) {
+   const validated = validateOrder(order);
+   const finalized = calculatePricing(validated);
+   const saved = await persistOrder(finalized);
+   await notifyCustomer(saved);
+   return saved;
+ }
```

Keep the extracted sub-functions unexported unless an external caller exists. Exporting them converts one smell into four dead exports.

---

### Smell 2: Deep Nesting & the Arrow Anti-Pattern

Detect logic indented three or more levels deep:

```bash
rg -n '^( {12,}|\t{3,})(if|for|while|switch)\b' src/
```

Invert the conditions into guard clauses and return early:

```diff
- function handlePayment(user: User, amount: number) {
-   if (user) {
-     if (user.isActive) {
-       if (amount > 0) {
-         executeCharge(user, amount);
-       }
-     }
-   }
- }
+ function handlePayment(user: User, amount: number) {
+   if (!user.isActive || amount <= 0) return;
+   executeCharge(user, amount);
+ }
```

Drop guards on non-nullable parameters entirely — see phantom null checks in [../detection/code-slop-catalog.md](../detection/code-slop-catalog.md).

---

### Smell 3: Speculative Generality & Ghost Abstractions

Generic interfaces, abstract base classes, factory functions, and polymorphic handlers built for requirements that never arrived. A dead-code engine reports them as unused types (`export interface IAbstractPaymentStrategyProvider`), unused exports (`export class FactoryBuilderFactory`), and unused enum members.

```bash
# Interfaces named for abstraction rather than for a domain concept
rg -n 'export (interface|abstract class) I?[A-Z]\w*(Provider|Strategy|Factory|Handler|Adapter|Manager)\b' src/

# Count implementations of a suspect interface before deleting it
rg -n 'implements\s+IPaymentStrategy\b' src/
```

Apply YAGNI pruning:
1. Delete any interface with exactly one implementer; use the concrete class or a structural type instead.
2. Delete unreferenced enum variants and union members.
3. Un-export factory wrappers and construct the class directly at the single call site.

---

### Smell 4: Long Parameter Lists & Ghost Parameters

Four or more positional arguments invite transposition bugs and sentinel padding (`renderButton("Submit", true, false, true, undefined, 12)`). Ghost parameters — accepted but never read in the body — are flagged by `no-unused-vars` / `correctness/noUnusedFunctionParameters`.

```diff
- export function createServer(host: string, port: number, ssl: boolean, timeout: number, retries: number) { ... }
+ export interface ServerOptions {
+   host: string;
+   port: number;
+   ssl?: boolean;
+   timeout?: number;
+   retries?: number;
+ }
+ export function createServer(options: ServerOptions) { ... }
```

Delete ghost parameters instead of migrating them into the options object.

---

### Smell 5: Boolean Flag Arguments

A `boolean` parameter that selects between two procedures is two functions wearing one signature:

```typescript
function getUser(id: string, includeBillingDetails: boolean) {
  if (includeBillingDetails) {
    // 20 lines fetching user and billing...
  } else {
    // 5 lines fetching basic user...
  }
}
```

Count the call sites per branch before splitting — one branch commonly has zero:

```bash
rg -n 'getUser\([^,)]+,\s*true\)' src/
rg -n 'getUser\([^,)]+,\s*false\)' src/
```

```diff
- export function getUser(id: string, includeBilling: boolean) { ... }
+ export function getUser(id: string) { ... }
+ export function getUserWithBilling(id: string) { ... }
```

If a branch has zero call sites, delete it rather than promoting it to its own function.

---

### Smell 6: Dead Stores & Shadow Bindings

Variables initialized then overwritten before any read, and inner bindings shadowing an outer identifier. Both are pure AST-local findings that a linter resolves mechanically:

```bash
# Biome
npx @biomejs/biome check --only=correctness/noUnusedVariables src/

# ESLint
npx eslint --rule 'no-unused-vars: "error"' --rule 'no-shadow: "error"' src/
```

Strip the dead assignment, or inline the computation at its single consumption point.

---

## 3. Validation

Complexity refactors change control flow, so they carry more regression risk than pure deletion. Run the canonical verification gate in [waves.md](waves.md) after each batch — do not invent a local variant. For the behaviour-preservation checks specific to structural moves, see [structural-refactor.md](structural-refactor.md).

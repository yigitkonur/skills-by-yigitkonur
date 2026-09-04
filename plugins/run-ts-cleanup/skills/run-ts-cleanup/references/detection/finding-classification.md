# Finding Classification

Classify every raw engine finding into a numbered batch, score its risk, and route it to the remediation wave that removes it.

---

## 1. The Three Axes — Do Not Mix Them

This skill uses three numbering schemes. They measure different things and never substitute for one another.

| Axis | Range | Means | Owned by |
|---|---|---|---|
| **Phase** | 0–5 | A step in the agent's workflow: pre-flight, discovery, detection, triage, root-cause, remediation. Phase 5 is the last phase. | `SKILL.md` |
| **Wave** | 1–5 (+ bridge) | A remediation step *inside Phase 5*. One structural layer, one gate run, one commit. | [`../remediation/waves.md`](../remediation/waves.md) |
| **Batch** | 1–9 | A *kind of finding*. Carries no phase number and no order of its own — it carries a `wave:` pointer to the wave that remediates it. | this file |

Rules:

- Never label a batch with a phase number. A batch is a category, not a workflow step.
- Never assume batch N maps to wave N. The mapping is many-to-one (§2).
- A generated report names the batch and its `wave:` target. It never emits a phase number.

---

## 2. Batch → Wave Map

Nine batches collapse into five waves plus the inter-wave bridge:

| Batch | Finding kind | Producing engine | `wave:` |
|---|---|---|---|
| **1** | Unused dependencies and devDependencies | Knip | Wave 1 |
| **2** | Unused and unreferenced files | Knip | Wave 2 |
| **3** | Dead barrel re-exports | Knip | Wave 3 |
| **9** | Circular dependencies | madge (or dpdm) | Wave 3 |
| **4** | Test-only leaks | Knip | Wave 4 |
| **5** | Internally-only-used exports | Knip | Wave 4 |
| **7** | Unused locals and dangling imports | Biome / Oxlint / ESLint, `tsc` | Bridge (after Wave 4) |
| **6** | Unused types, interfaces, enums | Knip | Wave 5 |
| **8** | Type-safety findings | `tsc`, `type-coverage` | Wave 5 |

### The Collapses

Three batch pairs merge because they mutate the same structural layer and must land in one commit:

- **Batches 4 and 5 both feed Wave 4.** Test-only leaks and internally-only-used exports are the same edit — removing the `export` keyword — differing only in *why* the symbol was exported. Splitting them into two waves produces two commits touching the same lines, and un-exporting a test-only leak without first relocating the test breaks the suite mid-sequence. Land both together.
- **Batches 3 and 9 both feed Wave 3.** A dead barrel re-export and a circular dependency are usually the same edge seen by two engines. Fixing one fixes the other.
- **Batches 6 and 8 both feed Wave 5.** Both are type-layer edits with zero runtime blast radius, and both are verified by the same declaration-emit extension of the gate.

### Ordering Mechanics

Wave order is causal, not stylistic. Editing exports before pruning dependencies creates ghost references; deleting files before pruning barrels creates dangling imports.

```
 Wave 1  <-- batch 1        manifests and lockfile
    |
 Wave 2  <-- batch 2        orphan modules
    |
 Wave 3  <-- batches 3, 9   graph decoupling
    |
 Wave 4  <-- batches 4, 5   encapsulation
    |
 Bridge  <-- batch 7        linter autofix clears un-export residue
    |
 Wave 5  <-- batches 6, 8   type hygiene
```

---

## 3. The Batches

### Batch 1: Unused Dependencies and DevDependencies

**Engine:** Knip · **`wave:` 1**

Packages declared in `package.json` that are never imported or referenced by any configuration.

**Rules:** `dependencies`, `devDependencies`, `unlisted`.

**Sub-kinds:**
- *True unused* — added for a decommissioned feature or replaced by another utility.
- *Hidden runtime dependency* — loaded by string from a CLI, native binary, Babel preset, PostCSS or Tailwind config. False positive.

```bash
knip --dependencies --strict
rg -g '!node_modules' -g '!dist' "dependency-name"   # catch config-string usage
```

---

### Batch 2: Unused and Unreferenced Files

**Engine:** Knip · **`wave:` 2**

Files with no incoming import edge from any configured entry point.

**Rules:** `files`.

**Common manifestations:** components stranded by a redesign, obsolete route handlers, mocks whose targets were renamed, spike scripts in `utils/`.

```bash
knip --files --reporter json > dead-files.json
rg "OldButton" --glob '!dead-files.json'   # catch dynamic and string references
```

Highest blast radius in the package: a framework-routed file deleted here passes typecheck, tests, and build, then 404s in production. Quarantine rather than delete whenever a dynamic consumer is plausible.

---

### Batch 3: Dead Barrel Re-exports

**Engine:** Knip · **`wave:` 3**

Exports inside aggregator modules (`index.ts`, `api.ts`) never consumed outside the barrel.

**Rules:** `exports` (within barrel files), `nsExports`, `duplicateExports`.

**Structural hazard:** barrels defeat tree-shaking and manufacture cycles (`A -> index -> B -> A`).

```typescript
// src/components/index.ts — before
export * from './Button';
export * from './DeadModal';                       // no consumer outside this barrel
export { ActiveCard, ObsoleteCard } from './Cards';

// after: widen nothing, name only what is consumed
export * from './Button';
export { ActiveCard } from './Cards';
```

Re-run the engine after pruning: `DeadModal.ts` now has zero incoming imports and cascades into batch 2 on the next cycle.

---

### Batch 4: Test-Only Leaks

**Engine:** Knip · **`wave:` 4**

Production symbols carrying `export` solely so a unit test can reach internal state.

**Rules:** `exports`, detected when production files are analysed against production entries only.

```bash
knip --include exports --exclude-libs
rg "internalCalculationHelper" src/    # only *.test.ts / *.spec.ts hits => test-only leak
```

**Remediation options, in preference order:**
1. Re-target the test at the public function that calls the helper.
2. Move the helper into a test harness module (`test/helpers/state.ts`).
3. If exposure is temporarily unavoidable, mark intent: `/** @internal */ export const _helper = ...`.

Never resolve this batch by un-exporting alone — the suite turns red inside Wave 4. Relocate the test first, then strip the keyword in the same commit.

---

### Batch 5: Internally-Only-Used Exports

**Engine:** Knip · **`wave:` 4**

Symbols declared with `export` but imported by no other file; used only where they are declared.

**Rules:** `exports` with `ignoreExportsUsedInFile: false`.

**Risk: lowest.** Stripping `export` changes visibility from module-public to module-private. Runtime behaviour, AST execution, and import resolution are unchanged.

```bash
rg "formatTimestampInternal" --glob '!src/utils/date.ts'   # prove zero external consumers
```

```diff
- export const formatTimestampInternal = (timestamp: number): string => {
+ const formatTimestampInternal = (timestamp: number): string => {
```

Symbols in this batch that were never called *anywhere* become unused locals on un-export and reappear as batch 7 in the bridge.

---

### Batch 6: Unused Types, Interfaces and Enums

**Engine:** Knip · **`wave:` 5**

Type declarations, interfaces, and enum members with no consumers.

**Rules:** `types`, `nsTypes`, `enumMembers`.

**Risk: zero runtime blast radius.** Types are erased at compile time; removal cannot change emitted JavaScript. The cost they impose is maintenance drag, autocomplete pollution, and agent-navigation noise.

```diff
- export interface LegacyApiResponsePayload {
-   oldField: string;
- }
```

```diff
  export enum UserStatus {
    ACTIVE = 'ACTIVE',
    INACTIVE = 'INACTIVE',
-   PENDING_VERIFICATION = 'PENDING_VERIFICATION',
  }
```

Verify with the declaration-emit extension of the gate, not with `tsc --noEmit` alone — see [`../types/declaration-emit.md`](../types/declaration-emit.md).

---

### Batch 7: Unused Locals and Dangling Imports

**Engine:** lint engine (Biome, Oxlint, ESLint) and `tsc` · **`wave:` bridge, after Wave 4**

Bindings that exist and are never read. Mostly *created* by Wave 4 rather than found before it.

**Rules:** `noUnusedVariables` / `noUnusedImports` (Biome), `no-unused-vars` / `unused-imports` (Oxlint, ESLint), `noUnusedLocals` and `noUnusedParameters` (`tsc`, diagnostic `TS6133`).

**Sub-kinds:**

| Sub-kind | Origin | Action |
|---|---|---|
| Un-export residue local | Wave 4 stripped `export` from a symbol nothing called | Delete the declaration. |
| Dangling import specifier | Consumer still imports a now-private symbol (`TS2305`) | Delete the specifier. |
| Pre-existing unused local | Ordinary rot, present before cleanup started | Delete; report separately from cleanup churn. |
| Intentionally unused parameter | Signature conformance, `_`-prefixed | False positive — see [`false-positive-triage.md`](false-positive-triage.md). |

Autofix commands live in [`../engines/lint-engines.md`](../engines/lint-engines.md). Findings in this batch are cleared by autofix, not by hand-triage.

---

### Batch 8: Type-Safety Findings

**Engine:** `tsc` and `type-coverage` · **`wave:` 5**

Type-layer defects that dead-code analysis cannot see because the symbols in question are used — just badly typed.

**Sub-kinds:**

| Sub-kind | Detector | Signal |
|---|---|---|
| Any-creep | `type-coverage --detail` | Coverage below threshold, or below the pre-flight baseline. |
| Declaration-emit risk | `tsc -b --noEmit` | `TS4023`, `TS4060`, `TS4081`, `TS2742`, `TS2883`. |
| Blind assertion | `rg "as any\|as unknown as"` | Assertions masking a real type error. |
| Implicit any parameter | `tsc --noImplicitAny` | `TS7006`, `TS7031`. |

```bash
type-coverage --detail --strict --at-least 95
tsc -b --noEmit
```

Declaration-emit failures in this batch are frequently *caused* by Wave 4: internalizing a type that still appears in a public signature. Diagnose with [`../types/declaration-emit.md`](../types/declaration-emit.md); the coverage baseline comparison belongs to post-flight in [`../remediation/waves.md`](../remediation/waves.md).

---

### Batch 9: Circular Dependencies

**Engine:** madge (or dpdm) · **`wave:` 3**

Import cycles between modules. Cause non-deterministic initialization order, `undefined` at module scope, and tree-shaking failure.

```bash
madge --circular --extensions ts,tsx src/
madge --circular --json src/ | jq '.[] | select(length > 0)'
```

**Sub-kinds:**

| Sub-kind | Action |
|---|---|
| Barrel-manufactured cycle (`A -> index -> B -> A`) | Same edit as batch 3: prune the re-export. |
| Value cycle between two modules | Extract the shared value into a leaf module. |
| Type-only cycle | Usually a false positive — `import type` is erased before runtime. Confirm before acting; see [`false-positive-triage.md`](false-positive-triage.md). |

Cycle-breaking strategies are in [`../remediation/structural-refactor.md`](../remediation/structural-refactor.md).

---

## 4. Risk Scoring Matrix

Score every batch across five vectors before remediating:

- **Blast radius** — breadth of downstream disruption across files and packages.
- **Runtime impact** — likelihood of a production exception.
- **Rollback complexity** — cost of reverting cleanly through git.
- **Gate coverage** — which leg of the gate actually catches a mistake in this batch.
- **`wave:`** — the remediation wave that removes it.

| Batch | Category | Engine / rule | Blast radius | Runtime impact | Rollback | Gate leg that catches it | `wave:` |
|---|---|---|---|---|---|---|---|
| **1** | Unused dependencies | Knip `dependencies`, `devDependencies` | Medium | Low–Medium | Low (`git checkout package.json <lockfile>` + install) | Leg 3 build | Wave 1 |
| **2** | Unused files | Knip `files` | High | Medium–High | Low (`git checkout <file>`) | Legs 1–3, and *no leg* for dynamic routes | Wave 2 |
| **3** | Dead barrel re-exports | Knip `exports`, `nsExports` | High | Low | Low (`git diff`) | Leg 1 typecheck | Wave 3 |
| **9** | Circular dependencies | madge `--circular` | High | Medium | Medium (structural edit) | Leg 2 tests, leg 3 build | Wave 3 |
| **4** | Test-only leaks | Knip `exports` | Medium | Zero | Low (`git diff`) | Leg 2 tests | Wave 4 |
| **5** | Internally-used exports | Knip `exports` | Low | Zero | Lowest (`git diff`) | Leg 1 typecheck | Wave 4 |
| **7** | Unused locals, dangling imports | lint engine, `tsc` `TS6133` | Low | Zero | Lowest (`git diff`) | Leg 1 typecheck | Bridge |
| **6** | Unused types and enums | Knip `types`, `enumMembers` | Lowest | Zero (erased) | Lowest (`git diff`) | Leg 1 + declaration emit | Wave 5 |
| **8** | Type-safety findings | `tsc`, `type-coverage` | Low | Zero | Lowest (`git diff`) | Declaration emit, coverage delta | Wave 5 |

Batch 2 is the only row where a green gate does not prove safety. Apply the Three-Question Verification Test in [`false-positive-triage.md`](false-positive-triage.md) to every batch 2 finding without exception.

---

## 5. Per-Batch Checklist

Apply to each batch, in `wave:` order:

1. **Confirm clean.** `git status --porcelain` is empty.
2. **Isolate.** Run the producing engine with only this batch's rules or flags.
3. **Triage.** Classify each finding as true defect or false positive per [`false-positive-triage.md`](false-positive-triage.md). Codify every false positive in configuration; never in a broad top-level ignore.
4. **Edit.** Apply this batch's remediation only. Do not opportunistically fix findings belonging to another wave.
5. **Run the gate.** Defined once in [`../remediation/waves.md`](../remediation/waves.md). Add the wave's extension where the wave specifies one.
6. **Commit atomically.** One commit per wave, naming the wave — not the batch number, and never a phase number.
7. **Re-run the engine.** Confirm this batch reports zero findings before advancing. A batch that does not reach zero has an uncodified false positive.

Batches sharing a wave (4+5, 3+9, 6+8) complete steps 2–4 for both, then run steps 5–7 once.

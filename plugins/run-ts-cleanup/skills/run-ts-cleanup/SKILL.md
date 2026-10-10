---
name: run-ts-cleanup
description: "Use if cleaning up a TypeScript codebase — dead code, unused deps, AI slop, weak types."
disable-model-invocation: true
---

# Run TS Cleanup

A TypeScript codebase accumulates. Features get deprecated but their files stay. A refactor lands half-finished and both abstractions survive. An LLM writes `cn` for the fourth time in a fourth directory, launders types with `as any`, duplicates schemas, and blankets properties in defensive `?.` optional chains. Dependencies outlive the code that imported them. Types get exported "just in case" and never consumed. This skill sweeps all of it into a clean end state guided by **The 4 Pillars of TypeScript Project Cleanup**:

1. **Reachability & Dead Code (Graph Layer):** Prune unreferenced files, dead exports, orphaned dependencies, and abandoned zombie features using Knip.
2. **Encapsulation & Boundary Integrity (Visibility Layer):** Decouple test-only leaks, internalize in-file exports, and designate explicit public API entry points.
3. **Type System Rigor & Soundness (Semantic Layer):** Eradicate type laundering (`as any`, `as unknown as T`), maintain the type-coverage ratchet, enforce schema inference as single source of truth (`z.infer`), and ensure declaration-emit safety.
4. **Architectural Deepening & Structural Health (Architecture Layer):** Eliminate barrel smog, inline shallow single-use wrappers, break cyclic dependency loops via Knip (`--cycles`) or `madge`/`dpdm`, restore tree-shaking, enforce locality/colocation, and maintain deterministic lockfiles.

- Every **dead symbol, file, export, type, and dependency** is found by a real engine, not by guesswork — and each finding is **triaged before deletion**, never deleted on the engine's word alone.
- Every deletion lands in a **reversible causal wave** behind a passing verification gate, so any single step reverts with one `git reset` or `git revert`.
- The **root cause** is addressed, not just the symptom: duplicate helpers get consolidated, circular barrels get untangled, single-use wrappers get inlined, and shallow abstractions are deepened — so the same bloat does not regrow.
- The codebase ends **more navigable and structurally sound than it started**, for the next agent and the next human, without a single unintended behavioral change.

This is a *finishing* tool. Run it on a green main branch, not mid-feature.

## When To Use

Trigger on phrases and repo states like:

- *"clean up this TypeScript project"*, *"my codebase is a mess"*, *"remove the dead code"*
- *"find unused dependencies"*, *"prune unused exports"*, *"delete orphaned files"*
- *"there's too much AI slop in here"*, *"tighten up the types"*, *"untangle these imports"*
- *"set up knip"*, *"run knip"*, *"why is this bundle so big"*
- Repo state: after a feature deprecation, a framework migration, or a long LLM-driven build-out.

Do **NOT** use this skill for:

- *Pure formatting or style-only changes* — run the project's own formatter; this skill deletes code.
- *Branch, worktree, and repo-artifact cleanup* — use `run-repo-cleanup`.
- *Reviewing a diff or PR* — use `run-review`.
- *A dirty working tree* — commit or stash first; Phase 0 refuses to start otherwise.
- *A red baseline* — fix the failing build or tests first. Cleanup on a broken repo cannot tell your breakage from its own.

## Modes

Pick the mode explicitly at the start, from the user's ask. Announce which one you picked. Escalating mid-run is fine; silently doing more than was asked is not.

| Mode | Runs | Fires on |
|---|---|---|
| **Sweep** | Phase 0-1, then lint autofix and Wave 1 only | *"tidy this up quickly"*, *"drop the dead files"* |
| **Standard** | Phases 0-3, then Waves 1-5 | *"clean up the dead code"* — **the default** |
| **Deep** | Standard, plus Phase 4 root-cause work, type hardening, and structural refactor | *"the codebase is a mess"*, *"make this maintainable"* |

## The Engines

No single tool finds everything. Each engine sees one scope and is blind to the others.

| Engine | Finds | Scope | Autofix? |
|---|---|---|---|
| **Knip (v5/v6)** | Unused files, exports, types, dependencies, unlisted binaries, import cycles | Module graph | Yes — native `--fix` (`--fix-type dependencies,exports,types,files`, `--allow-remove-files`) |
| **Biome / Oxlint / ESLint / Ultracite** | Unused locals (`TS6133`), dead imports, correctness lint | File AST | Yes — native autofix per engine |
| **`tsc`** | Type errors, declaration-emit breakage (`TS4023`, `TS2742`) | Program | No — diagnostic verification gate |
| **`type-coverage`** | `any`-creep score and untyped identifier coordinates | Program | No — numeric ratchet measurement |
| **`dpdm` / `madge`** | Circular dependency visualization & type-only vs runtime cycles | Import graph | No — inspection & verification |
| **anti-slop rules** | LLM-generated antipatterns (`as any`, schema drift, duplicate helpers) | File AST | Partial — targeted linters & scripts |

Knip and the linters are complements, not alternatives: Knip finds a file nothing imports, a linter finds an import nothing uses. Read [references/engines/engine-matrix.md](references/engines/engine-matrix.md) for the full matrix and the auto-detection protocol.

## Pinned Defaults

Decided once; override per-project only if the repo says otherwise (`AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` win over this skill).

| Key | Default | Why |
|---|---|---|
| **the gate** | `tsc --noEmit` (or `tsc -b --emitDeclarationOnly` / `--isolatedDeclarations` for composite projects) → `test` → `build` | The single verification barrier. Defined once in [references/remediation/waves.md](references/remediation/waves.md); every "Run the gate" in this skill means exactly that. |
| **branch** | `chore/ts-cleanup` | Never work on `main`. |
| **config file** | `knip.jsonc` (fallback `knip.json`) | JSONC carries comments explaining why each entry exists. Schema: `https://unpkg.com/knip@5/schema-jsonc.json` (or `knip@6`). |
| **package manager** | Detected from `packageManager` field, else lockfile | Never hardcode `pnpm` or run `bun test` where `bun run test` is required. See waves.md §1.2. |
| **wave order** | Files → Barrels/Cycles → Encapsulation → Types → Dependencies | Causal order: pruning leaves first eliminates dead import branches; dependencies pruned last avoids TS2307 crashes. |
| **commit unit** | One commit per wave | Each wave reverts independently. |
| **suppression** | Targeted keys only | `ignoreDependencies`, `ignoreBinaries`, `ignoreExportsUsedInFile`, explicit `entry`. |

## Non-Negotiable Safety Rails

1. **Start green.** Verify `git status --porcelain` is empty, the typecheck passes, and the test suite passes before touching anything. A cleanup that begins on a red baseline cannot distinguish its own damage from pre-existing damage.
2. **Suppress false positives with targeted keys.** Reach for `ignoreDependencies`, `ignoreBinaries`, `ignoreExportsUsedInFile`, or an explicit `entry` — each one silences exactly the finding it names. A broad top-level `ignore` severs graph edges instead, so files the ignored code imports start reporting as dead and get deleted.
3. **Triage every finding before deleting it.** Apply the Three-Question Verification Test to each one. An engine reports what it cannot see a reference to; framework entry points, dynamic imports, and published API surfaces are all invisible to it.
4. **Delete in causal wave order.** Files first, then barrels and cycles, then internalizing exports, then unused types, then dependencies and lockfile sync.
5. **Run the gate after every wave, before every commit.** A wave that fails the gate is reverted or fixed, never committed.
6. **Prove declaration-emit safety before un-exporting.** `tsc --noEmit` builds the implementation graph and never the declaration graph, so it passes on code that `tsc -b` will reject. Use `--outDir /tmp/dts-check` (avoiding the `TS5053` flag conflict) or `--isolatedDeclarations`. Never run `tsc -b --noEmit` (fails with `TS5094`). See [references/types/declaration-emit.md](references/types/declaration-emit.md).
7. **Fix the cause, then the symptom.** Consolidate the four copies of `cn` before deleting three of them; migrate the call sites before pruning the abstraction.

## The Six Phases

```
        dead code · unused deps · AI slop · weak types · tangled imports
                              │
   Phase 0 — Baseline: clean tree, green typecheck, green tests, branch cut
                              │
   Phase 1 — Engine setup: detect the stack, configure each engine, resolve the manager
                              │
   Phase 2 — Survey: run every engine, batch findings (1-9), score risk
                              │
   Phase 3 — Triage: every finding gets a verdict — dead, false-positive, or deferred
                              │
   Phase 4 — Architectural Deepening & Root Cause: consolidate duplicates, inline wrappers, [Deep]
             unify schemas via z.infer, enforce locality, generate codebase-health.md
                              │
   Phase 5 — Waves: delete in causal order, gate after each, one commit per wave
                              │
     zero dead code · green gate · one revertable commit per wave · a report you trust
```

Each phase gates the next. If you are tempted to skip one, re-survey instead.

---

## Phase 0 — Baseline

**Think first:** *"Is this repo green right now, and can I prove it?"*

1. Refuse to proceed on a dirty tree:
   ```bash
   test -z "$(git status --porcelain)" || { echo "Dirty tree — commit or stash first."; exit 1; }
   ```
2. Cut the working branch: `git checkout -b chore/ts-cleanup`
3. Resolve the package manager and write the gate script once — [references/remediation/waves.md](references/remediation/waves.md) §1.2-1.4 gives the detection snippet.
4. **Run the gate.** Record that it passed. This is the baseline every later gate is compared against.
5. Capture the starting metrics for the final report: finding counts per engine, `type-coverage` percentage, cycle count.

**Gate → Phase 1 when:** the tree is clean, the branch exists, the gate passes, and baseline metrics are recorded.

---

## Phase 1 — Engine Setup

**Think first:** *"Which engines does this repo already have, and which does it need?"*

1. Detect what is installed — Biome, Oxlint, ESLint, Prettier, Ultracite, Knip, madge, type-coverage:
   ```bash
   python3 scripts/audit-ts-health.py --target .
   ```
   With no `--check-*` flag it runs all four audits. Passing any `--check-*` flag narrows it to just those.
2. Generate or review the Knip config:
   ```bash
   python3 scripts/init-knip-config.py --dry-run     # inspect first
   python3 scripts/init-knip-config.py --format jsonc
   ```
   It detects frameworks and monorepo layout, and stamps the valid `$schema` URL (`https://unpkg.com/knip@5/schema-jsonc.json` or `knip@6`).
3. Resolve configuration hints before trusting any finding. Knip reports config hints ahead of issues; a hint left unresolved produces a cascade of false findings downstream. Tune entry points until the hints are gone — [references/engines/knip-configuration.md](references/engines/knip-configuration.md) has the plugin catalog, monorepo patterns, and built-in compiler settings.
4. Confirm zero broad top-level `ignore` patterns in the config.

**Gate → Phase 2 when:** every engine the mode needs is runnable, config hints are resolved, and no broad ignores remain.

---

## Phase 2 — Survey

**Think first:** *"What does every engine see, and how much of it is worth acting on?"*

1. Run the dead-code engine and batch its output:
   ```bash
   python3 scripts/batch-findings.py --run --output markdown --out-file cleanup-plan.md
   ```
   Batches 1-6 come from Knip, each with a risk score and a gate rendered for the detected manager.
2. Run the remaining engines the mode calls for — linters, `type-coverage`, and cycle detection (`knip --cycles` or `madge`). Their findings form Batches 7-9. Commands in [references/engines/lint-engines.md](references/engines/lint-engines.md) and [references/engines/analysis-engines.md](references/engines/analysis-engines.md).
3. Read the batch definitions and risk model in [references/detection/finding-classification.md](references/detection/finding-classification.md):
   - **Batch 1:** Unused Dependencies (Knip) → feeds Wave 5
   - **Batch 2:** Unused Files (Knip) → feeds Wave 1
   - **Batch 3:** Dead Exports (Knip) → feeds Wave 2 (barrels) & Wave 3 (internal)
   - **Batch 4:** Unused Exported Types (Knip) → feeds Wave 4
   - **Batch 5:** Unused In-File Exports (Knip) → feeds Wave 3
   - **Batch 6:** Unlisted Binaries / Missing Dependencies (Knip) → feeds Wave 5
   - **Batch 7:** Unused Local Variables & Dead Imports (`TS6133`, Linters) → feeds Inter-wave Bridge
   - **Batch 8:** Type Soundness Leaks & `any`-Creep (`type-coverage`) → feeds Phase 4
   - **Batch 9:** Import Cycles (`knip --cycles` / `madge`) → feeds Wave 2

**Gate → Phase 3 when:** `cleanup-plan.md` exists, all findings are batched (1-9), and every batch carries a risk score.

---

## Phase 3 — Triage

**Think first:** *"Which of these findings would break production if I deleted it?"*

Apply the **Three-Question Verification Test** to every finding:

1. **Framework lifecycle?** Does a convention invoke this without importing it — a Next.js `page.tsx` / `route.ts`, a Remix `loader`, an Astro content config, a Playwright fixture?
2. **Dynamic invocation?** Is it reached through a template-literal `import()`, a string-keyed registry, or runtime reflection?
3. **Public contract?** Is it exported to consumers outside this repo's static graph, via `exports` or `typesVersions`?

Verify with the codebase, not from memory:

```bash
rg -g '!node_modules' -g '!dist' 'symbolOrPackageName'
```

Codify each confirmed false positive back into config as a targeted key — never as a broad ignore. Framework entry catalogs, dynamic-import patterns, and lint/type false positives are in [references/detection/false-positive-triage.md](references/detection/false-positive-triage.md).

**Gate → Phase 4 when:** every finding in `cleanup-plan.md` carries an explicit `verdict` of `dead`, `false-positive`, or `deferred`. Zero blanks. Count them and state the number.

---

## Phase 4 — Architectural Deepening & Root Cause

**Think first:** *"Why did this bloat appear, and what stops it coming back?"*

Deep mode only. Sweep and Standard skip to Phase 5.

Deleting the symptom leaves the generator running. AI agents consistently introduce shallow abstractions, micro-file sprawl, and type escapes. Synthesizing Matt Pocock's architectural principles (deep modules, locality, seams, deletion test) into pure Markdown analysis, generate `codebase-health.md` and address the root causes:

| What you found | Core Architectural Principle | Remediation Action |
|---|---|---|
| Four copies of `cn`, duplicate `formatDate`, scattered micro-helpers | **Locality & Colocation** | Colocate single-consumer helpers in the file that uses them. Consolidate multi-consumer utilities into one canonical home. |
| Single-use wrappers (`const fetchX = (id) => api.get(...)`) | **Deep Modules** | Inline one-line wrappers or deepen the module by hiding caching, retry, and auth logic behind the interface. |
| Duplicate manual interface alongside Zod / Valibot schema | **Single Source of Truth** | Replace manual interfaces with `type T = z.infer<typeof TSchema>`. Prevent silent schema drift. |
| Java-style ghost interfaces (`IUserService` with 1 implementation) | **The Seam Test** | If an interface has exactly one implementation and no polymorphic boundary, delete the interface and expose the class/module directly. |
| Circular `index.ts` re-exports (`export * from ...`) | **Module Graph Health** | Replace barrel re-exports with explicit direct imports; untangle cyclic dependency loops (`knip --cycles`). |
| Type laundering (`as any`, `as unknown as T`, `!.`) | **Type Soundness** | Refactor data flow using discriminated unions or type guards. Remove escape hatches. |
| Blind `catch (e) { return null; }` error swallowing | **Invariant Safety** | Preserve error causality; log or bubble errors with structured context. |

Detailed patterns and code examples are cataloged in [references/detection/code-slop-catalog.md](references/detection/code-slop-catalog.md) and [references/remediation/structural-refactor.md](references/remediation/structural-refactor.md).

Consolidation is a code change like any other: run the gate and commit it before starting Wave 1.

**Gate → Phase 5 when:** duplicates are consolidated, single-use wrappers are inlined, schemas are inferred, cycles are broken, and the gate passes.

---

## Phase 5 — Waves

**Think first:** *"What is the smallest deletion I can make, prove, and commit right now?"*

Five waves, in causal order. After each: **run the gate**, then commit. A wave that fails the gate gets fixed or reverted — never committed. Full protocol, per-wave scope, and rollback in [references/remediation/waves.md](references/remediation/waves.md).

| Wave | Deletes | Additional check | Commit |
|---|---|---|---|
| **1** | Orphaned and unreferenced files (`git rm`) | — | `chore: remove unreferenced files` |
| **2** | Dead barrel re-exports; break cycles and repoint consumers | Import cycles (`knip --cycles` / `madge`) | `refactor: prune dead barrel re-exports and cycles` |
| **3** | Test-only leaks and in-file-only exports (strip `export`) | — | `refactor: internalize private exports` |
| **BRIDGE** | Linter autofix and formatter pass (between Wave 3 & 4) | Clears unused locals (`TS6133`) and formats | `chore: linter autofix and format after un-export` |
| **4** | Unused types, interfaces, enum members | Declaration emit (`--outDir /tmp/dts-check` or `tsc -b --emitDeclarationOnly`) | `refactor: prune dead types` |
| **5** | Unused dependencies, then refresh the lockfile | Lockfile synchronization (`npm`, `pnpm`, `yarn`, `bun install`) | `chore(deps): prune unused dependencies and sync lockfile` |

**Wave 3 needs the linter bridge.** Stripping an `export` turns unused in-module bindings into unused locals (`TS6133`). Run the detected engine's autofix immediately after — recipes in [references/engines/lint-engines.md](references/engines/lint-engines.md), timing rationale in waves.md §8. Note: linters clean file-local un-export residue; any consumer actively referencing a stripped export must be refactored in Wave 3 directly. Verify declaration emit before stripping anything reachable from a public signature: [references/types/declaration-emit.md](references/types/declaration-emit.md).

### Post-flight

1. Re-run every engine. Confirm zero remaining findings, or an explicit deferred list.
2. Diff the metrics against the Phase 0 baseline: findings removed, `type-coverage` delta, cycle count delta, dependency count delta.
3. Remove scratch artifacts: `cleanup-plan.md`, `.cleanup-gate.sh`, any baseline JSON. Keep `codebase-health.md` if Deep mode was requested.
4. Report what was deleted, what was deferred and why, and the metric deltas.

**Gate → done when:** every wave is committed, the gate passes on the final commit, engines report clean, and the report is delivered.

---

## Common Mistakes

| Mistake | Consequence | Instead |
|---|---|---|
| Running `tsc -b --noEmit` | Fails immediately with fatal error TS5094 | Use `tsc -b --emitDeclarationOnly` or `--outDir /tmp/dts-check` (or `--isolatedDeclarations`) |
| Passing `--no-eslintrc` in ESLint v9 | Fails immediately with `Unknown option '--no-eslintrc'` | Flat Config is the default in v9; use `--no-config-lookup` or a custom flat config |
| Pointing `$schema` to `overview/schema.json` | 404 Not Found error on schema fetch | Use `https://unpkg.com/knip@5/schema-jsonc.json` (or `knip@6`) |
| Broad top-level `"ignore": ["src/legacy/**"]` | Knip stops traversing those files, so their imports report as dead and get deleted | Use `ignoreDependencies` / `ignoreBinaries` / `ignoreExportsUsedInFile` / explicit `entry` |
| Acting on findings before resolving config hints | Every downstream finding is suspect; you triage noise | Clear hints in Phase 1, then survey |
| Suffixing entries with `!` to suppress unused export reports | `!` marks production code for `--production` mode, not public API status | Use `includeEntryExports: false` or JSDoc `@public` tags |
| Using dummy compilers like `(text) => text` | Passes raw template markup into JS parser, causing syntax parse crashes | Use Knip's built-in compilers: `"compilers": { "astro": true, "mdx": true, "svelte": true, "vue": true }` |
| One big cleanup commit | No bisect, no partial revert, unreviewable | One commit per wave |
| Deleting dependencies before pruning dead files | Orphaning transitive packages and triggering TS2307 on unreferenced code | Wave order: files → barrels → exports → types → dependencies |
| Trusting `tsc --declaration --emitDeclarationOnly --noEmit` | Fails immediately with error TS5053 option conflict | Use `tsc --declaration --emitDeclarationOnly --outDir /tmp/dts-check` or `--isolatedDeclarations` |
| Hardcoding `pnpm` or `bun test` in the gate | Breaks repositories or ignores `package.json` scripts | Resolve manager dynamically; run `bun run test` |
| Dual declaration of Zod schema + manual TypeScript interface | Types drift silently when schemas are updated | Use `type T = z.infer<typeof TSchema>` as single source of truth |
| Deleting duplicate helpers without migrating callers | Each copy had drifted; consumers depended on the differences | Consolidate, migrate, gate, *then* delete |
| Skipping Phase 0 because the repo "looks fine" | Pre-existing failures get attributed to the cleanup | Prove green first |

## Scripts

Python 3 stdlib only — no dependencies, no network beyond the engines they invoke.

| Script | Phase | Purpose | Mutates? |
|---|---|---|---|
| `scripts/audit-ts-health.py` | 1, 4 | Detects linters and formatters, audits `tsconfig.json` flags, finds import cycles, flags AI slop markers & schema drift. | No |
| `scripts/init-knip-config.py` | 1 | Scans frameworks and monorepo layout; emits `knip.jsonc`/`knip.json` with a valid, version-matched `$schema` and built-in compilers. | Yes — `--dry-run` to preview, `--force` to overwrite |
| `scripts/batch-findings.py` | 2 | Runs or parses the dead-code and analysis engines; batches findings across all 9 batches, scores risk, renders gates for the detected manager. | Only with `--out-file` |

Run any script with `--help` for its full flag surface.

## References

- [references/engines/engine-matrix.md](references/engines/engine-matrix.md) — which engine finds which class of problem, at what scope and speed; the auto-detection protocol.
- [references/engines/knip-configuration.md](references/engines/knip-configuration.md) — Knip config formats, schema, monorepo workspace isolation, built-in compilers, the plugin catalog, and targeted-vs-broad ignores.
- [references/engines/lint-engines.md](references/engines/lint-engines.md) — Biome, Oxlint, ESLint (Flat Config v9), and Ultracite recipes; safe formatting rules versus mutations to avoid mid-remediation.
- [references/engines/analysis-engines.md](references/engines/analysis-engines.md) — `type-coverage`, native Knip cycles (`knip --cycles`), `madge`, and the anti-slop rules: install, invoke, read the output.
- [references/detection/finding-classification.md](references/detection/finding-classification.md) — the nine batches, which engine produces each, the wave each feeds, and the risk model.
- [references/detection/false-positive-triage.md](references/detection/false-positive-triage.md) — the Three-Question Test, framework entry catalogs, dynamic imports, public contracts, and lint/type false positives.
- [references/detection/code-slop-catalog.md](references/detection/code-slop-catalog.md) — the 8 Sins of Agent-Written TypeScript, architectural origins of bloat, detection commands, and before/after remediation.
- [references/remediation/waves.md](references/remediation/waves.md) — **the gate**, package-manager resolution, all five waves, the linter bridge, rollback, and the post-flight metrics gate.
- [references/remediation/structural-refactor.md](references/remediation/structural-refactor.md) — Matt Pocock architectural deepening: inlining wrappers, breaking cycles, restructuring barrels, co-locating helpers, deep modules vs shallow abstractions.
- [references/remediation/complexity-thresholds.md](references/remediation/complexity-thresholds.md) — cyclomatic and cognitive complexity thresholds and the code-smell index, for prioritising what to refactor first.
- [references/types/strict-migration.md](references/types/strict-migration.md) — eliminating `any`-creep, the type-coverage ratchet, incremental strict-mode migration, type tidying.
- [references/types/declaration-emit.md](references/types/declaration-emit.md) — why un-exporting breaks `tsc -b`, compiler flag conflicts (TS5094/TS5053), `--isolatedDeclarations`, the TS4023/4081/4082/4060/2742/2883 matrix, and the pre-un-export checklist.

## Bottom Line

Prove green → configure the engines → survey every scope across all 9 batches → triage with the Three-Question Test → deepen architecture & fix the cause → delete in five gated waves → report the deltas.


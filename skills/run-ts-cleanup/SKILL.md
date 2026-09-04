---
name: run-ts-cleanup
description: "Use if cleaning up a TypeScript codebase — dead code, unused deps, AI slop, weak types."
---

# Run TS Cleanup

A TypeScript codebase accumulates. Features get deprecated but their files stay. A refactor lands half-finished and both abstractions survive. An LLM writes `cn` for the fourth time in a fourth directory. Dependencies outlive the code that imported them. Types get exported "just in case" and never consumed. This skill sweeps all of it into a clean end state:

- Every **dead symbol, file, export, type, and dependency** is found by a real engine, not by guesswork — and each finding is **triaged before deletion**, never deleted on the engine's word alone.
- Every deletion lands in a **reversible wave** behind a passing verification gate, so any single step reverts with one `git revert`.
- The **root cause** is addressed, not just the symptom: duplicate helpers get consolidated, circular barrels get untangled, single-use wrappers get inlined — so the same bloat does not regrow.
- The codebase ends **more navigable than it started**, for the next agent and the next human, without a single behavioural change.

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
| **Sweep** | Phase 0-1, then lint autofix and Wave 1 only | *"tidy this up quickly"*, *"drop the unused deps"* |
| **Standard** | Phases 0-3, then Waves 1-5 | *"clean up the dead code"* — **the default** |
| **Deep** | Standard, plus Phase 4 root-cause work, type hardening, and structural refactor | *"the codebase is a mess"*, *"make this maintainable"* |

## The Engines

No single tool finds everything. Each engine sees one scope and is blind to the others.

| Engine | Finds | Scope |
|---|---|---|
| **Knip** | Unused files, exports, types, dependencies | Module graph |
| **Biome / Oxlint / ESLint / Ultracite** | Unused locals, dead imports, correctness lint | File AST |
| **`tsc`** | Type errors, declaration-emit breakage | Program |
| **`type-coverage`** | `any`-creep, as a number | Program |
| **`madge`** | Circular dependencies | Import graph |
| **anti-slop (Oxlint plugin)** | LLM-generated antipatterns | File AST |

Knip and the linters are complements, not alternatives: Knip finds a file nothing imports, a linter finds an import nothing uses. Read [references/engines/engine-matrix.md](references/engines/engine-matrix.md) for the full matrix and the auto-detection protocol.

## Pinned Defaults

Decided once; override per-project only if the repo says otherwise (`AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` win over this skill).

| Key | Default | Why |
|---|---|---|
| **the gate** | `tsc --noEmit` → `test` → `build`, resolved for the detected package manager | The single verification barrier. Defined once in [references/remediation/waves.md](references/remediation/waves.md); every "Run the gate" in this skill means exactly that. |
| **branch** | `chore/ts-cleanup` | Never work on `main`. |
| **config file** | `knip.jsonc` (fallback `knip.json`) | JSONC carries comments explaining why each entry exists. |
| **package manager** | Detected from `packageManager` field, else lockfile | Never hardcode `pnpm`. See waves.md §1.2. |
| **wave order** | Deps → Files → Barrels → Exports → Types | Reverse order leaves dangling imports and ghost references. |
| **commit unit** | One commit per wave | Each wave reverts independently. |
| **suppression** | Targeted keys only | `ignoreDependencies`, `ignoreBinaries`, `ignoreExportsUsedInFile`, explicit `entry`. |

## Non-Negotiable Safety Rails

1. **Start green.** Verify `git status --porcelain` is empty, the typecheck passes, and the test suite passes before touching anything. A cleanup that begins on a red baseline cannot distinguish its own damage from pre-existing damage.
2. **Suppress false positives with targeted keys.** Reach for `ignoreDependencies`, `ignoreBinaries`, `ignoreExportsUsedInFile`, or an explicit `entry` — each one silences exactly the finding it names. A broad top-level `ignore` severs graph edges instead, so files the ignored code imports start reporting as dead and get deleted.
3. **Triage every finding before deleting it.** Apply the Three-Question Verification Test to each one. An engine reports what it cannot see a reference to; framework entry points, dynamic imports, and published API surfaces are all invisible to it.
4. **Delete in wave order.** Dependencies, then files, then barrels, then exports, then types. Each wave's output is the next wave's input.
5. **Run the gate after every wave, before every commit.** A wave that fails the gate is reverted or fixed, never committed.
6. **Prove declaration-emit safety before un-exporting.** `tsc --noEmit` builds the implementation graph and never the declaration graph, so it passes on code that `tsc -b` will reject. See [references/types/declaration-emit.md](references/types/declaration-emit.md).
7. **Fix the cause, then the symptom.** Consolidate the four copies of `cn` before deleting three of them; migrate the call sites before pruning the abstraction.

## The Six Phases

```
        dead code · unused deps · AI slop · weak types · tangled imports
                              │
   Phase 0 — Baseline: clean tree, green typecheck, green tests, branch cut
                              │
   Phase 1 — Engine setup: detect the stack, configure each engine, resolve the manager
                              │
   Phase 2 — Survey: run every engine, batch findings, score risk
                              │
   Phase 3 — Triage: every finding gets a verdict — dead, false-positive, or deferred
                              │
   Phase 4 — Root cause: consolidate duplicates, untangle cycles, inline wrappers  [Deep]
                              │
   Phase 5 — Waves: delete in order, gate after each, one commit per wave
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
   It detects frameworks and monorepo layout, and stamps a `$schema` matching the installed Knip major version.
3. Resolve configuration hints before trusting any finding. Knip reports config hints ahead of issues; a hint left unresolved produces a cascade of false findings downstream. Tune entry points until the hints are gone — [references/engines/knip-configuration.md](references/engines/knip-configuration.md) has the plugin catalog, monorepo patterns, and compiler settings.
4. Confirm zero broad top-level `ignore` patterns in the config.

**Gate → Phase 2 when:** every engine the mode needs is runnable, config hints are resolved, and no broad ignores remain.

---

## Phase 2 — Survey

**Think first:** *"What does every engine see, and how much of it is worth acting on?"*

1. Run the dead-code engine and batch its output:
   ```bash
   python3 scripts/batch-findings.py --run --output markdown --out-file cleanup-plan.md
   ```
   Batches 1-6 come from the dead-code engine, each with a risk score and a gate rendered for the detected manager.
2. Run the remaining engines the mode calls for — lint, `type-coverage`, `madge`. Their findings form batches 7-9. Commands in [references/engines/lint-engines.md](references/engines/lint-engines.md) and [references/engines/analysis-engines.md](references/engines/analysis-engines.md).
3. Read the batch definitions and risk model in [references/detection/finding-classification.md](references/detection/finding-classification.md) — nine batches, each naming its producing engine and the wave it feeds. Several collapse: batches 4 and 5 both feed Wave 4, 3 and 9 feed Wave 3, 6 and 8 feed Wave 5.

**Gate → Phase 3 when:** `cleanup-plan.md` exists, every finding sits in a batch, and every batch carries a risk score.

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

## Phase 4 — Root Cause

**Think first:** *"Why did this bloat appear, and what stops it coming back?"*

Deep mode only. Sweep and Standard skip to Phase 5.

Deleting the symptom leaves the generator running. Work out which origin produced each cluster, then fix that:

| What you found | Where to go |
|---|---|
| Four copies of `cn`, duplicate `formatDate`, useless try/catch, phantom null checks, boolean theater | [references/detection/code-slop-catalog.md](references/detection/code-slop-catalog.md) — origins and per-pattern remediation |
| Circular imports, bloated barrels, single-use wrappers, scattered helpers | [references/remediation/structural-refactor.md](references/remediation/structural-refactor.md) — plan-first structural work |
| Brain methods, deep nesting, long parameter lists, speculative generality | [references/remediation/complexity-thresholds.md](references/remediation/complexity-thresholds.md) — numeric thresholds to prioritise by |
| `any` sprawl, missing strict flags, weak inference | [references/types/strict-migration.md](references/types/strict-migration.md) — the ratchet |

Consolidation is a code change like any other: run the gate and commit it before starting Wave 1.

**Gate → Phase 5 when:** duplicates are consolidated behind one canonical implementation, call sites are migrated, cycles are broken, and the gate passes.

---

## Phase 5 — Waves

**Think first:** *"What is the smallest deletion I can make, prove, and commit right now?"*

Five waves, in order. After each: **run the gate**, then commit. A wave that fails the gate gets fixed or reverted — never committed. Full protocol, per-wave scope, and rollback in [references/remediation/waves.md](references/remediation/waves.md).

| Wave | Deletes | Additional check | Commit |
|---|---|---|---|
| **1** | Unused dependencies, then refresh the lockfile | — | `chore(deps): prune unused dependencies` |
| **2** | Orphaned and unreferenced files (`git rm`) | — | `chore: remove unreferenced files` |
| **3** | Dead barrel re-exports; repoint consumers at source modules | — | `refactor: prune dead barrel re-exports` |
| **4** | Test-only leaks and in-file-only exports (strip `export`) | Declaration emit, then **lint autofix** | `refactor: internalize private exports` |
| **5** | Unused types, interfaces, enum members | Declaration emit | `refactor: prune dead types` |

**Wave 4 needs the linter bridge.** Stripping an `export` leaves the importing files holding specifiers that now reference nothing. Run the detected engine's autofix immediately after — recipes in [references/engines/lint-engines.md](references/engines/lint-engines.md), timing rationale in waves.md §7. Verify declaration emit before stripping anything reachable from a public signature: [references/types/declaration-emit.md](references/types/declaration-emit.md).

### Post-flight

1. Re-run every engine. Confirm zero remaining findings, or an explicit deferred list.
2. Diff the metrics against the Phase 0 baseline: findings removed, `type-coverage` delta, cycle count delta, dependency count delta.
3. Remove scratch artifacts: `cleanup-plan.md`, `.cleanup-gate.sh`, any baseline JSON.
4. Report what was deleted, what was deferred and why, and the metric deltas.

**Gate → done when:** every wave is committed, the gate passes on the final commit, engines report clean, and the report is delivered.

---

## Common Mistakes

| Mistake | Consequence | Instead |
|---|---|---|
| Broad top-level `"ignore": ["src/legacy/**"]` | Knip stops traversing those files, so their imports report as dead and get deleted | Use `ignoreDependencies` / `ignoreBinaries` / `ignoreExportsUsedInFile` / explicit `entry` |
| Acting on findings before resolving config hints | Every downstream finding is suspect; you triage noise | Clear hints in Phase 1, then survey |
| One big cleanup commit | No bisect, no partial revert, unreviewable | One commit per wave |
| Deleting exports before pruning dependencies | Dangling imports and confusing compiler cascades | Wave order: deps → files → barrels → exports → types |
| Trusting `tsc --noEmit` before un-exporting | It never builds the declaration graph; `tsc -b` then fails on TS4023 | Verify declaration emit explicitly |
| Hardcoding `pnpm` in the gate | The gate silently no-ops on npm/yarn/bun repos | Resolve the manager from `packageManager` or the lockfile |
| Deleting duplicate helpers without migrating callers | Each copy had drifted; consumers depended on the differences | Consolidate, migrate, gate, *then* delete |
| Skipping Phase 0 because the repo "looks fine" | Pre-existing failures get attributed to the cleanup | Prove green first |

## Scripts

Python 3 stdlib only — no dependencies, no network beyond the engines they invoke.

| Script | Phase | Purpose | Mutates? |
|---|---|---|---|
| `scripts/audit-ts-health.py` | 1, 4 | Detects linters and formatters, audits `tsconfig.json` flags, finds import cycles, flags slop markers. | No |
| `scripts/init-knip-config.py` | 1 | Scans frameworks and monorepo layout; emits `knip.jsonc`/`knip.json` with a version-matched `$schema`. | Yes — `--dry-run` to preview, `--force` to overwrite |
| `scripts/batch-findings.py` | 2 | Runs or parses the dead-code engine; batches findings, scores risk, renders gates for the detected manager. | Only with `--out-file` |

Run any script with `--help` for its full flag surface.

## References

- [references/engines/engine-matrix.md](references/engines/engine-matrix.md) — which engine finds which class of problem, at what scope and speed; the auto-detection protocol.
- [references/engines/knip-configuration.md](references/engines/knip-configuration.md) — Knip config formats, schema, monorepo workspace isolation, compilers, the plugin catalog, and targeted-vs-broad ignores.
- [references/engines/lint-engines.md](references/engines/lint-engines.md) — Biome, Oxlint, ESLint, and Ultracite recipes; safe formatting rules versus mutations to avoid mid-remediation.
- [references/engines/analysis-engines.md](references/engines/analysis-engines.md) — `type-coverage`, `madge`, and the anti-slop Oxlint plugin: install, invoke, read the output.
- [references/detection/finding-classification.md](references/detection/finding-classification.md) — the six batches, which engine produces each, the wave each feeds, and the risk model.
- [references/detection/false-positive-triage.md](references/detection/false-positive-triage.md) — the Three-Question Test, framework entry catalogs, dynamic imports, public contracts, and lint/type false positives.
- [references/detection/code-slop-catalog.md](references/detection/code-slop-catalog.md) — architectural origins of bloat and the slop patterns they produce, with detection commands and before/after remediation.
- [references/remediation/waves.md](references/remediation/waves.md) — **the gate**, package-manager resolution, all five waves, the linter bridge, rollback, and the post-flight metrics gate.
- [references/remediation/structural-refactor.md](references/remediation/structural-refactor.md) — plan-first structural work: inlining wrappers, breaking cycles, restructuring barrels, co-locating helpers.
- [references/remediation/complexity-thresholds.md](references/remediation/complexity-thresholds.md) — cyclomatic and cognitive complexity thresholds and the code-smell index, for prioritising what to refactor first.
- [references/types/strict-migration.md](references/types/strict-migration.md) — eliminating `any`-creep, the type-coverage ratchet, incremental strict-mode migration, type tidying.
- [references/types/declaration-emit.md](references/types/declaration-emit.md) — why un-exporting breaks `tsc -b`, the TS4023/4081/4082/4060/2742/2883 matrix, and the pre-un-export checklist.

## Bottom Line

Prove green → configure the engines → survey every scope → give every finding a verdict → fix the cause → delete in five gated waves → report the deltas.

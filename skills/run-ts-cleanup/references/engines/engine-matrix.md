# Engine Matrix and Auto-Detection

Map the TypeScript cleanup toolchain: which engine finds which class of problem, at what scope, at what speed, and whether it can fix the problem itself. Detect the engines a repository already has before running anything. Never install a new engine or rewrite existing engine configuration during a cleanup operation.

---

## 1. Engine Capability Matrix

Six engines drive a TypeScript cleanup. Each answers a question no other engine can answer.

| Engine | What It Finds | Scope | Speed | Autofix? | Detail |
|---|---|---|---|---|---|
| **Knip** | Unused files, unused exports, unused types, unused dependencies, unused binaries | Whole-project module graph | Seconds (batch, whole repo) | No — reports only; removal is manual and waved | [`./knip-configuration.md`](./knip-configuration.md) |
| **Biome** | Unused locals, dead imports, correctness lint, formatting, import order | Single-file AST | Sub-second (Rust, parallel) | Yes — `check --write` | [`./lint-engines.md`](./lint-engines.md) |
| **Oxlint** | Unused locals, dead imports, correctness lint | Single-file AST | Sub-second (Rust, parallel) | Yes — `--fix` | [`./lint-engines.md`](./lint-engines.md) |
| **ESLint** | Unused locals, dead imports, correctness lint, type-aware rules | Single-file AST (+ project types when type-aware) | Seconds to minutes | Yes — `--fix` | [`./lint-engines.md`](./lint-engines.md) |
| **Ultracite** | Same class as Biome (zero-config wrapper) | Single-file AST | Sub-second | Yes — `fix` | [`./lint-engines.md`](./lint-engines.md) |
| **`tsc`** | Type errors, unused locals/params, broken imports, declaration emit failures (TS4023, TS4081, TS2742) | Whole-program type graph | Seconds to minutes | No — diagnostic gate only | [`../types/strict-migration.md`](../types/strict-migration.md) |
| **`type-coverage`** | Numeric any-creep score; every untyped identifier | Whole-program type graph | Seconds | No — measurement only | [`./analysis-engines.md`](./analysis-engines.md) |
| **`madge`** | Circular dependency cycles, orphan modules, leaf modules | Whole-project import graph | Seconds | No — reports cycles; breaking them is manual | [`./analysis-engines.md`](./analysis-engines.md) |
| **anti-slop** (Oxlint plugin) | LLM-generated antipatterns: chained type assertions, `unknown` laundering, widen-then-assert, runtime `typeof` | Single-file AST (runs inside Oxlint) | Sub-second | No — flags only; fixes are judgement calls | [`./analysis-engines.md`](./analysis-engines.md) |

### Reading the Matrix

- **Report-only engines** (`Knip`, `tsc`, `type-coverage`, `madge`, `anti-slop`) produce work items. Feed their output into the wave protocol in [`../remediation/waves.md`](../remediation/waves.md).
- **Autofix engines** (`Biome`, `Oxlint`, `ESLint`, `Ultracite`) consume work items mechanically. Run them to clear residue left by the report-only engines.
- **Speed dictates cadence.** Run sub-second engines on every edit. Run second-scale engines once per wave. Run minute-scale engines at wave gates only.

---

## 2. The Scope Boundary: Graph, Program, and File

No single engine sees the whole picture. Cleanup requires all three scopes because each is blind to what the others see.

```
+-------------------------------------------------------------------------------+
|                    TYPESCRIPT CLEANUP ANALYSIS SCOPES                         |
+-------------------------------------------------------------------------------+
| GRAPH SCOPE  --  Knip, madge                                                  |
| - Traverses the whole-repository module graph from configured entry points    |
| - Finds orphaned source files never imported by any module                    |
| - Finds unused npm packages in dependencies and devDependencies               |
| - Finds exported symbols, types, and enums unreferenced across files          |
| - Finds import cycles spanning arbitrarily many modules (madge)               |
| - BLIND SPOT: Internal lexical scopes; type-level correctness                 |
+---------------------------------------+---------------------------------------+
                                        | Leaves orphaned local bindings & imports
                                        v
+-------------------------------------------------------------------------------+
| FILE SCOPE  --  Biome, Oxlint, ESLint, Ultracite, anti-slop                   |
| - Parses single-file Abstract Syntax Trees (ASTs) in isolation                |
| - Tracks lexical scopes, closures, and local variable declarations            |
| - Strips unused 'import' statements within consuming files                    |
| - Removes unreferenced local 'const', 'let', 'function', and 'type' bindings  |
| - Flags syntactic antipatterns (anti-slop plugin, inside Oxlint)              |
| - BLIND SPOT: Cross-file graph resolution; cannot verify an export is dead    |
+---------------------------------------+---------------------------------------+
                                        | Cannot prove type-level soundness
                                        v
+-------------------------------------------------------------------------------+
| PROGRAM SCOPE  --  tsc, type-coverage                                         |
| - Resolves the full type graph across every file in the compilation           |
| - Proves no broken import or signature survives a removal (tsc --noEmit)      |
| - Verifies public '.d.ts' emit stays sound (tsc -b --noEmit)                  |
| - Scores the proportion of identifiers that are not 'any' (type-coverage)     |
| - BLIND SPOT: Reachability. A fully-typed export can still be 100% dead code  |
+-------------------------------------------------------------------------------+
```

### Why Cleanup Demands Every Scope

1. **Graph engines alone leave orphaned imports.** Removing `export` from a utility in Wave 4 leaves consuming files holding dangling import specifiers (`import { helper } from './utils'`). Knip cannot prune those consuming declarations.
2. **File engines alone leave zombie code.** A linter cannot determine whether `export function calculateTotal()` in `math.ts` is consumed anywhere in the repository. While `export` is present, the linter treats the symbol as public interface and ignores it.
3. **Neither proves correctness.** Only `tsc` confirms a removal broke nothing. Only `type-coverage` proves the removal did not launder types through `any` on the way.
4. **The paired workflow.** Knip un-exports the unreferenced symbol; the linter autofix strips the now-unused import in consuming files; `tsc --noEmit` passes cleanly with zero manual intervention.

### Engine Selection by Symptom

| Symptom | Engine to Run | Command |
|---|---|---|
| "This file looks abandoned" | Knip | `npx knip --include files` |
| "This package may be unused" | Knip | `npx knip --include dependencies` |
| "This export may be dead" | Knip | `npx knip --include exports,types` |
| "This import is unused" | Lint engine | `npx oxlint --fix` (or detected equivalent) |
| "Compilation broke after a removal" | `tsc` | `npx tsc --noEmit` |
| "Public `.d.ts` emit broke" | `tsc` | `npx tsc -b --noEmit` |
| "`any` is creeping back in" | `type-coverage` | `npx type-coverage --detail` |
| "Modules import each other in a loop" | `madge` | `npx madge --circular --extensions ts,tsx src/` |
| "This code reads like LLM output" | anti-slop + ripgrep | `npx oxlint` + [`../detection/code-slop-catalog.md`](../detection/code-slop-catalog.md) |

---

## 3. Lint Engine Auto-Detection Protocol

Detect the project's active linting and formatting tooling before attempting autofixes. Exactly one lint engine wins. Inspect config files and package manifests in strict priority order.

```
                  Check package.json for "ultracite"
                  or presence of ultracite.json
                                 │
                     ┌───────────┴───────────┐
                     │ Found?                │
                    YES                      NO
                     │                       │
           [Engine: Ultracite]       Check for biome.json
                                     or biome.jsonc
                                             │
                                 ┌───────────┴───────────┐
                                 │ Found?                │
                                YES                      NO
                                 │                       │
                       [Engine: Biome]       Check for .oxlintrc.json
                                             or oxlint in package.json
                                                         │
                                             ┌───────────┴───────────┐
                                             │ Found?                │
                                            YES                      NO
                                             │                       │
                                   [Engine: Oxlint]          Check for eslint.config.*
                                                             or .eslintrc.*
                                                                     │
                                                         ┌───────────┴───────────┐
                                                         │ Found?                │
                                                        YES                      NO
                                                         │                       │
                                               [Engine: ESLint]        [Fallback: tsc only]
```

### Lint Engine Detection Matrix

| Engine | Config Markers | Manifest Marker (`package.json`) | Default Autofix Command |
|---|---|---|---|
| **Ultracite** | `ultracite.json`, `.ultraciterc` | `"ultracite"` in `dependencies` or `devDependencies` | `bunx ultracite fix` or `npx ultracite fix` |
| **Biome** | `biome.json`, `biome.jsonc` | `"@biomejs/biome"` | `npx @biomejs/biome check --write` |
| **Oxlint** | `.oxlintrc.json`, `oxlint.json`, `oxlint.config.ts` | `"oxlint"` | `npx oxlint --fix` |
| **ESLint (Flat)** | `eslint.config.js`, `eslint.config.mjs`, `eslint.config.ts`, `eslint.config.cjs` | `"eslint"` (v9+) | `npx eslint --fix` |
| **ESLint (Legacy)** | `.eslintrc.js`, `.eslintrc.cjs`, `.eslintrc.json`, `.eslintrc.yaml`, `.eslintrc.yml` | `"eslint"` (v8 and earlier) | `npx eslint --fix` |

### Analysis Engine Detection Matrix

Analysis engines are additive, not exclusive — a repository may have all, some, or none. Run them via `npx` even when absent from the manifest.

| Engine | Config / Manifest Markers | Invocation | Absent? |
|---|---|---|---|
| **`tsc`** | `tsconfig.json`, `"typescript"` | `npx tsc --noEmit` | Blocking — a TypeScript cleanup requires a compiler |
| **`type-coverage`** | `"type-coverage"`, `typeCoverage` key in `package.json` | `npx type-coverage --detail` | Run ad hoc via `npx`; no ratchet baseline exists |
| **`madge`** | `"madge"` | `npx madge --circular --extensions ts,tsx src/` | Run ad hoc via `npx`, or substitute `dpdm` |
| **anti-slop** | `tools/oxlint/anti-slop/`, `jsPlugins` entry in `oxlint.config.ts` | Runs inside `npx oxlint` | Fall back to the ripgrep sweep in [`../detection/code-slop-catalog.md`](../detection/code-slop-catalog.md) |

### Automated Detection Script

Execute this snippet from the repository root to resolve the active lint engine, then inventory the available analysis engines.

```bash
#!/usr/bin/env bash
set -euo pipefail

detect_lint_engine() {
  # 1. Ultracite
  if [ -f "ultracite.json" ] || [ -f ".ultraciterc" ] || grep -q '"ultracite"' package.json 2>/dev/null; then
    if command -v bunx >/dev/null 2>&1 && { [ -f "bun.lockb" ] || [ -f "bun.lock" ]; }; then
      echo "LINT_ENGINE=ultracite"; echo "LINT_COMMAND=bunx ultracite fix"
    else
      echo "LINT_ENGINE=ultracite"; echo "LINT_COMMAND=npx ultracite fix"
    fi
    return 0
  fi

  # 2. Biome
  if [ -f "biome.json" ] || [ -f "biome.jsonc" ] || grep -q '"@biomejs/biome"' package.json 2>/dev/null; then
    echo "LINT_ENGINE=biome"; echo "LINT_COMMAND=npx @biomejs/biome check --write"
    return 0
  fi

  # 3. Oxlint
  if [ -f ".oxlintrc.json" ] || [ -f "oxlint.json" ] || [ -f "oxlint.config.ts" ] || grep -q '"oxlint"' package.json 2>/dev/null; then
    echo "LINT_ENGINE=oxlint"; echo "LINT_COMMAND=npx oxlint --fix"
    return 0
  fi

  # 4. ESLint (Flat Config)
  if compgen -G "eslint.config.*" >/dev/null; then
    echo "LINT_ENGINE=eslint-flat"; echo "LINT_COMMAND=npx eslint --fix"
    return 0
  fi

  # 5. ESLint (Legacy Config)
  if compgen -G ".eslintrc*" >/dev/null || grep -q '"eslintConfig"' package.json 2>/dev/null; then
    echo "LINT_ENGINE=eslint-legacy"; echo "LINT_COMMAND=npx eslint --fix"
    return 0
  fi

  echo "LINT_ENGINE=none"; echo "LINT_COMMAND=none"
  return 1
}

detect_analysis_engines() {
  [ -f "tsconfig.json" ] && echo "HAS_TSC=1" || echo "HAS_TSC=0"
  grep -q '"type-coverage"' package.json 2>/dev/null && echo "HAS_TYPE_COVERAGE=1" || echo "HAS_TYPE_COVERAGE=0"
  grep -qE '"(madge|dpdm)"' package.json 2>/dev/null && echo "HAS_CYCLE_TOOL=1" || echo "HAS_CYCLE_TOOL=0"
  [ -d "tools/oxlint/anti-slop" ] && echo "HAS_ANTI_SLOP=1" || echo "HAS_ANTI_SLOP=0"
  if [ -f "knip.jsonc" ] || [ -f "knip.json" ] || [ -f "knip.ts" ]; then
    echo "HAS_KNIP_CONFIG=1"
  else
    echo "HAS_KNIP_CONFIG=0"
  fi
}

detect_lint_engine || true
detect_analysis_engines
```

---

## 4. Where Each Engine Runs

Engines are not interchangeable across phases. Bind each to its stage.

| Stage | Engines | Purpose |
|---|---|---|
| **Pre-flight baseline** | `tsc`, `type-coverage`, test runner | Prove a green starting point and record ratchet baselines |
| **Discovery** | Knip, `madge`, anti-slop, ripgrep sweep | Enumerate dead code, cycles, and slop into work items |
| **Root-cause pass** | `madge`, anti-slop, lint engine | Break cycles and strip antipatterns before pruning symbols |
| **Waves 1-5** | Knip (report), manual edits | Remove dependencies, files, barrels, exports, types in order |
| **Inter-wave bridge** | Lint engine autofix | Clear un-export residue between Wave 4 and Wave 5 |
| **Wave gates** | `tsc --noEmit`, `tsc -b --noEmit`, tests, build | Prove each wave introduced zero regressions |
| **Post-flight** | Knip, `type-coverage`, `madge` | Confirm zero findings and no ratchet regression |

Consult [`../remediation/waves.md`](../remediation/waves.md) for the canonical wave sequence, the inter-wave linter bridge, and every verification gate. That file — not this one — decides *when* an engine runs.

---

## 5. Onward References

| Topic | File |
|---|---|
| Knip config schema, plugins, monorepo workspaces, compilers | [`./knip-configuration.md`](./knip-configuration.md) |
| Per-engine lint and format command recipes; safe vs prohibited autofix rules | [`./lint-engines.md`](./lint-engines.md) |
| `type-coverage`, `madge`, and the anti-slop Oxlint plugin | [`./analysis-engines.md`](./analysis-engines.md) |
| Wave sequencing, linter bridge timing, verification gates, rollback | [`../remediation/waves.md`](../remediation/waves.md) |
| Agent-driven slop heuristics and remediation recipes | [`../detection/code-slop-catalog.md`](../detection/code-slop-catalog.md) |
| Strict-mode migration, any-creep elimination, declaration emit | [`../types/strict-migration.md`](../types/strict-migration.md) |
| Cycle-breaking strategies and lightweight refactors | [`../remediation/structural-refactor.md`](../remediation/structural-refactor.md) |
| False-positive triage against framework lifecycles | [`../detection/false-positive-triage.md`](../detection/false-positive-triage.md) |

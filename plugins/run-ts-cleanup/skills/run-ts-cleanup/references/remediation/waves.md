# Remediation Waves and The Gate

Sequential, individually-revertible remediation for TypeScript cleanup. Defines **the gate** — the single verification barrier every phase, wave, and reference file in this skill refers to by name — then applies it across five waves and one inter-wave linter bridge.

---

## 1. The Gate

### 1.1 Canonical Definition

> **The Gate** is the verification barrier run after every remediation step and before every commit.
>
> **Running the gate means executing these three legs, in this order, aborting on the first non-zero exit code:**
>
> | # | Leg | Command shape | Proves |
> |---|---|---|---|
> | 1 | **Typecheck** | `tsc --noEmit` | No type error introduced or unmasked by the removal. |
> | 2 | **Test** | package `test` script | No behavioural regression; nothing deleted was live. |
> | 3 | **Build** | package `build` script | Bundler graph still resolves; no asset or dynamic edge severed. |
>
> Resolve the binary and script runner from the repository's package manager (§1.2). Never hardcode one manager.
>
> Every "Run the gate" instruction in this skill — in `SKILL.md` and in every reference file — means exactly this and nothing more. No other file restates the command.

Wave-specific work is expressed as **"the gate, plus X"** (§1.6), never as a different gate.

### 1.2 Package Manager Resolution

Resolve the manager once, at the start of Phase 0, and reuse the result for every gate invocation. Resolution order:

1. **`packageManager` field in `package.json`** (Corepack pin) — authoritative when present: `"packageManager": "pnpm@9.12.0"` resolves to `pnpm`.
2. **Lockfile at the repository root** — the table below.
3. **Fallback** — `npm`.

| Lockfile | Manager | Exec prefix (run a local binary) | Script prefix (run a `package.json` script) |
|---|---|---|---|
| `pnpm-lock.yaml` | pnpm | `pnpm exec` | `pnpm run` |
| `yarn.lock` | yarn | `yarn run` | `yarn run` |
| `bun.lockb` or `bun.lock` | bun | `bun x` | `bun run` |
| `package-lock.json` | npm | `npm exec --` | `npm run` |

### 1.3 Resolved Gate Command Per Manager

Copy the row matching the detected manager:

| Manager | The gate, fully resolved |
|---|---|
| **pnpm** | `pnpm exec tsc --noEmit && pnpm run test && pnpm run build` |
| **yarn** | `yarn run tsc --noEmit && yarn run test && yarn run build` |
| **bun** | `bun x tsc --noEmit && bun run test && bun run build` |
| **npm** | `npm exec -- tsc --noEmit && npm run test && npm run build` |

Manager-specific hazards that silently break the gate:

- **bun:** `bun test` invokes Bun's own test runner and ignores the `package.json` `test` script entirely. Always write `bun run test` in the gate.
- **npm:** `npm build` is not an alias for the `build` script. Always write `npm run build`.
- **yarn:** `yarn run <binary>` executes binaries from `node_modules/.bin` in both Yarn 1 and Yarn Berry, so it is the portable form. Berry repositories may substitute `yarn exec tsc --noEmit`.
- **all:** prefer the manager's exec prefix over bare `npx`. `npx tsc` fetches TypeScript from the registry when it is absent locally, typechecking against a version the repository does not pin.

### 1.4 Detection Snippet

Write once to `.cleanup-gate.sh`, source it in every wave, and delete it during post-flight cleanup (§11).

```bash
#!/usr/bin/env bash
# .cleanup-gate.sh — single source of truth for the gate.

detect_pm() {
  local pinned
  pinned=$(node -p "require('./package.json').packageManager || ''" 2>/dev/null)
  case "$pinned" in
    pnpm@*) echo pnpm; return ;;
    yarn@*) echo yarn; return ;;
    bun@*)  echo bun;  return ;;
    npm@*)  echo npm;  return ;;
  esac
  if   [ -f pnpm-lock.yaml ];                 then echo pnpm
  elif [ -f yarn.lock ];                      then echo yarn
  elif [ -f bun.lockb ] || [ -f bun.lock ];   then echo bun
  elif [ -f package-lock.json ];              then echo npm
  else echo npm
  fi
}

PM=$(detect_pm)
case "$PM" in
  pnpm) PM_EXEC="pnpm exec";   PM_RUN="pnpm run" ;;
  yarn) PM_EXEC="yarn run";    PM_RUN="yarn run" ;;
  bun)  PM_EXEC="bun x";       PM_RUN="bun run"  ;;
  npm)  PM_EXEC="npm exec --"; PM_RUN="npm run"  ;;
esac

has_script() { node -p "!!(require('./package.json').scripts||{})['$1']" 2>/dev/null | grep -q true; }

gate() {
  echo "--- gate [$PM] leg 1/3: typecheck ---"
  $PM_EXEC tsc --noEmit || { echo "GATE FAILED: typecheck"; return 1; }

  echo "--- gate [$PM] leg 2/3: test ---"
  if has_script test; then
    $PM_RUN test || { echo "GATE FAILED: tests"; return 1; }
  else
    echo "GATE DEGRADED: no 'test' script — see §1.5"; return 1
  fi

  echo "--- gate [$PM] leg 3/3: build ---"
  if [ "${GATE_SKIP_BUILD:-0}" = "1" ]; then
    echo "GATE PARTIAL: build skipped (inner loop only, never before a commit)"
  elif has_script build; then
    $PM_RUN build || { echo "GATE FAILED: build"; return 1; }
  else
    echo "GATE NOTE: no 'build' script — leg 3 not applicable"
  fi

  echo "--- gate PASSED ---"
}
```

Invoke it as `source .cleanup-gate.sh && gate`. Every "Run the gate" below means precisely that call.

### 1.5 Missing Script Rules

| Condition | Rule |
|---|---|
| No `test` script | The gate cannot pass. Halt cleanup and report: an untested repository has no safety net for deletions. Only proceed if the operator explicitly accepts the risk in writing, and then restrict remediation to Wave 5 (zero-runtime type pruning). |
| No `build` script | Leg 3 is not applicable — a library compiled only by `tsc` is already covered by leg 1. Record the omission in the wave commit body. |
| `test` script exits 0 with zero tests collected | Treat as no `test` script. Verify collection count before trusting a green leg 2. |
| Typecheck lives behind a script (`typecheck`, `check-types`) | Still call `tsc --noEmit` directly. Repository scripts often narrow the project scope with `-p`, hiding regressions outside that scope. |

`GATE_SKIP_BUILD=1` exists for tight iteration inside a single wave. Run the full three-leg gate before every commit without exception.

### 1.6 Gate Extensions

Extensions add a leg; they never replace one. Only these three exist:

| Extension | Where | Additional command |
|---|---|---|
| **the gate + baseline capture** | Pre-flight (§3) | Record `tsc`, `type-coverage`, and dead-code-engine snapshots. |
| **the gate + declaration emit** | Wave 5 (§10) and post-flight (§11) | `tsc -b --noEmit`, plus the diagnostics protocol in [`../types/declaration-emit.md`](../types/declaration-emit.md). |
| **the gate + type coverage** | Post-flight (§11) | `type-coverage` compared against the pre-flight baseline. |

### 1.7 Gate Failure Triage

Map the failing leg and diagnostic straight to the cause:

| Failing leg | Signal | Cause | Action |
|---|---|---|---|
| 1 typecheck | `TS2307 Cannot find module` | Wave 2 deleted a file still imported by a live consumer. | `git checkout HEAD -- <file>`; re-triage as a false positive. |
| 1 typecheck | `TS6133 declared but never read` | Wave 4 un-export residue with `noUnusedLocals: true`. | Run the inter-wave bridge (§9) before retrying. |
| 1 typecheck | `TS2305 has no exported member` | Wave 3 or 4 removed an export a consumer still imports. | Restore the export or update the consumer in the same wave. |
| 1 typecheck | `TS4023`, `TS4060`, `TS2742` | Declaration emit leak from internalizing a type. | Follow [`../types/declaration-emit.md`](../types/declaration-emit.md). |
| 2 test | Import error in a spec file | A production symbol was exported solely for tests. | Test-only leak; remediate per Wave 4 (§8), not by re-exporting. |
| 2 test | Assertion failure | Deleted code was reachable at runtime. | Revert the wave. Static analysis was wrong. |
| 3 build only | Bundler resolution error | Edge visible only to the bundler: asset import, glob, or dynamic `import()`. | Restore, then declare the entry point to the dead-code engine. |
| 3 build only | Plugin or config error | Removed a config-referenced dependency (PostCSS, Tailwind, Babel). | Reinstall and add to the engine's ignore list. |

Never bypass a red gate by loosening `tsconfig.json`, skipping a test, or adding `// @ts-expect-error`. Restore and re-triage.

---

## 2. Safety Architecture: Why Waves

Large removals landed as one commit make review impossible, break `git bisect`, obscure which deletion caused a regression, and force all-or-nothing rollback.

Remediation proceeds in isolated, sequential waves. Each wave mutates exactly one structural layer, passes the gate, and lands as one commit with a known rollback command. Order is not stylistic — it is causal: pruning exports before dependencies produces ghost references; deleting files before pruning barrels produces dangling imports.

```
 PRE-FLIGHT      the gate + baseline capture            §3
      |
      v
 WAVE 1          Dependency pruning + lockfile refresh  §5
      |
      v
 WAVE 2          Dead file pruning                      §6
      |
      v
 WAVE 3          Barrel and re-export pruning           §7
      |
      v
 WAVE 4          Internalizing exports (un-export)      §8
      |
      v
 BRIDGE          Linter autofix + format                §9
      |          (clears un-export residue)
      v
 WAVE 5          Unused type and enum pruning           §10
      |
      v
 POST-FLIGHT     the gate + declaration emit + coverage §11
```

Findings are classified into batches before any wave runs; each batch names the wave it feeds. See [`../detection/finding-classification.md`](../detection/finding-classification.md).

---

## 3. Pre-Flight: Green Baseline

Never start on a dirty tree, a red test suite, or a failing typecheck. Prove green and record baselines first.

Run each step in order. Abort immediately on any non-zero exit:

```bash
# 1. Working tree strictly clean
test -z "$(git status --porcelain)" || { echo "ERROR: dirty tree. Commit or stash."; exit 1; }

# 2. Isolated cleanup branch, never the default branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
case "$BRANCH" in
  main|master) echo "ERROR: create a branch: git checkout -b chore/ts-cleanup"; exit 1 ;;
esac

# 3. Resolve the package manager and load the gate
source .cleanup-gate.sh
echo "Detected package manager: $PM"

# 4. The gate must be green BEFORE any edit
gate || { echo "ERROR: baseline is red. Fix pre-existing failures first."; exit 1; }

# 5. Declaration emit baseline (composite projects and published libraries)
$PM_EXEC tsc -b --noEmit || { echo "ERROR: declaration build baseline failed."; exit 1; }

# 6. Type coverage baseline
$PM_EXEC type-coverage --detail > .type-coverage-baseline.txt 2>&1 || true

# 7. Dead-code engine baseline snapshot
$PM_EXEC knip --reporter json > .knip-baseline.json 2>/dev/null || true

echo "Pre-flight passed. Baselines recorded."
```

A red baseline is disqualifying, not a starting point: pre-existing failures make every subsequent gate result unreadable.

---

## 4. Per-Wave Contract

Every wave follows the same five steps. The waves below specify only what differs.

1. **Confirm clean.** `git status --porcelain` is empty.
2. **Scope.** Query the engine with only this wave's filters; act on nothing outside them.
3. **Edit.** Apply deletions or edits for this layer only.
4. **Run the gate.** Plus any extension named by the wave.
5. **Commit atomically.** One conventional commit; record the rollback command.

---

## 5. Wave 1: Dependency Pruning and Lockfile Refresh

Remove packages from `package.json` with no static consumers and no runtime binary invocation.

**Scope:** `dependencies`, `devDependencies`.
**Feeds from:** batch 1.

```bash
# 1. Isolate unused dependencies
$PM_EXEC knip --dependencies --reporter json > .wave1-deps.json
```

2. Verify each candidate against config-string consumers — PostCSS plugins, Tailwind plugins, Babel presets, Node `--loader`/`-r` flags. See [`../detection/false-positive-triage.md`](../detection/false-positive-triage.md).

3. Uninstall, then refresh the lockfile with the detected manager:

```bash
case "$PM" in
  pnpm) pnpm remove <pkg...>    && pnpm install ;;
  yarn) yarn remove <pkg...>    && yarn install ;;
  bun)  bun remove <pkg...>     && bun install  ;;
  npm)  npm uninstall <pkg...>  && npm install  ;;
esac
```

**Run the gate.** Leg 3 carries the weight here: a dependency used only by the bundler or a config file fails at build, not at typecheck.

```bash
git commit -am "chore(cleanup): wave 1 - prune unused dependencies and sync lockfile"
```

**Rollback:** `git reset --hard HEAD~1 && $PM_RUN install` (or `$PM install`) to restore `node_modules` to the reverted lockfile.

---

## 6. Wave 2: Dead File Pruning

Delete unreferenced source files, obsolete components, abandoned pages, and orphaned test utilities.

**Scope:** unreferenced `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`, `.svelte`, `.astro`.
**Feeds from:** batch 2.

```bash
# 1. Isolate unreferenced files
$PM_EXEC knip --files --reporter json > .wave2-files.json

# 2a. High confidence: delete
git rm src/components/ObsoleteComponent.tsx

# 2b. Low confidence: quarantine, keeping history
mkdir -p .quarantine && git mv src/components/ObsoleteComponent.tsx .quarantine/
```

Quarantine any file whose only apparent consumer would be dynamic. Deleting a framework-routed file typechecks, tests, and builds cleanly, then 404s in production — the highest blast radius in the whole protocol.

**Run the gate.**

```bash
git commit -m "chore(cleanup): wave 2 - delete orphaned and unreferenced files"
```

**Rollback:** `git reset --hard HEAD~1`, or restore one file with `git checkout HEAD~1 -- <path>`.

---

## 7. Wave 3: Barrel and Re-export Pruning

Break tree-shaking barriers and cycles by removing dead re-exports from aggregator files.

**Scope:** `export * from './module'`, `export { DeadSymbol } from './module'`.
**Feeds from:** batches 3 and 9.

```bash
# 1. Isolate barrel-level export findings
$PM_EXEC knip --include exports,nsExports --reporter json > .wave3-barrels.json

# 2. Confirm cycles that the barrel creates
$PM_EXEC madge --circular --extensions ts,tsx src/
```

3. Replace wildcard `export *` with explicit named exports of consumed symbols only.
4. Delete re-export statements with zero external consumers.
5. Re-run the dead-code engine: files orphaned by step 4 cascade into Wave 2 on the next cycle.

Cycle-breaking strategies beyond deletion — leaf type modules, dependency inversion — are in [`structural-refactor.md`](structural-refactor.md).

**Run the gate.**

```bash
git commit -am "chore(cleanup): wave 3 - prune unused barrel re-exports"
```

**Rollback:** `git reset --hard HEAD~1`.

---

## 8. Wave 4: Internalizing Exports (Un-Export)

Convert exported symbols consumed only inside their defining module into private declarations by removing the `export` keyword.

**Scope:** `export const helper` → `const helper`; `export function parse` → `function parse`.
**Feeds from:** batches 4 and 5 — both land in this wave (see §2 of [`../detection/finding-classification.md`](../detection/finding-classification.md)).

```bash
# 1. Isolate export findings
$PM_EXEC knip --include exports --reporter json > .wave4-exports.json

# 2. Prove no external consumer before stripping each symbol
rg -w "SYMBOL_NAME" --glob '!src/defining-module.ts' --glob '!**/node_modules/**'
```

3. Strip `export` from each verified symbol.
4. For a test-only leak (batch 4), do not un-export blindly: move the helper into a test utility module or re-target the test at the public caller. Un-exporting alone turns a green suite red.

**Run the gate.** Expect leg 1 to surface `TS6133` under `noUnusedLocals` — that is the residue the bridge (§9) exists to clear, not a reason to revert.

```bash
git commit -am "chore(cleanup): wave 4 - internalize in-file exports"
```

**Rollback:** `git reset --hard HEAD~1`.

---

## 9. Inter-Wave Bridge: Linter and Formatter Phase

Run between Wave 4 and Wave 5. **This section owns the timing rationale; it does not own the commands.**

### 9.1 Why Here, Not Earlier or Later

Stripping `export` in Wave 4 produces an **un-export residue cascade** that no earlier wave can create and that Wave 5 cannot tolerate:

1. **Unused local bindings.** A symbol exported "just in case" and never called anywhere becomes an unused local the moment `export` is removed. `noUnusedLocals: true` fails leg 1 of the gate immediately.
2. **Dangling import specifiers.** Consumers that imported the now-private symbol hold broken specifiers — `import { nowPrivateHelper } from './module'`.
3. **AST formatting disruption.** Scripted edits leave trailing commas, orphaned braces, and misaligned import brackets that pollute the Wave 5 diff.

```
 Wave 4 action   Strip 'export' from in-file-only symbols
       |
       v
 Residue         1. Unused local declarations  (TS6133)
                 2. Dangling import specifiers (TS2305)
                 3. Malformed import brackets
       |
       v
 Cure            Linter autofix + formatter pass
       |
       v
 Result          Clean AST, zero dangling bindings, Wave 5 ready
```

Running the linter **before** Wave 4 fixes nothing — the residue does not exist yet. Running it **after** Wave 5 is worse: dangling imports and unused locals contaminate the type-pruning diff, so an unrelated formatting change and a semantic type deletion land in the same commit and become unbisectable.

### 9.2 Commands

Detect the active engine and run its autofix and format recipe from [`../engines/lint-engines.md`](../engines/lint-engines.md) — the canonical source for Biome, Oxlint, and ESLint invocations, unsafe-fix flags, and formatter pairing. Do not restate those commands here.

Constraints on the bridge pass:

| Rule | Reason |
|---|---|
| Scope the autofix to source directories only. | A repo-wide format pass buries the semantic diff. |
| Run the linter and the formatter as one commit. | Splitting them produces two noisy, non-semantic commits. |
| Never let autofix delete an exported symbol. | Export removal is Wave 4's decision, made with consumer proof. |
| Review the diff before committing, especially unsafe fixes. | Unsafe rules rewrite semantics, not just formatting. |

**Run the gate.**

```bash
git commit -am "chore(cleanup): bridge - linter autofix and format after un-export"
```

**Rollback:** `git reset --hard HEAD~1`.

---

## 10. Wave 5: Unused Type and Enum Pruning

Prune unused type aliases, interfaces, and enum members.

**Scope:** `export type UnusedAlias`, `export interface ObsoleteContract`, dead enum variants.
**Feeds from:** batches 6 and 8.

```bash
# 1. Isolate type-only findings
$PM_EXEC knip --include types,nsTypes,enumMembers --reporter json > .wave5-types.json
```

2. Delete unreferenced interfaces, type aliases, and enum members.
3. Clean up dangling `import type { DeadType } from './types'` specifiers.

**Run the gate, plus declaration emit:**

```bash
gate && $PM_EXEC tsc -b --noEmit
```

Leg 1 of the gate validates local types only. In composite projects and published libraries, `tsc -b --noEmit` is the only check that proves `.d.ts` generation still succeeds across project references and that no now-private type leaked into a public signature. Diagnose `TS4023`, `TS4060`, `TS4081`, `TS2742`, and `TS2883` with [`../types/declaration-emit.md`](../types/declaration-emit.md).

```bash
git commit -am "chore(cleanup): wave 5 - prune unused types, interfaces, and enum members"
```

**Rollback:** `git reset --hard HEAD~1`.

---

## 11. Post-Flight Reconciliation and Metrics

Run once, after Wave 5 commits.

### 1. Dead-code engine reaches zero

```bash
$PM_EXEC knip
```

Any remaining finding is either an unremediated batch or an uncodified false positive. Resolve it in configuration, not by another ad-hoc deletion.

### 2. The gate + declaration emit

```bash
source .cleanup-gate.sh
gate && $PM_EXEC tsc -b --noEmit || { echo "ERROR: post-flight verification failed."; exit 1; }
```

### 3. The gate + type coverage

Prove that pruning did not degrade type safety or admit implicit `any`:

```bash
$PM_EXEC type-coverage --detail --strict --at-least 95 \
  || echo "WARNING: coverage below threshold — inspect newly introduced any types."

if [ -f .type-coverage-baseline.txt ]; then
  diff -u .type-coverage-baseline.txt <($PM_EXEC type-coverage --detail 2>&1) || true
fi
```

Coverage must be greater than or equal to the pre-flight baseline. Deleting well-typed code while leaving `any`-heavy code raises the untyped ratio — a real regression that a green gate will not catch.

### 4. Diff accounting

```bash
git diff --stat origin/main...HEAD
git log --oneline origin/main..HEAD   # expect one commit per wave, plus the bridge
```

### 5. Remove temporary artifacts

```bash
rm -f .knip-baseline.json .wave*-*.json .type-coverage-baseline.txt .cleanup-gate.sh
```

---

## 12. Rollback Reference

| Situation | Command |
|---|---|
| Last wave is bad, nothing pushed | `git reset --hard HEAD~1` |
| Last wave is bad, already pushed | `git revert HEAD` |
| Wave 1 reverted (lockfile changed) | `git reset --hard HEAD~1 && $PM install` |
| One file from a wave was wrong | `git checkout HEAD~1 -- <path>` |
| Regression found later, wave unknown | `git bisect start HEAD origin/main`, then bisect with `gate` as the test command |
| Abandon the whole cleanup | `git checkout main && git branch -D chore/ts-cleanup` |

One commit per wave is what makes each of these a single command. Never squash waves before the cleanup is verified in production.

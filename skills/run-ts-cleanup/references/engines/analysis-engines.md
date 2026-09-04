# Analysis Engines

Three measurement engines that no linter and no module-graph tool replaces: `type-coverage` scores any-creep, `madge` maps import cycles, and the `anti-slop` Oxlint plugin mechanically flags LLM-generated antipatterns.

All three are **report-only**. They produce work items; they never edit source. Feed their output into the wave protocol in [`../remediation/waves.md`](../remediation/waves.md).

| Engine | Question It Answers | Clean Result |
|---|---|---|
| `type-coverage` | "What fraction of identifiers are not `any`?" | Percentage at or above the recorded ratchet |
| `madge` | "Do modules import each other in a loop?" | `No circular dependency found!` |
| `anti-slop` | "Does this code carry mechanical LLM tells?" | Zero `anti-slop/*` diagnostics from `npx oxlint` |

---

## 1. `type-coverage` — Any-Creep Score

`type-coverage` computes a single number: the count of identifiers whose type is not `any`, divided by the total count of identifiers. Use it as a ratchet — a floor that only ever rises.

### Install and Invoke

```bash
npm i -D type-coverage                       # or run ad hoc via npx

npx type-coverage                            # global percentage only
npx type-coverage --detail                   # every untyped identifier
npx type-coverage --strict --detail          # count catch + dynamic-index any
npx type-coverage -p tsconfig.build.json     # non-root tsconfig
npx type-coverage --json-output              # machine-readable
```

### Verified Flag Surface

| Flag | Effect |
|---|---|
| `-p, --project` | Path to the `tsconfig.json` to analyze |
| `--detail` | Print every untyped identifier with file, line, and column |
| `--at-least <n>` | Exit non-zero when the coverage rate falls below `n` |
| `--strict` | Stricter counting; includes catch-clause and dynamic-index `any` |
| `--ignore-catch` | Exclude catch-clause variables from the score |
| `--ignore-files <glob>` | Exclude files from analysis |
| `--ignore-unread` | Permit writes to variables with implicit `any` |
| `--cache` | Cache results between runs for speed |
| `--update` | Write the current rate into the `typeCoverage` block in `package.json` |
| `--json-output` | Emit results as JSON |
| `--history-file <path>` | Append the score to a history file for trend tracking |
| `--report-semantic-error` | Surface TypeScript semantic errors alongside the score |

### Read the Output

The summary line reports typed identifiers over total identifiers, followed by the rate:

```
2874 / 3011 95.45%
```

With `--detail`, each untyped identifier is listed as `file:line:column: identifier`. Rank the worst files to find hotspots:

```bash
npx type-coverage --detail | grep -v success | awk -F: '{print $1}' \
  | sort | uniq -c | sort -rn | head -n 30
```

**A clean result is not 100%.** It is *no lower than the recorded baseline*. Third-party type gaps and unavoidable dynamic boundaries put a real ceiling below 100.

### Use as a Ratchet

Record a baseline before touching code, then re-measure at the post-flight gate. Cleanup must raise the number or leave it flat — never lower it.

```bash
# Pre-flight: capture the baseline
npx type-coverage --detail > .type-coverage-baseline.txt 2>&1 || true

# Post-flight: see exactly which identifiers regressed
diff -u .type-coverage-baseline.txt <(npx type-coverage --detail 2>&1) || true

# Raise the floor after a successful pass (rewrites typeCoverage.atLeast)
npx type-coverage --update
```

### Gate in CI

Pin the threshold in `package.json` so CI and local runs agree, then enforce it with `--at-least` — the documented failure flag:

```json
{
  "typeCoverage": {
    "atLeast": 95,
    "strict": true,
    "ignoreCatch": true,
    "ignoreFiles": ["src/generated/**"],
    "cache": true
  }
}
```

```bash
npx type-coverage --at-least 95 --strict    # non-zero exit below the floor
```

### Feed into the Workflow

A coverage drop during cleanup means a removal was papered over with `any` or a cast instead of being resolved. Treat any regression as a defect in the wave, not as a new baseline. Consult [`../types/strict-migration.md`](../types/strict-migration.md) for replacing `any` at input boundaries, dictionary indexing, and catch clauses.

---

## 2. `madge` — Circular Dependency Graph

`madge` builds the import graph and reports cycles. Cycles cause non-deterministic module initialization, `undefined` imports at runtime, and defeat tree-shaking — and they routinely block barrel pruning during cleanup.

### Install and Invoke

```bash
npm i -D madge                               # or run ad hoc via npx

# Primary cycle scan
npx madge --circular --extensions ts,tsx src/

# Resolve TypeScript path aliases (@/lib/...) through tsconfig
npx madge --circular --extensions ts,tsx --ts-config tsconfig.json src/

npx madge --circular --extensions ts,tsx --json src/    # machine-readable
npx madge --image graph.svg --extensions ts,tsx src/    # render (needs Graphviz)
npx madge --orphans --extensions ts,tsx src/            # modules nothing imports
npx madge --depends src/lib/utils.ts src/               # dependents of one module
```

### Verified Flag Surface

| Flag | Effect |
|---|---|
| `-c, --circular` | Report circular dependencies |
| `--extensions <list>` | Comma-separated extensions to resolve (`ts,tsx`) |
| `--ts-config <path>` | Resolve aliased modules through a `tsconfig.json` |
| `--json` | Emit results as JSON |
| `--image <file>` | Write the graph to an image (requires Graphviz) |
| `--dot` | Emit DOT format for downstream processing |
| `--exclude <regexp>` | Exclude modules matching a pattern |
| `--orphans` | List modules with no dependents |
| `--leaves` | List modules with no dependencies |
| `--depends <module>` | List modules depending on the given module |
| `--warning` | Show skipped files and warnings |

### Read the Output

A clean repository prints exactly:

```
No circular dependency found!
```

A repository with cycles prints a count, then one numbered chain per cycle, where each chain lists the modules in import order and implicitly loops back to the first:

```
Found 2 circular dependencies!

1) src/store/index.ts > src/store/user.ts > src/store/index.ts
2) src/lib/api.ts > src/lib/auth.ts > src/lib/client.ts > src/lib/api.ts
```

Read the **shortest** cycle first — two-module cycles almost always resolve by extracting a shared type or constant into a leaf file. Long chains usually pass through a barrel `index.ts`; break those by importing directly from source modules.

`madge --circular` exits with code **1** when any cycle is found and **0** when the graph is clean, so it gates cleanly in CI:

```bash
npx madge --circular --extensions ts,tsx src/ || {
  echo "ERROR: circular dependencies detected"; exit 1;
}
```

### `dpdm` Alternative

`dpdm` resolves TypeScript and path aliases natively and traverses from explicit entry points rather than a directory glob. Prefer it when `madge` mis-resolves aliases or when cycle detection must start at a known entry.

```bash
# Cycles only, suppressing the tree and warnings
npx dpdm --circular --warning=false --tree=false ./src/index.ts

# Fail CI on cycles (format is CASE:CODE; 'circular' is the only supported CASE)
npx dpdm --exit-code circular:1 ./src/index.ts

# Write results to JSON
npx dpdm --circular -o cycles.json ./src/index.ts
```

| Trait | `madge` | `dpdm` |
|---|---|---|
| Traversal root | Directory glob (`src/`) | Explicit entry point(s) |
| Alias resolution | Via `--ts-config` | Native |
| Graph images | Yes (Graphviz) | No |
| CI failure | Exit 1 on `--circular` | `--exit-code circular:1` |

### Feed into the Workflow

Run the cycle scan during the root-cause pass, **before** pruning barrels or exports. Cycles distort the module graph Knip reads, and breaking a cycle frequently converts a "false positive" export into genuinely dead code. Consult [`../remediation/structural-refactor.md`](../remediation/structural-refactor.md) for leaf-module extraction and other cycle-breaking strategies. Re-run at the post-flight gate to confirm cleanup introduced no new cycles.

---

## 3. `anti-slop` — Oxlint Plugin for LLM Antipatterns

`anti-slop` (`dmmulroy/anti-slop`) is an opinionated Oxlint JS plugin that rejects low-evidence TypeScript patterns — the mechanical tells of LLM-generated code. It ships roughly 15 generic rules plus an opt-in Effect ruleset.

The plugin is **not published to npm**. Vendor it into the repository and register it as an Oxlint JS plugin.

> The plugin's own README and its bundled `install-anti-slop` skill are authoritative for the current rule list, rule options, and install surface. Verify against the source before relying on any specific rule name below.

### Install

**Path A — bundled agent skill (recommended):**

```bash
# Fetch the skill, which carries the plugin source and its installer
npx skills add dmmulroy/anti-slop --skill install-anti-slop

# Run the installer from the target repository root.
# Copies the plugin to tools/oxlint/anti-slop/ by default.
node <skill-directory>/scripts/install.mjs
```

The installer takes an alternate relative destination as its first positional argument. It refuses to overwrite an existing destination; `--force` overrides that only after reviewing the existing files.

**Path B — manual vendoring:** copy the plugin's `src/` directory into the repository (for example `tools/oxlint/anti-slop/`), then pin `@oxlint/plugins` to *exactly* the repository's installed `oxlint` version so future upgrades move both together:

```bash
npm i -D @oxlint/plugins@<exact-oxlint-version>
```

### Register

Add the plugin to `oxlint.config.ts`, ignore agent-tooling directories and the vendored plugin itself, and enable the rules:

```ts
import { defineConfig } from "oxlint";

export default defineConfig({
  ignorePatterns: [
    ".agent/**", ".agents/**", ".claude/**", ".codex/**", ".cursor/**",
    ".gemini/**", ".opencode/**", ".windsurf/**",
    "tools/oxlint/anti-slop/**",
  ],
  jsPlugins: [
    { name: "anti-slop", specifier: "./tools/oxlint/anti-slop/index.ts" },
  ],
  rules: {
    "anti-slop/no-chained-type-assertions": "error",
    "anti-slop/no-conditional-empty-object-spread": "error",
    "anti-slop/no-known-value-widening": "error",
    "anti-slop/no-module-mocking": "error",
    "anti-slop/no-object-parameters": "error",
    "anti-slop/no-reflect-apply": "error",
    "anti-slop/no-reflect-get": "error",
    "anti-slop/no-runtime-typeof": "error",
    "anti-slop/no-shape-in-symbol-names": "error",
    "anti-slop/no-unknown-parameters": "error",
    "anti-slop/no-unknown-returns": "error",
    "anti-slop/no-unknown-type-aliases": "error",
    "anti-slop/no-unsafe-dictionary-type": "error",
    "anti-slop/no-widen-then-assert": "error",
    "anti-slop/require-safety-comment-for-type-assertion": "error",
  },
});
```

Merge these fields into existing configuration rather than replacing it. Preserve every existing ignore pattern.

Register the Effect ruleset **only** when `effect` is a direct dependency in a package manifest, or when explicitly requested — never because Effect appears transitively in a lockfile:

```ts
jsPlugins: [
  { name: "anti-slop-effect", specifier: "./tools/oxlint/anti-slop/effect/index.ts" },
],
rules: { "anti-slop-effect/no-service-constructor-imports": "error" },
```

### Invoke

Once registered, the plugin runs as part of the ordinary Oxlint pass — no separate binary and no extra flags:

```bash
npx oxlint
npx oxlint src/
```

### Read the Output

Diagnostics arrive in standard Oxlint format, namespaced under `anti-slop/`. **A clean result is zero `anti-slop/*` diagnostics.**

`anti-slop` rules are **not autofixable** — every finding is a design decision. Resolve findings by strengthening types: prefer inference, `as const`, `satisfies`, named owner contracts, and parsing at boundaries. Never resolve a finding by lowering rule severity, adding a suppression comment, or inserting a cast to launder the type.

A small number of rules take options — for example, the safety-comment rule accepts a configurable marker prefix (default `SAFETY`), and the runtime-`typeof` rule can permit usage inside type guards. Consult the plugin README for exact option names and shapes rather than guessing.

### Mechanical Detection vs. Judgement Calls

`anti-slop` and the ripgrep heuristics in [`../detection/code-slop-catalog.md`](../detection/code-slop-catalog.md) target the same problem from opposite directions. Run both.

| Dimension | `anti-slop` plugin | Ripgrep heuristics (`code-slop-catalog.md`) |
|---|---|---|
| **Basis** | AST-aware Oxlint rules | Text patterns over source |
| **Precision** | High — understands syntax and scope | Lower — matches text, produces false positives |
| **Coverage** | Fixed rule set, mostly type-level laundering | Open-ended: dead try/catch, obvious comments, boolean theater, duplicated utilities |
| **Determinism** | Deterministic, repeatable, CI-gateable | Requires agent judgement on every hit |
| **Setup cost** | Vendoring plus config registration | None — ripgrep only |
| **Fix mode** | Manual; no autofix | Manual, per the catalog's remediation recipes |

**Prefer `anti-slop` when** the repository already uses Oxlint, cleanup will recur, or a durable CI gate is the goal. Deterministic rules beat re-derived heuristics and cost nothing per run once installed.

**Prefer the ripgrep sweep when** the repository has no Oxlint setup, the cleanup is one-off, or the target slop is outside the plugin's rule set — duplicated `formatDate` implementations, passthrough `catch (e) { throw e; }`, and tautological comments are text-pattern problems the plugin does not cover.

**Run both when** cleaning up after sustained LLM-driven development. Their coverage overlaps only slightly: the plugin catches type-level laundering that ripgrep cannot see, and the catalog catches structural and semantic slop that no fixed rule set enumerates.

### Feed into the Workflow

Run `anti-slop` during the root-cause pass, before pruning exports. Slop removal frequently deletes the only consumer of a symbol, converting a live export into genuinely dead code that the next Knip run will surface. Fixing slop *after* pruning wastes a wave.

---

## 4. Combined Analysis Sweep

Run all three engines together during the root-cause pass and again at the post-flight gate:

```bash
#!/usr/bin/env bash
set -uo pipefail

echo "=== Type coverage ==="
npx type-coverage --detail --strict | tail -n 1

echo "=== Circular dependencies ==="
npx madge --circular --extensions ts,tsx --ts-config tsconfig.json src/

echo "=== LLM antipatterns (anti-slop via oxlint) ==="
npx oxlint src/ 2>&1 | grep -E 'anti-slop/' || echo "No anti-slop findings."
```

Record the pre-flight results as baselines. At the post-flight gate, require: coverage at or above baseline, zero cycles, and zero `anti-slop` diagnostics. Consult [`../remediation/waves.md`](../remediation/waves.md) for gate sequencing and rollback, and [`./engine-matrix.md`](./engine-matrix.md) for how these engines relate to Knip and the lint engines.

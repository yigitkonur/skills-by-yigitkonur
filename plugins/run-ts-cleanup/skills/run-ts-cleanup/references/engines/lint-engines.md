# Lint and Format Engines

Per-engine command reference for the file-level AST engines: Biome, Oxlint, ESLint, and Ultracite. Use these recipes to strip unused local bindings, remove dangling import specifiers, and produce clean non-breaking formatting diffs.

**Scope of this file:** engine commands and configuration only.

- Detect which engine a repository uses: [`./engine-matrix.md`](./engine-matrix.md) §3.
- Decide *when* to run an engine, and run the verification gate afterward: [`../remediation/waves.md`](../remediation/waves.md) §7 (Inter-Wave Bridge) and §9 (Post-Flight Reconciliation). That file is the canonical authority for linter timing and for every gate command.

---

## 1. Command Cheat Sheet

Run the recipe matching the detected engine. Restrict autofixes to files modified in the active wave, or to target source directories directly.

| Engine | Full Autofix | Unused-Only Autofix | Formats? | Sorts Imports? |
|---|---|---|---|---|
| **Biome** | `npx @biomejs/biome check --write src/` | `--only=lint/correctness/noUnusedVariables,lint/correctness/noUnusedImports` | Yes | Yes |
| **Oxlint** | `npx oxlint --fix src/` | `npx oxlint --fix -D no-unused-vars src/` | No — pair with Prettier or Biome | No |
| **ESLint** | `npx eslint --fix "src/**/*.{ts,tsx}"` | `--rule 'unused-imports/no-unused-imports: error'` | Only via `eslint-plugin-prettier` | Only via plugin |
| **Ultracite** | `npx ultracite fix` | Not exposed — wrapper applies its bundled ruleset | Yes | Yes |

---

## 2. Biome

Biome combines sub-millisecond linting, formatting, and import organization into a single binary.

### Primary Autofix Command

```bash
# Full autofix across project files (formats, organizes imports, removes unused)
npx @biomejs/biome check --write src/

# For pnpm projects
pnpm biome check --write src/

# For Bun projects
bunx biome check --write src/
```

### Targeted Unused Import and Variable Autofix

Run strictly to clean up un-export residue without modifying unrelated code:

```bash
npx @biomejs/biome check --write \
  --only=lint/correctness/noUnusedVariables,lint/correctness/noUnusedImports \
  src/
```

### Unsafe Autofix Flag

Pass `--unsafe` when Biome requires permission to remove code that may carry subtle AST side effects, such as imports with side-effect initializers:

```bash
npx @biomejs/biome check --write --unsafe src/
```

Review the resulting diff before staging. `--unsafe` is the only lint flag in this file that can alter runtime behavior.

### Optimal `biome.json` Configuration for Dead Code Cleanup

Verify or configure `biome.json` to enable automated dead-import pruning and import organization:

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error",
        "noUnusedImports": "error"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  }
}
```

---

## 3. Oxlint

Oxlint is an ultra-fast Rust-based linter designed to run ahead of ESLint. It catches dead code and syntax issues in milliseconds.

### Primary Autofix Command

```bash
# Run Oxlint with autofixing enabled
npx oxlint --fix

# Target specific directories
npx oxlint --fix src/
```

### Targeted Rule Execution

Enforce strict unused variable and import pruning:

```bash
npx oxlint --fix \
  -D no-unused-vars \
  src/
```

### Oxlint + Formatter Pairing

Oxlint does not format files or sort imports. Pair Oxlint with Prettier or Biome for formatting:

```bash
# Run Oxlint autofix followed by Prettier import/comma formatting
npx oxlint --fix src/ && npx prettier --write "src/**/*.{ts,tsx}"
```

### Oxlint as the anti-slop Host

Oxlint doubles as the host for the `anti-slop` JS plugin, which mechanically flags LLM-generated antipatterns during the same pass. When `tools/oxlint/anti-slop/` is registered in `oxlint.config.ts`, a plain `npx oxlint` reports both standard lint diagnostics and `anti-slop/*` findings. Consult [`./analysis-engines.md`](./analysis-engines.md) §3 for installation and rule inventory.

---

## 4. ESLint

ESLint is the standard JavaScript/TypeScript linter. Configuration varies between Flat Config (v9+) and Legacy Config (v8).

### Primary Autofix Commands

```bash
# Standard autofix across source files
npx eslint --fix "src/**/*.{js,jsx,ts,tsx}"

# For pnpm projects
pnpm eslint --fix "src/**/*.{js,jsx,ts,tsx}"

# For Flat Config explicitly when environment requires flag
ESLINT_USE_FLAT_CONFIG=true npx eslint --fix "src/**/*.{js,jsx,ts,tsx}"
```

### Targeted Single-Rule Autofix

Avoid triggering slow style or complexity rules across the repository during a remediation wave by targeting strictly unused imports:

```bash
# Requires eslint-plugin-unused-imports in the project
npx eslint --fix \
  --no-eslintrc \
  --rule 'unused-imports/no-unused-imports: error' \
  "src/**/*.{ts,tsx}"
```

### Essential ESLint Rules for Dead Code Remediation

Ensure the project's ESLint configuration incorporates these rules for automated dead-import pruning:

```javascript
// eslint.config.js (Flat Config)
import unusedImports from "eslint-plugin-unused-imports";
import tsPlugin from "@typescript-eslint/eslint-plugin";

export default [
  {
    plugins: {
      "unused-imports": unusedImports,
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      // Strips unused import declarations automatically on --fix
      "unused-imports/no-unused-imports": "error",

      // Flags unused variables, ignoring identifiers with leading underscores
      "unused-imports/no-unused-vars": [
        "warn",
        {
          vars: "all",
          varsIgnorePattern: "^_",
          args: "after-used",
          argsIgnorePattern: "^_",
        },
      ],

      // Standard TypeScript unused vars rule
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
    },
  },
];
```

---

## 5. Ultracite

Ultracite is a zero-configuration linter and formatter wrapper built on Biome and ESLint, standardizing code quality with zero config bloat.

### Primary Autofix Commands

```bash
# Run Ultracite autofix across the entire workspace
npx ultracite fix

# When using Bun
bunx ultracite fix

# Target only staged files during an active wave
npx ultracite fix --staged
```

Prefer `--staged` during wave remediation. It confines the diff to files already touched in the active wave, keeping the commit reviewable.

---

## 6. Monorepo Execution Recipes

In monorepos (Turborepo, Nx, pnpm workspaces), invoke the linter across all packages or target modified packages specifically:

```bash
# pnpm workspaces: run across all packages
pnpm -r --parallel run lint:fix

# pnpm workspaces: target a single package during a scoped wave
pnpm --filter @scope/package run lint:fix

# Turborepo: execute cached lint task with autofix
turbo run lint -- --fix

# Biome across root and all monorepo packages
npx @biomejs/biome check --write apps/ packages/
```

---

## 7. Safe Automated Formatting Rules vs. Dangerous Mutations

Automated autofixes during cleanup remediation must remain **strictly behavior-invariant**. Formatting must produce clean, readable diffs without altering program semantics, type signatures, or runtime execution order.

### Safe Rules (Always Run During Remediation)

These transformations carry zero regression risk and improve code hygiene:

1. **Import Sorting & Deduplication**
   - Merges multiple import statements from the same module (`import { a } from './m'; import { b } from './m'` -> `import { a, b } from './m'`).
   - Alphabetizes or categorizes imports (built-ins -> third-party -> internal -> relative).
   - Biome rule: `organizeImports: { "enabled": true }`.
   - ESLint plugins: `eslint-plugin-simple-import-sort`, `eslint-plugin-import`.
2. **Trailing Comma Standardization**
   - Adds trailing commas on multiline object literals, arrays, interfaces, and function arguments.
   - Eliminates multiline git diff churn when adjacent exports are deleted.
3. **Quote and Semicolon Standardization**
   - Converts mixed single/double quotes to the project standard.
   - Standardizes semicolon presence without altering ASI (Automatic Semicolon Insertion) semantics.
4. **Whitespace and EOF Normalization**
   - Strips trailing whitespace.
   - Enforces a single newline at end of file.

### Dangerous Rules (PROHIBITED During Remediation)

Never enable autofixes for rules that modify runtime behavior, alter module exports, or change type inference. If present in the linter config, skip them or run targeted rules instead.

| Dangerous Rule | Engine | Why It Breaks Codebases | Correct Action |
|---|---|---|---|
| `import/no-default-export` or `import/prefer-default-export` | ESLint / Biome | Rewrites export style between named and default. Breaks framework routers (Next.js, Remix, Astro) and Knip dynamic entry tracking. | Disable autofix. Maintain original export style. |
| `@typescript-eslint/no-explicit-any` | ESLint | Replaces `any` with `unknown` or casts. Breaks generic constraints and downstream consumers expecting permissive types. | Never autofix. Require manual triage. |
| `@typescript-eslint/no-non-null-assertion` | ESLint | Removes `!` assertions. Changes TypeScript compiler error states and alters runtime execution paths. | Prohibit automated removal. |
| `@typescript-eslint/no-floating-promises` | ESLint | Automatically prefixes promises with `void`. Silences unhandled asynchronous errors rather than properly awaiting them. | Never autofix during cleanup. |
| `prefer-const` | ESLint / Biome | Converts `let` to `const`. In dynamic runtime scripts, variables reassigned across asynchronous callbacks or closures cause runtime `TypeError: Assignment to constant variable`. | Allow only when scope is purely local and verified. |
| `no-param-reassign` | ESLint | Rewrites parameter assignments into local shallow copies. Alters mutation contracts in libraries or state managers. | Prohibit automated modification. |
| `react-hooks/exhaustive-deps` | ESLint | Automatically adds variables to hook dependency arrays (`useEffect`, `useCallback`). Triggers unintended re-renders or infinite loops at runtime. | Never autofix automatically in a cleanup wave. |

### Enforcing the Boundary

Prove an autofix pass stayed behavior-invariant before staging:

```bash
# A safe formatting pass touches whitespace, imports, and punctuation only.
# Any hunk changing an identifier, signature, or control flow is a red flag.
git diff --stat
git diff -U0 | grep -E '^\+' | grep -vE '^\+\+\+' | grep -E 'as any|void |const |=>' || true
```

Run the full verification gate from [`../remediation/waves.md`](../remediation/waves.md) after every autofix pass. Never commit an autofix diff that has not passed `tsc --noEmit`.

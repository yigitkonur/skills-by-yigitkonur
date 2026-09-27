# Enforce astro check with Strict Failing Severity in CI Pipelines

> **Context:** Auditing & Next.js Migration | **Impact:** Critical | **Target:** Astro 4 / Astro 5

## 1. Why We Do This

Running `tsc --noEmit` in an Astro project is insufficient because the standard TypeScript compiler (`tsc`) completely ignores `.astro` component files. The `astro check` CLI command parses `.astro` templates, compiles virtual TypeScript representations, validates component prop contracts, and checks Content Layer schemas. Enforcing `astro check` as a mandatory blocking quality gate in CI prevents runtime template crashes and broken type contracts from reaching deployment.

## 2. How It Differs From Classic React / Next.js

In Next.js, all files are standard `.ts` / `.tsx` files; running `tsc --noEmit` or `next build` natively verifies every page and layout. In Astro, `.astro` files use a custom compiler fence and template syntax. Type errors in Astro frontmatter or template JSX expressions are invisible to vanilla `tsc`. Only `astro check` (backed by `@astrojs/check` and the Astro Language Server) can type-check both `.astro` and `.ts` files simultaneously.

## 3. Common Mistakes & Anti-Patterns

Relying solely on `tsc --noEmit` in CI pipelines, or running `astro build` without `astro check`. `astro build` transpiles templates with esbuild for maximum build speed and deliberately skips deep TypeScript type-checking to keep builds fast. Without `astro check`, invalid props pass silently into production.

### ❌ Bad Practice / Anti-Pattern

```json
// package.json - INCORRECT: tsc ignores .astro files, astro build skips type-checking
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "build": "astro build",
    "ci": "npm run typecheck && npm run build"
  }
}
```

### ✅ Best Practice / Idiomatic

```json
// package.json - CORRECT: astro check validates .astro files and syncs content types
{
  "scripts": {
    "typecheck": "astro check --minimumFailingSeverity error",
    "build": "astro check && astro build",
    "ci": "astro check --minimumFailingSeverity error && astro build"
  }
}
```

```bash
# In CI workflow step (GitHub Actions / GitLab CI):
# astro check automatically executes astro sync to generate .astro/types.d.ts
pnpm astro check --minimumFailingSeverity error
```

## 4. Verification & Audit

Test the quality gate locally by introducing an invalid prop type into an `.astro` file and verifying that `astro check` exits with code 1:

```bash
pnpm astro check --minimumFailingSeverity error
echo "Exit code: $?"
# Must output: Exit code: 0 on clean repo, or Exit code: 1 on type violation
```

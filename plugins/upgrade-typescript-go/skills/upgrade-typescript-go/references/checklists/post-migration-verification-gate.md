# Post-Migration Verification Gate

Every TypeScript upgrade must pass this six-tier verification gate before merging.

```
                  TypeScript Upgrade Verification Gate
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
 Tier 1: Typecheck (tsc --noEmit)               Tier 4: Linters (ESLint/Biome)
      │                                                       │
      ▼                                                       ▼
 Tier 2: Composite Build (tsc -b)               Tier 5: Test Suite (Vitest/Jest)
      │                                                       │
      ▼                                                       ▼
 Tier 3: Declaration Emit (.d.ts)               Tier 6: App Build (Next/Vite)
```

## Tier 1: Authoritative Native Type Check
Execute the native Go type checker across the entire workspace:
```bash
pnpm run type-check # or npx tsc --noEmit
```
* **Success Criteria**: Exit code 0, 0 errors reported.

## Tier 2: Composite Project References (Monorepos)
If the project uses project references (`"composite": true`):
```bash
npx tsc --build --verbose
```
* **Success Criteria**: All referenced package graphs build cleanly.

## Tier 3: Declaration Emit Verification (Libraries)
If building an npm library or shared types:
```bash
npx tsc --declaration --emitDeclarationOnly --noEmit false
```
* **Success Criteria**: All `.d.ts` files emit without TS4023 / TS4058 errors.

## Tier 4: Linter & AST Static Analysis
Run project linters to verify AST parser compatibility:
```bash
pnpm run lint
```
* **Success Criteria**: Linters parse all `.ts`/`.tsx` files without AST fatal exceptions.

## Tier 5: Complete Test Suite
Run unit and integration tests:
```bash
pnpm test # or vitest run
```
* **Success Criteria**: 100% tests pass.

## Tier 6: Production Application Build
Execute the full production build pipeline:
```bash
pnpm run build # (e.g. Next.js Turbopack, Vite SPA, etc.)
```
* **Success Criteria**: Production artifacts generated cleanly in `dist/` or `.next/`.

## Final Decision
* If all 6 tiers pass: Commit changes with `chore(deps): upgrade to typescript native (go compiler)`.
* If any tier fails: Inspect error output against `references/troubleshooting/` guides.

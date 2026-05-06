# Build and Type Errors

Errors at `tinacms build` or `next build` time, plus generated-types issues.

## `Cannot find module '../tina/__generated__/client'`

**Cause:** `next build` ran before `tinacms build`. Generated types don't exist yet.

**Fix:**

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

Order matters. Same applies to `start`:

```json
"start": "tinacms build && next start"
```

In CI:

```yaml
- run: pnpm tinacms build
- run: pnpm next build
```

## `require is not defined` / `ERR_REQUIRE_ESM`

**Cause:** TinaCMS 3.x is ESM-only. Your project (or `tina/config.ts`) uses CommonJS.

**Fix:**

1. Set `"type": "module"` in `package.json`, OR use `.ts`/`.mts` for `tina/config.ts`
2. Replace `require()` with `import`
3. Check `next.config.js` — rename to `next.config.ts` if needed

## `Could not resolve "tinacms"` / module resolution

**Cause:**

- Corrupted install
- `--no-optional` or `--omit=optional` flag used
- Missing `react`/`react-dom` peers
- Used npm/yarn instead of pnpm (TinaCMS 2.7.3+)

**Fix:**

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

Verify:

```bash
pnpm list tinacms @tinacms/cli react react-dom
```

If still failing, check for conflicting type definitions:

```bash
pnpm dedupe
```

## Type errors after schema change

**Cause:** Generated types drift from schema. `tinacms build` regenerates them, but the build hasn't run since schema changed.

**Fix:**

```bash
pnpm tinacms build
```

Or restart `pnpm dev` (which re-runs build).

## TypeScript "Cannot find module '@/tina/__generated__/types'"

**Cause:**

- `tinacms build` hasn't run
- `tsconfig.json` `paths` doesn't include `@/`

**Fix:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

Then run `pnpm tinacms build`.

## Generated client types are wrong

**Cause:** `__generated__/` was committed and is stale, or schema bundle has esbuild errors.

**Fix:**

1. Delete `tina/__generated__/`
2. Run `pnpm tinacms build`
3. Add to `.gitignore`:
   ```gitignore
   tina/__generated__/
   ```

## Build hangs or runs forever

**Cause:** Schema bundle has a circular import or imports an infinite-loop module.

**Fix:**

1. Run with verbose: `pnpm tinacms build --verbose`
2. Identify the offending import
3. Replace with a simpler version (type-only or extract to leaf module)

## "Schema not found" at runtime

**Cause:** `tina-lock.json` missing in deployed environment.

**Fix:**

- Verify `tina-lock.json` is committed to git (it should be — never gitignore it)
- Re-deploy

## CI build succeeds but admin breaks in production

**Cause:** Admin SPA was built with dev assets (`tinacms dev` ran instead of `tinacms build`).

**Fix:**

```bash
# In CI, always:
pnpm tinacms build  # NOT dev
```

## CI runs out of memory

**Cause:** Large schema + low CI memory.

**Fix:**

```yaml
# GitHub Actions
- run: pnpm tinacms build --noTelemetry
  env:
    NODE_OPTIONS: '--max-old-space-size=4096'
```

Bump to 4 GB or more.

## Common mistakes

| Mistake | Fix |
|---|---|
| Forgot `tinacms build` in CI | Add to build script |
| Committed `__generated__/` | Gitignore + delete |
| Mismatched `tinacms` and `@tinacms/cli` versions | Pin to same major |
| Used `--skip-cloud-checks` in CI | Remove unless absolutely necessary |
| Empty `tina-lock.json` after build | Schema didn't compile — read build logs |

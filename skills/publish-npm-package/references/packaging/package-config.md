# Package Configuration for npm Publishing

Complete reference for `package.json` fields, entry points, file inclusion, and dual CJS/ESM publishing.

---

## 1. Essential package.json Fields

### `name`

Must be lowercase, URL-safe, and unique on the registry.

```json
{ "name": "my-utils" }
{ "name": "@myorg/utils" }
```

Rules: max 214 chars, no uppercase, no leading `.` or `_`, only `a-z 0-9 - . _`. Check availability with `npm view <name>`.

### `version`

Semver format `MAJOR.MINOR.PATCH`:

```json
{ "version": "1.4.2" }
```

Tool behavior: **semantic-release** sets `"0.0.0-development"` in source (writes real version at publish time). **changesets** and **release-please** bump the version in a PR committed before publish. **npm version** bumps manually via `npm version patch|minor|major`.

### `description`

Short one-liner for npmjs.com search results. Keep under 120 characters:

```json
{ "description": "Lightweight date formatting utilities for Node.js and browsers" }
```

### `repository`

**Critical for provenance.** Must match the GitHub repo URL exactly — case-sensitive.

> **⚠️ Steering (F-12):** The `repository.url` field must **exactly** match your
> GitHub repository URL, including letter casing. `MyOrg/My-Package` ≠
> `myorg/my-package`. A mismatch silently breaks provenance verification, and npm
> will publish without provenance rather than failing — so you won't notice until
> consumers check. Always copy the URL directly from your GitHub repo page.

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/myorg/my-package.git"
  }
}
```

**Verification:** After publishing, check provenance on npmjs.com — the package
page should show a green checkmark linking to the exact source commit. If the
checkmark is missing, `repository.url` casing is the most likely cause.

**Gotchas:** wrong casing (`MyOrg` vs `myorg`) breaks provenance verification. For monorepos add `"directory": "packages/my-package"`.

### `license`

Use [SPDX identifiers](https://spdx.org/licenses/):

```json
{ "license": "MIT" }
{ "license": "Apache-2.0" }
{ "license": "(MIT OR Apache-2.0)" }
{ "license": "UNLICENSED" }
```

### `engines`

Declare supported Node.js versions (advisory by default):

```json
{ "engines": { "node": ">=18.0.0" } }
```

### `publishConfig`

> **⚠️ Steering:** Always set `publishConfig.provenance: true` and — for scoped
> packages — `publishConfig.access: "public"` as defaults in your `package.json`.
> This prevents the two most common first-publish failures: missing provenance
> (silent) and `E403 Forbidden` on scoped packages (blocks publish entirely).

Essential for scoped public packages and provenance:

```json
{
  "publishConfig": {
    "access": "public",
    "registry": "https://registry.npmjs.org/",
    "provenance": true,
    "tag": "latest"
  }
}
```

- `access` — scoped packages default to `"restricted"` (paid); set `"public"` for free publishing
- `provenance` — enables SLSA attestation when publishing from GitHub Actions with OIDC. **Recommended for all packages** — there is no downside to enabling it
- `tag` — use `"next"` or `"beta"` for pre-releases

---

## 2. The `files` Field (Whitelist Approach — Recommended)

The `files` array whitelists what goes into the tarball. Only listed files/directories are included.

**Always-included files** (regardless of `files`): `package.json`, `README`, `LICENSE`, `CHANGELOG`, and files referenced by `main`/`bin`.

### Examples by Project Type

```json
// Simple JS / TypeScript package
{ "files": ["dist"] }

// TypeScript shipping source for sourcemap debugging
{ "files": ["dist", "src"] }

// CLI tool
{ "files": ["dist", "bin"] }
```

### Verifying Contents

```bash
npm pack --dry-run          # show file list and size without creating tarball
npm pack && tar -tf my-package-1.0.0.tgz   # create and inspect tarball
```

**Common mistake:** forgetting type declarations. If `.d.ts` files are in a separate directory, include it: `"files": ["dist", "typings"]`. Better: configure your build to co-locate `.d.ts` next to `.js` in `dist/`.

---

## 3. `.npmignore` vs `files` Field

| Approach | Mechanism | Best for |
|---|---|---|
| `files` (whitelist) | Only listed paths are included | Most projects — explicit and safe |
| `.npmignore` (blacklist) | Listed paths are excluded | Legacy projects needing everything minus a few files |

If both exist, `files` defines the whitelist and `.npmignore` can further exclude within it. If neither exists, `.gitignore` patterns are used for exclusion.

**Recommendation:** Use `files` for all new projects.

---

## 4. The `exports` Field (Modern Entry Points)

### Why `exports` Over `main`/`module`

- **Encapsulation** — only explicitly exported paths are importable
- **Conditional resolution** — different code for `import` vs `require`
- **Subpath exports** — expose multiple entry points
- **Types-first** — TypeScript resolves `.d.ts` from `exports`

### Conditional Exports

Resolution order matters — Node.js picks the **first matching condition**. Always: `types` → `import` → `require` → `default`.

```json
{
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "default": "./dist/index.cjs"
    },
    "./utils": {
      "types": "./dist/utils.d.ts",
      "import": "./dist/utils.js",
      "require": "./dist/utils.cjs"
    },
    "./package.json": "./package.json"
  }
}
```

Consumers import as: `from "@myorg/utils"` (root), `from "@myorg/utils/utils"` (subpath).

### Self-Referencing

Packages can import their own exports by name (useful in tests):

```js
import { helper } from "@myorg/utils/utils"; // works inside the package itself
```

### Backwards Compatibility

Keep legacy fields as fallbacks for older tools:

```json
{
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": { "...as above..." }
}
```

---

## 5. Dual CJS/ESM Publishing

Support both when your package is a **library** consumed by CJS and ESM projects. CLI tools/apps need only one format.

### `type: "module"` and File Extensions

| `type` field | `.js` treated as | ESM ext | CJS ext |
|---|---|---|---|
| `"module"` | ESM | `.js` | `.cjs` |
| absent/`"commonjs"` | CJS | `.mjs` | `.js` |

**Recommendation:** Set `"type": "module"`, use `.cjs` for CJS output.

### tsup Configuration (Recommended)

```bash
npm install -D tsup
```

**tsup.config.ts:**
```ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts", "src/utils.ts"],
  format: ["cjs", "esm"],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  outDir: "dist",
});
```

Produces: `index.js` (ESM), `index.cjs` (CJS), `index.d.ts`, `index.d.cts` per entry.

### Alternative Build Tools

| Tool | Strengths |
|---|---|
| **tsup** | Zero-config, fast, bundles + dts in one step |
| **unbuild** | Auto-infers config from package.json |
| **rollup** | Maximum control, large plugin ecosystem |
| **tsc** | No bundling, file-per-file output, simplest for pure TS |

### tsconfig.json for Dual Output (tsc only)

Use two tsconfig files when building with `tsc` directly:

**tsconfig.esm.json:**
```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "module": "ESNext",
    "outDir": "./dist/esm",
    "declaration": true
  },
  "include": ["src"]
}
```

**tsconfig.cjs.json:**
```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "module": "CommonJS",
    "outDir": "./dist/cjs",
    "declaration": true
  },
  "include": ["src"]
}
```

```json
{ "scripts": { "build": "tsc -p tsconfig.esm.json && tsc -p tsconfig.cjs.json" } }
```

### Testing Both Formats

```bash
npm run build && npm pack

# Test CJS
mkdir /tmp/test-cjs && cd /tmp/test-cjs && npm init -y
npm install /path/to/my-package-1.0.0.tgz
node -e "const pkg = require('@myorg/utils'); console.log(pkg)"

# Test ESM
mkdir /tmp/test-esm && cd /tmp/test-esm
echo '{"type":"module"}' > package.json
npm install /path/to/my-package-1.0.0.tgz
node -e "import('@myorg/utils').then(pkg => console.log(pkg))"
```

---

## 6. TypeScript Declaration Files

### `types` vs `exports.types`

Top-level `types` for simple packages; `exports.types` for packages using `exports`:

```json
{ "types": "./dist/index.d.ts" }
```

With `exports`, put `types` **first** inside each condition:

```json
{ "exports": { ".": { "types": "./dist/index.d.ts", "import": "./dist/index.js" } } }
```

### Generating Declarations

**tsc:** set `"declaration": true, "declarationMap": true` in tsconfig.  
**tsup:** set `dts: true` in config — bundles declarations automatically.

### `typesVersions` (Legacy Fallback)

For TypeScript < 4.7 that doesn't read `exports`:

```json
{ "typesVersions": { "*": { "utils": ["./dist/utils.d.ts"] } } }
```

### Verifying Declarations

```bash
npx @arethetypeswrong/cli ./my-package-1.0.0.tgz
```

Catches: missing `.d.ts`, mismatched CJS/ESM declarations, incorrect `exports` conditions.

---

## 7. Lifecycle Scripts

### Execution Order for `npm publish`

1. `prepublishOnly` → 2. `prepack` → 3. *(tarball)* → 4. `postpack` → 5. `publish` → 6. `postpublish`

### Common Patterns

```json
{
  "scripts": {
    "build": "tsup",
    "test": "vitest run",
    "clean": "rm -rf dist",
    "prepublishOnly": "npm run build && npm test"
  }
}
```

`prepublishOnly` ensures you never publish without building and testing. In CI workflows (semantic-release, changesets), the build step is typically in the workflow YAML instead.

---

## 8. Complete package.json Template

```json
{
  "name": "@myorg/my-package",
  "version": "0.0.0",
  "description": "A brief description of what this package does",
  "keywords": ["keyword1", "keyword2"],
  "author": "Your Name <you@example.com>",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/myorg/my-package.git"
  },
  "bugs": { "url": "https://github.com/myorg/my-package/issues" },
  "homepage": "https://github.com/myorg/my-package#readme",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "default": "./dist/index.cjs"
    },
    "./package.json": "./package.json"
  },
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "files": ["dist"],
  "engines": { "node": ">=18.0.0" },
  "publishConfig": { "access": "public", "provenance": true },
  "scripts": {
    "build": "tsup",
    "test": "vitest run",
    "lint": "eslint src/",
    "clean": "rm -rf dist",
    "prepublishOnly": "npm run build && npm test"
  },
  "devDependencies": {
    "tsup": "^8.0.0",
    "typescript": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

Adjust for your version tool: **semantic-release** → `"version": "0.0.0-development"`, remove `prepublishOnly`. **changesets/release-please** → keep `"version": "0.0.0"`, they bump it in PRs.

---

## 9. Pre-Publish Checklist

```bash
# 1. Verify only intended files are included
npm pack --dry-run

# 2. Inspect tarball contents
npm pack
tar -tf myorg-my-package-1.0.0.tgz

# 3. Test install from tarball
mkdir /tmp/test-install && cd /tmp/test-install && npm init -y
npm install /path/to/myorg-my-package-1.0.0.tgz

# 4. Verify CJS import
node -e "console.log(require('@myorg/my-package'))"

# 5. Verify ESM import
node --input-type=module -e "import pkg from '@myorg/my-package'; console.log(pkg)"

# 6. Check package size
npm pack --dry-run 2>&1 | grep 'total files\|unpacked size'

# 7. Verify TypeScript types resolve
npx @arethetypeswrong/cli ./myorg-my-package-1.0.0.tgz
```

Size guidelines: small utility < 50 KB, medium library 50-500 KB, large framework < 5 MB. If larger than expected, audit with `npm pack --dry-run`.

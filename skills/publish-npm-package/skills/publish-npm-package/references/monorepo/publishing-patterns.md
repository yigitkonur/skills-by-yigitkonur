# Monorepo Publishing Patterns

> **⚠️ Steering:** Start with **changesets** for monorepo publishing unless your
> team already has strong conventional-commit discipline. Changesets requires
> explicit developer intent (running `npx changeset`) which prevents accidental
> releases, while release-please and semantic-release depend on commit message
> conventions that are easy to get wrong in a multi-package repo.

## 1. npm Workspaces Setup

### Root `package.json`
```json
{
  "name": "my-monorepo",
  "private": true,
  "workspaces": ["packages/*"]
}
```
`"private": true` prevents accidental publishing of the root. The `workspaces` array accepts globs.

### Workspace Commands
```bash
npm install                          # install all workspace deps
npm run build --workspaces           # build every workspace
npm run build --workspace=packages/core  # build one workspace
npm publish --workspaces             # publish every public workspace
```

### Per-Package Configuration
Each workspace package needs publish fields in its own `package.json`:
```json
{
  "name": "@myorg/core",
  "version": "1.0.0",
  "main": "dist/index.js",
  "files": ["dist"],
  "publishConfig": { "access": "public", "registry": "https://registry.npmjs.org/" }
}
```

### Hoisting and `nohoist`
npm hoists shared deps to root `node_modules`. Prevent it selectively:
```json
{
  "workspaces": {
    "packages": ["packages/*"],
    "nohoist": ["**/react-native", "**/react-native/**"]
  }
}
```

---

## 2. Changesets for Monorepos (Recommended)

Changesets has native monorepo support and is used by Vercel, Turborepo, Radix UI, and Chakra UI. It handles cross-package dependency bumps automatically.

### Setup
```bash
npm install -D @changesets/cli
npx changeset init
```

### `.changeset/config.json`
```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [["@myorg/core", "@myorg/utils"]],
  "linked": [["@myorg/react-*"]],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": ["@myorg/docs", "@myorg/playground"]
}
```
| Option | Description |
|---|---|
| `fixed` | Groups sharing the same version — change to one bumps all |
| `linked` | Versions linked for minor/major bumps, can drift on patch |
| `updateInternalDependencies` | How to bump internal consumers: `patch` / `minor` / `major` |
| `ignore` | Packages excluded from changesets entirely |

### Developer Workflow
```bash
npx changeset
# → select affected packages → choose bump type → describe change
# Creates .changeset/happy-lion-dance.md:
```
```markdown
---
"@myorg/cli": minor
"@myorg/utils": patch
---
Added verbose flag. Updated utility helpers for new logging format.
```
```bash
git add . && git commit -m "feat: add verbose flag"
npx changeset version   # consume changesets, bump versions
npx changeset publish   # publish all bumped packages
```

### Complete Workflow YAML (OIDC)
```yaml
name: Release
on:
  push:
    branches: [main]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: write
  pull-requests: write
  id-token: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, registry-url: "https://registry.npmjs.org" }
      - run: npm ci
      - run: npm run build --workspaces
      - uses: changesets/action@v1
        with:
          publish: npx changeset publish
          version: npx changeset version
          title: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_CONFIG_PROVENANCE: true
```

---

## 3. Release-Please for Monorepos

### Multi-Package Config (`release-please-config.json`)
```json
{
  "packages": {
    "packages/core": { "release-type": "node", "component": "core" },
    "packages/cli":  { "release-type": "node", "component": "cli" },
    "packages/utils": { "release-type": "node", "component": "utils" }
  },
  "group-pull-requests": false
}
```

### Manifest (`.release-please-manifest.json`)
Tracks current versions — updated automatically with each release:
```json
{ "packages/core": "2.1.0", "packages/cli": "1.5.3", "packages/utils": "3.0.1" }
```

### Component-Based Tagging
Each package gets its own git tag: `core-v2.2.0`, `cli-v1.6.0`. Default behavior for monorepos.

### Separate vs Combined PRs
- `"group-pull-requests": false` — one Release PR per package (independent releases)
- `"group-pull-requests": true` — single combined PR (atomic releases)

### Complete Workflow YAML
```yaml
name: Release
on:
  push:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
  id-token: write
jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      releases_created: ${{ steps.release.outputs.releases_created }}
      core_released: ${{ steps.release.outputs['packages/core--release_created'] }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with: { token: "${{ secrets.GITHUB_TOKEN }}" }
  publish-core:
    needs: release-please
    if: needs.release-please.outputs.core_released == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, registry-url: "https://registry.npmjs.org" }
      - run: npm ci
      - run: npm run build --workspace=packages/core --if-present
      - run: npm test --workspace=packages/core --if-present
      - run: npm publish --provenance --access public
        working-directory: packages/core
```

Duplicate the `publish-core` job once per releasable workspace (`core`,
`cli`, `utils`, etc.), changing the exposed output and `working-directory` each
time. Do **not** try to read `steps.release.outputs` from a different job inside
one shell loop — pass the outputs through `needs.release-please.outputs` first.

---

## 4. Semantic-Release for Monorepos

### Limitations
Semantic-release has **no native monorepo support** — it was designed for single-package repos.

### `multi-semantic-release` Wrapper
```bash
npm install -D multi-semantic-release
```
Each package needs its own `.releaserc.json`:
```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/npm",
    "@semantic-release/git"
  ]
}
```
**Known issues:** inconsistent maintenance, unreliable cross-package dep updates, OIDC provenance support may lag.

### When to Use Alternatives
**Prefer changesets** for explicit developer-authored changelogs and native monorepo support. **Prefer release-please** for fully automated releases from conventional commits. Use `multi-semantic-release` only if already invested in the semantic-release plugin ecosystem.

### Changesets vs Release-Please for Monorepos

| Aspect | Changesets | Release-Please |
|---|---|---|
| **Trigger** | Explicit `npx changeset` files | Conventional commit parsing |
| **Developer effort** | Must run `npx changeset` per PR | Must follow commit conventions |
| **Changelog quality** | Hand-written, high quality | Auto-generated from commits |
| **Cross-package bumps** | Automatic via `fixed`/`linked` config | Manual or grouped PRs |
| **Monorepo support** | Native, first-class | Config-based (`release-please-config.json`) |
| **PR flow** | "Version Packages" PR auto-created | Release PR per component or grouped |
| **OIDC provenance** | Via `--provenance` or `publishConfig.provenance: true` without npm secrets | Via `--provenance` flag in publish step |
| **Ecosystem** | Vercel, Turborepo, Radix, Chakra | Google Cloud SDKs, googleapis |
| **Risk of accidental release** | Low — requires explicit changeset file | Medium — any `fix:`/`feat:` commit triggers |
| **Best for** | Teams wanting explicit release control | Teams with strict commit conventions |

---

## 5. Turborepo Integration

### `turbo.json` Pipeline
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "test":  { "dependsOn": ["build"], "outputs": [] },
    "lint":  { "outputs": [] },
    "publish-packages": { "dependsOn": ["build", "test", "lint"], "cache": false }
  }
}
```
`"^build"` means a package's build waits for its workspace dependencies to build first.

### Affected Packages Only
```bash
turbo run build --filter=...[HEAD^]         # changed since last commit
turbo run build --filter=...[origin/main]   # changed vs main branch
turbo run build --filter=@myorg/cli...      # specific package + its deps
```

### Combining with Changesets
```json
{
  "scripts": {
    "build": "turbo run build",
    "test": "turbo run test",
    "release": "turbo run build test lint && changeset publish"
  }
}
```

### Caching
Set `"cache": false` on publish tasks. Build/test outputs should be cached. Use remote caching (`--remote-only`) in CI for cross-run cache hits.

---

## 6. pnpm Workspaces

### Configuration (`pnpm-workspace.yaml`)
```yaml
packages:
  - "packages/*"
  - "apps/*"
```

### Recursive Publishing
```bash
pnpm publish -r --access public              # publish all
pnpm publish -r --access public --provenance  # with provenance
pnpm publish -r --dry-run                     # verify first
```

### Differences from npm Workspaces
| Feature | npm Workspaces | pnpm Workspaces |
|---|---|---|
| Isolation | Hoisted (phantom deps possible) | Strict symlinks (no phantom deps) |
| Config | `package.json` workspaces field | `pnpm-workspace.yaml` |
| Publish | `npm publish --workspaces` | `pnpm publish -r` |
| Filter | `--workspace=name` | `--filter=name` |

Changesets works with pnpm automatically — it detects `pnpm-workspace.yaml` with no extra config.

---

## 7. Common Monorepo Publishing Patterns

### Independent Versioning
Each package has its own version. **Best for:** packages with different stability levels.
Config: `{ "fixed": [], "linked": [] }`

### Fixed Versioning
All packages in a group share the same version — change to one bumps all.
**Best for:** tightly coupled packages always used together.
Config: `{ "fixed": [["@myorg/core", "@myorg/renderer", "@myorg/cli"]] }`

### Linked Versioning
Packages bump together for minor/major but can drift on patches.
**Best for:** component libraries expecting coordinated minor/major releases.
Config: `{ "linked": [["@myorg/react-*"]] }`

---

## 8. Monorepo Workflow Template

Complete workflow with change detection, scoped testing, and selective publishing:
```yaml
name: CI & Release
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
  id-token: write
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      changed: ${{ steps.filter.outputs.changes }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            core:  ['packages/core/**']
            cli:   ['packages/cli/**']
            utils: ['packages/utils/**']
  test:
    needs: detect-changes
    if: needs.detect-changes.outputs.changed != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.changed) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run build --workspace=packages/${{ matrix.package }}
      - run: npm test --workspace=packages/${{ matrix.package }}
  release:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, registry-url: "https://registry.npmjs.org" }
      - run: npm ci && npm run build --workspaces
      - uses: changesets/action@v1
        with:
          publish: npx changeset publish
          version: npx changeset version
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_CONFIG_PROVENANCE: true
```
For token auth instead of OIDC: remove `id-token: write` and use the matching
token workflow template to add `NODE_AUTH_TOKEN` in the publish path.

---

## 9. Common Monorepo Issues

### Circular Dependencies
Detect early with `npx madge --circular packages/`. Prevent by enforcing a layered architecture — lower-level packages (utils, core) never import from higher-level ones (cli, app).

### Version Resolution Conflicts
When workspace packages need different versions of the same external dep, fix with root-level `overrides`: `{ "overrides": { "react": "^18.3.0" } }`

### Publishing Order
Packages must publish in dependency order. Both `changeset publish` and `pnpm publish -r` handle this automatically via workspace graph analysis.

### Private Packages in Public Monorepos
```json
{ "name": "@myorg/internal-docs", "private": true }
```
Both `npm publish --workspaces` and `changeset publish` skip private packages. Also add them to changesets `ignore` to suppress prompts:
```json
{ "ignore": ["@myorg/internal-docs", "@myorg/playground"] }
```

---

## 10. First-Publish Considerations for Monorepo Packages

> **⚠️ Steering (F-11):** Each package in a monorepo must be bootstrapped
> independently on its first publish. OIDC trusted publishing requires the
> package to already exist on the registry — so the very first version of each
> new workspace package needs token-based auth.

### Bootstrap Pattern for New Workspace Packages

When adding a new package to an existing monorepo:

```bash
# 1. Publish the new package manually with token auth
cd packages/new-package
npm publish --access public
# (uses NPM_TOKEN from environment or .npmrc)

# 2. Subsequent publishes via CI will work with OIDC
```

### CI Workflow Considerations

Your CI workflow should handle the case where some packages exist on the
registry and some don't:

```yaml
- name: Publish with fallback for new packages
  run: |
    for pkg in packages/*/; do
      if npm view "$(node -p "require('./$pkg/package.json').name")" 2>/dev/null; then
        npm publish --workspace="$pkg" --provenance --access public
      else
        echo "First publish for $pkg — requires token auth bootstrap"
        npm publish --workspace="$pkg" --access public
      fi
    done
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Per-Package Checklist (New Workspace Package)

- [ ] `package.json` has correct `name`, `version`, `repository.url` (with `directory` field)
- [ ] `publishConfig.access` is `"public"` for scoped packages
- [ ] `publishConfig.provenance` is `true`
- [ ] `files` field includes only intended files
- [ ] Package is NOT in changesets `ignore` list
- [ ] First version has been bootstrapped with token auth
- [ ] `npm pack --dry-run` shows expected contents

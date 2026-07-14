# Monorepo Publishing Patterns

## Contents

- [Monorepo decision table](#monorepo-decision-table)
- [npm workspaces setup](#1-npm-workspaces-setup)
- [Changesets for monorepos](#2-changesets-for-monorepos-recommended)
- [Release-please for monorepos](#3-release-please-for-monorepos)
- [Semantic-release for monorepos](#4-semantic-release-for-monorepos)
- [Nx Release](#5-nx-release)
- [Lerna](#6-lerna)
- [Turborepo integration](#7-turborepo-integration)
- [pnpm workspaces](#8-pnpm-workspaces)
- [Common monorepo publishing patterns](#9-common-monorepo-publishing-patterns)
- [Monorepo workflow routing](#10-monorepo-workflow-routing)
- [Common monorepo issues](#11-common-monorepo-issues)
- [First-publish considerations](#12-first-publish-considerations-for-monorepo-packages)

> **Guardrail:** Start with changesets for monorepo publishing unless the repo already has strong conventional-commit discipline or an adopted release tool. Turborepo is task orchestration, not versioning. Nx Release and Lerna are release tools only when already adopted or deliberately chosen.

## Monorepo Decision Table

| Layer | Options | Use when | Do not confuse with |
|---|---|---|---|
| Package manager | npm / pnpm / Yarn | Choose from lockfile and workspace config | Release/versioning tool |
| Task runner / orchestrator | Turborepo / Nx / Lerna task runner | Builds, tests, affected-package execution, caching | npm publishing auth lane |
| Versioning / release tool | changesets / release-please / Nx Release / Lerna / existing convention | Version bumps, changelogs, tags, Release PRs, npm publish orchestration | Turborepo cache/task graph |
| Auth lane | trusted publishing / token / token+provenance | Registry authentication and provenance behavior | Versioning model |

Recommended defaults:

- npm/pnpm/Yarn: follow the existing lockfile; do not introduce Bun unless the repo already uses it.
- Turborepo: use for `build`/`test` orchestration before publishing, then pair with changesets or another release tool.
- Nx: use Nx Release when the repo already uses Nx or wants Nx-managed versioning/changelogs/publishing.
- Lerna: use Lerna version/publish when already adopted; Lerna v9 supports npm trusted publishing in supported CI environments.
- Auth: use trusted publishing for public packages after first-publish bootstrap; use token auth for private packages, self-hosted runners, or bootstrap.

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

### Workflow fragment

Use `references/workflows/oidc-workflows.md` or `references/workflows/token-workflows.md` for complete workflow YAML. This fragment shows monorepo-specific changesets wiring only.

```yaml
- run: npm run build --workspaces
- uses: changesets/action@v1
  with:
    publish: npx changeset publish --access public
    version: npx changeset version
    title: "chore: version packages"
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
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

### Workflow fragment

Use `references/workflows/oidc-workflows.md` section 3 or `references/workflows/token-workflows.md` section 3 for complete YAML.

```yaml
- run: npm run build --workspace=packages/core --if-present
- run: npm test --workspace=packages/core --if-present
- run: npm publish --access public
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
**Known issues:** inconsistent maintenance, unreliable cross-package dependency updates, and release-tool support can lag current npm trusted-publishing behavior.

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
| **Trusted publishing** | Use the trusted-publishing workflow template; no npm secrets and no explicit provenance flag | Use the trusted-publishing workflow template; publish job has no npm secrets |
| **Ecosystem** | Vercel, Turborepo, Radix, Chakra | Google Cloud SDKs, googleapis |
| **Risk of accidental release** | Low — requires explicit changeset file | Medium — any `fix:`/`feat:` commit triggers |
| **Best for** | Teams wanting explicit release control | Teams with strict commit conventions |

---

## 5. Nx Release

Use Nx Release when the repo already uses Nx or explicitly chooses Nx to version, changelog, tag, and publish packages. Nx uses the project graph to understand release projects and can release all packages or a filtered set from `nx.json`.

Decision points:

| Need | Nx Release fit |
|---|---|
| Existing Nx workspace | Good default if release ownership should stay inside Nx |
| Fixed version group | Supported; first release can prompt for one shared bump |
| Independent package versions | Supported through Nx release configuration |
| Dry-run validation | Run `nx release --first-release --dry-run` for first release or `nx release --dry-run` later |
| Publishing | Nx can publish to npm; configure auth lane through the workflow reference |

Do not imply Nx itself is only a task runner when `nx release` is adopted. Also do not introduce Nx Release into a non-Nx monorepo unless the task explicitly asks for a new release tool.

## 6. Lerna

Use Lerna when the repo already has `lerna.json` or explicitly chooses Lerna for versioning and publishing. Lerna can version and publish in fixed/locked or independent modes.

Decision points:

| Need | Lerna fit |
|---|---|
| Existing Lerna repo | Keep Lerna if it already owns version tags and publish flow |
| Fixed versioning | Default mode; root `lerna.json` version controls the release line |
| Independent versioning | Supported with Lerna independent mode |
| Publish existing versioned packages | `lerna publish from-package` |
| Trusted publishing | Lerna v9+ supports npm trusted publishing in supported CI environments; follow npm trusted-publishing workflow requirements |
| Non-npm package manager | Lerna still uses npm to publish; configure `.npmrc`/auth accordingly |

Do not mix Lerna publish with a separate changesets/release-please versioning flow unless the repo already has that convention and the ownership boundary is explicit.

## 7. Turborepo Integration

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

## 8. pnpm Workspaces

### Configuration (`pnpm-workspace.yaml`)
```yaml
packages:
  - "packages/*"
  - "apps/*"
```

### Recursive Publishing
```bash
pnpm publish -r --access public              # publish all
pnpm publish -r --access public              # trusted publishing handles eligible provenance automatically
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

## 9. Common Monorepo Publishing Patterns

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

## 10. Monorepo Workflow Routing

Use the workflow references as the source of truth for release YAML. Add monorepo-specific change detection or scoped test jobs around those templates:

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
      - uses: actions/checkout@v6
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
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with: { node-version: 24, package-manager-cache: false }
      - run: npm ci
      - run: npm run build --workspace=packages/${{ matrix.package }}
      - run: npm test --workspace=packages/${{ matrix.package }}
  release:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: actions/setup-node@v6
        with: { node-version: 24, registry-url: "https://registry.npmjs.org", package-manager-cache: false }
      - run: npm ci && npm run build --workspaces
      - uses: changesets/action@v1
        with:
          publish: npx changeset publish --access public
          version: npx changeset version
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

For token auth, use `references/workflows/token-workflows.md` to add `NODE_AUTH_TOKEN` in the publish path. For token+provenance, add explicit provenance only in that token workflow.

---

## 11. Common Monorepo Issues

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

## 12. First-Publish Considerations for Monorepo Packages

> **Guardrail:** Each package in a monorepo must be bootstrapped independently on its first publish. Trusted publishing requires the package to already exist on the registry, so the first version of each new workspace package needs token auth.

### Bootstrap Pattern for New Workspace Packages

When adding a new package to an existing monorepo:

```bash
# 1. Publish the new package manually with token auth
cd packages/new-package
npm publish --access public
# (uses NPM_TOKEN from environment or .npmrc)

# 2. Subsequent publishes via CI can use trusted publishing after npm linking
```

### CI Workflow Considerations

Do not build a mixed token/trusted-publishing loop for new workspace packages. Bootstrap each new package with token auth, link it to trusted publishing in npm settings, then let the steady-state trusted-publishing workflow handle later releases.

### Per-Package Checklist (New Workspace Package)

- [ ] `package.json` has correct `name`, `version`, `repository.url` (with `directory` field)
- [ ] `publishConfig.access` is `"public"` for scoped packages
- [ ] Provenance behavior matches the auth lane
- [ ] `files` field includes only intended files
- [ ] Package is NOT in changesets `ignore` list
- [ ] First version has been bootstrapped with token auth
- [ ] `npm pack --dry-run` shows expected contents

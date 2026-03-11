# release-please — Google's Release PR Automation for npm

## Overview

release-please is Google's open-source tool for automating releases via GitHub pull
requests. It analyzes conventional commits, creates and maintains a Release PR, and
publishes releases when that PR is merged.

| Metric | Value |
|--------|-------|
| Weekly npm downloads | ~120K |
| Maintainer | Google (googleapis) |
| License | Apache-2.0 |
| Repository | `googleapis/release-please` |
| GitHub Action | `googleapis/release-please-action@v4` |

**Core philosophy:** A Release PR serves as a staging area for the next release.
Conventional commits flow into it automatically. Humans decide when to ship by
merging the PR.

---

## How It Works

```
1. Developers push conventional commits to main
2. release-please action runs on each push
3. If releasable commits exist:
   a. Creates (or updates) a Release PR
   b. PR includes version bump, changelog, updated package.json
4. Team reviews the Release PR
5. Merging the Release PR:
   a. Creates a GitHub Release with tag
   b. Triggers a separate publish job (your responsibility)
   c. release-please updates the manifest file
```

Unlike semantic-release (which publishes immediately), release-please separates the
"decide to release" step (merge the PR) from the "publish" step (a separate CI job).

---

## Installation

No npm packages to install. release-please runs entirely as a GitHub Action:

```yaml
- uses: googleapis/release-please-action@v4
```

For local development and debugging, the CLI is available:

```bash
npm install -g release-please
release-please release-pr --repo-url=your-org/your-repo --token=$GITHUB_TOKEN
```

---

## Configuration

### `.release-please-config.json`

This file lives in your repository root and controls release-please behavior.

#### Single Package Configuration

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "node",
  "packages": {
    ".": {
      "changelog-path": "CHANGELOG.md",
      "include-component-in-tag": false,
      "include-v-in-tag": true
    }
  },
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true,
  "changelog-sections": [
    { "type": "feat", "section": "Features" },
    { "type": "fix", "section": "Bug Fixes" },
    { "type": "perf", "section": "Performance Improvements" },
    { "type": "revert", "section": "Reverts" },
    { "type": "docs", "section": "Documentation", "hidden": true },
    { "type": "style", "section": "Styles", "hidden": true },
    { "type": "chore", "section": "Miscellaneous Chores", "hidden": true },
    { "type": "refactor", "section": "Code Refactoring", "hidden": true },
    { "type": "test", "section": "Tests", "hidden": true },
    { "type": "build", "section": "Build System", "hidden": true },
    { "type": "ci", "section": "Continuous Integration", "hidden": true }
  ]
}
```

### Option Reference

#### `release-type`

Determines how release-please manages version files and changelogs.

| Type | Language/Platform | Files updated |
|------|-------------------|---------------|
| `node` | JavaScript/TypeScript | `package.json`, `package-lock.json` |
| `python` | Python | `setup.py`, `setup.cfg`, `pyproject.toml` |
| `rust` | Rust | `Cargo.toml` |
| `java` | Java | `pom.xml` |
| `ruby` | Ruby | `*.gemspec`, `lib/**/version.rb` |
| `go` | Go | No version file (tag only) |
| `simple` | Any | Only updates `CHANGELOG.md` |

For npm packages, always use `"node"`.

#### `changelog-path`

Path to the changelog file relative to the package root.

```json
{ "changelog-path": "CHANGELOG.md" }
```

Default: `"CHANGELOG.md"`

#### `bump-minor-pre-major`

When the current version is `0.x.y` (pre-1.0):

| Value | `feat:` commit | `feat!:` commit |
|-------|----------------|-----------------|
| `true` (default) | 0.x.y → 0.(x+1).0 | 0.x.y → 0.(x+1).0 |
| `false` | 0.x.y → 0.(x+1).0 | 0.x.y → 1.0.0 |

This prevents accidental 1.0.0 releases from breaking change commits during
early development.

#### `bump-patch-for-minor-pre-major`

Controls how `feat:` commits are treated pre-1.0:

| Value | `feat:` becomes |
|-------|-----------------|
| `true` | Patch bump (0.1.0 → 0.1.1) |
| `false` (default) | Minor bump (0.1.0 → 0.2.0) |

Useful for libraries that want to reserve minor bumps for breaking changes
during the 0.x phase.

#### `include-component-in-tag`

Whether the tag includes the package/component name.

| Value | Tag format |
|-------|------------|
| `true` | `my-package-v1.2.3` |
| `false` | `v1.2.3` |

Use `true` for monorepos to distinguish package tags.

#### `include-v-in-tag`

Whether to prefix tags with `v`.

| Value | Tag format |
|-------|------------|
| `true` (default) | `v1.2.3` |
| `false` | `1.2.3` |

#### `changelog-sections`

Customize which commit types appear in the changelog and under what headings:

```json
{
  "changelog-sections": [
    { "type": "feat", "section": "🚀 Features" },
    { "type": "fix", "section": "🐛 Bug Fixes" },
    { "type": "perf", "section": "⚡ Performance" },
    { "type": "docs", "section": "📝 Documentation", "hidden": false },
    { "type": "chore", "section": "🔧 Maintenance", "hidden": true }
  ]
}
```

Setting `"hidden": true` excludes that type from the changelog entirely.

#### `draft`

Create Release PRs as draft PRs:

```json
{ "draft": true }
```

#### `draft-pull-request`

Create the version bump PR as a draft:

```json
{ "draft-pull-request": true }
```

#### `pull-request-title-pattern`

Customize the Release PR title:

```json
{ "pull-request-title-pattern": "chore: release ${version}" }
```

Default: `"chore(main): release${component} ${version}"`

---

## Manifest File

### `.release-please-manifest.json`

This file tracks the current version of each package. release-please reads and
writes this file automatically.

#### Single Package

```json
{
  ".": "1.4.2"
}
```

#### Monorepo

```json
{
  ".": "2.1.0",
  "packages/core": "3.0.1",
  "packages/cli": "1.5.0",
  "packages/utils": "2.0.0"
}
```

**Important:** This file must be committed to the repository. release-please uses
it to determine the current version and calculate the next one.

---

## Monorepo Support

### Configuration for Multiple Packages

```json
{
  "release-type": "node",
  "packages": {
    ".": {
      "component": "root",
      "include-component-in-tag": true
    },
    "packages/core": {
      "component": "core",
      "include-component-in-tag": true,
      "changelog-path": "CHANGELOG.md"
    },
    "packages/cli": {
      "component": "cli",
      "include-component-in-tag": true
    },
    "packages/utils": {
      "component": "utils",
      "include-component-in-tag": true
    }
  },
  "bump-minor-pre-major": true,
  "changelog-sections": [
    { "type": "feat", "section": "Features" },
    { "type": "fix", "section": "Bug Fixes" }
  ]
}
```

### Monorepo Manifest

```json
{
  ".": "1.0.0",
  "packages/core": "2.0.0",
  "packages/cli": "1.3.0",
  "packages/utils": "1.1.0"
}
```

### Component Names

The `component` field determines:
- Tag prefix: `core-v2.0.1`
- Release PR title: `chore(main): release core 2.0.1`
- Output variable names: `core--release_created`, `core--tag_name`

### Scoped Commits for Monorepos

Use commit scopes matching component names to target specific packages:

```
feat(core): add streaming API
fix(cli): handle missing config file
feat(utils): add retry helper
```

Commits without a scope that matches a component apply to the root package.

---

## Two-Job Workflow Pattern

The recommended pattern separates release-please from publishing:

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
    name: Release Please
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
      upload_url: ${{ steps.release.outputs.upload_url }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          config-file: .release-please-config.json
          manifest-file: .release-please-manifest.json

  publish:
    name: Publish to npm
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: lts/*
          registry-url: https://registry.npmjs.org

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build --if-present

      - name: Test
        run: npm test --if-present

      - name: Publish
        run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

This pattern ensures:
- Publishing only happens when a release is created (not on every push)
- Build and test run before publish
- The publish step can be customized independently

---

## Output Variables

### Single Package Outputs

| Output | Type | Description |
|--------|------|-------------|
| `release_created` | boolean | Whether a release was created |
| `tag_name` | string | Git tag name (e.g., `v1.2.3`) |
| `upload_url` | string | GitHub Release upload URL |
| `html_url` | string | GitHub Release page URL |
| `sha` | string | Release commit SHA |
| `major` | number | Major version number |
| `minor` | number | Minor version number |
| `patch` | number | Patch version number |
| `pr` | number | Release PR number |
| `prs_created` | boolean | Whether any PRs were created/updated |
| `paths_released` | string | JSON array of released package paths |

### Monorepo Per-Package Outputs

For monorepos, outputs are prefixed with the path (dots replaced with dashes):

```
packages/core → packages/core--release_created
packages/core → packages/core--tag_name
packages/cli  → packages/cli--release_created
```

Usage in workflow:

```yaml
- if: ${{ steps.release.outputs['packages/core--release_created'] == 'true' }}
  run: echo "Core was released: ${{ steps.release.outputs['packages/core--tag_name'] }}"
```

---

## Pre-release Support

### Configuration

```json
{
  "packages": {
    ".": {
      "prerelease-type": "beta"
    }
  }
}
```

This produces versions like `1.2.0-beta.0`, `1.2.0-beta.1`, etc.

### Toggling Pre-release

To enter pre-release mode, set `prerelease-type` in config and push.
To exit, remove `prerelease-type` and push — the next Release PR will be stable.

### Pre-release Branch Pattern

A common pattern is to use a separate branch for pre-releases:

```yaml
on:
  push:
    branches: [main, beta]

jobs:
  release-please:
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          target-branch: ${{ github.ref_name }}
```

With different config files per branch or `prerelease-type` set conditionally.

---

## Bootstrap for Existing Projects

### Setting Initial Version

If your project already has published versions, set the manifest to the current
version before first run:

1. Create `.release-please-manifest.json`:
   ```json
   {
     ".": "2.5.3"
   }
   ```

2. Create `.release-please-config.json`:
   ```json
   {
     "release-type": "node",
     "packages": {
       ".": {}
     }
   }
   ```

3. Commit both files to your main branch.

release-please will look for a git tag matching `v2.5.3` and analyze commits
since that tag for the next release.

### If No Git Tag Exists

Create a tag for the current version:

```bash
git tag v2.5.3
git push origin v2.5.3
```

Or use `bootstrap-sha` in config to specify the starting commit:

```json
{
  "packages": {
    ".": {
      "bootstrap-sha": "abc123def456"
    }
  }
}
```

### Last Release SHA

Alternatively, specify the last release SHA directly:

```json
{
  "packages": {
    ".": {
      "last-release-sha": "abc123def456"
    }
  }
}
```

This tells release-please to only consider commits after this SHA.

---

## Common Issues

### 1. Release PR Not Created

**Problem:** Pushes to main don't create a Release PR.

**Causes and fixes:**
- No releasable commits (only `chore:`, `docs:`, etc.) — add a `feat:` or `fix:` commit
- Missing config files — ensure both `.release-please-config.json` and `.release-please-manifest.json` exist
- Wrong `baseBranch` — verify it matches your default branch name
- Token permissions — `GITHUB_TOKEN` needs `contents: write` and `pull-requests: write`

### 2. Wrong Version Bump

**Problem:** Major bump expected but only got a minor.

**Fix:** Ensure breaking changes use the correct format:
```
feat!: redesign API          ← Correct: ! after type
feat: redesign API           ← Wrong: no breaking indicator

feat: redesign API

BREAKING CHANGE: old API removed   ← Correct: footer
```

With `bump-minor-pre-major: true`, breaking changes before 1.0 produce minor bumps.
Set to `false` if you want majors even during 0.x.

### 3. Manifest Out of Sync

**Problem:** release-please creates a release with wrong version or skips releases.

**Fix:** Manually update `.release-please-manifest.json` to match the latest
published version and ensure a matching git tag exists:

```bash
# Check latest tag
git tag --sort=-v:refname | head -5

# Update manifest to match
echo '{ ".": "2.5.3" }' > .release-please-manifest.json
git add .release-please-manifest.json
git commit -m "chore: sync release-please manifest"
git push
```

### 4. Multiple Release PRs

**Problem:** release-please creates duplicate Release PRs.

**Fix:** Close all existing Release PRs and let the action create a fresh one.
This can happen when the action's branch naming changes between versions.

### 5. Changelog Includes Hidden Types

**Problem:** `chore:` and `docs:` commits appear in changelog.

**Fix:** Set `"hidden": true` in `changelog-sections`:
```json
{
  "changelog-sections": [
    { "type": "chore", "section": "Miscellaneous", "hidden": true }
  ]
}
```

### 6. Tag Already Exists

**Problem:** `Error: tag v1.2.3 already exists`

**Fix:** The manifest version matches an existing tag. Update the manifest to
the current version and ensure you haven't manually created tags that conflict
with release-please's tagging.

---

## Complete Workflow with OIDC Provenance

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
    name: Release Please
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          config-file: .release-please-config.json
          manifest-file: .release-please-manifest.json

  publish:
    name: Publish to npm
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created == 'true' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: lts/*
          registry-url: https://registry.npmjs.org

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build --if-present

      - name: Test
        run: npm test --if-present

      - name: Publish with provenance
        run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Without OIDC (Token-Based)

```yaml
  publish:
    name: Publish to npm
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm run build --if-present
      - run: npm test --if-present

      - name: Publish
        run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## When to Use release-please

**Best for:**
- Projects that want a human-reviewed Release PR before publishing
- Monorepos with multiple packages (native support)
- Google-ecosystem projects (consistent tooling)
- Teams that use conventional commits but want release batching
- Projects that need to separate "release" from "publish"

**Avoid when:**
- You want fully automated publish on every commit (use semantic-release)
- You prefer explicit developer-authored changelogs (use changesets)
- You don't use conventional commits
- You need complex pre-release channel management

---

## Comparison with Other Tools

| Feature | release-please | semantic-release | changesets |
|---------|---------------|------------------|------------|
| Trigger | Merge Release PR | Push to branch | Merge Version PR |
| Commit convention | Required | Required | Not required |
| Human review | Release PR | None | Version PR + changeset |
| Monorepo | ✅ Native | ❌ Wrapper only | ✅ Native |
| Changelog source | Commits | Commits | Changeset descriptions |
| npm install needed | No (Action only) | Yes | Yes |
| Pre-releases | Config toggle | Branch-based | Mode-based |

---

## Quick Reference

```bash
# No local install needed — runs as GitHub Action

# Bootstrap: create config
cat > .release-please-config.json << 'EOF'
{
  "release-type": "node",
  "packages": { ".": {} },
  "bump-minor-pre-major": true
}
EOF

# Bootstrap: create manifest with current version
echo '{ ".": "1.0.0" }' > .release-please-manifest.json

# Commit both files
git add .release-please-config.json .release-please-manifest.json
git commit -m "chore: configure release-please"
git push

# Local CLI (optional, for debugging)
npm install -g release-please
release-please release-pr \
  --repo-url=your-org/your-repo \
  --token=$GITHUB_TOKEN

release-please github-release \
  --repo-url=your-org/your-repo \
  --token=$GITHUB_TOKEN
```

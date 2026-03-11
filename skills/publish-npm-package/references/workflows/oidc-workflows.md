# OIDC-Based npm Publishing Workflows

Production-ready GitHub Actions workflows using OIDC for npm authentication.
OIDC eliminates long-lived tokens — GitHub requests a short-lived token from npm at publish time.

> **Prerequisite:** Link your npm package to your GitHub repo at
> `https://www.npmjs.com/package/<pkg>/access` → Publishing access → Add GitHub Actions.

---

## 1. OIDC + semantic-release

Fully automated: push to `main` → analyze commits → bump version → publish → GitHub release.

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    branches: [main]

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false          # never cancel a publish mid-flight

permissions:
  contents: write      # push tags + GitHub releases
  issues: write        # comment on resolved issues
  pull-requests: write # comment on merged PRs
  id-token: write      # OIDC token for npm

jobs:
  release:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0              # full history for commit analysis
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm test

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
```

### `.releaserc.json`

```json
{
  "$schema": "https://json.schemastore.org/semantic-release.json",
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    ["@semantic-release/npm", { "provenance": true }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version} [skip ci]"
    }],
    "@semantic-release/github"
  ]
}
```

### Install

```bash
npm i -D semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github
```

### Checklist

- [ ] npm package linked to GitHub repo (npmjs.com → package settings)
- [ ] Repo uses Conventional Commits (`feat:`, `fix:`, `BREAKING CHANGE:`)
- [ ] `package.json` has `name`, `version`, and `repository` fields
- [ ] No `NPM_TOKEN` needed — OIDC handles auth

---

## 2. OIDC + changesets

Human-curated changelogs with PR-based version bumps via the Changesets bot.

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    branches: [main]

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: write
  pull-requests: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm test

      - uses: changesets/action@v1
        with:
          version: npm run version    # opens/updates "Version Packages" PR
          publish: npm run release    # publishes when that PR is merged
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `package.json` scripts

```json
{
  "scripts": {
    "version": "changeset version && npm install --package-lock-only",
    "release": "npm run build && changeset publish --access public"
  },
  "publishConfig": { "provenance": true }
}
```

### `.changeset/config.json`

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch"
}
```

### Install & workflow

```bash
npm i -D @changesets/cli @changesets/changelog-github
npx changeset init
```

1. Create feature branch → make changes.
2. Run `npx changeset` → select packages, bump type, write summary.
3. Commit the `.changeset/<id>.md` file with your PR.
4. Merge PR → bot opens a **"Version Packages"** PR.
5. Merge that PR → workflow publishes to npm.

### Checklist

- [ ] npm package linked to GitHub repo for OIDC
- [ ] `"publishConfig": { "provenance": true }` in `package.json`
- [ ] `.changeset/config.json` committed with `"access": "public"`

---

## 3. OIDC + release-please

Two-job pattern: release-please creates the release, then a separate job publishes.

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    branches: [main]

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  release-please:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    outputs:
      release_created: ${{ steps.rp.outputs.release_created }}
    steps:
      - id: rp
        uses: googleapis/release-please-action@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

  publish:
    needs: release-please
    if: needs.release-please.outputs.release_created == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm test
      - run: npm publish --provenance --access public
```

### `.release-please-config.json`

```json
{
  "packages": {
    ".": {
      "release-type": "node",
      "changelog-path": "CHANGELOG.md",
      "bump-minor-pre-major": true,
      "bump-patch-for-minor-pre-major": true
    }
  }
}
```

### `.release-please-manifest.json`

```json
{ ".": "0.0.0" }
```

> Replace `"0.0.0"` with your current version.

### Checklist

- [ ] npm package linked to GitHub repo for OIDC
- [ ] Both config files committed; manifest version matches `package.json`
- [ ] Uses Conventional Commits

---

## 4. OIDC + Manual Trigger

Publish when a GitHub Release is created. No automation tools needed.

### `.github/workflows/publish.yml`

```yaml
name: Publish to npm

on:
  release:
    types: [published]

concurrency:
  group: publish-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm test
      - run: npm publish --provenance --access public
```

### Developer workflow

```bash
npm version patch      # or minor / major
git push --follow-tags
gh release create v1.2.3
```

---

## Adding npm Caching

Already included in all workflows above via `cache: npm` in `actions/setup-node`.
For monorepos with multiple lock files:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: lts/*
    cache: npm
    cache-dependency-path: packages/*/package-lock.json
```

---

## Matrix Testing Before Publish

Add a `test` job and make the release job depend on it:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
      fail-fast: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm
      - run: npm ci
      - run: npm test

  release:
    needs: test
    # ... publish steps from any workflow above
```

Cross-OS testing — add `os: [ubuntu-latest, windows-latest, macos-latest]` to the matrix.

---

## Pre-release / Beta Patterns

### semantic-release

```json
{ "branches": ["main", { "name": "beta", "prerelease": true }] }
```

Update trigger: `branches: [main, beta]`. Pushes to `beta` → `1.2.3-beta.1`.

### changesets

```bash
npx changeset pre enter beta   # enter pre-release mode
# ... work normally, each publish → 1.2.3-beta.0, etc.
npx changeset pre exit          # exit when ready for stable
```

### release-please

```json
{ "packages": { ".": { "release-type": "node", "prerelease": true, "prerelease-type": "beta" } } }
```

### Manual — publish to dist-tag

```yaml
- run: |
    TAG="${{ github.event.release.tag_name }}"
    if [[ "$TAG" == *"-"* ]]; then
      npm publish --provenance --access public --tag beta
    else
      npm publish --provenance --access public
    fi
```

---

## Branch Protection Recommendations

| Setting | Value | Why |
|---|---|---|
| Require PR reviews | 1+ approvals | Prevent unreviewed publishes |
| Require status checks | `test` job | Never publish broken code |
| Require linear history | Enabled | Cleaner commit analysis |
| Require signed commits | Recommended | Verify committer identity |

---

## Concurrency Control

### Basic — prevent overlapping publishes

```yaml
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
```

### With approval gate

```yaml
jobs:
  publish:
    environment: npm   # configure required reviewers in Settings → Environments
```

### Monorepo — parallel packages, sequential per-package

```yaml
concurrency:
  group: publish-${{ matrix.package }}
  cancel-in-progress: false
```

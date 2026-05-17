# Trusted-Publishing npm Workflows

GitHub Actions templates for npm trusted publishing. These templates use OIDC auth, zero npm tokens, and automatic provenance for eligible public packages from public repositories.

## Contents

- [Template policy](#template-policy)
- [Package-manager blocks](#package-manager-blocks)
- [1. Trusted publishing + semantic-release](#1-trusted-publishing--semantic-release)
- [2. Trusted publishing + changesets](#2-trusted-publishing--changesets)
- [3. Trusted publishing + release-please](#3-trusted-publishing--release-please)
- [4. Trusted publishing + manual trigger](#4-trusted-publishing--manual-trigger)
- [Pre-release patterns](#pre-release-patterns)
- [Production hardening](#production-hardening)

## Template policy

- Use `actions/checkout@v6` and `actions/setup-node@v6` for new examples.
- Use Node 24 in release jobs so npm CLI satisfies trusted-publishing requirements.
- Set `package-manager-cache: false` in release jobs; cache can be used in test-only jobs.
- Keep templates tag-readable. Pin actions to full SHAs before production rollout and leave the version tag in a comment.
- Do not add `NPM_TOKEN`, `NODE_AUTH_TOKEN`, `--provenance`, `NPM_CONFIG_PROVENANCE`, or `publishConfig.provenance` to pure trusted-publishing templates.

## Package-manager blocks

Default npm block:

```yaml
- uses: actions/setup-node@v6
  with:
    node-version: '24'
    registry-url: https://registry.npmjs.org
    package-manager-cache: false

- run: npm ci
```

pnpm block:

```yaml
- uses: actions/setup-node@v6
  with:
    node-version: '24'
    registry-url: https://registry.npmjs.org
    package-manager-cache: false
- uses: pnpm/action-setup@v4
  with:
    run_install: false
- run: pnpm install --frozen-lockfile
```

Yarn Berry block:

```yaml
- uses: actions/setup-node@v6
  with:
    node-version: '24'
    registry-url: https://registry.npmjs.org
    package-manager-cache: false
- run: corepack enable
- run: yarn install --immutable
```

Use Bun only when the repo already has `bun.lockb` and a committed Bun workflow convention.

## 1. Trusted publishing + semantic-release

Fully automated: push to `main` -> analyze commits -> bump version -> publish -> GitHub release.

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
  issues: write
  pull-requests: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: https://registry.npmjs.org
          package-manager-cache: false

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
    "@semantic-release/npm",
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version} [skip ci]"
    }],
    "@semantic-release/github"
  ]
}
```

Checklist:

- package already exists on npm and is linked to this workflow as trusted publisher
- repo uses Conventional Commits
- `@semantic-release/npm` version supports npm trusted publishing
- no npm token is present in the release job

## 2. Trusted publishing + changesets

Human-curated changesets with a Version Packages PR, then publish when that PR merges.

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
      - uses: actions/checkout@v6

      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: https://registry.npmjs.org
          package-manager-cache: false

      - run: npm ci
      - run: npm test

      - uses: changesets/action@v1
        with:
          version: npm run version
          publish: npm run release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `package.json` scripts

```json
{
  "scripts": {
    "version": "changeset version && npm install --package-lock-only",
    "release": "npm run build --if-present && changeset publish --access public"
  }
}
```

For pnpm or Yarn, change the `version` and `release` scripts to the repo's package manager commands.

## 3. Trusted publishing + release-please

Two-job pattern: release-please creates the GitHub Release; a separate publish job publishes only when a release was created.

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
      tag_name: ${{ steps.rp.outputs.tag_name }}
    steps:
      - id: rp
        uses: googleapis/release-please-action@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          config-file: .release-please-config.json
          manifest-file: .release-please-manifest.json

  publish:
    needs: release-please
    if: needs.release-please.outputs.release_created == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: https://registry.npmjs.org
          package-manager-cache: false

      - run: npm ci
      - run: npm run build --if-present
      - run: npm test
      - run: npm publish --access public
```

Manifest version must match `package.json` before the first release-please run.

## 4. Trusted publishing + manual trigger

Publish when a GitHub Release is created. Use for low-frequency releases or repos that do not need a versioning bot.

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
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: https://registry.npmjs.org
          package-manager-cache: false

      - run: npm ci
      - run: npm test
      - run: npm run build --if-present
      - run: npm publish --access public
```

Developer workflow:

```bash
npm version patch
git push --follow-tags
gh release create v1.2.3
```

## Pre-release patterns

Use npm dist-tags without adding provenance flags:

```yaml
- run: |
    TAG="${{ github.event.release.tag_name }}"
    if [[ "$TAG" == *"-"* ]]; then
      npm publish --access public --tag beta
    else
      npm publish --access public
    fi
```

For semantic-release, use prerelease branches in `.releaserc.json`. For changesets, use `npx changeset pre enter beta`. For release-please, configure `prerelease-type`.

## Production hardening

- Pin GitHub Actions to full SHAs before production rollout.
- Add a separate test matrix job if the package needs multi-version Node coverage.
- Use `concurrency.cancel-in-progress: false` for publish jobs.
- Protect release branches/tags and require review for release environments when needed.
- Verify after publish with `npm audit signatures` when provenance/signatures are expected.

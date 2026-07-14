# Token-Based npm Publishing Workflows

GitHub Actions templates using `NPM_TOKEN` / `NODE_AUTH_TOKEN` for npm authentication. Use these when trusted publishing is unavailable or for first-publish bootstrap.

## Contents

- [When to use token auth](#when-to-use-token-auth)
- [Token diagnostics](#token-diagnostics)
- [Template policy](#template-policy)
- [1. Token + semantic-release](#1-token--semantic-release)
- [2. Token + changesets](#2-token--changesets)
- [3. Token + release-please](#3-token--release-please)
- [4. Token + manual trigger](#4-token--manual-trigger)
- [Adding provenance to token workflows](#adding-provenance-to-token-workflows)
- [Private registries](#private-registries)
- [Token rotation](#token-rotation)

## When to use token auth

Use token auth for:

- private packages
- self-hosted runners or GHES
- private registries
- first publish of a package before trusted publishing can be linked
- non-GitHub CI when trusted publishing is not configured
- token+provenance workflows where `NODE_AUTH_TOKEN` authenticates and `id-token: write` signs provenance

After a public package is bootstrapped and linked to a supported trusted publisher, switch to `oidc-workflows.md` unless a constraint keeps token auth necessary.

## Token diagnostics

`npm whoami` is useful only for token/login auth. It does not validate trusted publishing.

Local token check:

```bash
npm whoami --registry https://registry.npmjs.org \
  --//registry.npmjs.org/:_authToken="${NPM_TOKEN}"
```

CI token check:

```yaml
- run: npm whoami --registry https://registry.npmjs.org
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Run this diagnostic before a dry-run publish, not as proof that trusted publishing works.

## Template policy

- Use `actions/checkout@v6` and `actions/setup-node@v6` for new examples.
- Use Node 24 in release jobs.
- Set `package-manager-cache: false` in release jobs.
- Use `NODE_AUTH_TOKEN` in the publish step or release tool step that needs npm auth.
- Do not add `id-token: write` unless this is the token+provenance lane.

## 1. Token + semantic-release

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
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
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
    ["@semantic-release/npm", { "npmPublish": true }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version} [skip ci]"
    }],
    "@semantic-release/github"
  ]
}
```

Add semantic-release npm provenance config only in the token+provenance lane.

## 2. Token + changesets

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
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### `.npmrc`

```ini
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
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

For pnpm/Yarn, replace install and version scripts with the repo's package-manager commands.

## 3. Token + release-please

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
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## 4. Token + manual trigger

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
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## Adding provenance to token workflows

Token+provenance is a separate lane: token auth performs the publish, and OIDC signs provenance. It needs npm CLI 9.5.0+, a supported cloud-hosted runner, `id-token: write`, and explicit provenance config.

Add the permission:

```yaml
permissions:
  contents: read
  id-token: write
```

Add provenance to direct publish:

```yaml
- run: npm publish --provenance --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

For third-party tools:

- semantic-release: configure `["@semantic-release/npm", { "provenance": true }]`
- changesets: use `changeset publish --provenance --access public` or `NPM_CONFIG_PROVENANCE=true`
- release-please: add `--provenance` to the separate publish job

Do not copy these settings into pure trusted publishing. Trusted publishing already handles eligible provenance automatically.

## Private registries

Change `registry-url`, `.npmrc`, and token secret for non-npmjs registries.

| Registry | `registry-url` | Token secret |
|---|---|---|
| GitHub Packages | `https://npm.pkg.github.com` | `GITHUB_TOKEN` or package token |
| Artifactory | registry-specific URL | `ARTIFACTORY_TOKEN` |
| Verdaccio | registry-specific URL | `VERDACCIO_TOKEN` |

GitHub Packages also needs `scope: '@your-org'` in setup-node and `publishConfig.registry` in `package.json`.

## Token rotation

1. Create a new granular token with the same or narrower package scope.
2. Update the `NPM_TOKEN` GitHub secret.
3. Verify with `scripts/check-npm-auth.sh --token` or `npm whoami`.
4. Run `npm publish --dry-run` if safe for the package.
5. Revoke the old token on npmjs.com.

Use short-lived bootstrap tokens for first publish and revoke them immediately after switching to trusted publishing.

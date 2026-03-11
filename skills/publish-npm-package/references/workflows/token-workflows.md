# Token-Based npm Publishing Workflows

Production-ready GitHub Actions workflows using `NPM_TOKEN` for npm authentication.
Use when OIDC is unavailable (private npm orgs, self-hosted runners, GHES, or custom registries).

---

## Creating and Storing the npm Token

### 1. Generate the token

1. Log in to [npmjs.com](https://www.npmjs.com/) → Avatar → **Access Tokens** → **Generate New Token**.
2. Select **Granular Access Token** (recommended over legacy Automation tokens).
3. Configure: name it `github-actions-<repo>`, set 90–365 day expiry, scope to specific packages, grant Read+Write.
4. Copy the token — shown only once.

### 2. Add to GitHub

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** → Name: `NPM_TOKEN`, paste token.

### 3. Verify locally

```bash
npm whoami --registry https://registry.npmjs.org //registry.npmjs.org/:_authToken=<token>
```

---

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
  # No id-token — using NPM_TOKEN instead
  # Add id-token: write if you also want provenance (see section below)

jobs:
  release:
    runs-on: ubuntu-latest
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
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
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}    # ← token auth
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

> **vs OIDC:** No `"provenance": true` in the npm plugin config. Add it back
> if you also set `id-token: write` (see [Adding Provenance](#adding-provenance-to-token-workflows)).

### Install

```bash
npm i -D semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github
```

### Checklist

- [ ] `NPM_TOKEN` secret added to GitHub repo
- [ ] Conventional Commits in use
- [ ] Token has write permission for the target package

---

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
          version: npm run version
          publish: npm run release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### `.npmrc` (required for changesets with token auth)

```ini
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

> **vs OIDC:** Changesets needs `.npmrc` to find the token. The OIDC version
> doesn't need `.npmrc` because `actions/setup-node` configures auth automatically.

### `package.json` scripts

```json
{
  "scripts": {
    "version": "changeset version && npm install --package-lock-only",
    "release": "npm run build && changeset publish --access public"
  }
}
```

### Checklist

- [ ] `NPM_TOKEN` secret added
- [ ] `.npmrc` committed with `${NPM_TOKEN}` placeholder
- [ ] `.changeset/config.json` committed (same as OIDC version)

---

## 3. Token + release-please

Two-job pattern: release-please creates the release, publish job pushes to npm.

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
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
          registry-url: https://registry.npmjs.org

      - run: npm ci
      - run: npm test

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

> **vs OIDC:** No `id-token: write`, no `--provenance`. Auth via `NODE_AUTH_TOKEN` env var.

### Checklist

- [ ] `NPM_TOKEN` secret added
- [ ] `.release-please-config.json` and `.release-please-manifest.json` committed
- [ ] Uses Conventional Commits

---

## 4. Token + Manual Trigger

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

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

> **vs OIDC:** No `id-token: write`, no `--provenance`.

---

## Adding Provenance to Token Workflows

Combine token auth with OIDC provenance — the token authenticates, the OIDC token provides attestation.

Add `id-token: write` to permissions and `--provenance` to the publish command:

```yaml
permissions:
  contents: read
  id-token: write   # ← add for provenance
# ...
- run: npm publish --provenance --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

For semantic-release: add `["@semantic-release/npm", { "provenance": true }]` to `.releaserc.json`.
For changesets: add `"publishConfig": { "provenance": true }` to `package.json`.

---

## Publishing to Private Registries

Change `registry-url` and token secret. Everything else stays the same.

| Registry | `registry-url` | Token secret |
|---|---|---|
| GitHub Packages | `https://npm.pkg.github.com` | `GITHUB_TOKEN` (built-in) |
| Artifactory | `https://company.jfrog.io/artifactory/api/npm/npm-local/` | `ARTIFACTORY_TOKEN` |
| Verdaccio | `https://verdaccio.internal.example.com/` | `VERDACCIO_TOKEN` |

GitHub Packages also needs `scope: '@your-org'` in setup-node and `"publishConfig": { "registry": "https://npm.pkg.github.com" }` in `package.json`.

---

## Multi-Registry Publishing

Use parallel jobs — one per registry. Each job sets its own `registry-url` and token:

```yaml
jobs:
  publish-npm:
    runs-on: ubuntu-latest
    permissions: { contents: read, id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: lts/*, cache: npm, registry-url: 'https://registry.npmjs.org' }
      - run: npm ci && npm test
      - run: npm publish --provenance --access public
        env: { NODE_AUTH_TOKEN: '${{ secrets.NPM_TOKEN }}' }

  publish-gpr:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: lts/*, cache: npm, registry-url: 'https://npm.pkg.github.com' }
      - run: npm ci
      - run: npm publish
        env: { NODE_AUTH_TOKEN: '${{ secrets.GITHUB_TOKEN }}' }
```

---

## Token Rotation

1. **Create** new token on npmjs.com with the same permissions.
2. **Update** `NPM_TOKEN` in repo Settings → Secrets.
3. **Verify** — trigger a `workflow_dispatch` dry-run:

```yaml
name: Verify npm token
on: workflow_dispatch
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: lts/*, registry-url: 'https://registry.npmjs.org' }
      - run: npm publish --dry-run && npm whoami
        env: { NODE_AUTH_TOKEN: '${{ secrets.NPM_TOKEN }}' }
```

4. **Revoke** old token on npmjs.com.

**Schedule:** Granular tokens every 90 days, legacy Automation tokens every 30 days.

### Automated reminder (optional)

```yaml
name: Token rotation reminder
on:
  schedule:
    - cron: '0 9 1 */3 *'
jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner, repo: context.repo.repo,
              title: '🔑 NPM_TOKEN rotation due',
              body: '1. Create new token\n2. Update secret\n3. Verify\n4. Revoke old',
              labels: ['maintenance'],
            });
```

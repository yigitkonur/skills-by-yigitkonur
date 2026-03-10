# GitHub Actions Workflow Templates

Complete, copy-paste-ready workflow files for every auth + versioning tool combination.

---

## OIDC + semantic-release

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
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `.releaserc.json`

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    ["@semantic-release/changelog", { "changelogFile": "CHANGELOG.md" }],
    ["@semantic-release/npm", { "provenance": true }],
    ["@semantic-release/git", {
      "assets": ["package.json", "CHANGELOG.md"],
      "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }],
    "@semantic-release/github"
  ]
}
```

### Required devDependencies

```bash
npm install -D semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github
```

**Note**: The `@semantic-release/npm` plugin handles provenance when `id-token: write` permission is set. No `NPM_TOKEN` secret needed with OIDC trusted publishing.

---

## OIDC + changesets

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
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - uses: changesets/action@v1
        with:
          publish: npm run release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `package.json` scripts

```json
{
  "scripts": {
    "release": "changeset publish --provenance --access public"
  }
}
```

### `.changeset/config.json`

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.0.0/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

### Required devDependencies

```bash
npm install -D @changesets/cli
npx changeset init
```

### Developer workflow

1. Make changes in a feature branch
2. Run `npx changeset` to create a changeset file
3. Commit the changeset file with your changes
4. Create PR and merge to `main`
5. The action creates a "Version Packages" PR
6. Merge the "Version Packages" PR to trigger publish

---

## OIDC + release-please

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
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
    steps:
      - id: release
        uses: googleapis/release-please-action@v4
        with:
          release-type: node

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
          node-version: 20
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
{
  ".": "0.0.0"
}
```

**Note**: Update the manifest version to your current package version before first run.

---

## OIDC + manual trigger (npm version)

For simple projects where you create GitHub Releases manually.

### `.github/workflows/release.yml`

```yaml
name: Publish
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
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - run: npm publish --provenance --access public
```

### Release workflow (manual)

1. Bump version locally: `npm version patch` (or minor/major)
2. Push the commit and tag: `git push && git push --tags`
3. Create a GitHub Release from the tag
4. The workflow triggers and publishes to npm

---

## Token + semantic-release

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
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### `.releaserc.json`

Same as OIDC version, but remove `"provenance": true` from npm plugin if you don't have `id-token: write`.

Or keep provenance by adding `id-token: write` to permissions (works alongside `NPM_TOKEN`).

---

## Token + changesets

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
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - uses: changesets/action@v1
        with:
          publish: npm run release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### `package.json` scripts

```json
{
  "scripts": {
    "release": "changeset publish --access public"
  }
}
```

---

## Token + release-please

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
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
    steps:
      - id: release
        uses: googleapis/release-please-action@v4
        with:
          release-type: node

  publish:
    needs: release-please
    if: needs.release-please.outputs.release_created == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## Token + manual trigger (npm version)

### `.github/workflows/release.yml`

```yaml
name: Publish
on:
  release:
    types: [published]

concurrency:
  group: publish-${{ github.ref }}
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org

      - run: npm ci

      - run: npm test

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## Monorepo variants

### Changesets monorepo (most common)

The changesets workflows above work for monorepos without modification. Each changeset specifies which packages to bump.

For workspaces, ensure `package.json` at root has:
```json
{
  "workspaces": ["packages/*"],
  "private": true
}
```

### release-please monorepo

Update `.release-please-config.json`:
```json
{
  "packages": {
    "packages/core": { "release-type": "node", "component": "core" },
    "packages/cli": { "release-type": "node", "component": "cli" },
    "packages/utils": { "release-type": "node", "component": "utils" }
  }
}
```

And `.release-please-manifest.json`:
```json
{
  "packages/core": "1.0.0",
  "packages/cli": "0.5.0",
  "packages/utils": "2.1.0"
}
```

The publish job needs to iterate over released packages:
```yaml
- if: needs.release-please.outputs.releases_created == 'true'
  run: |
    for dir in packages/*/; do
      if [ -f "$dir/package.json" ]; then
        cd "$dir"
        npm publish --provenance --access public || true
        cd -
      fi
    done
```

---

## Common workflow patterns

### Adding provenance to any token-based workflow

Add `id-token: write` to permissions and `--provenance` to the publish command. Both work alongside `NPM_TOKEN`:

```yaml
permissions:
  id-token: write  # Add this
  contents: read

# ... in publish step:
- run: npm publish --provenance --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Pre-release / beta channel

For semantic-release, add branch config:
```json
{
  "branches": [
    "main",
    { "name": "beta", "prerelease": true },
    { "name": "alpha", "prerelease": true }
  ]
}
```

For changesets, use pre mode:
```bash
npx changeset pre enter beta
# ... merge PRs ...
npx changeset pre exit
```

For release-please, use `prerelease-type`:
```json
{
  "packages": {
    ".": {
      "release-type": "node",
      "prerelease-type": "beta"
    }
  }
}
```

### Dry-run / verification

```bash
# semantic-release
npx semantic-release --dry-run

# changesets
npx changeset status

# npm pack (works for any approach)
npm pack --dry-run
```

### Branch protection recommendations

- Require PR reviews before merge to `main`
- Require status checks (tests) to pass
- Do not allow force pushes to `main`
- Use `concurrency` groups in workflows to prevent parallel publishes
- For semantic-release: the `GITHUB_TOKEN` is sufficient (no PAT needed for pushing tags)

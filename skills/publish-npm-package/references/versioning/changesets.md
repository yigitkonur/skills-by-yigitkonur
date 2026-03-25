# Changesets — PR-Based Version Management for npm

## Overview

Changesets is a version management tool designed around the pull request workflow.
Instead of deriving version bumps from commit messages, developers explicitly declare
version changes by adding changeset files during development.

| Metric | Value |
|--------|-------|
| Weekly npm downloads | ~1M |
| Maintainer | Changesets team (Atlassian origin) |
| License | MIT |
| Repository | `changesets/changesets` |
| Native monorepo support | ✅ First-class |

**Core philosophy:** The person making the change is the best person to describe and
classify that change. Version intent is captured at PR time, not release time.

> **⚠️ Steering:** changesets works for **both monorepos AND single-package repos**.
> It does **not** require conventional commits — developers describe changes in
> plain English via changeset files. If the team wants a human-gated release
> without adopting a commit convention, changesets is the right choice.

---

## How It Works

```
1. Developer makes code changes in a branch
2. Developer runs `npx changeset` to create a changeset file
3. Changeset file is committed with the PR
4. PR is reviewed and merged to main
5. GitHub Action detects accumulated changesets
6. Action opens a "Version Packages" PR (auto-updated with each merge)
7. Merging the Version Packages PR:
   a. Consumes all changeset files
   b. Bumps versions in package.json
   c. Updates CHANGELOG.md
   d. Publishes to npm
   e. Creates git tags
```

The two-phase approach (accumulate changesets → merge Version PR) gives teams
explicit control over when releases happen.

---

## Installation and Setup

### Install the CLI

```bash
npm install -D @changesets/cli
```

### Initialize Changesets

```bash
npx changeset init
```

This creates the `.changeset/` directory with:
- `config.json` — configuration file
- `README.md` — explanation for contributors

---

## Configuration

### Complete `.changeset/config.json`

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": [
    "@changesets/changelog-github",
    { "repo": "your-org/your-repo" }
  ],
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": [],
  "privatePackages": {
    "version": false,
    "tag": false
  },
  "snapshot": {
    "useCalculatedVersion": false,
    "prereleaseTemplate": "{tag}-{datetime}-{commit}"
  }
}
```

### Option-by-Option Breakdown

#### `changelog`

Controls how changelog entries are generated.

| Value | Description |
|-------|-------------|
| `"@changesets/changelog-github"` | Links to PRs, commits, and authors |
| `"@changesets/changelog-git"` | Basic git-based changelog |
| `false` | Disable changelog generation |
| Custom function | `["/path/to/module", { options }]` |

For `@changesets/changelog-github`, install separately:
```bash
npm install -D @changesets/changelog-github
```

#### `commit`

Whether `changeset version` auto-commits changes.

| Value | Behavior |
|-------|----------|
| `false` | No auto-commit (default, recommended for CI) |
| `true` | Commits with default message |
| `["@changesets/commit", {}]` | Custom commit message module |

#### `fixed`

Groups of packages that always share the same version number:

```json
{
  "fixed": [
    ["@myorg/core", "@myorg/types", "@myorg/utils"]
  ]
}
```

When any package in a fixed group gets a bump, all packages in that group get the
same bump and the same new version number.

#### `linked`

Groups of packages whose versions are coordinated but not identical:

```json
{
  "linked": [
    ["@myorg/react-components", "@myorg/vue-components"]
  ]
}
```

Linked packages get the **highest** bump from the group. If one gets a minor and
another gets a patch, both get a minor bump — but they may have different version
numbers if they started at different versions.

#### `access`

Controls npm publish access.

| Value | Description |
|-------|-------------|
| `"public"` | Publish as public packages |
| `"restricted"` | Publish as private/scoped packages |

For scoped packages (`@org/pkg`), npm defaults to restricted. Set `"public"` to
override.

#### `baseBranch`

The branch that changesets compares against. Usually `"main"` or `"master"`.

#### `updateInternalDependencies`

How to update internal workspace dependency ranges when a dependency is bumped.

| Value | Behavior |
|-------|----------|
| `"patch"` | Always update internal dep ranges (default) |
| `"minor"` | Only update if bump is minor or higher |
| `"out-of-range"` | Only update if current range wouldn't include new version |

#### `ignore`

Packages to exclude from versioning entirely:

```json
{
  "ignore": ["@myorg/internal-tool", "@myorg/dev-scripts"]
}
```

#### `privatePackages`

How to handle packages with `"private": true` in package.json:

```json
{
  "privatePackages": {
    "version": true,
    "tag": false
  }
}
```

- `version: true` — bump version in package.json even for private packages
- `tag: false` — don't create git tags for private packages

---

## Developer Workflow

### Step 1: Make Code Changes

Work on your feature/fix branch as normal.

### Step 2: Create a Changeset

```bash
npx changeset
```

The interactive prompt asks:

```
🦋  Which packages would you like to include? (select with space)
❯ ◯ @myorg/core
  ◯ @myorg/utils
  ◯ @myorg/cli

🦋  Which packages should have a major bump?
🦋  Which packages should have a minor bump?

🦋  Please enter a summary for this change:
  Added streaming support to the core API
```

### Step 3: Commit the Changeset File

The command creates a file like `.changeset/happy-dogs-dance.md`. Commit it:

```bash
git add .changeset/happy-dogs-dance.md
git commit -m "docs: add changeset for streaming feature"
```

### Step 4: Open PR

The changeset file is part of the PR diff and can be reviewed alongside code changes.

### Adding Multiple Changesets

A single PR can include multiple changeset files for different logical changes:

```bash
npx changeset  # first changeset for feature A
npx changeset  # second changeset for bug fix B
```

### Empty Changeset

If a PR doesn't need a version bump:

```bash
npx changeset --empty
```

Creates an empty changeset that satisfies CI checks without triggering a release.

---

## Changeset File Format

Files in `.changeset/` are markdown with YAML frontmatter:

```markdown
---
"@myorg/core": minor
"@myorg/utils": patch
---

Added streaming support to the core API.

This introduces a new `stream()` method on the client that returns
an async iterator for processing large datasets.
```

### Frontmatter Rules

- Package names are keys, bump types are values
- Valid bump types: `major`, `minor`, `patch`
- Multiple packages can be listed
- The markdown body becomes the changelog entry

### Manual Creation

You can create changeset files manually instead of using the interactive CLI:

```bash
cat > .changeset/my-change.md << 'EOF'
---
"my-package": patch
---

Fixed null pointer when input is empty.
EOF
```

---

## GitHub Action Configuration

### Install the Action

```yaml
name: Release

on:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: write
  pull-requests: write
  id-token: write

jobs:
  release:
    name: Release
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

      - name: Create Release PR or Publish
        id: changesets
        uses: changesets/action@v1
        with:
          publish: npx changeset publish
          version: npx changeset version
          title: "chore: version packages"
          commit: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

> Pair this with the matching workflow template for auth wiring. Pure OIDC keeps
> only `GITHUB_TOKEN` here; token auth adds the npm token env or `.npmrc`
> placeholder from `references/workflows/token-workflows.md`.

### Action Options

| Option | Default | Description |
|--------|---------|-------------|
| `publish` | — | Command to publish packages |
| `version` | `"npx changeset version"` | Command to version packages |
| `title` | `"Version Packages"` | Title of the Version PR |
| `commit` | `"Version Packages"` | Commit message for version bump |
| `createGithubReleases` | `true` | Create GitHub releases |
| `setupGitUser` | `true` | Configure git user for commits |

### Action Outputs

| Output | Description |
|--------|-------------|
| `published` | `"true"` if packages were published |
| `publishedPackages` | JSON array of published packages |
| `hasChangesets` | `"true"` if pending changesets exist |
| `pullRequestNumber` | Number of the Version PR |

---

## Pre-release Mode

### Entering Pre-release

```bash
npx changeset pre enter beta
```

This creates `.changeset/pre.json`. From now on, `changeset version` produces
pre-release versions:

```
1.0.0 → 1.1.0-beta.0 → 1.1.0-beta.1 → ...
```

### Exiting Pre-release

```bash
npx changeset pre exit
```

The next `changeset version` produces a stable release:

```
1.1.0-beta.3 → 1.1.0
```

### Pre-release Tags

Pre-release versions are published to npm with the tag name as the dist-tag:

```bash
npm install your-package@beta    # installs 1.1.0-beta.3
npm install your-package@latest  # installs 1.0.0 (stable)
```

### Common Pre-release Tags

| Tag | Use case |
|-----|----------|
| `beta` | Feature-complete testing |
| `alpha` | Early development |
| `rc` | Release candidate |
| `canary` | Per-commit builds |
| `next` | Upcoming major version |

---

## Single-Package Configuration

For repos with only one package, changesets works out of the box with minimal config:

```json
// .changeset/config.json
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/changelog-github",
  "commit": false,
  "access": "public",
  "baseBranch": "main"
}
```

The interactive `npx changeset` prompt will show only your single package.
Everything else (Version PR, publishing, changelog) works identically to monorepos.

---

## Version Packages PR Workflow

When the changesets GitHub Action runs on `main` and finds pending changeset files,
it opens (or updates) a **"Version Packages" PR**. This PR:

1. **Consumes** all `.changeset/*.md` files (deletes them)
2. **Bumps** `version` in every affected `package.json`
3. **Updates** `CHANGELOG.md` with entries from the changeset descriptions
4. **Stays open** and auto-updates as more changesets are merged to `main`

When the team decides to release, they **merge the Version Packages PR**. The
action then runs the `publish` command (e.g., `npx changeset publish`), publishes
to npm, and creates git tags.

This two-phase flow (accumulate → merge PR → publish) gives explicit human control
over release timing without requiring any commit convention.

---

## Monorepo Patterns

### Fixed Versioning (All Packages Same Version)

```json
{
  "fixed": [
    ["@myorg/core", "@myorg/react", "@myorg/vue", "@myorg/utils"]
  ]
}
```

All packages always share the same version. A change to any package bumps all.

### Linked Versioning (Coordinated Bumps)

```json
{
  "linked": [
    ["@myorg/react-button", "@myorg/react-input", "@myorg/react-modal"]
  ]
}
```

Packages get the highest bump from the group but may have different version numbers.

### Independent Versioning (Default)

No `fixed` or `linked` configuration. Each package is versioned independently based
on its own changesets.

### Internal Dependency Updates

When `@myorg/core` is bumped, packages that depend on it are automatically updated:

```json
{
  "updateInternalDependencies": "patch"
}
```

This ensures consumers within the monorepo always reference compatible versions.

---

## Publishing with Provenance

### npm Provenance via OIDC

```yaml
      - name: Create Release PR or Publish
        uses: changesets/action@v1
        with:
          publish: npx changeset publish --provenance --access public
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Requirements:
- `id-token: write` permission in the workflow
- npm account linked to the GitHub repository
- `--access public` required for scoped packages with provenance
- No `NPM_TOKEN` / `NODE_AUTH_TOKEN` in the OIDC variant

---

## Snapshot Releases

Publish one-off versions from any branch without affecting the main release flow:

```bash
npx changeset version --snapshot canary
npx changeset publish --tag canary
```

Produces versions like `0.0.0-canary-20240115120000-abc1234` based on the
`prereleaseTemplate` config.

Useful for:
- Testing PR changes before merging
- Nightly builds
- CI/CD preview deployments

---

## Common Issues

### 1. Forgotten Changesets

**Problem:** PRs merged without changeset files, so changes aren't released.

**Fix:** Add a CI check that requires changesets:
```yaml
- name: Check for changesets
  run: npx changeset status
```

Or use the [changeset-bot](https://github.com/apps/changeset-bot) GitHub App which
comments on PRs missing changesets.

### 2. Version PR Merge Conflicts

**Problem:** The "Version Packages" PR gets conflicts from concurrent merges.

**Fix:** The changeset action auto-rebases the Version PR on each push to main.
If conflicts persist, close the PR and let the action create a new one.

### 3. Yarn/pnpm Compatibility

**pnpm:**
```yaml
publish: pnpm changeset publish
version: pnpm changeset version
```

Ensure `.npmrc` has:
```
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

**Yarn Berry:**
```yaml
publish: yarn changeset publish
version: yarn changeset version
```

### 4. Scoped Package Access

**Problem:** `npm ERR! 402 Payment Required` for scoped packages.

**Fix:** Set `"access": "public"` in `.changeset/config.json` or pass `--access public`:
```bash
npx changeset publish --access public
```

### 5. Changelog Not Linking to PRs

**Problem:** Changelog entries don't include PR/commit links.

**Fix:** Use `@changesets/changelog-github`:
```json
{
  "changelog": [
    "@changesets/changelog-github",
    { "repo": "your-org/your-repo" }
  ]
}
```

Requires `GITHUB_TOKEN` to be set for API access.

---

## Complete Workflow with OIDC Provenance

```yaml
name: Release

on:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: write
  pull-requests: write
  id-token: write

jobs:
  release:
    name: Release
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

      - name: Create Release PR or Publish
        id: changesets
        uses: changesets/action@v1
        with:
          publish: npx changeset publish --provenance --access public
          version: npx changeset version
          title: "chore: version packages"
          commit: "chore: version packages"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Report published packages
        if: steps.changesets.outputs.published == 'true'
        run: |
          echo "Published packages:"
          echo '${{ steps.changesets.outputs.publishedPackages }}' | jq '.'
```

### Using NPM_TOKEN Instead of OIDC

If your npm org doesn't support OIDC provenance, switch to the token workflow
template and add token auth explicitly:

```yaml
      - name: Create Release PR or Publish
        uses: changesets/action@v1
        with:
          publish: npx changeset publish --access public
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## First Publish (Greenfield)

For a brand-new package that has never been published to npm:

1. Run `npx changeset init` to create `.changeset/config.json`
2. Set `"version": "0.0.0"` in `package.json` (or your intended starting version)
3. Create your first changeset: `npx changeset` → select your package → choose
   `minor` for an initial feature release
4. Run `npx changeset version` locally to verify it bumps to `0.1.0`
5. Commit everything and push — the GitHub Action will open the first Version PR
6. Merge the Version PR to trigger the first npm publish

No git tags or prior history are needed. Changesets starts from whatever version
is in `package.json`.

If your long-term auth mode is OIDC, this section only covers the **versioning**
baseline. The first publish still needs token bootstrap before you switch the
workflow to pure OIDC.

---

## When to Use Changesets

**Best for:**
- Monorepos with multiple publishable packages
- **Single-package repos** that want human-gated releases without commit conventions
- Teams that want explicit control over version bumps
- Projects that batch releases (weekly, milestone-based)
- Teams where commit message discipline is inconsistent

**Avoid when:**
- You want fully automated releases on every merge (use semantic-release)
- You prefer commit-driven versioning over manual changeset creation

---

## Quick Reference

```bash
# Initialize changesets in your project
npx changeset init

# Create a new changeset (interactive)
npx changeset

# Create an empty changeset (no version bump)
npx changeset --empty

# Apply changesets and bump versions locally
npx changeset version

# Publish all changed packages
npx changeset publish

# Enter pre-release mode
npx changeset pre enter beta

# Exit pre-release mode
npx changeset pre exit

# Check for pending changesets
npx changeset status

# Publish with provenance
npx changeset publish --provenance --access public
```

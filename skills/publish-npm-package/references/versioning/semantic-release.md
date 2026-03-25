# semantic-release — Fully Automated npm Versioning & Publishing

## Overview

semantic-release automates the entire package release workflow: version determination,
changelog generation, npm publishing, git tagging, and GitHub release creation — all
driven by conventional commit messages.

| Metric | Value |
|--------|-------|
| Weekly npm downloads | ~10M |
| GitHub stars | ~20K |
| License | MIT |
| Repository | `semantic-release/semantic-release` |

**Core philosophy:** No human decides what the next version number will be. Commits
since the last release are analyzed, and the version bump is determined automatically.

> **⚠️ Steering:** Only choose semantic-release for **single-package repos** with
> strong conventional-commit discipline. It publishes automatically on every push —
> there is no human gate. For monorepos, use **changesets** or **release-please**
> instead (semantic-release has no native monorepo support).

---

## How It Works

The release pipeline executes these steps in order:

```
1. Verify conditions   → Check CI, tokens, branch config
2. Get last release    → Find latest git tag
3. Analyze commits     → Parse conventional commits since last tag
4. Verify release      → Confirm a release is needed
5. Generate notes      → Build changelog / release notes
6. Prepare             → Write changelog file, update package.json
7. Publish             → npm publish (with provenance if configured)
8. Add channel         → Apply npm dist-tags
9. Success             → Create GitHub release, comment on PRs/issues
10. Fail               → Post failure notifications
```

Each step is handled by a plugin. Plugins run in the order they appear in the
configuration array — **order matters**.

---

## Conventional Commit Format

semantic-release uses the Angular commit convention by default.

### Commit → Version Bump Mapping

| Commit prefix | Example | Version bump |
|---------------|---------|--------------|
| `fix:` | `fix: resolve null pointer in parser` | **Patch** (1.0.0 → 1.0.1) |
| `perf:` | `perf: reduce bundle size by 40%` | **Patch** (1.0.0 → 1.0.1) |
| `feat:` | `feat: add streaming API support` | **Minor** (1.0.0 → 1.1.0) |
| `feat!:` | `feat!: redesign auth module` | **Major** (1.0.0 → 2.0.0) |
| Any with `BREAKING CHANGE:` footer | See below | **Major** (1.0.0 → 2.0.0) |
| `chore:` | `chore: update dev dependencies` | No release |
| `docs:` | `docs: fix typo in README` | No release |
| `ci:` | `ci: add Node 20 to matrix` | No release |
| `refactor:` | `refactor: simplify error handling` | No release |
| `test:` | `test: add edge case coverage` | No release |
| `style:` | `style: fix indentation` | No release |
| `build:` | `build: upgrade webpack to v5` | No release |

### Breaking Change Footer

Any commit type can trigger a major bump with the `BREAKING CHANGE:` footer:

```
refactor: switch config format to YAML

BREAKING CHANGE: JSON configuration files are no longer supported.
Migrate using `npx migrate-config` before upgrading.
```

### Scoped Commits

Scopes are optional and don't affect version bumps:

```
feat(api): add rate limiting endpoint
fix(parser): handle escaped quotes
```

---

## Installation and Setup

### Install Dependencies

```bash
npm install -D semantic-release \
  @semantic-release/changelog \
  @semantic-release/git \
  @semantic-release/github
```

The core package includes `commit-analyzer`, `release-notes-generator`, and `npm`
plugins by default — no need to install them separately.

### Remove version from package.json (Optional)

Since semantic-release manages the version, you can set it to a placeholder:

```json
{
  "version": "0.0.0-semantically-released"
}
```

---

## Configuration

Create `.releaserc.json` in your project root.

### Complete Configuration Example

```json
{
  "branches": [
    "main",
    { "name": "beta", "prerelease": true },
    { "name": "alpha", "prerelease": true }
  ],
  "plugins": [
    ["@semantic-release/commit-analyzer", {
      "preset": "angular",
      "releaseRules": [
        { "type": "docs", "scope": "README", "release": "patch" },
        { "type": "refactor", "release": "patch" },
        { "type": "style", "release": "patch" },
        { "type": "perf", "release": "patch" }
      ],
      "parserOpts": {
        "noteKeywords": ["BREAKING CHANGE", "BREAKING CHANGES"]
      }
    }],
    ["@semantic-release/release-notes-generator", {
      "preset": "angular",
      "writerOpts": {
        "commitsSort": ["subject", "scope"]
      }
    }],
    ["@semantic-release/changelog", {
      "changelogFile": "CHANGELOG.md",
      "changelogTitle": "# Changelog"
    }],
    ["@semantic-release/npm", {
      "npmPublish": true,
      "pkgRoot": ".",
      "tarballDir": "dist"
    }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json", "package-lock.json"],
      "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }],
    ["@semantic-release/github", {
      "addReleases": "bottom",
      "labels": ["released"],
      "releasedLabels": ["released-on-@${nextRelease.channel}"],
      "successComment": "🎉 This ${issue.pull_request ? 'PR is included' : 'issue has been resolved'} in version ${nextRelease.version}."
    }]
  ]
}
```

### Plugin-by-Plugin Breakdown

#### @semantic-release/commit-analyzer

Determines the version bump type from commits.

| Option | Default | Description |
|--------|---------|-------------|
| `preset` | `"angular"` | Conventional commits preset |
| `releaseRules` | Angular defaults | Custom type→bump mappings |
| `parserOpts` | `{}` | Commit parser configuration |

Custom `releaseRules` are merged with defaults — they don't replace them.

#### @semantic-release/release-notes-generator

Generates release notes / changelog content from commits.

| Option | Default | Description |
|--------|---------|-------------|
| `preset` | `"angular"` | Template preset |
| `writerOpts` | `{}` | Handlebars template options |
| `presetConfig` | `{}` | Override preset config |

#### @semantic-release/changelog

Writes generated notes to a changelog file.

| Option | Default | Description |
|--------|---------|-------------|
| `changelogFile` | `"CHANGELOG.md"` | File path for changelog |
| `changelogTitle` | `""` | Title prepended to file |

#### @semantic-release/npm

Publishes the package to npm.

| Option | Default | Description |
|--------|---------|-------------|
| `npmPublish` | `true` | Whether to publish to npm |
| `pkgRoot` | `"."` | Directory with package.json |
| `tarballDir` | `false` | Directory to store .tgz tarball |

**Provenance** is enabled via the `--provenance` npm flag in CI, not a plugin option.

#### @semantic-release/git

Commits release artifacts back to the repository.

| Option | Default | Description |
|--------|---------|-------------|
| `assets` | `["CHANGELOG.md", ...]` | Files to commit |
| `message` | Template string | Commit message template |

The message template supports `${nextRelease.version}`, `${nextRelease.notes}`,
`${nextRelease.channel}`, `${branch.name}`, and `${lastRelease.version}`.

#### @semantic-release/github

Creates GitHub releases and comments on issues/PRs.

| Option | Default | Description |
|--------|---------|-------------|
| `addReleases` | `"bottom"` | Where to add releases |
| `labels` | `["released"]` | Labels for released issues/PRs |
| `successComment` | Template | Comment on resolved issues |
| `failComment` | Template | Comment on failed releases |

---

## Branch Configuration

### Simple (main only)

```json
{ "branches": ["main"] }
```

### Pre-release Channels

```json
{
  "branches": [
    "main",
    { "name": "beta", "prerelease": true },
    { "name": "alpha", "prerelease": true }
  ]
}
```

- Commits on `beta` → `2.0.0-beta.1`, `2.0.0-beta.2`, etc.
- Published to npm with `npm install pkg@beta`
- Merging `beta` → `main` triggers `2.0.0` stable release

### Maintenance Branches

```json
{
  "branches": [
    "+([0-9])?(.{+([0-9]),x}).x",
    "main",
    "next",
    { "name": "beta", "prerelease": true }
  ]
}
```

Maintenance branch `1.x` receives backported fixes, published as `1.x.y` patches.

---

## Pre-release Channels

### Beta Release Workflow

1. Create and push the `beta` branch from `main`
2. Commits on `beta` produce versions like `2.0.0-beta.1`
3. Published to npm under the `beta` dist-tag
4. Users install with `npm install your-package@beta`
5. When ready, merge `beta` → `main` for stable release

### Alpha Release Workflow

Same as beta but with `alpha` channel. Typically:
- `alpha` → early unstable builds
- `beta` → feature-complete pre-releases
- `main` → stable production releases

---

## Dry-Run Testing

> **⚠️ Always dry-run first** before enabling semantic-release in CI.
> This catches misconfigured tokens, missing tags, and commit-format issues.

```bash
# Requires GITHUB_TOKEN plus the publish auth for the mode you are testing.
# Local dry-runs usually use token auth; pure OIDC can only be exercised on
# GitHub-hosted runners.
npx semantic-release --dry-run

# With explicit branch
npx semantic-release --dry-run --branches main
```

Dry-run output shows:
- Which commits were analyzed
- What version would be determined
- What changelog would be generated
- What would be published (but skips actual publish)

---

## Commitlint Integration

Enforce conventional commits with commitlint + husky:

```bash
npm install -D @commitlint/cli @commitlint/config-conventional husky

# Initialize husky
npx husky init

# Add commit-msg hook
echo 'npx --no -- commitlint --edit "$1"' > .husky/commit-msg
```

Create `commitlint.config.js`:

```js
export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [2, "always", [
      "feat", "fix", "docs", "style", "refactor",
      "perf", "test", "build", "ci", "chore", "revert"
    ]],
    "subject-case": [2, "never", ["start-case", "pascal-case", "upper-case"]],
    "header-max-length": [2, "always", 100]
  }
};
```

---

## Monorepo Limitations

semantic-release does **not** natively support monorepos with multiple packages.

### Workaround: multi-semantic-release

```bash
npm install -D multi-semantic-release
```

This wrapper runs semantic-release for each package in a workspace. However:

- **Maintenance status is questionable** — sporadic updates, open issues pile up
- Inter-package dependency updates are fragile
- Each package needs its own `.releaserc.json`

**Recommendation:** For monorepos, use **changesets** or **release-please** instead.
They have first-class monorepo support.

---

## Common Issues

### 1. Wrong Version Bumps

**Problem:** All commits produce patch bumps regardless of type.

**Fix:** Verify commit format matches the configured preset exactly:
```
feat: add feature     ← correct (space after colon)
feat:add feature      ← wrong (no space)
Feat: add feature     ← wrong (capitalized type)
```

### 2. Plugin Order Matters

Plugins execute in array order. The changelog plugin must come **before** the git
plugin so the changelog file exists when git commits it:

```
✅ commit-analyzer → notes-generator → changelog → npm → git → github
❌ commit-analyzer → notes-generator → npm → git → changelog → github
```

### 3. Shallow Clone Breaks Analysis

**Problem:** CI only fetches the latest commit; semantic-release can't find previous tags.

**Fix:** Always use `fetch-depth: 0` in checkout:
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

### 4. Git Push Permission Denied

**Problem:** The git plugin can't push the changelog commit back to the repo.

**Fix:** Use `persist-credentials: false` and set up a token with write access:
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    persist-credentials: false
    token: ${{ secrets.GITHUB_TOKEN }}
```

### 5. Release Not Created on First Run

**Problem:** No previous git tag exists, so semantic-release doesn't know the baseline.

**Fix:** Create an initial tag manually:
```bash
git tag v1.0.0
git push origin v1.0.0
```

Or set `"tagFormat": "v${version}"` and ensure the initial version in package.json
matches the intended starting point.

### Greenfield Setup (No Existing Tags)

For a brand-new package that has never been published:

1. Set `"version": "0.0.0"` (or `"0.0.0-semantically-released"`) in `package.json`
2. **Do not** create any git tags — semantic-release will treat the first
   releasable commit as the initial release
3. Make sure your first commit is a `feat:` to get `1.0.0` (or `feat!:` for an
   explicit major), or a `fix:` to get `1.0.1` if you prefer starting at `1.0.x`
4. Run `npx semantic-release --dry-run` to verify the first release will be created
   correctly before enabling the CI workflow

If your steady-state auth mode is OIDC, the versioning setup above still needs a
token-based first publish before you switch the workflow to pure OIDC.

---

## Complete GitHub Actions Workflow (Pure OIDC)

```yaml
name: Release
on:
  push:
    branches: [main, beta]

permissions:
  contents: write
  issues: write
  pull-requests: write
  id-token: write

jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

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

      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx semantic-release
```

### With npm Provenance (OIDC)

```yaml
      - name: Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_CONFIG_PROVENANCE: true
        run: npx semantic-release
```

The `id-token: write` permission in the `permissions` block is required for OIDC
provenance to work. npm will generate and attach a signed SLSA provenance statement
to the published package.

For token auth, start from `references/workflows/token-workflows.md` and only add
`NPM_TOKEN` / `NODE_AUTH_TOKEN` in that token variant.

---

## When to Use semantic-release

**Best for:**
- Single-package repositories
- Teams that want zero manual release steps
- Projects where commit discipline is enforced
- Libraries with frequent, automated patch releases

**Avoid when:**
- You have a monorepo with multiple publishable packages
- Your team doesn't follow conventional commits consistently
- You need human review of version bumps before publishing
- You want to batch multiple changes into a single versioned release

---

## Quick Reference

```bash
# Install
npm install -D semantic-release @semantic-release/changelog @semantic-release/git

# Dry run
npx semantic-release --dry-run

# CI release (runs automatically via GitHub Actions)
npx semantic-release

# Verify CI environment
npx semantic-release --verify-conditions
```

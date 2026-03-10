# Version Bumping & Release Tools Comparison

## semantic-release

### Overview

Fully automated versioning and publishing. Analyzes conventional commit messages to determine the next version, generates changelogs, creates Git tags, and publishes to npm. Zero human intervention after merge.

**npm downloads**: ~10M/week | **GitHub stars**: ~20K | **Best for**: Single packages with disciplined commit messages

### How version bumping works

Parses commit messages using the Angular convention (default):

| Commit prefix | Version bump | Example |
|---|---|---|
| `fix:` | Patch (0.0.x) | `fix: resolve null pointer in parser` |
| `feat:` | Minor (0.x.0) | `feat: add CSV export option` |
| `feat!:` or `BREAKING CHANGE:` in footer | Major (x.0.0) | `feat!: redesign API response format` |
| `chore:`, `docs:`, `ci:`, `refactor:`, `test:` | No bump | `chore: update dev dependencies` |

### Configuration

**`.releaserc.json`** (or `release` key in `package.json`):

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    "@semantic-release/npm",
    ["@semantic-release/git", {
      "assets": ["package.json", "CHANGELOG.md"],
      "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }],
    "@semantic-release/github"
  ]
}
```

### Required packages

```bash
npm install -D semantic-release @semantic-release/changelog @semantic-release/git @semantic-release/github
```

### Changelog generation

Auto-generated from commit messages. Groups by type (Features, Bug Fixes, Breaking Changes). Written to `CHANGELOG.md` via `@semantic-release/changelog` plugin.

### Monorepo support

Not native. Requires third-party plugins:
- `@semantic-release/monorepo` — basic multi-package support
- `multi-semantic-release` — independent versioning per package

Community pain point: these plugins are poorly maintained (Reddit consensus).

### Strengths

- Fully automated — no human step between merge and publish
- Mature ecosystem with many plugins
- Forces commit discipline
- Built-in npm publish, GitHub release, Git tag

### Weaknesses

- Strict commit format requirement (misformatted commits = wrong version bump)
- Monorepo support via third-party plugins only
- Plugin-heavy (20+ dependencies)
- Direct push to main (no review gate on release)
- Overkill for simple projects

---

## changesets

### Overview

PR-based version management. Developers create "changeset" files describing their changes and the intended version bump. A GitHub Action aggregates changesets into a "Version Packages" PR. Merging that PR triggers the publish.

**npm downloads**: ~1M/week | **GitHub stars**: ~6K | **Best for**: Monorepos and teams wanting human review of version bumps

### How version bumping works

Manual — developers run `npx changeset` during development:

```
$ npx changeset
> Which packages would you like to include? @myorg/core
> What type of change is this? minor
> Summary: Added CSV export feature
```

This creates `.changeset/fuzzy-lions-dance.md`:
```markdown
---
"@myorg/core": minor
---

Added CSV export feature
```

When merged to `main`, the changesets action creates a PR that:
1. Bumps versions in all affected `package.json` files
2. Aggregates changeset descriptions into per-package `CHANGELOG.md`
3. Deletes consumed `.changeset/*.md` files

Merging that PR triggers publishing.

### Configuration

**`.changeset/config.json`** (created by `npx changeset init`):

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

Key options:
- `fixed`: Groups of packages that always share the same version (e.g., `[["@myorg/core", "@myorg/cli"]]`)
- `linked`: Packages whose versions are linked (bump together if any changes)
- `access`: Default publish access (`"public"` or `"restricted"`)
- `ignore`: Packages to exclude from version management

### Required packages

```bash
npm install -D @changesets/cli
npx changeset init
```

### Changelog generation

Aggregated from changeset file descriptions. Each package gets its own `CHANGELOG.md`. The summaries are written by developers, not auto-generated from commits.

### Monorepo support

Native and first-class. Designed for monorepos. Each changeset can bump multiple packages independently. Supports `fixed` and `linked` versioning strategies.

Used by: Vercel, SvelteKit, Turborepo, Radix UI, many design systems.

### Strengths

- Human review of every version bump (via PR)
- Native monorepo support
- Lightweight (core ~1MB)
- Flexible — works with any commit convention
- Changelog quality is high (human-written summaries)

### Weaknesses

- Extra step for developers (must run `npx changeset`)
- Forgetting to create a changeset blocks the release
- Two-PR workflow (feature PR + version PR) adds process overhead
- Semi-automated — requires human action at each change

---

## release-please

### Overview

Google's release tool. Creates "Release PR" automatically from conventional commits. The PR contains version bumps and changelogs. Merging the PR triggers the release and publish.

**npm downloads**: ~120K/week | **GitHub stars**: ~3K | **Best for**: OSS projects, multi-language monorepos

### How version bumping works

Parses conventional commits (same rules as semantic-release):

| Commit prefix | Version bump |
|---|---|
| `fix:` | Patch |
| `feat:` | Minor |
| `feat!:` or `BREAKING CHANGE:` | Major |

But unlike semantic-release, it doesn't publish immediately. Instead it opens/updates a Release PR that accumulates changes until merged.

### Configuration

**`.release-please-config.json`**:

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

For monorepos:
```json
{
  "packages": {
    "packages/core": { "release-type": "node" },
    "packages/cli": { "release-type": "node" },
    "packages/utils": { "release-type": "node" }
  }
}
```

**`.release-please-manifest.json`** (tracks current versions):
```json
{
  ".": "1.2.3"
}
```

### Required packages

None to install — uses a GitHub Action:
```yaml
- uses: googleapis/release-please-action@v4
```

### Changelog generation

Auto-generated from conventional commits. Groups by type. Written into the Release PR. Customizable via Handlebars templates.

### Monorepo support

Native. Supports multiple packages with independent versioning via `packages` config. Handles cross-package dependency updates. Scales to 1000+ packages (used at Google).

### Strengths

- PR-based review (like changesets) but auto-generated (like semantic-release)
- No npm packages to install in your project
- Multi-language support (Node, Python, Rust, Go, Java, etc.)
- Release PR accumulates changes — fewer releases, more deliberate
- Google-maintained

### Weaknesses

- Requires conventional commits (same discipline as semantic-release)
- Release PR can accumulate too many changes if not merged regularly
- Smaller ecosystem than semantic-release
- Publishing step must be added separately (not built-in)

---

## npm version (built-in)

### Overview

Built-in npm CLI command. Manual version bump with Git tag creation.

### How it works

```bash
npm version patch    # 1.0.0 -> 1.0.1
npm version minor    # 1.0.0 -> 1.1.0
npm version major    # 1.0.0 -> 2.0.0
npm version 1.2.3    # Set exact version
```

This updates `package.json`, creates a Git commit, and creates a Git tag.

### When to use

- Very simple projects with infrequent releases
- When the user wants full manual control
- Combined with a `on: release` GitHub Actions trigger (user creates GitHub Release manually, workflow publishes)

### Strengths

- Zero dependencies
- Full control
- No commit convention required

### Weaknesses

- Manual process — easy to forget steps
- No changelog generation
- No monorepo support
- No automation — just a version bump tool

---

## Decision tree

```
Is this a monorepo?
├── Yes
│   ├── Do you use conventional commits? → release-please
│   └── Do you prefer manual changeset descriptions? → changesets
└── No (single package)
    ├── Do you want full automation (no human step)? → semantic-release
    ├── Do you want a review PR before release? → release-please
    ├── Do you want to write changelog entries manually? → changesets
    └── Do you rarely release / want full control? → npm version + on:release trigger
```

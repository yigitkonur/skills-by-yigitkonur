---
name: publish-npm-package
description: Use skill if you are setting up automated npm publishing via GitHub Actions with OIDC or token auth and version bumping tools.
---

# npm Publish CI/CD

Automate npm package publishing via GitHub Actions with proper authentication, version bumping, changelog generation, and provenance.

## Trigger

Activate when the user wants to:
- Set up automated npm publishing via GitHub Actions
- Configure OIDC or token-based npm authentication in CI/CD
- Add automatic version bumping to their npm package
- Create a release workflow that publishes to npm on merge/tag/release
- Migrate from manual `npm login` + `npm publish` to automated CI/CD
- Add npm provenance to their published packages
- Choose between semantic-release, changesets, or release-please

## Decision sequence

### Step 1 — Choose authentication method

Read `references/auth-methods.md` for the full comparison. Ask the user which path fits:

| Method | When to use |
|---|---|
| **OIDC + Trusted Publishing** | Public packages on GitHub Actions. Most secure. No secrets to manage. Enables provenance. |
| **Granular Access Token** | Private packages, or need to publish from non-GitHub CI. Scoped to specific packages. Set expiry. |
| **Automation Token (Classic)** | Legacy fallback. Account-wide access. Avoid for new projects. |

Default recommendation: **OIDC** for public packages, **Granular Token** for private packages.

### Step 2 — Choose version bumping strategy

Read `references/version-tools.md` for the full comparison. Ask the user about their project shape:

| Project type | Recommended tool |
|---|---|
| Single package, conventional commits | **semantic-release** |
| Single package, manual control | **changesets** or **release-please** |
| Monorepo, team review workflow | **changesets** |
| Monorepo, conventional commits | **release-please** |
| Simple/small project, manual releases | **npm version** + GitHub Release trigger |

### Step 3 — Generate the workflow

Based on Steps 1-2, generate the appropriate files. Read the relevant reference for exact configuration:

| Combination | Reference |
|---|---|
| OIDC + semantic-release | `references/workflows.md` section "OIDC + semantic-release" |
| OIDC + changesets | `references/workflows.md` section "OIDC + changesets" |
| OIDC + release-please | `references/workflows.md` section "OIDC + release-please" |
| OIDC + manual (npm version) | `references/workflows.md` section "OIDC + manual trigger" |
| Token + semantic-release | `references/workflows.md` section "Token + semantic-release" |
| Token + changesets | `references/workflows.md` section "Token + changesets" |
| Token + release-please | `references/workflows.md` section "Token + release-please" |
| Token + manual (npm version) | `references/workflows.md` section "Token + manual trigger" |

### Step 4 — Configure package.json

Always ensure:

```json
{
  "name": "@scope/package-name",
  "version": "0.0.0",
  "repository": {
    "type": "git",
    "url": "https://github.com/OWNER/REPO.git"
  },
  "publishConfig": {
    "access": "public",
    "provenance": true
  }
}
```

- `repository` field **must** match the actual GitHub repo (case-sensitive) for provenance to work
- `version` is managed by the chosen tool (semantic-release sets it to `0.0.0-development`, changesets and release-please bump it in PRs)
- Add `"files"` array to control what gets published
- Add `"engines"` if Node version matters

### Step 5 — Set up commit conventions (if using semantic-release or release-please)

Install and configure commitlint + husky:

```bash
npm install -D @commitlint/cli @commitlint/config-conventional husky
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
```

Create `commitlint.config.js`:
```js
export default { extends: ['@commitlint/config-conventional'] };
```

Commit types that affect version:
- `fix:` -> patch bump
- `feat:` -> minor bump
- `feat!:` or `BREAKING CHANGE:` footer -> major bump
- `chore:`, `docs:`, `ci:`, `refactor:` -> no version bump (but included in changelog)

### Step 6 — Verify the setup

Checklist before first publish:
- [ ] `npm pack --dry-run` shows only intended files
- [ ] `package.json` has correct `name`, `version`, `repository`, `publishConfig`
- [ ] GitHub Actions workflow file exists at `.github/workflows/release.yml`
- [ ] For OIDC: workflow has `permissions: { id-token: write, contents: read }`
- [ ] For token: `NPM_TOKEN` secret is set in repo settings
- [ ] For semantic-release: `.releaserc.json` or `release` key in `package.json` exists
- [ ] For changesets: `.changeset/config.json` exists (run `npx changeset init`)
- [ ] For release-please: `.release-please-config.json` exists
- [ ] Branch protection is enabled on `main` (prevents unauthorized publishes)
- [ ] Test the workflow with a dry run before actual publish

## Guardrails

- Never commit `.npmrc` files containing tokens to version control
- Never use `npm login` in CI — use `NODE_AUTH_TOKEN` env var or OIDC
- Never publish without running tests first in the same workflow
- Always pin GitHub Actions to full SHA (not `@v4`) in production workflows for supply-chain safety
- Always use `npm ci` (not `npm install`) in CI for reproducible builds
- Always set `concurrency` groups in workflows to prevent parallel publish race conditions
- Prefer `on: release` or `on: push to main` triggers — avoid `on: push to tags` (can't require PR review)

## Reference files

| File | When to read |
|---|---|
| `references/auth-methods.md` | When choosing between OIDC, granular token, or automation token |
| `references/version-tools.md` | When choosing between semantic-release, changesets, release-please, or npm version |
| `references/workflows.md` | When generating the actual GitHub Actions YAML and config files |

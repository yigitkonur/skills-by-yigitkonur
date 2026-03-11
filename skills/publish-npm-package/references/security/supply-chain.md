# npm Supply Chain Security Reference

Guide to securing every link in the npm publishing supply chain—from source commit to published package.

> **⚠️ Steering:** Supply-chain hardening applies to **ALL** publishing scenarios—not
> just fully-automated pipelines. Whether you use OIDC or token auth, semantic-release
> or manual `npm version`, provenance attestation and action pinning protect your
> users from supply-chain attacks. Apply these practices from day one, including
> your very first publish.

---

## 1. npm Provenance Attestation

**Provenance** is a SLSA (Supply-chain Levels for Software Artifacts) attestation that cryptographically links a published package to its source repository, exact commit SHA, CI/CD workflow, build runner, and lockfile hash. Consumers get verifiable proof the package was built from claimed source without manual intervention.

npm provenance achieves **SLSA Build Level 2**: the build ran on a hosted, verified platform (GitHub Actions), the workflow is version-controlled, and the provenance is non-forgeable without compromising the build platform itself.

### How Sigstore Integration Works

```
1. `npm publish --provenance` detects GitHub OIDC environment
   └─ Reads ACTIONS_ID_TOKEN_REQUEST_URL + ACTIONS_ID_TOKEN_REQUEST_TOKEN
2. Exchanges OIDC JWT for a Fulcio short-lived signing certificate
   └─ Certificate embeds CI identity — no long-lived keys needed
3. Signs an in-toto SLSA provenance bundle
   └─ Subject: package tarball hash; Predicate: build metadata
4. Logs the signing event to Rekor transparency log
   └─ Creates an immutable, publicly auditable record
```

### Attestation Contents

Key fields in the provenance predicate: **source repo**, **commit SHA**, **workflow path** (`.github/workflows/publish.yml`), **runner OS**, and **lockfile integrity hash**.

### Consumer Verification

On **npmjs.com**, packages with provenance show a green checkmark linking to the exact source commit and workflow. Via CLI:

```bash
npm audit signatures
# audited 347 packages in 2s — 347 have verified registry signatures
```

### Configuration Options

```bash
npm publish --provenance                          # CLI flag
echo "provenance=true" >> .npmrc                  # .npmrc
# package.json: { "publishConfig": { "provenance": true } }
NPM_CONFIG_PROVENANCE=true npm publish            # env var
```

> Provenance only works in supported CI environments (GitHub Actions, GitLab CI)—not local machines.

---

## 2. GitHub Actions Supply Chain Security

### Pin Actions to Full SHA

Tags like `@v4` are mutable—a compromised maintainer account can move the tag to malicious code:

```yaml
# ❌ Bad — tag can be moved to malicious code
- uses: actions/checkout@v4

# ✅ Good — immutable reference
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

Find SHAs with `git ls-remote --tags https://github.com/actions/checkout.git refs/tags/v4.1.1`. Use Dependabot for GitHub Actions to get automated update PRs.

### How to Find and Pin SHAs

**Step 1 — Find the SHA for a specific tag:**

```bash
# Get the SHA for a specific version tag
git ls-remote https://github.com/actions/checkout | grep 'refs/tags/v4$'
# Output: b4ffde65f46336ab88eb53be808477a3936bae11  refs/tags/v4

# For an exact patch version
git ls-remote https://github.com/actions/setup-node | grep 'refs/tags/v4.2.0$'
```

**Step 2 — Use the format `owner/action@SHA # vX.Y.Z`:**

```yaml
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
- uses: actions/setup-node@1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a # v4.2.0
- uses: changesets/action@c8bada60c408975afd1a20b3db81d6eee6789571 # v1.4.9
```

> The trailing comment (`# v4.1.1`) is critical for human readability and for
> Dependabot/Renovate to propose SHA updates when new versions are released.

**Step 3 — Automate pinning with tools:**

```bash
# pin-github-action — bulk-pin all actions in a workflow file
npx pin-github-action .github/workflows/publish.yml

# Or use Renovate with pinGitHubActionDigests enabled:
# renovate.json: { "extends": ["helpers:pinGitHubActionDigests"] }
```

**Step 4 — Keep pinned SHAs updated:**

Configure Dependabot for GitHub Actions to get automated update PRs:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

### Dependency Review in PRs

```yaml
name: Dependency Review
on: pull_request
permissions:
  contents: read
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - uses: actions/dependency-review-action@4901385134134e04cec5fbe5ddfe3b2c5bd5d976 # v4.5.0
        with:
          fail-on-severity: high
```

### GITHUB_TOKEN — Least Privilege

```yaml
permissions: {}  # restrict defaults for entire workflow
jobs:
  publish:
    permissions:
      contents: read    # checkout code
      id-token: write   # OIDC for provenance
```

### Workflow Security

- **Never** use `pull_request_target` to run untrusted fork code (it gets write permissions)
- **Never** interpolate untrusted input in `run:` blocks — use env vars instead:

```yaml
# ❌ Command injection risk
run: echo "${{ github.event.pull_request.title }}"
# ✅ Safe
env:
  PR_TITLE: ${{ github.event.pull_request.title }}
run: echo "$PR_TITLE"
```

- Use concurrency groups to prevent parallel publishes:

```yaml
concurrency:
  group: npm-publish
  cancel-in-progress: false  # never cancel an in-progress publish
```

---

## 3. npm Token Security

### Never Commit Tokens

Add `.npmrc` to `.gitignore`. Check history: `git log --all -p -- .npmrc`. Use `NODE_AUTH_TOKEN` env var instead:

```yaml
- uses: actions/setup-node@1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a # v4.2.0
  with:
    node-version: 20
    registry-url: https://registry.npmjs.org
# Creates .npmrc with: //registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}
- run: npm publish --provenance
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Granular Token Scopes

| Token Type       | Use Case     | Scope                         |
| ---------------- | ------------ | ----------------------------- |
| Granular Publish | CI publish   | Read/write, specific packages |
| Automation       | CI publish   | Publish, bypasses 2FA         |
| Granular Read    | CI install   | Read-only, specific packages  |

Create at: `npmjs.com/settings/~/tokens/granular-access-tokens/new`

### Token Rotation (90-day recommended)

```bash
# 1. Generate new token on npmjs.com (keep old token active)
# 2. Update GitHub Actions secret
gh secret set NPM_TOKEN --body "npm_NEW_TOKEN_VALUE"
# 3. Trigger a test publish or dry-run to verify
gh workflow run publish.yml
# 4. After verification succeeds, revoke OLD token on npmjs.com
```

Monitor usage at `npmjs.com/settings/~/tokens` and enable publish email notifications.

---

## 4. Lockfile Security

### Commit `package-lock.json` and Use `npm ci`

```yaml
# ❌ npm install may update lockfile, introducing drift
- run: npm install

# ✅ npm ci enforces exact lockfile, fails if out of sync, is faster
- run: npm ci
```

`npm ci` deletes `node_modules/`, installs from scratch, and fails if `package-lock.json` is missing or mismatched with `package.json`—guaranteeing reproducible builds.

### Lockfile v3

npm v7+ uses lockfile v3 with full dependency tree, `resolved` URLs, and `integrity` hashes. Verify: `node -e "console.log(require('./package-lock.json').lockfileVersion)"`.

### Audit in CI

```yaml
- run: npm ci
- run: npm audit --audit-level=high  # fails on high/critical
```

**Caution:** `npm audit fix` is safe for semver-compatible patches. `npm audit fix --force` may introduce breaking major-version upgrades—never run it unattended in CI.

---

## 5. Dependency Auditing

### Built-in Scanning

```bash
npm audit                        # full report
npm audit --audit-level=high     # fail on high+ only
npm audit --omit=dev             # production deps only
npm audit signatures             # verify provenance + registry signatures
```

### Automated Updates

**Dependabot:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

**Renovate** (more flexible):
```json
{
  "extends": ["config:recommended"],
  "packageRules": [{ "matchUpdateTypes": ["patch"], "automerge": true }]
}
```

### Deeper Analysis

[Socket.dev](https://socket.dev) goes beyond known CVEs—detects install scripts running arbitrary code, typosquat packages, unexpected network/filesystem access, and maintainer account takeovers.

---

## 6. 2FA and Account Security

```bash
npm profile enable-2fa auth-and-writes   # require 2FA for login AND publishing
```

Always use `auth-and-writes`, not `auth-only`. Org admins can enforce 2FA for all members at `npmjs.com/settings/<org>/members`.

**Automation tokens** bypass the interactive 2FA prompt while still requiring 2FA on the account. **Granular tokens** add further control: scope to specific packages, set IP allowlists, and set expiration dates.

---

## 7. Publishing Security Checklist

### Repository
- [ ] No secrets, tokens, or credentials in the repository
- [ ] `.npmrc` and `.env` are in `.gitignore`
- [ ] `npm pack --dry-run` shows no sensitive files

### Build Pipeline
- [ ] Provenance enabled (`--provenance`)
- [ ] All actions pinned to full commit SHA
- [ ] `npm ci` used (not `npm install`)
- [ ] `npm audit --audit-level=high` passes
- [ ] `permissions: {}` default with explicit per-job grants
- [ ] Concurrency groups prevent parallel publishes

### Access Control
- [ ] Token has minimum required scopes with expiration date
- [ ] 2FA enabled (`auth-and-writes`)
- [ ] Branch protection + required reviews on release branch

### Monitoring
- [ ] Dependabot configured for npm + GitHub Actions
- [ ] Publish email notifications enabled
- [ ] Token rotation scheduled (every 90 days)

---

## 8. First-Publish Security Considerations

The first publish of a package has unique security implications:

### Bootstrap Token Security

When bootstrapping a new package (required before OIDC can work), use the
most restricted token possible:

```bash
# Create a granular token scoped to ONLY the new package name
# Set a short expiration (e.g., 1 day) — you only need it once
# After bootstrap, switch to OIDC and revoke the bootstrap token
```

### Name Squatting Prevention

Publish your package name early, even as `0.0.1`, to prevent typosquatting:

```bash
# Reserve the package name with a minimal publish
npm publish --access public
# Then deprecate if not ready for consumers
npm deprecate @scope/pkg@0.0.1 "Initial placeholder — real release coming soon"
```

### First-Publish Checklist

- [ ] Package name is not confusingly similar to popular packages
- [ ] `repository.url` in `package.json` exactly matches your GitHub repo (case-sensitive)
- [ ] Bootstrap token has minimal scope and short expiration
- [ ] Provenance is enabled from the very first automated publish
- [ ] 2FA is enabled on the npm account (`auth-and-writes`)
- [ ] After bootstrap, revoke the bootstrap token immediately

---

## 9. Incident Response

### Token Leaked

```bash
# 1. IMMEDIATELY revoke token at npmjs.com/settings/~/tokens
# 2. Generate new token + update CI secrets
gh secret set NPM_TOKEN --body "npm_NEW_TOKEN_VALUE"
# 3. Audit recent publishes
npm view <package> versions --json
# 4. Check for unauthorized collaborators
npm access ls-collaborators <package>
# Note: GitHub secret scanning auto-revokes detected npm tokens
```

### Malicious Version Published

```bash
# Within 72 hours — unpublish the specific version
npm unpublish <package>@<version>
# After 72 hours — contact npm support at npmjs.com/support

# Publish a patched version immediately
npm version patch && npm publish --provenance

# If unpublish fails, deprecate with a security warning
npm deprecate <package>@<version> \
  "SECURITY: compromised version. Upgrade immediately."
```

**Notify consumers:** post a GitHub Security Advisory, file a CVE if appropriate, contact downstream maintainers.

### npm unpublish Limitations

- **72-hour window** after publishing
- Cannot unpublish if other packages depend on the version
- The same version number **cannot be reused** after unpublish—you must bump

### npm deprecate Alternative

```bash
npm deprecate <package>@"<1.2.4" "Versions before 1.2.4 have a security issue"
# Users see: npm warn deprecated <package>@1.2.3: ...
```

---

## Quick Reference: Complete Secure Workflow

```yaml
name: Publish
on:
  release:
    types: [published]
permissions: {}
concurrency:
  group: npm-publish
  cancel-in-progress: false
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - uses: actions/setup-node@1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a # v4.2.0
        with:
          node-version: 20
          registry-url: https://registry.npmjs.org
      - run: npm ci
      - run: npm audit --audit-level=high
      - run: npm test
      - run: npm publish --provenance
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

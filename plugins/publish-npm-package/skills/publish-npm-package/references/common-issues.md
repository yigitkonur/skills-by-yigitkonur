# Common Issues — npm Publishing via GitHub Actions

Troubleshooting guide covering trusted publishing, provenance, token auth, version bumping,
package publishing, and GitHub Actions workflow failures.

## Contents

- [First publish failures](#0-first-publish-failures)
- [Trusted publishing and provenance failures](#1-trusted-publishing--provenance-failures)
- [Token authentication failures](#2-token-authentication-failures)
- [Version bumping issues](#3-version-bumping-issues)
- [Package publishing failures](#4-package-publishing-failures)
- [GitHub Actions workflow issues](#5-github-actions-workflow-issues)
- [Debugging workflow](#6-debugging-workflow)
- [Recovery procedures](#7-recovery-procedures)
- [Quick reference](#quick-reference-error--fix)

> **Guardrail:** For a package's first publish, start with "First Publish Failures". Trusted-publishing errors and token errors often have different root causes on first publish than on later publishes.

## 0. First Publish Failures

First-time publishing has unique failure modes that don't apply to subsequent
publishes. These are the most common traps:

### Trusted Publishing First Publish Fails with 404

**Symptom:** `npm ERR! 404 Not Found - PUT https://registry.npmjs.org/@scope%2fpkg`

**Cause:** npm's OIDC trusted publishing requires the package to already exist
on the registry. On first publish, it doesn't exist yet, so the OIDC handshake
has no package to authorize against.

**Fix — bootstrap with a token:**

```bash
# 1. Create a granular access token on npmjs.com with publish scope
# 2. Publish the initial version locally or via CI with token auth:
npm publish --access public
# 3. After the package exists, link trusted publishing
```

> See also: [auth/oidc-trusted-publishing.md](auth/oidc-trusted-publishing.md)
> and [auth/granular-tokens.md](auth/granular-tokens.md) for the bootstrap pattern.

### E403 on Scoped Packages

**Symptom:** `npm ERR! 403 Forbidden - PUT https://registry.npmjs.org/@scope%2fpkg`

**Cause:** Scoped packages (`@scope/name`) default to `restricted` (paid npm
Org feature). Free accounts cannot publish restricted packages.

**Fix:**

```bash
npm publish --access public
```

Or set it permanently in `package.json`:

```json
{ "publishConfig": { "access": "public" } }
```

> See also: [package-config.md](package-config.md) for
> full `publishConfig` guidance.

### ERR_SOCKET_TIMEOUT on First Publish with Explicit Provenance

**Symptom:** `ERR_SOCKET_TIMEOUT` when contacting Fulcio for signing.

**Cause:** Missing `id-token: write` permission in a workflow that is trying to generate provenance. Without it, GitHub cannot mint the OIDC token used for signing.

**Fix:** Add permissions at the **job** level (not just workflow level):

```yaml
jobs:
  publish:
    permissions:
      contents: read
      id-token: write
```

### Quick Diagnosis Flowchart

```
First publish failing?
├─ 404 on PUT?
│  └─ Package doesn't exist yet → bootstrap with token auth first
├─ 403 Forbidden?
│  ├─ Scoped package? → add --access public or publishConfig.access
│  └─ Token/OIDC? → check token scopes or trusted publishing config
├─ ERR_SOCKET_TIMEOUT?
│  └─ Explicit provenance? add id-token: write permission
├─ ENEEDAUTH?
│  ├─ Trusted publishing? → verify npm trusted-publisher settings and setup-node registry-url
│  └─ Token? → verify NPM_TOKEN secret is set and not empty
└─ 401 Unauthorized?
   ├─ Token for wrong registry? → create token on npmjs.com
   └─ OIDC audience mismatch? → check runner environment
```

> **Cross-references:**
> - Auth setup: [auth/oidc-trusted-publishing.md](auth/oidc-trusted-publishing.md) and [auth/granular-tokens.md](auth/granular-tokens.md)
> - Version tool config: [versioning/semantic-release.md](versioning/semantic-release.md), [versioning/changesets.md](versioning/changesets.md), and [versioning/release-please.md](versioning/release-please.md)
> - Package config: [package-config.md](package-config.md)
> - Supply chain security: [supply-chain.md](supply-chain.md)

---

## 1. Trusted Publishing / Provenance Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `ENEEDAUTH` with trusted publishing | npm trusted-publisher settings do not match workflow, or `id-token: write` is missing | Match org/repo/workflow filename exactly and add `id-token: write` |
| `ERR_SOCKET_TIMEOUT` on Fulcio | Explicit provenance without `id-token: write` | Add `permissions: { id-token: write }` to the job |
| `401 Unauthorized` from Sigstore | Wrong OIDC audience or misconfigured runner | Verify supported cloud-hosted runner and OIDC request vars |
| `403 Forbidden` on npm publish | Branch/ref mismatch in npm `trustOrigin` | Publish only from the branch configured in npm trusted publishing settings |
| Provenance verification fails | `repository` URL in `package.json` doesn't match repo | Fix `repository` — **case-sensitive**, use `https://github.com/OWNER/REPO.git` |
| Empty `materials` in provenance | Missing `contents: read` permission | Add `contents: read` alongside `id-token: write` |
| No provenance badge | private repo/package, CircleCI trusted publishing, or provenance disabled | Use public GitHub/GitLab repo and package, or accept no provenance |
| `npm whoami` fails | trusted publishing is publish-only | Do not use `npm whoami` for trusted-publishing auth checks |

### Correct Pure Trusted-Publishing Block

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: 'https://registry.npmjs.org'
          package-manager-cache: false
      - run: npm ci
      - run: npm publish --access public
```

### Debugging Commands

**Verbose publish for pure trusted publishing:**

```bash
npm publish --access public --loglevel=verbose 2>&1 | tee publish.log
```

**Inspect OIDC token claims inside a workflow:**

```yaml
- name: Debug OIDC token
  run: |
    OIDC_TOKEN=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=npm" | jq -r '.value')
    echo "$OIDC_TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .
```

Key claims to verify: `sub` = `repo:OWNER/REPO:ref:refs/heads/main`,
`aud` = `npm`, `runner_environment` = `github-hosted`.

**Check Rekor transparency log:**

```bash
rekor-cli search --rekor_server https://rekor.sigstore.dev \
  --email "$(git config user.email)"
```

**Verify published provenance:** `npm audit signatures`

---

## 2. Token Authentication Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `EOTP` with automation/granular token (local) | npm is NOT using your token — it's using the interactive `npm login` session which has 2FA | Pass token via CLI flag: `--//registry.npmjs.org/:_authToken=TOKEN`. The `NODE_AUTH_TOKEN` env var only works with setup-node's `.npmrc`. |
| `EOTP` with automation/granular token (CI) | `actions/setup-node` missing `registry-url`, so `.npmrc` with `${NODE_AUTH_TOKEN}` was never created | Add `registry-url: 'https://registry.npmjs.org'` to setup-node config |
| `ENEEDAUTH` | `NPM_TOKEN` secret not set, empty, or misspelled | Verify secret in repo **Settings → Secrets → Actions** |
| `403 Forbidden` | Token lacks write access to the package | Create a **granular access token** scoped to the package |
| `403 Forbidden` | Token expired | Rotate token, update GitHub Secret, re-run workflow |
| `E401` | Token created for wrong registry (e.g., GitHub Packages) | Create token on **npmjs.com** → Access Tokens |
| Publish succeeds but wrong registry | `registry-url` missing in `actions/setup-node` | Always set `registry-url: 'https://registry.npmjs.org'` |

### EOTP Diagnosis Flowchart

```
Getting EOTP error?
├─ Local publish?
│  ├─ Run: npm whoami
│  │  └─ Shows your username? → npm is using login session, not the token
│  │     └─ Fix: npm publish --//registry.npmjs.org/:_authToken="${NPM_TOKEN}"
│  ├─ Check: grep NPM_TOKEN ~/.zshrc ~/.bashrc
│  │  └─ Token exists in shell profile? → Use it with the CLI flag above
│  └─ Check: Is the token type "Automation" or "Granular" with "Bypass 2FA"?
│     └─ It's a "Publish" token? → ❌ Publish tokens CANNOT bypass 2FA. Create a granular or automation token.
├─ CI publish?
│  ├─ Does setup-node have registry-url? → If no, add it
│  └─ Is NODE_AUTH_TOKEN set in the publish step? → If no, add env block
└─ Neither? → Token might be expired or revoked. Check npmjs.com → Access Tokens.
```

### Token Setup

```yaml
- uses: actions/setup-node@v6
  with:
    node-version: '24'
    registry-url: 'https://registry.npmjs.org'
    package-manager-cache: false
- run: npm publish --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Verify auth before publishing:**

```yaml
- name: Verify npm auth
  run: npm whoami --registry https://registry.npmjs.org
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## 3. Version Bumping Issues

### semantic-release

| Issue | Cause | Fix |
|-------|-------|-----|
| No version bump after merge | No conventional commit prefixes | Use `fix:`, `feat:`, `perf:` — plain messages are ignored |
| Wrong version bump | Commit parsing mismatch | Check `.releaserc.json` `commit-analyzer` preset/rules |
| `ENOTINHISTORY` | Shallow clone | Set `fetch-depth: 0` in `actions/checkout` |
| `EINVALIDNPMTOKEN` with trusted publishing | semantic-release expects `NPM_TOKEN` | Upgrade `@semantic-release/npm` to a version that supports trusted publishing |
| Release runs but no publish | `[skip ci]` in version-bump commit | Modify git plugin's `message` template |

```yaml
- uses: actions/checkout@v6
  with:
    fetch-depth: 0
    persist-credentials: false
```

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/npm",
    ["@semantic-release/github", { "successComment": false }]
  ]
}
```

### changesets

| Issue | Cause | Fix |
|-------|-------|-----|
| No "Version Packages" PR | No `.changeset/*.md` files merged | Developers must run `npx changeset` and commit the file |
| Version PR has conflicts | Multiple competing changesets | Resolve conflicts in the Version Packages PR |
| `changeset publish` fails | Missing npm auth | Set `NODE_AUTH_TOKEN` for token auth or configure trusted publishing |
| Empty changelog | Changeset files deleted before version bump | Keep `.changeset/*.md` until `changeset version` runs |

```yaml
- uses: changesets/action@v1
  with:
    publish: npx changeset publish
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### release-please

| Issue | Cause | Fix |
|-------|-------|-----|
| No Release PR created | No conventional commits since last release | Push a `fix:` or `feat:` commit |
| Release PR not updating | Wrong `release-type` or branch config | Verify `release-type: node` in `release-please-config.json` |
| Manifest out of sync | Manual version change without manifest update | Sync `.release-please-manifest.json` with `package.json` |
| Publish job doesn't run | `release_created` output not passed between jobs | Check `${{ steps.release.outputs.release_created }}` step id |

```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: node
  publish:
    needs: release
    if: ${{ needs.release.outputs.release_created == 'true' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: 'https://registry.npmjs.org'
          package-manager-cache: false
      - run: npm ci
      - run: npm publish --access public
```

---

## 4. Package Publishing Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `EPUBLISHCONFLICT` | Version already exists on registry | Bump version — npm forbids republishing same version |
| `E403` on scoped package | Default access is `restricted` | Add `--access public` or set `publishConfig.access` |
| Package too large | Unnecessary files included | Use `files` field; run `npm pack --dry-run` to inspect |
| Missing files in package | `files` allowlist too restrictive | Add missing paths; verify with `npm pack --dry-run` |
| `ERR_MODULE_NOT_FOUND` for consumers | Wrong `exports` field | Test: `node -e "require('pkg')"` and `node -e "import('pkg')"` |
| TypeScript types not found | Missing `types` in exports | Add `"types"` condition to each path in `exports` map |

### publishConfig & exports Example

```json
{
  "name": "@scope/my-package",
  "publishConfig": {
    "access": "public",
    "registry": "https://registry.npmjs.org"
  },
  "files": ["dist", "LICENSE", "README.md"],
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    }
  }
}
```

### Pre-Publish Validation

```bash
npm pack --dry-run 2>&1 | head -40   # Check contents
npm pack --dry-run 2>&1 | tail -1    # Check packed size
npm publish --dry-run                 # Simulate full publish
```

---

## 5. GitHub Actions Workflow Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Workflow doesn't trigger | Wrong event/branch config | Check `on:` trigger matches your branch |
| Parallel publishes race condition | No concurrency group | Add `concurrency: { group: "release-${{ github.ref }}", cancel-in-progress: false }` |
| `GITHUB_TOKEN` insufficient permissions | Default token is read-only | Set explicit `permissions` at job level |
| Release cache drift | Release workflow uses dependency cache | Set `package-manager-cache: false` in release jobs; cache only test jobs |

```yaml
concurrency:
  group: publish-${{ github.ref }}
  cancel-in-progress: false

# ...
- uses: actions/setup-node@v6
  with:
    node-version: '24'
    registry-url: 'https://registry.npmjs.org'
    package-manager-cache: false
```

---

## 6. Debugging Workflow

Follow this sequence when a publish fails:

**Step 1 — Read workflow logs.** Open the failed run in GitHub Actions; expand
the `npm publish` step for the actual error.

**Step 2 — Enable verbose logging.** Use the command for the selected auth lane.

```yaml
- run: npm publish --access public --loglevel=verbose
```

For token+provenance:

```yaml
- run: npm publish --provenance --access public --loglevel=verbose
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Or re-run with **Enable debug logging** checked (sets `ACTIONS_RUNNER_DEBUG`
and `ACTIONS_STEP_DEBUG` to `true`).

**Step 3 — Verify token authentication when token auth is intended.**

```yaml
- run: |
    npm whoami --registry https://registry.npmjs.org
    cat ~/.npmrc | grep -v '_authToken' | head -5
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Step 4 — Check package contents.**

```bash
npm pack --dry-run
```

Look for: missing `dist/`, oversized package, unexpected files.

**Step 5 — Verify version availability.**

```bash
npm view <package-name> versions --json | jq '.[-3:]'
```

If the version exists, you'll get `EPUBLISHCONFLICT`.

**Step 6 — Test locally.**

```bash
npm publish --dry-run
```

**Step 7 — Check npm status** at [status.npmjs.org](https://status.npmjs.org).
Outages cause transient `ERR_SOCKET_TIMEOUT`, `5xx`, and `ECONNRESET` errors.

---

## 7. Recovery Procedures

### Published the Wrong Version

**Within 72 hours:**

```bash
npm unpublish @scope/pkg@1.2.3
```

**After 72 hours:**

```bash
npm deprecate @scope/pkg@1.2.3 "Critical bug — use >=1.2.4"
```

Then publish a patched version immediately.

### Token Leaked

1. Revoke the token immediately on [npmjs.com](https://www.npmjs.com/settings/~/tokens)
2. Generate a new granular access token
3. Update the GitHub Secret (`NPM_TOKEN`)
4. Audit recent publishes:

```bash
npm access ls-collaborators @scope/pkg
npm audit signatures
```

5. If a malicious version was published, `npm unpublish` within 72h or contact npm support

### Broken Release

**Patch forward (preferred):**

```bash
git commit --allow-empty -m "fix: revert broken change from v1.2.3"
git push origin main
```

**Manual hotfix:**

```bash
git checkout -b hotfix/1.2.4
npm version patch
npm publish --access public
git push origin hotfix/1.2.4 --tags
```

Add `--provenance` only when using the token+provenance CI lane.

### Stuck Release PR

**release-please:**

```bash
gh pr close <PR_NUMBER>
git commit --allow-empty -m "fix: trigger new release PR"
git push origin main
```

**changesets:**

```bash
npx changeset version
git add . && git commit -m "Version Packages (manual)"
git push origin main
npx changeset publish
```

### Accidental Major Version Bump

```bash
npm deprecate @scope/pkg@2.0.0 "Accidental major bump — use @scope/pkg@^1.3.0"
npm version 1.3.0 --allow-same-version
npm publish --access public
```

---

## Quick Reference: Error → Fix

| Error Message | Likely Fix |
|---------------|------------|
| `EOTP` (local) | npm is using interactive login, not your token. Use `--//registry.npmjs.org/:_authToken=TOKEN` CLI flag |
| `EOTP` (CI) | Missing `registry-url` in setup-node, so `NODE_AUTH_TOKEN` is not wired. Or token is a classic "Publish" type (not automation/granular) |
| `ENEEDAUTH` | Set `NODE_AUTH_TOKEN` or add `registry-url` to setup-node |
| `E401` | Regenerate npm token; verify it's for npmjs.com |
| `E403` | Add `--access public` or check token scopes |
| `EPUBLISHCONFLICT` | Bump version — can't overwrite existing |
| `ERR_SOCKET_TIMEOUT` | Check `id-token: write` permission; check npm status |
| `ENOTINHISTORY` | Set `fetch-depth: 0` in actions/checkout |
| `EINVALIDNPMTOKEN` | Upgrade `@semantic-release/npm` to v11+ for OIDC |
| `ENOWORKSPACES` | Remove `--workspaces` flag or verify workspace config |

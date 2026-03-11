# Common Issues — npm Publishing via GitHub Actions

Troubleshooting guide covering OIDC/provenance, token auth, version bumping,
package publishing, and GitHub Actions workflow failures.

> **⚠️ Steering:** First-publish failures are the #1 source of CI frustration.
> If this is your package's **very first publish**, start with the "First Publish
> Failures" section below — most OIDC/token errors have a different root cause
> on first publish vs subsequent publishes.

---

## 0. First Publish Failures

First-time publishing has unique failure modes that don't apply to subsequent
publishes. These are the most common traps:

### OIDC First Publish Fails with 404

**Symptom:** `npm ERR! 404 Not Found - PUT https://registry.npmjs.org/@scope%2fpkg`

**Cause:** npm's OIDC trusted publishing requires the package to already exist
on the registry. On first publish, it doesn't exist yet, so the OIDC handshake
has no package to authorize against.

**Fix — bootstrap with a token:**

```bash
# 1. Create a granular access token on npmjs.com with publish scope
# 2. Publish the initial version locally or via CI with token auth:
npm publish --access public
# 3. After the package exists, switch your workflow to OIDC
```

> See also: [auth/token-vs-oidc.md](../auth/token-vs-oidc.md) for full OIDC
> setup and the bootstrap pattern.

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

> See also: [packaging/package-config.md](../packaging/package-config.md) for
> full `publishConfig` guidance.

### ERR_SOCKET_TIMEOUT on First Publish with OIDC

**Symptom:** `ERR_SOCKET_TIMEOUT` when contacting Fulcio for signing.

**Cause:** Missing `id-token: write` permission in the workflow. Without it,
GitHub cannot mint the OIDC token, and the Fulcio request hangs until timeout.

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
│  └─ Missing id-token: write permission → add to job permissions
├─ ENEEDAUTH?
│  ├─ OIDC? → add registry-url to setup-node
│  └─ Token? → verify NPM_TOKEN secret is set and not empty
└─ 401 Unauthorized?
   ├─ Token for wrong registry? → create token on npmjs.com
   └─ OIDC audience mismatch? → check runner environment
```

> **Cross-references:**
> - Auth setup: [auth/token-vs-oidc.md](../auth/token-vs-oidc.md)
> - Version tool config: [versioning/tool-comparison.md](../versioning/tool-comparison.md)
> - Package config: [packaging/package-config.md](../packaging/package-config.md)
> - Supply chain security: [security/supply-chain.md](../security/supply-chain.md)

---

## 1. OIDC / Provenance Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `ERR_SOCKET_TIMEOUT` on Fulcio | Missing `id-token: write` permission | Add `permissions: { id-token: write }` to the **job** (not just workflow) |
| `401 Unauthorized` from Sigstore | Wrong OIDC audience or misconfigured runner | Verify GitHub-hosted runners; check `ACTIONS_ID_TOKEN_REQUEST_URL` is set |
| `403 Forbidden` on npm publish | Branch/ref mismatch in npm `trustOrigin` | Publish only from the branch configured in npm trusted publishing settings |
| Provenance verification fails | `repository` URL in `package.json` doesn't match repo | Fix `repository` — **case-sensitive**, use `https://github.com/OWNER/REPO.git` |
| Empty `materials` in provenance | Missing `contents: read` permission | Add `contents: read` alongside `id-token: write` |
| `ENEEDAUTH` with OIDC | `registry-url` not set in `actions/setup-node` | Add `registry-url: 'https://registry.npmjs.org'` |
| Provenance works but publish fails | Self-hosted runner can't mint OIDC tokens | Use **GitHub-hosted** runners for the publish job |

### Correct Permissions Block

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm publish --provenance --access public
```

### Debugging Commands

**Verbose publish:**

```bash
npm publish --provenance --access public --loglevel=verbose 2>&1 | tee publish.log
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
| `ENEEDAUTH` | `NPM_TOKEN` secret not set, empty, or misspelled | Verify secret in repo **Settings → Secrets → Actions** |
| `403 Forbidden` | Token lacks write access to the package | Create a **granular access token** scoped to the package |
| `403 Forbidden` | Token expired | Rotate token, update GitHub Secret, re-run workflow |
| `E401` | Token created for wrong registry (e.g., GitHub Packages) | Create token on **npmjs.com** → Access Tokens |
| Publish succeeds but wrong registry | `registry-url` missing in `actions/setup-node` | Always set `registry-url: 'https://registry.npmjs.org'` |

### Token Setup

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    registry-url: 'https://registry.npmjs.org'
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
| `EINVALIDNPMTOKEN` with OIDC | semantic-release expects `NPM_TOKEN` | Upgrade to `@semantic-release/npm` **v11+** for OIDC |
| Release runs but no publish | `[skip ci]` in version-bump commit | Modify git plugin's `message` template |

```yaml
- uses: actions/checkout@v4
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
| `changeset publish` fails | Missing npm auth | Set `NODE_AUTH_TOKEN` or configure OIDC |
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
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm publish --provenance --access public
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
| Cache not working | Missing cache config | Add `cache: 'npm'` in `actions/setup-node` |

```yaml
concurrency:
  group: publish-${{ github.ref }}
  cancel-in-progress: false

# ...
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    registry-url: 'https://registry.npmjs.org'
    cache: 'npm'
```

---

## 6. Debugging Workflow

Follow this sequence when a publish fails:

**Step 1 — Read workflow logs.** Open the failed run in GitHub Actions; expand
the `npm publish` step for the actual error.

**Step 2 — Enable verbose logging.**

```yaml
- run: npm publish --provenance --access public --loglevel=verbose
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Or re-run with **Enable debug logging** checked (sets `ACTIONS_RUNNER_DEBUG`
and `ACTIONS_STEP_DEBUG` to `true`).

**Step 3 — Verify authentication.**

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
npm publish --provenance --access public
git push origin hotfix/1.2.4 --tags
```

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
npm publish --provenance --access public
```

---

## Quick Reference: Error → Fix

| Error Message | Likely Fix |
|---------------|------------|
| `ENEEDAUTH` | Set `NODE_AUTH_TOKEN` or add `registry-url` to setup-node |
| `E401` | Regenerate npm token; verify it's for npmjs.com |
| `E403` | Add `--access public` or check token scopes |
| `EPUBLISHCONFLICT` | Bump version — can't overwrite existing |
| `ERR_SOCKET_TIMEOUT` | Check `id-token: write` permission; check npm status |
| `ENOTINHISTORY` | Set `fetch-depth: 0` in actions/checkout |
| `EINVALIDNPMTOKEN` | Upgrade `@semantic-release/npm` to v11+ for OIDC |
| `ENOWORKSPACES` | Remove `--workspaces` flag or verify workspace config |

# OIDC Trusted Publishing for npm via GitHub Actions

Zero-secret npm publishing using GitHub Actions' built-in OIDC identity. The most secure method for public packages.

---

## How OIDC trusted publishing works

The flow involves four systems working together:

1. **GitHub Actions** mints a short-lived OIDC ID token (JWT) for the workflow run. This token contains claims about the repository, workflow, branch, commit SHA, and runner environment.

2. **npm registry** receives the publish request and the OIDC token. It verifies the token signature against GitHub's JWKS endpoint (`https://token.actions.githubusercontent.com/.well-known/jwks`). If valid, it authenticates the publish without any stored secret.

3. **Sigstore (Fulcio)** issues a short-lived X.509 signing certificate based on the verified OIDC identity. This certificate binds the package contents to the exact workflow run identity.

4. **Sigstore (Rekor)** records the signing event in an append-only transparency log. This creates an immutable, publicly auditable record that the package was built and signed by a specific GitHub Actions workflow.

The result: a published package with a cryptographic provenance attestation linking it to the exact source commit, build workflow, and runner environment — with zero long-lived secrets stored anywhere.

---

## Complete setup guide

### Prerequisites

- npm CLI >= 9.5.0 (ships with Node.js >= 18.x)
- GitHub-hosted runner (self-hosted runners cannot mint OIDC tokens)
- Package must be public (private packages require npm Enterprise for OIDC)
- npm account linked to the package scope (required for first publish only)
- `package.json` `repository` field matching the GitHub repo URL exactly

### Step 1 — Configure package.json

```json
{
  "name": "@yourorg/your-package",
  "version": "1.0.0",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourorg/your-package.git"
  },
  "publishConfig": {
    "access": "public",
    "provenance": true
  }
}
```

**Critical**: The `repository.url` must exactly match your GitHub repository URL, including casing. A mismatch like `YourOrg` vs `yourorg` will cause provenance verification to fail.

### Step 2 — Create the workflow file

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to npm

on:
  release:
    types: [published]

concurrency:
  group: npm-publish
  cancel-in-progress: false

permissions:
  id-token: write   # Required: mint OIDC token for npm authentication
  contents: read     # Required: checkout repository code

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20.x'
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci

      - run: npm test

      # No NODE_AUTH_TOKEN needed — OIDC handles authentication
      - run: npm publish --provenance --access public
```

### Step 3 — Verify before first publish

```bash
# Check npm CLI version (must be >= 9.5.0)
npm --version

# Verify package.json repository field
cat package.json | jq '.repository'

# Dry run to see what will be published
npm pack --dry-run
```

### Step 4 — Create a GitHub Release

```bash
gh release create v1.0.0 --title "v1.0.0" --notes "Initial release"
```

---

## Required permissions

### `id-token: write`

Allows the GitHub Actions runtime to mint an OIDC ID token. Without this:

- The npm CLI cannot obtain a token to authenticate with the registry
- Sigstore (Fulcio) cannot issue a signing certificate
- The publish will fail with `ERR_SOCKET_TIMEOUT` errors against Fulcio endpoints

This permission is **not** granted by default. Setting any `permissions` key disables all defaults — you must list every permission you need.

### `contents: read`

Allows the workflow to read repository contents. Required for:

- `actions/checkout` to clone the repository
- Sigstore to populate the provenance attestation with source materials (commit SHA, repo URL)
- Without it, the provenance attestation will have empty `materials` fields

### Additional permissions for version bumping tools

```yaml
permissions:
  id-token: write
  contents: write       # Push tags, create releases
  issues: write         # Comment on issues (semantic-release)
  pull-requests: write  # Comment on PRs (semantic-release)
```

---

## How provenance works

### SLSA framework

npm provenance implements [SLSA (Supply-chain Levels for Software Artifacts)](https://slsa.dev) at Level 2:

| SLSA Level | Requirement | npm OIDC |
|---|---|---|
| Level 0 | No provenance | — |
| Level 1 | Build process documented | ✅ Workflow YAML is linked |
| Level 2 | Hosted build, signed provenance | ✅ GitHub-hosted, Sigstore signed |
| Level 3 | Hardened build platform | ❌ (requires isolated build) |

### Sigstore signing flow

```
npm publish --provenance
  → npm CLI generates SLSA provenance statement
  → CLI requests OIDC token from GitHub Actions runtime
  → CLI sends OIDC token to Fulcio (Sigstore CA)
  → Fulcio verifies token, issues short-lived X.509 certificate (~10 min)
  → CLI signs provenance with the certificate's ephemeral key
  → Signed provenance recorded in Rekor transparency log
  → npm registry stores signed provenance alongside tarball
  → Certificate and key are discarded
```

**Fulcio certificates**: Ephemeral ECDSA P-256 key pairs, ~10 minute lifetime, bound to the OIDC subject claim. No key management required.

**Rekor transparency log**: Append-only, publicly auditable at `https://rekor.sigstore.dev`. Every signing event is timestamped and immutable.

### Provenance attestation contents

The attestation follows the [in-toto](https://in-toto.io) format:

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "subject": [{
    "name": "pkg:npm/@yourorg/your-package@1.0.0",
    "digest": { "sha512": "abc123..." }
  }],
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "predicate": {
    "buildType": "https://github.com/npm/cli/gha/v2",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/yourorg/your-package@refs/heads/main",
        "entryPoint": ".github/workflows/publish.yml"
      }
    }
  }
}
```

---

## Provenance configuration options

Four ways to enable provenance (any one is sufficient):

### CLI flag

```bash
npm publish --provenance --access public
```

### package.json

```json
{
  "publishConfig": { "provenance": true }
}
```

### .npmrc

```ini
provenance=true
```

### Environment variable

```bash
NPM_CONFIG_PROVENANCE=true npm publish --access public
```

### Precedence order

CLI flag > environment variable > project `.npmrc` > user `.npmrc` > `package.json` `publishConfig`

**Recommendation**: Set `provenance: true` in `publishConfig` as the default, so it cannot be accidentally omitted.

---

## Requirements and constraints

| Requirement | Details |
|---|---|
| **npm CLI version** | >= 9.5.0. Check with `npm --version`. Ships with Node.js >= 18.x. |
| **Runner type** | GitHub-hosted only. Self-hosted runners lack the OIDC identity provider endpoint. |
| **Package visibility** | Public packages only. Private requires npm Enterprise. |
| **Repository field** | `package.json` `repository.url` must exactly match GitHub repo URL. Case-sensitive. |
| **First publish** | npm account must own the scope. OIDC handles auth for subsequent publishes. |
| **Concurrency** | Use `concurrency` groups to prevent parallel publishes of the same version. |

---

## Security properties

### Zero secrets

No tokens, passwords, or API keys stored anywhere. The OIDC token is minted fresh per workflow run and expires automatically (~1 hour).

### Token binding

The OIDC token is bound to the specific repository, ref, workflow run, and runner environment. A stolen token cannot be replayed in another context.

### Audit trail

Every publish creates entries in the npm registry audit log, Rekor transparency log (cryptographic proof), and GitHub Actions workflow logs.

### Immutable provenance

The attestation is cryptographically signed, recorded in an append-only log, linked to a specific commit SHA, and publicly verifiable by any consumer.

### Comparison with token-based auth

| Property | OIDC | Token-based |
|---|---|---|
| Secret storage | None | GitHub Secrets |
| Token lifetime | ~1 hour (auto-expires) | Days to never (manual) |
| Blast radius if leaked | Single workflow run | All scoped packages until revoked |
| Rotation required | No | Yes (90-day recommended) |
| Works on self-hosted | No | Yes |

---

## Debugging OIDC failures

### Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `ERR_SOCKET_TIMEOUT` connecting to Fulcio | Missing `id-token: write` permission | Add `permissions: { id-token: write }` to the workflow or job |
| `401 Unauthorized` from Sigstore/Fulcio | Wrong OIDC audience claim | Ensure `registry-url: 'https://registry.npmjs.org'` is set in `actions/setup-node` |
| `403 Forbidden` from npm registry | Branch/ref not authorized or scope not linked | Verify publishing branch. Ensure npm account owns the package scope. |
| `EOTP` (OTP required) | Workflow not using OIDC correctly | Check `id-token: write` is set and no `NODE_AUTH_TOKEN` is overriding OIDC |
| Empty `materials` in provenance | Missing `contents: read` permission | Add `permissions: { contents: read }` |
| Provenance verification fails on npmjs.com | `repository.url` mismatch | Fix URL to exactly match GitHub repo (case-sensitive). Republish. |
| `404 Not Found` on first publish | Package/scope not linked to npm account | Run `npm publish` manually once to create the package, then switch to OIDC |
| Token expired mid-publish | Large package or slow network | Ensure `npm ci` and `npm test` run before publish step, not in the same `run` block |
| `ENEEDAUTH` | Missing `registry-url` in `setup-node` | Add `registry-url: 'https://registry.npmjs.org'` |

### Debugging steps

```bash
# 1. Check npm version (must be >= 9.5.0)
npm --version

# 2. Verify OIDC token is available (in GitHub Actions)
curl -s -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
  "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sigstore" | jq .

# 3. Check permissions — if ACTIONS_ID_TOKEN_REQUEST_URL is empty,
#    id-token: write is not set

# 4. Verify package.json repository field
node -e "console.log(require('./package.json').repository)"

# 5. Test with dry run
npm publish --provenance --access public --dry-run

# 6. Verify Fulcio connectivity
curl -s https://fulcio.sigstore.dev/api/v2/configuration | jq .
```

### Self-hosted runner fallback

If you must use a self-hosted runner, OIDC is not available. Use a granular access token instead (see `granular-tokens.md`):

```yaml
jobs:
  publish:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20.x'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci && npm test
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## Verifying provenance

### On npmjs.com

Published packages with provenance show a green checkmark on the package page. Click it to see the source repository, commit SHA, workflow file, and Rekor log entry.

### npm audit signatures

```bash
npm audit signatures

# Expected output:
# audited 1 package in 1s
# 1 package has a verified registry signature
# 1 package has a verified attestation
```

### Using cosign (advanced)

```bash
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp "https://github.com/yourorg/your-package" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  <package-tarball>
```

### Checking Rekor transparency log

```bash
rekor-cli search --email "workflow@github.com" \
  --rekor_server https://rekor.sigstore.dev

rekor-cli get --uuid <entry-uuid> \
  --rekor_server https://rekor.sigstore.dev
```

# npm Authentication Methods for CI/CD Publishing

## Method 1: OIDC + Trusted Publishing (Recommended for public packages)

### How it works

GitHub Actions mints a short-lived OIDC ID token for each workflow run. npm verifies this token against GitHub's JWKS endpoint. Sigstore issues a signing certificate based on the verified identity. The published package gets a cryptographic provenance attestation linking it to the exact source commit, build environment, and workflow.

No long-lived secrets are stored anywhere. The token lives only for the duration of the workflow run (~1 hour).

### Setup steps

1. **No npm token needed** — no secrets to create or rotate
2. **Configure workflow permissions**:
   ```yaml
   permissions:
     id-token: write    # Mint OIDC token
     contents: read     # Checkout code
   ```
3. **Use `actions/setup-node`** with `registry-url`:
   ```yaml
   - uses: actions/setup-node@v4
     with:
       node-version: '20.x'
       registry-url: 'https://registry.npmjs.org'
   ```
4. **Publish with provenance**:
   ```yaml
   - run: npm publish --provenance --access public
   ```

### Requirements

- npm CLI >= 9.5.0
- GitHub-hosted runner (not self-hosted — self-hosted runners cannot mint OIDC tokens)
- `package.json` must have a `repository` field that exactly matches the GitHub repo URL (case-sensitive)
- Package must be public (private packages require npm Enterprise for OIDC)
- First publish of a package still requires an npm account linked to the package scope

### Provenance details

The `--provenance` flag generates a [SLSA provenance](https://slsa.dev) attestation containing:
- Source repository URL and commit SHA
- Build workflow file path
- Runner OS and architecture
- Dependencies lockfile hash

Consumers can verify provenance on npmjs.com (green checkmark) or via `npm audit signatures`.

You can enable provenance without the CLI flag by any of:
- `package.json`: `"publishConfig": { "provenance": true }`
- `.npmrc`: `provenance=true`
- Environment variable: `NPM_CONFIG_PROVENANCE=true`

### Security properties

- Zero secrets in repository settings — nothing to leak
- Token is bound to the specific workflow run — cannot be replayed
- Full audit trail via Sigstore transparency log
- Provenance attestation is immutable and publicly verifiable

---

## Method 2: Granular Access Token (Recommended for private packages)

### How it works

npm granular access tokens are scoped to specific packages, organizations, or IP ranges. They have configurable expiry dates. They authenticate via the standard `NODE_AUTH_TOKEN` mechanism.

### Setup steps

1. **Create the token on npmjs.com**:
   - Login to npmjs.com
   - Profile > Access Tokens > Generate New Token > "Granular Access Token"
   - Set token name (e.g., `github-actions-mypackage`)
   - Scope: Select "Read and Write" for specific packages (e.g., `@myorg/mypackage`)
   - Expiry: Set to 90-365 days (mandatory rotation)
   - IP allowlists: Optionally restrict to GitHub Actions IP ranges
   - Click Generate, copy immediately (hidden after creation)

2. **Store as GitHub Secret**:
   - Repository > Settings > Secrets and variables > Actions > New repository secret
   - Name: `NPM_TOKEN`
   - Value: paste the token

3. **Configure workflow**:
   ```yaml
   - uses: actions/setup-node@v4
     with:
       node-version: '20.x'
       registry-url: 'https://registry.npmjs.org'
   - run: npm publish --access public
     env:
       NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
   ```

### Scoping options

| Scope | How to set |
|---|---|
| Specific packages | Enter package names during creation (e.g., `@org/pkg1`, `@org/pkg2`) |
| All packages in org | Select org scope |
| Read-only | Select "Read" permission only (useful for CI install jobs) |
| IP restriction | Enter CIDR ranges to limit where the token can be used |

### Rotation best practice

- Set expiry to 90 days at creation
- Set a calendar reminder to rotate before expiry
- When rotating: create new token first, update GitHub Secret, verify publish works, then delete old token
- Never have zero valid tokens during rotation

---

## Method 3: Automation Token (Classic) — Legacy

### How it works

Classic automation tokens provide read+write access to all packages the user owns. They have no expiry date and no package-level scoping. They bypass interactive 2FA prompts (designed for CI use).

### Why to avoid for new projects

- Account-wide blast radius — one leaked token compromises all packages
- No expiry — forgotten tokens remain valid indefinitely
- npm advisory recommends migration to granular tokens or OIDC by 2025
- No IP scoping
- No provenance support (you can still use `--provenance` with OIDC permissions alongside a classic token, but OIDC alone is preferred)

### If you must use one

1. **Create on npmjs.com**: Profile > Access Tokens > Generate New Token > Classic Token > "Automation"
2. **Store as GitHub Secret**: Name `NPM_TOKEN`
3. **Configure in workflow**: Same as granular token (uses `NODE_AUTH_TOKEN`)

---

## Decision matrix

| Factor | OIDC | Granular Token | Automation Token |
|---|---|---|---|
| Public packages on GitHub Actions | Best choice | Works | Works (avoid) |
| Private packages | Requires npm Enterprise | Best choice | Works (avoid) |
| Non-GitHub CI (GitLab, CircleCI) | Not available | Best choice | Works |
| Secret management overhead | None | Medium (rotation) | High (no expiry, broad scope) |
| Supply-chain attack resistance | Highest | Medium | Lowest |
| Provenance attestation | Native | Add `--provenance` + `id-token: write` | Add `--provenance` + `id-token: write` |
| First-time setup complexity | Medium | Medium | Simple |

## Common mistakes

- Committing `.npmrc` with `_authToken` to version control (use `.gitignore`)
- Using `npm login` in CI (use `NODE_AUTH_TOKEN` env var instead)
- Creating an automation token when a granular token would suffice
- Forgetting to set `registry-url` in `actions/setup-node` (publish fails silently or goes to wrong registry)
- Not setting `id-token: write` permission (OIDC silently falls back, provenance fails)
- Mismatched `repository` URL in `package.json` (provenance verification fails)

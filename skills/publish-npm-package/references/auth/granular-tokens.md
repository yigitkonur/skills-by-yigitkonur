# npm Access Tokens for CI/CD Publishing

Granular access tokens and automation tokens for npm publishing in GitHub Actions. Use when OIDC is not available (private packages, self-hosted runners, non-GitHub CI).

---

## Granular access tokens

### How they work

Granular access tokens are scoped credentials that provide fine-grained control over npm registry access:

- **Package-level scoping**: Restrict to specific packages or all packages in an organization
- **Permission levels**: Read-only or read-and-write
- **Configurable expiry**: 1 day to 365 days (mandatory — no permanent tokens)
- **IP allowlists**: Restrict token usage to specific IP ranges
- **Audit logging**: All token usage is logged on npmjs.com

Granular tokens authenticate via the standard `NODE_AUTH_TOKEN` mechanism. The `actions/setup-node` action configures `.npmrc` to read this environment variable automatically.

### Step-by-step creation on npmjs.com

1. Log in to [npmjs.com](https://www.npmjs.com)
2. Click your profile avatar (top right) → **Access Tokens**
3. Click **Generate New Token** → **Granular Access Token**
4. Fill in the form:
   - **Token name**: Descriptive name (e.g., `github-actions-mypackage-publish`)
   - **Expiration**: Choose duration (90 days recommended for CI)
   - **Packages and scopes**: Select "Only select packages and scopes", then choose specific packages or an organization
   - **Permissions**: Select "Read and Write" for publishing
   - **IP Ranges** (optional): Enter CIDR ranges to restrict usage
5. Click **Generate Token**
6. **Copy the token immediately** — it is hidden after you leave the page

### Scoping options

| Scope type | Configuration | Use case |
|---|---|---|
| **Specific packages** | Select individual package names | Single package or small set |
| **Organization-wide** | Select org name | Monorepo or multi-package org |
| **Read-only** | Set permissions to "Read" | CI install jobs, audit pipelines |
| **Read and write** | Set permissions to "Read and Write" | Publishing workflows |
| **IP restricted** | Enter CIDR ranges | Lock to GitHub Actions IP ranges |
| **Short-lived** | Set expiry to 1-7 days | One-off migrations, temp access |

### Storing as a GitHub Secret

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `NPM_TOKEN`
5. Value: Paste the granular access token
6. Click **Add secret**

For organization-wide tokens, store as an **Organization secret** and grant access to specific repositories.

### Workflow configuration

```yaml
name: Publish to npm

on:
  release:
    types: [published]

concurrency:
  group: npm-publish
  cancel-in-progress: false

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

      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**How it works**: `actions/setup-node` with `registry-url` creates an `.npmrc` containing:
```ini
//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}
```

The `NODE_AUTH_TOKEN` env var is substituted at runtime. The actual token value never appears in workflow files or logs.

### Adding provenance with a granular token

Combine a granular token with OIDC-based provenance signing:

```yaml
permissions:
  id-token: write    # For provenance signing via Sigstore
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20.x'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci && npm test
      - run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Rotation best practices

**90-day rotation cycle** (recommended):

| Day | Action |
|---|---|
| Day 1 | Create new token on npmjs.com with 90-day expiry |
| Day 1 | Update `NPM_TOKEN` GitHub Secret with the new token value |
| Day 1 | Trigger a test publish (dry run or pre-release) to verify |
| Day 2 | Delete the old token on npmjs.com |
| Day 85 | Begin next rotation cycle (5-day buffer before expiry) |

**Zero-downtime rotation**:

```bash
# 1. Create new token on npmjs.com (UI)
# 2. Update GitHub Secret via CLI
gh secret set NPM_TOKEN --body "npm_NEW_TOKEN_VALUE" --repo owner/repo
# 3. Verify with dry-run publish
gh workflow run publish.yml -f dry-run=true
# 4. Delete old token on npmjs.com (UI)
```

---

## Automation tokens (classic) — Legacy

### How they work

Classic automation tokens are the original npm CI authentication method:

- **Account-wide access**: Full read+write to every package the account owns
- **No expiry**: Valid indefinitely until manually revoked
- **2FA bypass**: Designed to bypass interactive 2FA prompts in automated environments
- **No scoping**: Cannot be restricted to specific packages or IP ranges

### Why to avoid for new projects

| Risk | Impact |
|---|---|
| **Account-wide blast radius** | One leaked token compromises every package the account can publish |
| **No expiry** | Forgotten tokens remain valid indefinitely |
| **No package scoping** | All-or-nothing access |
| **No IP restriction** | Token works from any IP address |
| **Deprecation path** | npm recommends migration to granular tokens or OIDC |

### Creating an automation token (if you must)

1. Log in to npmjs.com → **Access Tokens** → **Classic Token** → **Automation**
2. Copy the token immediately
3. Store as `NPM_TOKEN` GitHub Secret
4. Use in workflow same as granular token (`NODE_AUTH_TOKEN` env var)

### Migration to granular tokens

1. Identify all classic tokens on npmjs.com → **Access Tokens**
2. For each classic token: create a granular token with equivalent package scope
3. Update the GitHub Secret, test with a dry-run publish
4. Delete the classic token
5. Set up rotation reminders for the new granular token

---

## 2FA requirements

npm enforces 2FA in two modes:

| Setting | Behavior |
|---|---|
| **auth-only** | 2FA required for login and profile changes. Publishing works without OTP. |
| **auth-and-writes** | 2FA required for login, profile changes, AND publishing. |

### How token types interact with 2FA

| Token type | auth-only 2FA | auth-and-writes 2FA |
|---|---|---|
| **OIDC** | Bypasses | Bypasses |
| **Granular token** | Works | Bypasses (by design for CI) |
| **Automation token (classic)** | Works | Bypasses (by design for CI) |
| **Publish token (classic)** | Works | ❌ Blocked — requires OTP |

If you see `EOTP` errors in CI, switch to a granular token, automation token, or OIDC.

---

## Token security best practices

### Never commit .npmrc with tokens

```gitignore
# .gitignore
.npmrc
```

If you need a project `.npmrc`, use environment variable substitution:

```ini
# .npmrc (safe to commit)
//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}
```

### Use NODE_AUTH_TOKEN environment variable

```yaml
# ✅ Correct: token in env var (masked in logs)
- run: npm publish
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

# ❌ Wrong: token as CLI argument (visible in logs)
- run: npm publish --//registry.npmjs.org/:_authToken=${{ secrets.NPM_TOKEN }}

# ❌ Wrong: writing token to file directly
- run: echo "//registry.npmjs.org/:_authToken=${{ secrets.NPM_TOKEN }}" >> .npmrc
```

### Set minimum required scopes

| CI use case | Token scope needed |
|---|---|
| Publishing a single package | Read+Write on that specific package |
| Publishing monorepo packages | Read+Write on the org or package list |
| Installing private packages | Read-only on relevant packages/org |

### Rotation and monitoring

- Set 90-day expiry at creation time
- Never share tokens across repositories — one per repo
- Immediately revoke tokens when team members leave
- Check npmjs.com → **Access Tokens** for last-used timestamps

---

## Decision matrix: OIDC vs Granular vs Automation

| Factor | OIDC | Granular Token | Automation Token |
|---|---|---|---|
| **Security** | Highest — zero secrets | High — scoped + expiring | Lowest — broad + permanent |
| **Public packages** | ✅ Best choice | ✅ Works | ⚠️ Avoid |
| **Private packages** | ❌ Requires npm Enterprise | ✅ Best choice | ⚠️ Avoid |
| **GitHub Actions** | ✅ Native | ✅ Works | ✅ Works |
| **Non-GitHub CI** | ❌ Not available | ✅ Best choice | ✅ Works |
| **Self-hosted runners** | ❌ Not available | ✅ Works | ✅ Works |
| **Secret management** | None | Rotation required | No rotation (risky) |
| **Provenance** | ✅ Native | ✅ Add `id-token: write` | ✅ Add `id-token: write` |
| **2FA bypass** | ✅ Automatic | ✅ By design | ✅ By design |
| **IP restriction** | N/A (bound to workflow) | ✅ Configurable | ❌ Not available |
| **Package scoping** | Automatic (repo-bound) | ✅ Configurable | ❌ Account-wide |

### Quick decision

```
Is the package public?
  └─ Yes → On GitHub Actions with GitHub-hosted runners?
              └─ Yes → Use OIDC
              └─ No  → Use Granular Token
  └─ No  → Use Granular Token
```

---

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Committing `.npmrc` with `_authToken` | Token exposed in version control | Add `.npmrc` to `.gitignore`. Revoke token immediately. |
| Using `npm login` in CI | Interactive prompt hangs workflow | Use `NODE_AUTH_TOKEN` env var with `setup-node` `registry-url` |
| Forgetting `registry-url` in `setup-node` | `ENEEDAUTH` or wrong registry | Add `registry-url: 'https://registry.npmjs.org'` |
| Using automation token when granular suffices | Unnecessarily broad access | Create scoped granular token |
| Sharing one token across repos | Multiplied blast radius | Create one granular token per repository |
| Hardcoding token in workflow YAML | Token in repo history | Use GitHub Secrets. Rotate token. Clean history with BFG. |
| Not testing after rotation | Next publish fails `401` | Always dry-run publish after updating secret |
| Token expired without rotation | `401 Unauthorized` | Create new token, update secret, test, delete old |
| Using `NPM_TOKEN` as env var name | Not standard for `setup-node` | Use `NODE_AUTH_TOKEN` in your publish step |

# OIDC Trusted Publishing for npm via GitHub Actions

Zero-secret npm publishing using trusted publishing. The npm CLI authenticates the publish from the CI provider's OIDC identity instead of an npm token.

## Contents

- [Auth lane](#auth-lane)
- [Prerequisites](#prerequisites)
- [package.json setup](#packagejson-setup)
- [GitHub Actions workflow](#github-actions-workflow)
- [Link the npm package](#link-the-npm-package)
- [First publish bootstrap](#first-publish-bootstrap)
- [Automatic provenance](#automatic-provenance)
- [Debugging](#debugging)
- [Verification](#verification)

## Auth lane

Use this lane only when all of these are true:

- package is public
- repository is public when provenance is required
- package already exists on npm and is linked to the CI trusted publisher
- publish runs on GitHub-hosted runners
- npm CLI is 11.5.1 or newer
- Node.js is 22.14.0 or newer
- publish step has no `NPM_TOKEN` or `NODE_AUTH_TOKEN`

> **Guardrail:** Trusted publishing is a publish-time auth mechanism. `npm whoami` does not prove this lane works because OIDC authentication happens only during `npm publish`.

npm trusted publishing also supports GitLab CI/CD shared runners and CircleCI cloud runners. This reference keeps GitHub Actions examples because the skill targets GitHub Actions workflows.

## Prerequisites

- npm CLI 11.5.1+.
- Node.js 22.14.0+.
- GitHub-hosted runner, not self-hosted.
- `id-token: write` and `contents: read` permissions in the publish job.
- `actions/setup-node` configured with `registry-url: https://registry.npmjs.org`.
- `package.json.repository.url` exactly matches the GitHub repository URL, including casing.
- Package is already published once, then linked in npm package settings under Trusted Publisher / Publishing access.

## package.json setup

```json
{
  "name": "@yourorg/your-package",
  "version": "1.0.0",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourorg/your-package.git"
  },
  "publishConfig": {
    "access": "public"
  }
}
```

Do not require `publishConfig.provenance` for the pure trusted-publishing baseline. npm automatically generates provenance for eligible public packages from public repositories. Set `publishConfig.provenance` only when using token auth with explicit provenance or a third-party release tool that needs npm provenance config.

For monorepos, add the package directory:

```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/yourorg/your-repo.git",
    "directory": "packages/your-package"
  }
}
```

## GitHub Actions workflow

The current npm docs show `actions/setup-node@v6`, Node 24, and `package-manager-cache: false` for release builds. Keep those defaults in new examples. If an existing repo deliberately stays on older action tags for compatibility, document that decision in the workflow comments.

```yaml
name: Publish to npm

on:
  release:
    types: [published]

concurrency:
  group: npm-publish
  cancel-in-progress: false

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/setup-node@v6
        with:
          node-version: '24'
          registry-url: 'https://registry.npmjs.org'
          package-manager-cache: false

      - run: npm ci
      - run: npm run build --if-present
      - run: npm test

      - run: npm publish --access public
```

Pure trusted publishing does not use `--provenance`, `NPM_CONFIG_PROVENANCE`, `publishConfig.provenance`, `NPM_TOKEN`, or `NODE_AUTH_TOKEN`.

## Link the npm package

1. Open `https://www.npmjs.com/package/your-package/access`.
2. Find Trusted Publisher or Publishing access.
3. Add GitHub Actions as the publisher.
4. Enter the GitHub organization/user, repository, and workflow filename.
5. Optionally restrict by environment.
6. Save the trusted publisher.

All configured fields are case-sensitive. npm validates the trust configuration when publishing, not when saving it.

## First publish bootstrap

Trusted publishing cannot create a package that does not exist yet. Bootstrap the first version with a short-lived granular token, then switch to trusted publishing.

1. Create a granular access token on npmjs.com with Read and Write access.
2. Publish once locally or with the token workflow:
   ```bash
   npm publish --access public
   ```
3. Link the package to GitHub Actions in npm package settings.
4. Delete the GitHub `NPM_TOKEN` secret if one was added.
5. Revoke the bootstrap token on npmjs.com.
6. Switch the workflow to the pure trusted-publishing template above.

Do not build a mixed OIDC/token fallback loop for first publishes. First publish is token bootstrap; steady state is trusted publishing.

## Automatic provenance

When trusted publishing runs from GitHub Actions or GitLab CI/CD, npm automatically generates provenance for public packages from public repositories. No `--provenance` flag is required.

Automatic provenance currently does not apply to:

- private repositories
- private packages
- CircleCI trusted-publishing publishes
- token-auth publishes unless explicit provenance is enabled

To disable automatic provenance intentionally:

```bash
NPM_CONFIG_PROVENANCE=false npm publish
```

or:

```json
{
  "publishConfig": {
    "provenance": false
  }
}
```

## Debugging

| Symptom | Likely cause | Fix |
|---|---|---|
| `ENEEDAUTH` | trusted publisher fields do not match, missing `id-token: write`, or wrong workflow filename | Match npm settings to org/repo/workflow filename exactly and grant `id-token: write` |
| `403 Forbidden` | branch, environment, or package scope is not authorized | Check npm trusted-publisher settings and package ownership |
| `404 Not Found` on first publish | package does not exist yet | Bootstrap once with token auth |
| no provenance badge | private repo/package, CircleCI, or provenance disabled | Use a public repo/package on GitHub/GitLab or accept no provenance |
| `NODE_AUTH_TOKEN` present | workflow is token auth, not trusted publishing | Remove npm token env from the trusted-publishing publish step |

Useful checks:

```bash
npm --version        # must be 11.5.1+
node --version       # must be 22.14.0+
npm pack --dry-run   # validates package contents, not OIDC auth
```

Inside GitHub Actions, check the OIDC request variables only for debugging:

```yaml
- name: Check OIDC request availability
  run: |
    test -n "$ACTIONS_ID_TOKEN_REQUEST_URL"
    test -n "$ACTIONS_ID_TOKEN_REQUEST_TOKEN"
```

Do not add `npm whoami` to prove trusted publishing. It verifies token/login auth only.

## Verification

Before publishing:

- `npm pack --dry-run` shows intended tarball contents.
- workflow permissions include `contents: read` and `id-token: write`.
- publish step has no npm token environment variable.
- package has a matching trusted publisher on npmjs.com.

After publishing:

```bash
npm audit signatures
```

Also inspect the npm package page for provenance metadata and confirm the package URL, version, dist-tag, GitHub release/tag URL, and workflow run URL in the final report.

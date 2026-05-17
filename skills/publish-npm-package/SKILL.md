---
name: publish-npm-package
description: Use skill if you are publishing to npm via GitHub Actions release workflow with trusted publishing, NPM_TOKEN, provenance, semantic-release, changesets, release-please, or fixing npm publish CI.
---

# Publish npm Package

Set up npmjs publishing via GitHub Actions with a complete, internally consistent release flow: auth, version management, package-manager installs, workflow trigger, provenance, validation, and recovery. Decisions and routing live here; full YAML and tool deep-dives live in `references/`.

## When to use

Use this skill if the request is one of:

- *"publish this package to npm"*, *"set up npm publishing"*, *"automate npm releases"*
- *"npm publish from GitHub Actions"*, *"release workflow for npm"*, *"npm CI/CD"*
- *"trusted publishing"*, *"OIDC for npm"*, *"NPM_TOKEN provenance"*, *"id-token: write"*
- *"semantic-release"*, *"changesets"*, *"release-please"*, *"automate version bumps"*
- *"first publish of a new package"*, *"bootstrap npm package"*, *"link GitHub repo to npm"*
- *"why is my npm publish failing"*, *"EOTP / ENEEDAUTH / E403 in CI"*, *"npm whoami in Actions"*

`package.json` / repo signals that should pull this skill in:

- `"name"` field plus `"version"` and a `repository.url` pointing at GitHub
- `.github/workflows/*.yml` with `npm publish`, `setup-node`, `id-token: write`, or `NPM_TOKEN`
- `.npmrc` with `//registry.npmjs.org/:_authToken` or `${NODE_AUTH_TOKEN}`
- presence of `.releaserc*`, `release.config.js`, `.changeset/`, or `.release-please-*.json`
- scoped name (`@scope/name`) plus `publishConfig.access` decisions

Do NOT use this skill when:

- deploying apps/services to a runtime (Railway, Vercel, Fly) — use the platform skill (e.g. `run-railway`)
- writing the package's own runtime code, SDK internals, or APIs — use the relevant `build-*` skill
- publishing to a non-npm registry (Docker Hub, GHCR, PyPI, crates.io) and npm is not also in scope
- the only ask is which `npm` / package-manager command to run with no CI or release-automation context

## Decide auth first, versioning second, then route to the workflow template

Always follow this order. Skipping it produces half-configured release automation.

1. Classify the repo (table below).
2. Pick auth: OIDC trusted publishing, or token (`NPM_TOKEN` → `NODE_AUTH_TOKEN`).
3. Pick versioning: semantic-release, changesets, release-please, or manual.
4. Route to the exact workflow template in `references/workflows/`.
5. Check package/repo prerequisites and lockfile/package-manager.
6. Verify with `npm pack --dry-run`, build/test in CI, tool-specific dry runs.
7. If the repo is mid-migration or already failing, jump to recovery routing at the bottom.

### Classify the repo first

Answer these and **record the answers** — they drive every later decision:

1. Public or private package?
2. GitHub Actions on a GitHub-hosted runner (vs self-hosted / GHES / non-GitHub CI)?
3. Single package or monorepo / workspaces?
4. Conventional commits actually used (majority of meaningful commits in `type: description` form)?
5. Auto-publish on every releasable merge, or human-reviewed Release/Version PR?
6. Greenfield (never published) or already published with tags/versions?
7. Target really `npmjs.org`?

Derive answers from `package.json` + workspace manifests → existing workflows → git remote/tags → npm registry state. If still ambiguous, stop and ask — do not guess.

### Decision matrix

| Public? | GH-hosted runner? | Single/Mono | Conv. commits? | Gate | Auth | Versioning |
|---|---|---|---|---|---|---|
| Yes | Yes | Single | Yes | Auto | OIDC | semantic-release |
| Yes | Yes | Single | Yes | Human | OIDC | release-please |
| Yes | Yes | Single | No | Human | OIDC | changesets |
| Yes | Yes | Single | No (greenfield, will adopt) | Human | OIDC | release-please |
| Yes | Yes | Monorepo | Any | Any | OIDC | changesets (default) |
| No | Any | Any | Any | Any | Token | (any) |
| Any | No (self-hosted/GHES) | Any | Any | Any | Token | (any) |

## Auth lanes — keep them separate

| Lane | Use when | Requirements | Publish | Provenance |
|---|---|---|---|---|
| **OIDC trusted publishing** | Public package, public repo, GitHub-hosted runner, package already linked on npm | No npm token, `id-token: write`, `contents: read`, npm CLI 11.5.1+, Node 22.14.0+ | `npm publish --access public` | Automatic for eligible public packages — do **not** add `--provenance` |
| **Token + provenance** | Token auth required, public provenance desired | `NODE_AUTH_TOKEN`, `id-token: write`, cloud runner, npm CLI 9.5.0+ | `npm publish --provenance --access public` | Explicit flag, `NPM_CONFIG_PROVENANCE=true`, or tool config |
| **Token only** | Private package, self-hosted runner, GHES, private registry, bootstrap | `NODE_AUTH_TOKEN`; no `id-token` needed | `npm publish --access public` | None |

Auth rules:

- Default to OIDC whenever supported. Trusted publishing means **zero npm secrets** — if the publish step has `NODE_AUTH_TOKEN` or `NPM_TOKEN`, it is token auth, not trusted publishing, even if `id-token: write` is set.
- OIDC requires the package to **already exist** on npm. First publish of a brand-new package always bootstraps with a granular token, then switches to OIDC after linking the repo on npm.
- OIDC does not work on self-hosted runners. Use a granular token there.
- Use `secrets.NPM_TOKEN` exposed as `NODE_AUTH_TOKEN`. Do not run `npm login` in CI. Avoid classic automation tokens for new work.
- One granular token per repo or workflow surface; rotate on a schedule.

Read the full lane:

- `references/auth/oidc-trusted-publishing.md` — OIDC bootstrap, repo linking, provenance defaults
- `references/auth/granular-tokens.md` — granular token creation, scoping, rotation, secret wiring

## Local publish vs CI publish — know which mode you're in

Mixing these up is the #1 cause of `EOTP` / `ENEEDAUTH` errors.

> **Guardrail:** `NODE_AUTH_TOKEN` as a bare env var only works when an `.npmrc` contains `${NODE_AUTH_TOKEN}`. In GitHub Actions, `actions/setup-node` writes that file when `registry-url` is set. On a developer machine, npm ignores `NODE_AUTH_TOKEN` unless the placeholder `.npmrc` exists.

### Local publish (developer terminal)

Check existing auth before issuing tokens:

```bash
npm whoami --registry https://registry.npmjs.org
echo "${NPM_TOKEN:+NPM_TOKEN is set}"
cat ~/.npmrc 2>/dev/null | grep -v authToken | head
grep -l 'NPM_TOKEN' ~/.zshrc ~/.bashrc ~/.zprofile ~/.bash_profile 2>/dev/null
```

Wire the token (pick one):

```bash
# 1) CLI flag (most reliable locally; do NOT use in CI logs)
npm publish --access public --//registry.npmjs.org/:_authToken="${NPM_TOKEN}"

# 2) Temporary .npmrc (session-scoped)
echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
npm publish --access public
rm .npmrc

# 3) Browser 2FA login (no token needed)
npm login && npm publish --access public
```

> **Guardrail:** `--//registry.npmjs.org/:_authToken=TOKEN` is **not** a security risk on a local terminal. The "wrong" label in `references/auth/granular-tokens.md` applies only to CI logs.

### CI publish (GitHub Actions)

Pure trusted publishing — no npm secret:

```yaml
permissions:
  contents: read
  id-token: write
steps:
  - uses: actions/setup-node@v6
    with:
      node-version: '24'
      registry-url: 'https://registry.npmjs.org'
      package-manager-cache: false
  - run: npm publish --access public
```

Token auth — `NODE_AUTH_TOKEN` env on the publish step plus `setup-node` `registry-url`:

```yaml
- uses: actions/setup-node@v6
  with:
    registry-url: 'https://registry.npmjs.org'
    package-manager-cache: false
- run: npm publish --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Diagnose "EOTP when token should bypass 2FA"

If a granular automation token with "Bypass 2FA" still gets `EOTP`:

1. npm is **not using your token** — it has fallen back to interactive session auth.
2. Run `npm whoami`. A personal username confirms session auth is active.
3. Fix the wiring (CLI flag locally, `setup-node` + `NODE_AUTH_TOKEN` in CI). Do not rotate the token.

`npm whoami` does **not** validate trusted publishing. OIDC auth applies only during `npm publish` itself.

## Versioning models — pick the model, not the tool

| Need | Choose | Use when | Avoid when | Read |
|---|---|---|---|---|
| Publish on every releasable merge | **semantic-release** | Single package, strong conventional-commit discipline, no human gate | Monorepos, weak commits, teams that want a reviewable Release PR | `references/versioning/semantic-release.md` |
| Reviewable Release PR, publish on merge | **release-please** | Conventional commits exist, team wants a human merge gate | Untrustworthy commit messages, or zero-handling target | `references/versioning/release-please.md` |
| Per-PR version intent, batched releases | **changesets** | Monorepos, single-package without conventional commits, explicit version notes | Repo wants publish-on-merge with no human-authored version data | `references/versioning/changesets.md` |
| Rare/simple releases | **manual trigger + `npm version`** | Automation would outweigh release frequency | Task explicitly asks for full automation | "Manual Trigger" section of the matching workflow file |

Versioning rules:

- Monorepo default: changesets. Use release-please only when conventional commits already drive the repo.
- changesets is **not** monorepo-only. Single-package repos without conventional commits that want a human-reviewed Version PR are a valid use case.
- Distinguish **greenfield** ("team will adopt conventional commits going forward") from **existing repo** ("commits already lack them"). Existing repos with inconsistent history → changesets, not semantic-release.
- For existing published packages, bootstrap baseline state before the first automated run (initial tag for semantic-release; aligned config + manifest for release-please; initialized config for changesets).

> **Guardrail:** "Current version" in the release-please manifest = the version in `package.json`. For greenfield never-published packages, set it to whatever `package.json` says (typically `1.0.0` or `0.1.0`). Do not guess `0.0.0`.

## Workflow templates — do not hand-assemble YAML from memory

| Auth | Versioning | Template |
|---|---|---|
| OIDC | semantic-release | `references/workflows/oidc-workflows.md` → **1. OIDC + semantic-release** |
| OIDC | changesets | `references/workflows/oidc-workflows.md` → **2. OIDC + changesets** |
| OIDC | release-please | `references/workflows/oidc-workflows.md` → **3. OIDC + release-please** |
| OIDC | manual trigger | `references/workflows/oidc-workflows.md` → **4. OIDC + Manual Trigger** |
| Token | semantic-release | `references/workflows/token-workflows.md` → **1. Token + semantic-release** |
| Token | changesets | `references/workflows/token-workflows.md` → **2. Token + changesets** |
| Token | release-please | `references/workflows/token-workflows.md` → **3. Token + release-please** |
| Token | manual trigger | `references/workflows/token-workflows.md` → **4. Token + Manual Trigger** |

Monorepos: read `references/monorepo-publishing.md` before choosing a workspace flow. Prefer the changesets template; fall back to release-please when conventional commits already exist; do not default to semantic-release for monorepos.

> **Guardrail:** The workflow templates are the source of truth for full GitHub Actions YAML. The versioning references explain tool config, customization, and tool-specific failure modes — they are not standalone YAML sources.

## Pre-implementation prerequisites

### Package + repo

- Code pushed to a GitHub repository.
- `package.json.repository.url` exactly matches the GitHub repo URL, **including casing**.
- Scoped public packages set `publishConfig.access: "public"` (or equivalent).
- For pure trusted publishing, do not set `publishConfig.provenance`; npm auto-generates provenance for eligible public packages. Provenance config belongs to the token+provenance lane only.
- Lockfile committed; CI uses the matching deterministic install.
- `npm pack --dry-run` matches the intended tarball. If it includes `src/` while `main`/`module`/`types`/`exports` point at `dist/`, stop and fix packaging before touching CI.
- Packaging shape (`files`, `exports`, types, dual ESM/CJS): `references/package-config.md`.

### Lockfile and package-manager detection

| Lockfile / marker | Install | Notes |
|---|---|---|
| `package-lock.json` or `npm-shrinkwrap.json` | `npm ci` | Default when no other PM is in use |
| `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` | Enable pnpm via Corepack |
| `yarn.lock` + `.yarnrc.yml` or `packageManager: yarn@…` | `yarn install --immutable` | Yarn Berry / modern Yarn |
| `yarn.lock` without Berry markers | `yarn install --frozen-lockfile` | Yarn Classic |
| `bun.lockb` | `bun install --frozen-lockfile` | Only if the repo already uses Bun |

Multiple lockfiles: stop and reconcile the package-manager choice before changing release automation.

### CI

- `actions/setup-node` with `registry-url: https://registry.npmjs.org`.
- Build/test runs in the same job (or upstream of) publish.
- `concurrency` set to avoid publish races.
- Permissions least-privilege and explicit.
- Templates use `actions/setup-node@v6`, Node 24, `package-manager-cache: false` unless the repo deliberately keeps tag-readable examples.
- For production: pin actions to full SHAs with tag comments — see `references/supply-chain.md`.

### First-publish bootstrap (greenfield → OIDC)

> **Guardrail:** Trusted publishing requires the package to **already exist** on npm. Brand-new packages must bootstrap with token auth before linking trusted publishing.

1. Create a granular access token on npmjs.com (`references/auth/granular-tokens.md`).
2. Add it as `NPM_TOKEN` in GitHub Actions secrets.
3. Publish once: `npm publish --access public`, or use a token-based workflow template for the first release.
4. On `https://www.npmjs.com/package/<your-package>/access` → **Publishing access** → **Add GitHub Actions** to link the repo.
5. Remove `NPM_TOKEN` and switch the workflow to pure OIDC.

### Migration prerequisites

- semantic-release: full git history (`fetch-depth: 0`) and a baseline tag.
- release-please: config + manifest aligned to the **current `package.json` version**.
- changesets: contributor rule for adding changesets and clear handling of empty changesets.

## Guardrails — half-configured release automation is worse than none

- Prefer OIDC over granular tokens; granular tokens over classic automation tokens.
- Prefer changesets over semantic-release for monorepos unless there is a strong existing reason not to.
- Prefer release-please over semantic-release when the team wants a human-reviewed Release PR.
- Prefer workflow templates from the references over inventing YAML from memory.
- Do not pick semantic-release without real conventional commits, `fetch-depth: 0`, and a current toolchain that supports the chosen auth.
- release-please needs the **two-job pattern**: one job creates/updates the Release PR, a second publish job runs only when `release_created == 'true'`.
- Do not assume OIDC works on self-hosted runners.
- Do not commit tokenized `.npmrc` files. Placeholder-based `.npmrc` is fine; real tokens are not.
- Do not forget scoped public package access; `E403` on a scoped package usually means `publishConfig.access: "public"` was never configured.
- Do not add `--provenance` to pure trusted-publishing baselines. Use it only for token+provenance lanes.
- Do not use `pull_request_target` to expose release secrets to untrusted code.
- If the repo is mid-migration, finish auth + versioning + workflow + bootstrap together. Do not ship a half-state.

## Validation scripts

Bundled helpers — read the paired `.md` for flags; do not load script source during normal use.

| Script | Use |
|---|---|
| `scripts/check-package-json.mjs` | Inspect `package.json`, detect package manager/lockfile, flag metadata and `src`/`dist` mismatches; emits JSON + human output. |
| `scripts/dry-run-publish.sh` | Run `npm pack --dry-run` (and optionally `npm publish --dry-run`) without publishing. |
| `scripts/check-npm-auth.sh` | Token-auth diagnostic: token env presence + `npm whoami` when token auth is intended. Does **not** validate trusted publishing. |

## Verification before declaring done

Always run:

- `scripts/check-package-json.mjs [package-dir]` (or equivalent in the target repo)
- `scripts/dry-run-publish.sh [package-dir]` or `npm pack --dry-run`
- build + test in the same workflow that publishes
- a check that the chosen versioning tool is wired, not just installed

Auth-specific:

| Check | OIDC | Token |
|---|---|---|
| Runner | GitHub-hosted / supported cloud | Any |
| Permissions | `contents: read`, `id-token: write` | None unless token+provenance |
| Registry | `setup-node` → `registry-url: https://registry.npmjs.org` | Same |
| Secret wiring | None (no `NODE_AUTH_TOKEN`) | `NPM_TOKEN` secret, `NODE_AUTH_TOKEN` env on publish |
| Auth diagnostic | publish-only; `npm whoami` does not prove OIDC | `scripts/check-npm-auth.sh --token` or `npm whoami` |
| Post-publish | `npm audit signatures` | `npm audit signatures` only if provenance/signatures expected |

Tool-specific:

| Tool | Dry-run | Key files | Critical check |
|---|---|---|---|
| semantic-release | `npx semantic-release --dry-run` | `.releaserc` / `release.config.js` | Full git history, baseline tags, plugin order |
| changesets | `npx changeset status` | `.changeset/config.json` | Release/version PR path matches template |
| release-please | `release-please release-pr --repo-url=<owner/repo> --token=TOKEN --dry-run` (optional) | `.release-please-config.json`, `.release-please-manifest.json` | Manifest version matches `package.json`; publish gated on `release_created == 'true'` |

> **Guardrail:** release-please has no built-in dry-run equivalent. Verify config + manifest files and manifest/`package.json` alignment.

## Output contract

When setup or diagnosis is complete, report:

- selected auth lane and versioning model
- files changed
- exact publish workflow trigger
- package name, version, npm dist-tag
- npm package URL (`https://www.npmjs.com/package/<name>`)
- GitHub release / tag URL when the flow creates one
- validation commands actually run
- provenance / signature verification status
- rollback or recovery note for failed or wrong publishes

## Recovery routing

If the task is about an existing failure, jump straight to the narrowest reference.

| Problem | Read first | Focus |
|---|---|---|
| OIDC / provenance failure | `references/common-issues.md`, then `references/auth/oidc-trusted-publishing.md` | missing `id-token: write`, missing `contents: read`, wrong repo URL, self-hosted runner, missing npmjs registry config |
| Token auth failure | `references/common-issues.md`, then `references/auth/granular-tokens.md` | expired token, wrong scopes, wrong secret wiring, rotation mistakes |
| semantic-release failure | `references/common-issues.md`, then `references/versioning/semantic-release.md` | shallow clone, missing baseline tag, non-releasable commits, old plugin versions |
| changesets failure | `references/common-issues.md`, then `references/versioning/changesets.md` | forgotten changesets, release PR drift, access/public config, prerelease state |
| release-please failure | `references/common-issues.md`, then `references/versioning/release-please.md` | manifest drift, no releasable commits, duplicate/stuck Release PRs, broken publish gating |
| Published wrong version / broken package | `references/common-issues.md` | unpublish within 72h if allowed; otherwise deprecate and patch forward |
| Token leak / security incident | `references/supply-chain.md` | revoke, rotate, audit publishes, harden workflow before re-enabling release |

## Smallest reading set by scenario

- **Public single package, fully automatic:** `references/auth/oidc-trusted-publishing.md` + `references/versioning/semantic-release.md` + `references/workflows/oidc-workflows.md` (#1) + `references/supply-chain.md`.
- **Public single package, reviewable gate:** `references/auth/oidc-trusted-publishing.md` + `references/versioning/release-please.md` or `references/versioning/changesets.md` + `references/workflows/oidc-workflows.md` (#3 or #2) + `references/supply-chain.md`.
- **Monorepo / workspaces:** `references/monorepo-publishing.md` + `references/versioning/changesets.md` (default) or `references/versioning/release-please.md` + matching OIDC/token workflow section + `references/supply-chain.md`.
- **Private package, self-hosted runner, or non-GitHub CI:** `references/auth/granular-tokens.md` + chosen versioning reference + matching section in `references/workflows/token-workflows.md`.
- **Failing existing workflow:** `references/common-issues.md` + auth reference for the current mode + versioning reference for the current tool.

## Known traps — quick reference

| Trap | Impact | Fix |
|---|---|---|
| `NODE_AUTH_TOKEN` env var locally without setup-node's `.npmrc` | P0 — npm ignores token, falls back to interactive login, `EOTP` | Locally use `--//registry.npmjs.org/:_authToken=TOKEN`; in CI use `setup-node` + `NODE_AUTH_TOKEN` together |
| `EOTP` and assuming the token type is wrong | P0 — misdiagnosis | `EOTP` means npm is using interactive session auth, not your token. Fix wiring, not the token. |
| Not checking `~/.zshrc` / `~/.bashrc` for existing `NPM_TOKEN` | P1 — duplicate token issued | `grep NPM_TOKEN ~/.zshrc ~/.bashrc` before asking the user for a new one |
| `NODE_AUTH_TOKEN` / `NPM_TOKEN` set and calling it "OIDC" | P0 — silent wrong auth | OIDC = zero npm secrets. With a token in scope, it is token auth. |
| First-publish with OIDC on a never-published package | P0 — 404 | Bootstrap with a granular token, then switch to OIDC after linking the repo on npm |
| semantic-release / release-please without conventional commits | P0 — blocked | Use changesets if the team will not adopt conventional commits |
| Treating `--//registry.npmjs.org/:_authToken=TOKEN` as always wrong | P1 — blocks local publish | The "wrong" label applies to CI logs only; locally the CLI flag is the most reliable form |
| Assuming changesets is monorepo-only | P1 — wrong tool | changesets works for single-package repos and does not require conventional commits |
| Confusing greenfield "will adopt" with existing "does not have" | P1 — wrong guidance | Greenfield can adopt; existing repos without conventional commits need changesets |
| Copying config from a versioning reference instead of the workflow template | P1 — config mismatch | Workflow template is baseline; versioning reference is for customization |
| Using `@v4` action tags in production | P1 — supply-chain risk | Pin to full SHAs with tag comments; see `references/supply-chain.md` |
| release-please manifest version not matching `package.json` | P1 — release-please misfires | Manifest must match `package.json` exactly, including for greenfield |

## Final reminder

Keep `SKILL.md` focused on decisions, sequencing, and guardrails. Read only:

1. the auth reference,
2. the versioning reference,
3. the exact workflow-template section,
4. and `references/common-issues.md` / `references/supply-chain.md` only when needed.

Do not expand into full YAML or packaging deep dives here when the references already cover them.

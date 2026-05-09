---
name: publish-npm-package
description: Use skill if you are automating npm package releases from GitHub Actions and need trusted publishing, token auth, versioning, provenance, or workflow templates.
---

# npm Publish CI/CD

Set up npmjs publishing via GitHub Actions with a complete, internally consistent release flow: auth, version management, package-manager installs, workflow trigger, provenance, validation, and recovery.

## Trigger

Use this skill when the task is about:
- automating npmjs.org package releases from GitHub Actions
- publishing to npmjs.org locally from a developer machine
- first-time npm publishing of a new package (local bootstrap or CI)
- replacing manual `npm login` / `npm publish` with CI/CD
- choosing trusted publishing vs `NPM_TOKEN`
- choosing semantic-release vs changesets vs release-please vs manual trigger
- adding provenance, least-privilege permissions, or supply-chain hardening
- wiring single-package or monorepo npm releases
- debugging a failing npm publish workflow (including EOTP, ENEEDAUTH, E403)

This skill assumes npmjs.org. For deep `package.json` / exports / files shaping, route to `references/package-config.md` instead of expanding that detail here.

Do not use this skill when:
- deploying apps/services or infrastructure instead of npm packages; use `use-railway` only for Railway CLI operations
- implementing package code, SDK internals, or runtime APIs; use the relevant `build-*` skill
- publishing Docker images, packages for another registry ecosystem, or non-npm artifacts unless npm publishing is also required
- asking only about exact Railway, Vercel, cloud, or platform CLI commands

## Auth/provenance lanes

Keep these lanes separate in every workflow and diagnosis:

| Lane | Use when | Requirements | Publish command | Provenance |
|---|---|---|---|---|
| **Trusted publishing auth** | Public package, public repo, GitHub Actions on GitHub-hosted runners, package already linked on npm | No npm token, `id-token: write`, `contents: read`, npm CLI 11.5.1+, Node 22.14.0+ | `npm publish --access public` | Automatic for eligible public packages/repos; do not add `--provenance` for the pure baseline |
| **Token auth with provenance** | Token auth is required but public provenance is desired | `NODE_AUTH_TOKEN`, `id-token: write`, cloud-hosted runner, npm CLI 9.5.0+ | `npm publish --provenance --access public` | Explicit via flag, `NPM_CONFIG_PROVENANCE=true`, or tool config |
| **Token auth without provenance** | Private package, self-hosted runner, GHES, private registry, bootstrap, or provenance not supported | `NODE_AUTH_TOKEN`; no `id-token` needed | `npm publish --access public` | None |

Trusted publishing is currently supported by npm for GitHub Actions, GitLab CI/CD, and CircleCI cloud runners. This skill defaults to GitHub Actions templates; do not describe GitHub-only support as a universal npm limitation.

## Local publish vs CI publish — know which mode you're in

Before doing anything, determine whether this is a **local publish** (from the user's terminal) or a **CI publish** (from GitHub Actions). The token wiring is fundamentally different and mixing them up is the #1 cause of EOTP/ENEEDAUTH errors.

> **Guardrail:** `NODE_AUTH_TOKEN` as an environment variable only works when an `.npmrc` contains `${NODE_AUTH_TOKEN}`. In GitHub Actions, `actions/setup-node` creates that file when `registry-url` is set. On a developer machine, npm ignores `NODE_AUTH_TOKEN` unless the placeholder `.npmrc` exists.

### Local publish (developer terminal)

**Check existing auth first:**
```bash
npm whoami --registry https://registry.npmjs.org    # Who am I logged in as?
echo "${NPM_TOKEN:+NPM_TOKEN is set}"               # Is NPM_TOKEN in environment?
cat ~/.npmrc 2>/dev/null | grep -v authToken | head  # What .npmrc exists?
```

**Check shell profile for existing tokens:**
```bash
grep -l 'NPM_TOKEN' ~/.zshrc ~/.bashrc ~/.zprofile ~/.bash_profile 2>/dev/null
```

Many developers already have `NPM_TOKEN` exported in their shell profile. Use it if present — do not create a new one.

**Wire the token for local publish** (one of these):
```bash
# Option 1: CLI flag (works everywhere, no .npmrc needed)
npm publish --access public --//registry.npmjs.org/:_authToken="${NPM_TOKEN}"

# Option 2: Temporary .npmrc (creates file, works for session)
echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
npm publish --access public
rm .npmrc   # clean up

# Option 3: Interactive login (triggers browser-based 2FA, no token needed)
npm login   # then npm publish --access public
```

> **Guardrail:** The `--//registry.npmjs.org/:_authToken=TOKEN` CLI flag is not a security risk on a local machine. The granular-tokens reference marks this as wrong only for CI, where secrets can appear in logs. Locally, it is the most reliable token-passing method.

### CI publish (GitHub Actions)

For pure trusted publishing, use no npm token:
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

For token auth, use `NODE_AUTH_TOKEN` env var **with** `actions/setup-node` `registry-url`:
```yaml
- uses: actions/setup-node@v6
  with:
    registry-url: 'https://registry.npmjs.org'  # Creates .npmrc with ${NODE_AUTH_TOKEN}
    package-manager-cache: false
- run: npm publish --access public
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Diagnosing "EOTP when token should bypass 2FA"

If you see `EOTP` with an automation/granular token that has "Bypass 2FA" enabled:
1. **npm is not using your token.** It's falling back to the interactive `npm login` session.
2. Run `npm whoami` only for token-auth diagnosis. If it shows your personal username, the session auth is active.
3. Fix: pass the token explicitly via CLI flag (`--//registry.npmjs.org/:_authToken=...`) or properly wire `NODE_AUTH_TOKEN` with a setup-node `.npmrc`.

Do not use `npm whoami` to validate trusted publishing. npm OIDC auth applies only during `npm publish`.

## Always classify the repo first

Before writing YAML, answer these questions and **record the answers** — they drive the auth (Step 1) and versioning (Step 2) decisions below:

1. Is the package **public** or **private**?
2. Is publishing on **GitHub Actions** with a **GitHub-hosted runner**?
3. Is this a **single package** or a **monorepo/workspaces** repo?
4. Does the team already use **conventional commits** (the majority of meaningful commits follow `type: description` format)?
5. Should every releasable merge publish **automatically**, or should there be a **human-reviewed Release/Version PR**?
6. Is this **greenfield** (never published), or does the package already exist with tags/versions/releases?
7. Is the target really **npmjs.org**?

> **Guardrail:** Record answers explicitly, for example as inline comments or a checklist. Without a recorded classification, the auth and versioning decisions become guesswork.

Derive those answers in this order:
1. `package.json` and workspace manifests
2. existing GitHub Actions workflows
3. git remote, tags, and current versioning config files
4. npm registry state for the package

If the classification is still ambiguous after those checks, stop and ask instead of guessing.

### Quick-reference decision matrix

| Q1: Public? | Q2: GH Actions + hosted runner? | Q3: Single/Mono? | Q4: Conv. commits? | Q5: Auto/Human gate? | → Auth | → Versioning |
|---|---|---|---|---|---|---|
| Yes | Yes | Single | Yes | Auto | OIDC | semantic-release |
| Yes | Yes | Single | Yes | Human gate | OIDC | release-please |
| Yes | Yes | Single | No | Human gate | OIDC | changesets |
| Yes | Yes | Single | No (greenfield, will adopt) | Human gate | OIDC | release-please |
| Yes | Yes | Monorepo | Any | Any | OIDC | changesets (default) |
| No | Any | Any | Any | Any | Token | (any versioning) |
| Any | No (self-hosted/GHES) | Any | Any | Any | Token | (any versioning) |

## Always follow this order

1. Choose authentication.
2. Choose the versioning model.
3. Route to the exact workflow template.
4. Check package/repo prerequisites.
5. Implement the smallest complete configuration set.
6. Verify with dry runs and publish checks.
7. Add recovery notes if the workflow is already failing or the repo is mid-migration.

## 1) Choose authentication first

| Situation | Choose | Why | Read next |
|---|---|---|---|
| Public package + GitHub Actions + GitHub-hosted runner | **OIDC trusted publishing** | Best default: zero secret sprawl, repo-bound trust, provenance-friendly | `references/auth/oidc-trusted-publishing.md` |
| Private package, self-hosted runner, GHES, non-GitHub CI, or OIDC unsupported | **Granular access token** | Correct fallback when OIDC is unavailable | `references/auth/granular-tokens.md` |
| Existing classic automation token setup | **Migrate to granular token** unless blocked | Smaller blast radius, expiry, better hygiene | `references/auth/granular-tokens.md` |

**Auth rules**
- Default to **OIDC** whenever it is supported.
- Trusted publishing requires a supported cloud-hosted runner, npm CLI **11.5.1+**, Node **22.14.0+**, exact `package.json.repository.url`, `id-token: write`, `contents: read`, and public package/repo visibility for automatic provenance.
- If the publish runner is self-hosted, do **not** choose OIDC and hope it works; use a granular token.
- If this is the **first publish of a brand-new package**, bootstrap with a granular token even if the steady-state target is OIDC.
- Token-based publishing should use `secrets.NPM_TOKEN` exposed as `NODE_AUTH_TOKEN` in the publish step. Do not use `npm login` in CI.
- Use one granular token per repo or workflow surface, and rotate it on a regular schedule instead of treating it as permanent infrastructure.
- Do not keep both OIDC and token auth just because an old workflow used both. The only valid mixed setup is when **token auth is still required** but you also grant `id-token: write` for provenance.
- Avoid classic automation tokens for new work.

> **Guardrail:** Trusted publishing means **zero npm secrets**. If the publish step has `NODE_AUTH_TOKEN` or `NPM_TOKEN`, it is token auth, not trusted publishing, even if `id-token: write` is set.

## 2) Choose the versioning model, not just a tool

| Need | Choose | Choose when | Avoid when | Read next |
|---|---|---|---|---|
| Publish automatically on every releasable merge | **semantic-release** | Single package, strong conventional-commit discipline, no human release gate | Monorepos, weak commit discipline, teams that want a reviewable release PR | `references/versioning/semantic-release.md` |
| Generate a reviewable Release PR, publish after merge | **release-please** | Conventional commits already exist, team wants a human merge gate, explicit release PR is desirable | Commit messages are not trustworthy, or the goal is zero human release handling | `references/versioning/release-please.md` |
| Put version intent in each PR and batch releases deliberately | **changesets** | Monorepos, single-package repos without strict conventional commits, explicit version notes, teams that want a human-reviewed Version PR without adopting conventional commits | The repo wants publish-on-merge with no human-authored version data | `references/versioning/changesets.md` |
| Rare/simple releases | **manual trigger + `npm version`** | Automation would be heavier than the release frequency | The task explicitly asks for full release automation | matching workflow "Manual Trigger" section |

> **Guardrail:** changesets is **not** monorepo-only. It works for single-package repos and does not require conventional commits. If a single-package repo wants a human-reviewed Version PR without adopting conventional commits, choose changesets.

### Quick-decision flowchart

```
Is this a monorepo?
  YES → changesets (default) — or release-please if conv. commits already drive the repo
  NO (single package) →
       Does the team use conventional commits?
         YES →
              Want fully automatic publish? → semantic-release
              Want a human-reviewed Release PR? → release-please
         NO →
              Greenfield and willing to adopt? → release-please (commit to the format)
              Existing repo, won't adopt? → changesets
              Rare releases? → manual trigger
```

**Versioning rules**
- **Monorepo default: changesets.** Use release-please only when conventional commits already drive the repo. Treat semantic-release in monorepos as a last resort, not the default.
- **Single-package repo without conventional commits that wants a human release gate:** changesets is a viable choice — it is not monorepo-only. Alternatively, adopt conventional commits and choose release-please.
- If conventional commits are weak or absent **in an existing repo**, do **not** silently pick semantic-release or release-please. For greenfield repos, adopting conventional commits is a valid starting choice — pick release-please if the team commits to the format going forward.
- For existing published packages, bootstrap before the first automated run:
  - semantic-release: initial tag / baseline release state
  - release-please: config + manifest aligned to the current published version
  - changesets: initialized config and contributor workflow for changeset files

> **Guardrail:** Distinguish **greenfield** (team can choose to adopt conventional commits going forward) from **existing repo** (commit history already exists without them). For existing repos with inconsistent history, changesets avoids the commit-discipline prerequisite.

## 3) Route to the exact workflow template

Do not hand-assemble publish YAML from memory if a matching reference already exists.

> **Guardrail:** Use workflow templates as the source of truth for full GitHub Actions YAML. Versioning references explain tool config and tool-specific failure modes.

| Auth | Versioning | Workflow template |
|---|---|---|
| OIDC | semantic-release | `references/workflows/oidc-workflows.md` → **1. OIDC + semantic-release** |
| OIDC | changesets | `references/workflows/oidc-workflows.md` → **2. OIDC + changesets** |
| OIDC | release-please | `references/workflows/oidc-workflows.md` → **3. OIDC + release-please** |
| OIDC | manual trigger | `references/workflows/oidc-workflows.md` → **4. OIDC + Manual Trigger** |
| Token | semantic-release | `references/workflows/token-workflows.md` → **1. Token + semantic-release** |
| Token | changesets | `references/workflows/token-workflows.md` → **2. Token + changesets** |
| Token | release-please | `references/workflows/token-workflows.md` → **3. Token + release-please** |
| Token | manual trigger | `references/workflows/token-workflows.md` → **4. Token + Manual Trigger** |

**Monorepo routing**
- Read `references/monorepo-publishing.md` before choosing a monorepo flow.
- Prefer the **changesets** template for most workspaces repos.
- Use the **release-please** template when the repo already relies on conventional commits and wants a Release PR gate.
- Do not default to semantic-release for monorepos unless the repo is already invested in that ecosystem and the limitation is understood.

## 4) Pre-implementation prerequisites

Before editing or validating the workflow, confirm:

### Package/repo prerequisites
- The code is pushed to a **GitHub repository** (the workflow runs on GitHub Actions).
- `package.json.repository.url` exactly matches the GitHub repo URL, **including casing**.
- Scoped public packages set `publishConfig.access: "public"` or an equivalent publish flag.
- For pure trusted publishing, do not require `publishConfig.provenance`; npm automatically generates provenance for eligible public packages/repos. Use provenance config only for token+provenance or third-party tools that do not call `npm publish` directly.
- The repo's lockfile is committed and CI uses the matching deterministic install.
- `npm pack --dry-run` shows the intended tarball contents.
- If `npm pack --dry-run` includes `src/` files while `main`, `module`, `types`, or `exports` point at `dist/`, stop and fix packaging before touching CI/CD.
- Packaging details such as `files`, `exports`, types, and dual ESM/CJS output are correct. Use `references/package-config.md` for those details.

### Lockfile and package-manager detection

Detect the package manager before writing install commands:

| Lockfile / marker | Install command | Notes |
|---|---|---|
| `package-lock.json` or `npm-shrinkwrap.json` | `npm ci` | Default when no other package manager is clearly in use |
| `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` | Enable pnpm before install, usually with Corepack |
| `yarn.lock` with `.yarnrc.yml` or `packageManager: "yarn@..."` | `yarn install --immutable` | Yarn Berry/modern Yarn |
| `yarn.lock` without Berry markers | `yarn install --frozen-lockfile` | Yarn Classic |
| `bun.lockb` | `bun install --frozen-lockfile` | Use only if the repo already uses Bun |

When multiple lockfiles exist, stop and reconcile the package-manager choice before changing release automation.

### CI prerequisites
- `actions/setup-node` uses `registry-url: https://registry.npmjs.org`
- publish jobs run build/test before publish
- explicit `concurrency` is present to avoid publish races
- permissions are least-privilege and set deliberately
- Release builds should use `actions/setup-node@v6`, Node 24, and `package-manager-cache: false` unless the repo deliberately keeps tag-readable examples for compatibility. The workflow references document this choice.
- For production hardening, consider pinning GitHub Actions to full SHAs with a tag comment (e.g., `actions/checkout@<sha> # v6`). The reference templates use tags for readability; pin to SHAs before shipping to production. See `references/supply-chain.md` for SHA pinning guidance.

> **Guardrail:** The workflow templates use version tags for readability. For production, pin to full commit SHAs with tag comments. This prevents supply-chain attacks via mutable tags.

### First-publish / OIDC bootstrap (critical for greenfield)

> **Guardrail:** Trusted publishing requires the package to **already exist** on npm. For a brand-new package, bootstrap the first publish with token auth before linking trusted publishing.

Even when the long-term target is OIDC, the first release must use token-based auth to bootstrap the package on npm.

**Bootstrap steps for first publish with OIDC:**
1. Create a **granular access token** on npmjs.com (see `references/auth/granular-tokens.md`).
2. Add it as `NPM_TOKEN` in your repo's GitHub Actions secrets.
3. Publish once manually: `npm publish --access public` (or use the token-based workflow template for the first release).
4. Go to `https://www.npmjs.com/package/<your-package>/access` → **Publishing access** → **Add GitHub Actions** to link the package to your repo.
5. Remove the `NPM_TOKEN` secret and switch the workflow to pure OIDC.

### Migration prerequisites
- For semantic-release, ensure full git history (`fetch-depth: 0`) and baseline tags exist.
- For release-please, ensure both config and manifest files exist with the **manifest version matching `package.json`**. For never-published packages, use the `package.json` version (typically `1.0.0` or `0.1.0`).
- For changesets, ensure contributors know when to add a changeset and how empty changesets are handled.

> **Guardrail:** "Current version" in the release-please manifest means the version in `package.json`. For greenfield packages that have never been published, set the manifest to match `package.json` exactly. Do not guess `"0.0.0"` unless `package.json` says `"0.0.0"`.

## Guardrails: avoid half-configured release automation

- Prefer **OIDC over granular tokens**, and **granular tokens over classic automation tokens**.
- Prefer **changesets over semantic-release** for monorepos unless there is a strong existing reason not to.
- Prefer **release-please over semantic-release** when the team wants a human-reviewed Release PR.
- Prefer **workflow templates from the references** over inventing a new workflow from memory.
- Do not choose semantic-release without real conventional-commit discipline, `fetch-depth: 0`, and a current npm plugin/toolchain that supports the auth mode you selected.
- Do not create a release-please workflow without the **two-job pattern**: one job creates/updates the Release PR, and a second publish job runs only when `release_created == 'true'`.
- Do not create a changesets flow without a contributor rule for adding changesets.
- Do not assume OIDC works on self-hosted runners.
- Do not commit tokenized `.npmrc` files or hardcode `_authToken` values. A placeholder-based `.npmrc` is fine; real tokens are not.
- Do not forget scoped public package access settings; `E403` on a scoped package often means `public` access was never configured.
- Do not add `--provenance` to pure trusted-publishing baselines. Use it only for token+provenance lanes or tools that need explicit provenance config.
- Do not use `pull_request_target` for untrusted code to reach release secrets or publish permissions.
- If the repo is mid-migration, finish the auth + versioning + workflow + bootstrap state together. Half-migrated release automation is worse than a temporary manual process.

## Validation scripts

Run these bundled helpers from the skill directory or copy them into the target repo when useful. Read the paired `.md` docs for flags; do not load script source during normal skill use.

| Script | Use |
|---|---|
| `scripts/check-package-json.mjs` | Inspect `package.json`, detect package manager/lockfile state, flag package metadata and `src`/`dist` mismatches, and emit JSON with human output. |
| `scripts/dry-run-publish.sh` | Run `npm pack --dry-run`, optionally `npm publish --dry-run`, from a package directory without publishing for real. |
| `scripts/check-npm-auth.sh` | Token-auth diagnostic only: check token env presence safely and run `npm whoami` when token auth is intended. It does not validate trusted publishing. |

## Verification before calling the setup done

### Always run
- `scripts/check-package-json.mjs [package-dir]` or equivalent checks in the target repo
- `scripts/dry-run-publish.sh [package-dir]` or `npm pack --dry-run` directly to verify tarball contents
- build/test in the same workflow that publishes
- a check that the intended versioning tool is actually wired, not just installed

### Auth-specific checks

| Check | OIDC | Token |
|---|---|---|
| Runner type | GitHub-hosted / supported cloud runner | Any |
| Permissions | `contents: read`, `id-token: write` | no `id-token` unless token+provenance |
| Registry config | `actions/setup-node` → `registry-url: https://registry.npmjs.org` | Same |
| Secret wiring | None needed (no `NODE_AUTH_TOKEN`) | `NPM_TOKEN` in secrets, `NODE_AUTH_TOKEN` in publish step |
| Auth diagnostic | publish-only; `npm whoami` does not prove OIDC | `scripts/check-npm-auth.sh --token` or `npm whoami` |
| Post-publish verify | `npm audit signatures` | `npm audit signatures` only if provenance/signatures are expected |

### Tool-specific checks

| Tool | Dry-run command | Key files | Critical check |
|---|---|---|---|
| semantic-release | `npx semantic-release --dry-run` | `.releaserc` or `release.config.js` | Full git history, baseline tags, plugin order |
| changesets | `npx changeset status` | `.changeset/config.json` | Release/version PR path matches template |
| release-please | `release-please release-pr --repo-url=<owner/repo> --token=TOKEN --dry-run` (optional, requires CLI install) | `.release-please-config.json`, `.release-please-manifest.json` | Manifest version matches `package.json`, publish gated on `release_created == 'true'` |

> **Guardrail:** release-please has no built-in dry-run equivalent to `npx semantic-release --dry-run`. Verify config + manifest files and manifest/package version alignment. The CLI dry run above is optional and requires installing release-please.

## Output contract

When the setup or diagnosis is complete, report:

- selected auth lane and versioning model
- files changed
- exact publish workflow trigger
- package name, version, and npm dist-tag
- npm package URL (`https://www.npmjs.com/package/name`)
- GitHub release or tag URL when the chosen flow creates one
- validation commands actually run
- provenance/signature verification status
- rollback or recovery note for failed or wrong publishes

## Recovery routing

If the task is about an existing failure, jump straight to the narrowest reference instead of rereading everything.

| Problem | Read first | Immediate focus |
|---|---|---|
| OIDC / provenance failure | `references/common-issues.md`, then `references/auth/oidc-trusted-publishing.md` | missing `id-token: write`, missing `contents: read`, wrong repo URL, self-hosted runner, missing npmjs registry config |
| Token auth failure | `references/common-issues.md`, then `references/auth/granular-tokens.md` | expired token, wrong scopes, wrong secret wiring, rotation mistakes |
| semantic-release failure | `references/common-issues.md`, then `references/versioning/semantic-release.md` | shallow clone, missing baseline tag, commit messages not releasable, old plugin versions |
| changesets failure | `references/common-issues.md`, then `references/versioning/changesets.md` | forgotten changesets, release PR drift, access/public config, prerelease state |
| release-please failure | `references/common-issues.md`, then `references/versioning/release-please.md` | manifest drift, missing releasable commits, duplicate/stuck Release PRs, broken publish gating |
| Published wrong version / broken package | `references/common-issues.md` | unpublish within 72 hours if allowed, otherwise deprecate and patch forward |
| Token leak / security incident | `references/supply-chain.md` | revoke, rotate, audit publishes, harden workflow before re-enabling release |

## Smallest reading set by scenario

### Public single-package repo, fully automatic
- `references/auth/oidc-trusted-publishing.md`
- `references/versioning/semantic-release.md`
- `references/workflows/oidc-workflows.md` → **1. OIDC + semantic-release**
- `references/supply-chain.md`

### Public single-package repo, reviewable release gate
- `references/auth/oidc-trusted-publishing.md`
- `references/versioning/release-please.md` or `references/versioning/changesets.md`
- `references/workflows/oidc-workflows.md` → **3. OIDC + release-please** or **2. OIDC + changesets**
- `references/supply-chain.md`

### Monorepo / workspaces
- `references/monorepo-publishing.md`
- `references/versioning/changesets.md` (default) or `references/versioning/release-please.md`
- matching OIDC/token workflow section
- `references/supply-chain.md`

### Private package, self-hosted runner, or non-GitHub CI
- `references/auth/granular-tokens.md`
- chosen versioning reference
- matching section in `references/workflows/token-workflows.md`

### Failing existing workflow
- `references/common-issues.md`
- auth reference for the current auth mode
- versioning reference for the current tool

## Known traps — quick reference

These are the highest-impact traps found during derailment testing. Each is documented in detail at the relevant decision point above and in the reference files.

| Trap | Impact | What to do |
|---|---|---|
| Setting `NODE_AUTH_TOKEN` env var locally without setup-node's `.npmrc` | P0 — npm ignores the token, falls back to interactive login, triggers EOTP | `NODE_AUTH_TOKEN` only works when `.npmrc` contains `${NODE_AUTH_TOKEN}`. Locally, use `--//registry.npmjs.org/:_authToken=TOKEN` CLI flag instead. |
| Seeing EOTP and assuming the token type is wrong | P0 — misdiagnosis, wasted cycles | EOTP means npm is using the *interactive session auth*, not your token. Run `npm whoami` to confirm. The token isn't reaching npm — fix the wiring, not the token. |
| Not checking shell profile (`~/.zshrc`, `~/.bashrc`) for existing `NPM_TOKEN` | P1 — user already has a token but agent creates a new one or asks for one | Always `grep NPM_TOKEN ~/.zshrc ~/.bashrc` before asking the user to create or provide a token. |
| Using `NODE_AUTH_TOKEN`/`NPM_TOKEN` and calling it "OIDC" | P0 — silent wrong auth | OIDC means zero npm secrets. If the publish step has `NODE_AUTH_TOKEN`, it is token auth. |
| First-publish with OIDC on a package that does not exist on npm yet | P0 — 404 error | Bootstrap: publish once with a granular token, then switch to OIDC. |
| Picking semantic-release/release-please without conventional commits | P0 compound — blocked | Use changesets if the team will not adopt conventional commits. |
| Treating `--//registry.npmjs.org/:_authToken=TOKEN` as always wrong | P1 — blocks local publish | The "❌ Wrong" label in the granular-tokens reference applies to CI logs only. On a local terminal, the CLI flag is the most reliable token-passing method. |
| Assuming changesets is monorepo-only | P1 — wrong tool choice | changesets works for single-package repos and does not require conventional commits. |
| Confusing greenfield "will adopt" with existing "does not have" | P1 — wrong guidance | Greenfield can adopt conventional commits (design choice). Existing repos without them need changesets. |
| Copying config from versioning reference instead of workflow template | P1 — config mismatch | Workflow template is baseline; versioning reference shows customization options. |
| Using `@v4` action tags in production | P1 — supply-chain risk | Pin to full SHAs with tag comments for production workflows. |
| Not verifying manifest version matches `package.json` | P1 — release-please misfire | Manifest must match `package.json`. For greenfield, use the `package.json` version exactly. |

## Final reminder

Keep `SKILL.md` focused on decisions, sequencing, and guardrails. Read only:
1. the auth reference,
2. the versioning reference,
3. the exact workflow-template section,
4. and security/troubleshooting only if needed.

Do not expand into full YAML or packaging deep dives here when the references already cover them.

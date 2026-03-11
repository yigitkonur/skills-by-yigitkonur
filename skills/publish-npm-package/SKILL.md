---
name: publish-npm-package
description: Use skill if you are automating npm publishing via GitHub Actions and need auth, versioning, provenance, or workflow-template choices.
---

# npm Publish CI/CD

Set up npmjs publishing via GitHub Actions with a complete, internally consistent release flow: auth, version management, workflow trigger, provenance, and recovery.

## Trigger

Use this skill when the task is about:
- publishing to npmjs.org from GitHub Actions
- replacing manual `npm login` / `npm publish` with CI/CD
- choosing OIDC trusted publishing vs `NPM_TOKEN`
- choosing semantic-release vs changesets vs release-please vs manual trigger
- adding provenance, least-privilege permissions, or supply-chain hardening
- wiring single-package or monorepo npm releases
- debugging a failing npm publish workflow

This skill assumes npmjs.org. For deep `package.json` / exports / files shaping, route to `references/packaging/package-config.md` instead of expanding that detail here.

## Always classify the repo first

Before writing YAML, confirm:
1. Is the package public or private?
2. Is publishing happening on GitHub Actions, and is the publish job on a GitHub-hosted runner?
3. Is this a single package or a monorepo/workspaces repo?
4. Does the team already use reliable conventional commits?
5. Should every releasable merge publish automatically, or should there be a human-reviewed Release/Version PR?
6. Is this greenfield, or does the package already exist with tags/versions/releases?
7. Is the target really npmjs.org?

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
- OIDC requires **GitHub-hosted runners**, npm CLI **>= 9.5.0**, exact `package.json.repository.url`, `id-token: write`, `contents: read`, and public package visibility unless npm Enterprise support exists.
- If the publish runner is self-hosted, do **not** choose OIDC and hope it works; use a granular token.
- Token-based publishing should use `secrets.NPM_TOKEN` exposed as `NODE_AUTH_TOKEN` in the publish step. Do not use `npm login` in CI.
- Use one granular token per repo or workflow surface, and rotate it on a regular schedule instead of treating it as permanent infrastructure.
- Do not keep both OIDC and token auth just because an old workflow used both. The only valid mixed setup is when **token auth is still required** but you also grant `id-token: write` for provenance.
- Avoid classic automation tokens for new work.

## 2) Choose the versioning model, not just a tool

| Need | Choose | Choose when | Avoid when | Read next |
|---|---|---|---|---|
| Publish automatically on every releasable merge | **semantic-release** | Single package, strong conventional-commit discipline, no human release gate | Monorepos, weak commit discipline, teams that want a reviewable release PR | `references/versioning/semantic-release.md` |
| Generate a reviewable Release PR, publish after merge | **release-please** | Conventional commits already exist, team wants a human merge gate, explicit release PR is desirable | Commit messages are not trustworthy, or the goal is zero human release handling | `references/versioning/release-please.md` |
| Put version intent in each PR and batch releases deliberately | **changesets** | Monorepos, explicit version notes, teams without strict conventional commits | The repo wants publish-on-merge with no human-authored version data | `references/versioning/changesets.md` |
| Rare/simple releases | **manual trigger + `npm version`** | Automation would be heavier than the release frequency | The task explicitly asks for full release automation | matching workflow "Manual Trigger" section |

**Versioning rules**
- **Monorepo default: changesets.** Use release-please only when conventional commits already drive the repo. Treat semantic-release in monorepos as a last resort, not the default.
- If conventional commits are weak or absent, do **not** silently pick semantic-release or release-please.
- For existing published packages, bootstrap before the first automated run:
  - semantic-release: initial tag / baseline release state
  - release-please: config + manifest aligned to the current published version
  - changesets: initialized config and contributor workflow for changeset files

## 3) Route to the exact workflow template

Do not hand-assemble publish YAML from memory if a matching reference already exists.

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
- Read `references/monorepo/publishing-patterns.md` before choosing a monorepo flow.
- Prefer the **changesets** template for most workspaces repos.
- Use the **release-please** template when the repo already relies on conventional commits and wants a Release PR gate.
- Do not default to semantic-release for monorepos unless the repo is already invested in that ecosystem and the limitation is understood.

## 4) Pre-implementation prerequisites

Before editing or validating the workflow, confirm:

### Package/repo prerequisites
- `package.json.repository.url` exactly matches the GitHub repo URL, including casing.
- Scoped public packages set `publishConfig.access: "public"` or an equivalent publish flag.
- Prefer `publishConfig.provenance: true` so provenance is not a human-memory step.
- The repo's lockfile is committed and CI uses deterministic installs (`npm ci` or the repo's equivalent)
- `npm pack --dry-run` shows the intended tarball contents.
- Packaging details such as `files`, `exports`, types, and dual ESM/CJS output are correct. Use `references/packaging/package-config.md` for those details.

### CI prerequisites
- `actions/setup-node` uses `registry-url: https://registry.npmjs.org`
- publish jobs run build/test before publish
- explicit `concurrency` is present to avoid publish races
- permissions are least-privilege and set deliberately
- production-hardening work pins GitHub Actions to full SHAs, not mutable tags

### First-release / migration prerequisites
- For a new OIDC setup, ensure npm is linked to the correct GitHub repo and the package/scope is allowed to publish from that repo.
- If OIDC complains about repo/package linkage or first publish state, do the minimum bootstrap the auth reference describes before retrying.
- For semantic-release, ensure full git history and baseline tags exist.
- For release-please, ensure both config and manifest files exist and reflect current state.
- For changesets, ensure contributors know when to add a changeset and how empty changesets are handled.

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
- Do not rely on a human remembering `--provenance`; prefer package or tool config that bakes it in.
- Do not use `pull_request_target` for untrusted code to reach release secrets or publish permissions.
- If the repo is mid-migration, finish the auth + versioning + workflow + bootstrap state together. Half-migrated release automation is worse than a temporary manual process.

## Verification before calling the setup done

### Always run
- `npm pack --dry-run`
- build/test in the same workflow that publishes
- a check that the intended versioning tool is actually wired, not just installed

### Auth-specific checks
- OIDC:
  - publish job runs on a GitHub-hosted runner
  - `permissions` include at least `contents: read` and `id-token: write`
  - `actions/setup-node` points to npmjs
  - after the first successful publish, verify provenance with `npm audit signatures`
- Token:
  - `NPM_TOKEN` exists in repo/org secrets
  - publish step uses `NODE_AUTH_TOKEN`
  - if debugging auth, verify with `npm whoami` in a safe CI/local diagnostic path

### Tool-specific checks
- semantic-release:
  - `npx semantic-release --dry-run`
  - full git history is available
  - plugin order and baseline tags are sane
- changesets:
  - `npx changeset status`
  - `.changeset/config.json` exists
  - the release/version PR path matches the chosen template
- release-please:
  - config and manifest files both exist
  - publish is gated on `release_created == 'true'`
  - bootstrap state matches the current published version

## Recovery routing

If the task is about an existing failure, jump straight to the narrowest reference instead of rereading everything.

| Problem | Read first | Immediate focus |
|---|---|---|
| OIDC / provenance failure | `references/troubleshooting/common-issues.md`, then `references/auth/oidc-trusted-publishing.md` | missing `id-token: write`, missing `contents: read`, wrong repo URL, self-hosted runner, missing npmjs registry config |
| Token auth failure | `references/troubleshooting/common-issues.md`, then `references/auth/granular-tokens.md` | expired token, wrong scopes, wrong secret wiring, rotation mistakes |
| semantic-release failure | `references/troubleshooting/common-issues.md`, then `references/versioning/semantic-release.md` | shallow clone, missing baseline tag, commit messages not releasable, old plugin versions |
| changesets failure | `references/troubleshooting/common-issues.md`, then `references/versioning/changesets.md` | forgotten changesets, release PR drift, access/public config, prerelease state |
| release-please failure | `references/troubleshooting/common-issues.md`, then `references/versioning/release-please.md` | manifest drift, missing releasable commits, duplicate/stuck Release PRs, broken publish gating |
| Published wrong version / broken package | `references/troubleshooting/common-issues.md` | unpublish within 72 hours if allowed, otherwise deprecate and patch forward |
| Token leak / security incident | `references/security/supply-chain.md` | revoke, rotate, audit publishes, harden workflow before re-enabling release |

## Smallest reading set by scenario

### Public single-package repo, fully automatic
- `references/auth/oidc-trusted-publishing.md`
- `references/versioning/semantic-release.md`
- `references/workflows/oidc-workflows.md` → **1. OIDC + semantic-release**
- `references/security/supply-chain.md`

### Public single-package repo, reviewable release gate
- `references/auth/oidc-trusted-publishing.md`
- `references/versioning/release-please.md`
- `references/workflows/oidc-workflows.md` → **3. OIDC + release-please**

### Monorepo / workspaces
- `references/monorepo/publishing-patterns.md`
- `references/versioning/changesets.md` (default) or `references/versioning/release-please.md`
- matching OIDC/token workflow section

### Private package, self-hosted runner, or non-GitHub CI
- `references/auth/granular-tokens.md`
- chosen versioning reference
- matching section in `references/workflows/token-workflows.md`

### Failing existing workflow
- `references/troubleshooting/common-issues.md`
- auth reference for the current auth mode
- versioning reference for the current tool

## Final reminder

Keep `SKILL.md` focused on decisions, sequencing, and guardrails. Read only:
1. the auth reference,
2. the versioning reference,
3. the exact workflow-template section,
4. and security/troubleshooting only if needed.

Do not expand into full YAML or packaging deep dives here when the references already cover them.

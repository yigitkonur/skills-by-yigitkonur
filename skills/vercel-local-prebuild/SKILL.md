---
name: vercel-local-prebuild
description: Use skill if you are converting Vercel projects to local `vercel build` plus `vercel deploy --prebuilt` to save build minutes.
---

# Vercel Local Prebuild

## Goal

Move Vercel deployment cost from Vercel Build CPU Minutes to a controlled local build:

```bash
vercel pull --yes --environment=<env> --scope <team>
vercel build [--prod|--target=<env>] --yes --scope <team>
vercel deploy --prebuilt [--prod] --scope <team> --yes --archive=tgz
```

Keep the deployment fail-closed: real source/content changes must build, secrets must not be printed, and production traffic should move only after the repo's checks pass.

## First Pass

1. Run the audit helper:

   ```bash
   python3 ~/.codex/skills/vercel-local-prebuild/scripts/audit_vercel_local_prebuild.py --repo .
   ```

2. Read `references/scenario-matrix.md` before editing if the project has any of:
   monorepo layout, custom `vercel.json`, Git deployments currently enabled, secrets needed at build time, Blob/storage credentials, large `.vercel/output`, non-Next framework, or production-domain risk.

3. Inspect repo instructions first (`AGENTS.md`, `README.md`, deploy docs, package scripts). Existing local deploy conventions override generic snippets unless they are unsafe.

4. Use the project-pinned Vercel CLI when possible:
   `pnpm exec vercel`, `npm exec vercel --`, `yarn vercel`, or `bunx vercel`.
   If no local CLI exists, add/pin `vercel` as a dev dependency or document the deliberate global fallback.

## Implementation Workflow

1. **Link and env**
   - Confirm `.vercel/project.json` exists or run `vercel link --scope <team>`.
   - Run `vercel pull --yes --environment=production --scope <team>` before `vercel build`.
   - Use `vercel env run --environment=production --scope <team> -- <command>` for one-off checks that need env without writing secrets to disk.
   - Do not read, print, commit, or summarize `.env*` or `.vercel/.env*` values.

2. **Local build**
   - Preserve framework caches such as `.next/cache`; do not force cold builds unless diagnosing.
   - Delete only stale prebuilt output (`.vercel/output`) before rebuilding.
   - Run `vercel build --prod --yes --scope <team>` for production output.
   - Confirm `.vercel/output/config.json` exists before any `--prebuilt` deploy.

3. **Prebuilt deploy**
   - Use `vercel deploy --prebuilt --prod --scope <team> --yes --archive=tgz`.
   - Prefer `--prod --skip-domain` for staged production proof when traffic should not move yet; promote/alias only after checks pass.
   - Keep `--archive=tgz` by default for large outputs. Benchmark raw/no-archive only on staged deployments, because Vercel documents archive tradeoffs and raw uploads can hit request/file limits.

4. **Verification**
   - Run the repo's normal gates before production: typecheck, lint, tests, content/schema freshness, and local Vercel build.
   - After deploy, run smoke checks against the deployment URL, not only the custom domain.
   - If the custom domain is not on Vercel, state that clearly; a Vercel deploy may not affect live traffic.
   - Capture timings for pull, build, upload, checks, total, `.vercel/output` size, and upload strategy.

5. **Project integration**
   - Add scripts conservatively. Typical names:
     - `vercel:pull:prod`
     - `vercel:build:prod`
     - `vercel:deploy:prebuilt:prod`
     - `deploy:prod`
   - If rollback, parity gates, env backfill, or timing reports are needed, add a wrapper under `scripts/vercel/` instead of complex package-script chains.
   - Update the repo's `AGENTS.md` or deploy docs with the exact commands, scope/team, env behavior, and any benchmark result.

## Safety Rules

- Never use plain `vercel deploy --prod` as the cost-saving path; that can trigger a Vercel-side build.
- Never claim "changed-only upload" unless measured on that project. Vercel has `--prebuilt` and `--archive`, not a guaranteed changed-only prebuilt flag.
- Never weaken correctness gates just to save time. Add skip/fingerprint gates only when missing metadata, dirty generated artifacts, unknown dependencies, or changed inputs force a full build.
- Never print secret values. Presence checks may print only `present` or `missing`.
- Never delete user caches or generated state outside the deployment output without explicit evidence and approval.

## Useful References

- Read `references/scenario-matrix.md` for edge cases, framework-specific notes, timing-report fields, and failure responses.
- Official Vercel docs verified while creating this skill:
  - `vercel build`: https://vercel.com/docs/cli/build
  - `vercel deploy --prebuilt --archive=tgz`: https://vercel.com/docs/cli/deploy
  - `vercel env pull` / `vercel env run`: https://vercel.com/docs/cli/env
  - Vercel Blob env token behavior: https://vercel.com/docs/vercel-blob/using-blob-sdk

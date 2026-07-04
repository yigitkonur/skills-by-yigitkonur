# Scenario Matrix

## Core Facts

- `vercel build` writes Build Output API artifacts to `.vercel/output`; `vercel deploy --prebuilt` deploys that prior output.
- Run `vercel pull` before `vercel build` so project settings and env are current.
- `vercel env run -- <command>` injects env without writing a local env file.
- `--prebuilt` deployments can be missing Vercel System Environment Variables at build time. Audit `process.env.VERCEL_*`, Git SHA/branch usage, and framework assumptions.
- `--archive=tgz` reduces file-count/upload-limit risk but can reduce upload caching benefits. Benchmark raw upload only in staged/non-traffic deployments.

## Project Types

| Project | Local build path | Notes |
|---|---|---|
| Next.js | `vercel pull`, then `vercel build --prod` | Preserve `.next/cache`; avoid deleting it in deploy scripts. If app relies on `VERCEL_URL` or Git system vars at build time, synthesize them deliberately. |
| Static/Vite/Astro | `vercel build --prod` | Check `outputDirectory`, `buildCommand`, and env mode. Verify generated static output exists in `.vercel/output/static` or equivalent. |
| SvelteKit/Remix/Nuxt | `vercel build --prod` | Confirm adapter/framework integration emits valid Build Output API output. Run framework smoke tests before deploy. |
| Monorepo/Turborepo | Run from linked project root | Confirm Vercel `rootDirectory` matches the package being built. Preserve `.turbo` or framework caches. Do not assume repo root equals app root. |
| Custom `vercel.json` | Respect existing commands | Treat `installCommand`, `buildCommand`, `outputDirectory`, `functions`, routes, and Git settings as project contract. |
| Git deployments enabled | Disable only with approval | Prefer `git.deploymentEnabled=false` when local-prebuilt is mandatory; otherwise keep ignored-build gate fail-safe. |

## Env and Secrets

- Prefer:
  ```bash
  vercel pull --yes --environment=production --scope <team>
  vercel env run --environment=production --scope <team> -- node -e "console.log(process.env.KEY ? 'present' : 'missing')"
  ```
- Do not read `.env`, `.env.local`, `.vercel/.env*`, or dashboard-sensitive values.
- If `vercel pull` yields empty values for account/permission reasons, either:
  - use `vercel env run` for commands that can run directly under injected env, or
  - add a local wrapper that backfills missing pulled values from existing local env files without printing values.
- For Vercel Blob, `BLOB_READ_WRITE_TOKEN` is the stable read-write token env. If OIDC vars are present but Blob SDK access fails, explicitly pass `token: process.env.BLOB_READ_WRITE_TOKEN` when present and redeploy after restoring/rotating store credentials.

## Scripts to Add

Choose names that fit the repo. Generic package scripts:

```json
{
  "scripts": {
    "vercel:pull:prod": "vercel pull --yes --environment=production --scope <team>",
    "vercel:build:prod": "vercel build --prod --yes --scope <team>",
    "vercel:deploy:prebuilt:prod": "vercel deploy --prebuilt --prod --scope <team> --yes --archive=tgz",
    "deploy:prod": "npm run vercel:pull:prod && npm run vercel:build:prod && npm run vercel:deploy:prebuilt:prod"
  }
}
```

For serious production repos, prefer a wrapper script instead of a chain. It should:

- log project/local/global Vercel CLI versions,
- capture previous production deployment for rollback,
- pull env and project settings,
- preserve caches and rebuild `.vercel/output`,
- validate `.vercel/output/config.json`,
- deploy with `--prebuilt --archive=tgz`,
- run post-deploy gates against the deployment URL,
- rollback or stop promotion on failure,
- write a timing report.

## Timing Report Fields

Record at least:

- command, target, scope, archive/upload strategy,
- git SHA/branch and dirty status,
- Vercel CLI path/version,
- seconds for env pull, local build, upload/deploy, post-deploy checks, total,
- `.vercel/output` bytes and file count,
- build-skip/fingerprint decision if any,
- deployment URL and inspect URL when available.

## Upload Strategy

Default to `--archive=tgz` for large Build Output API trees. To evaluate raw upload:

1. Build locally.
2. Deploy with `--prebuilt --prod --skip-domain` and no archive.
3. Time it.
4. If it fails with request/file limits, is slower, or produces an unsafe deployment, keep `tgz`.
5. Document the result in repo deploy docs.

## Failure Responses

| Failure | Response |
|---|---|
| `.vercel/project.json` missing | Run `vercel link --scope <team>` or ask for the correct team/project. |
| Build needs unavailable Vercel System Env | Inject deterministic values via build env or use Git-based build only if local-prebuilt is explicitly impossible. |
| `.vercel/output/config.json` missing | Do not deploy; rerun `vercel build` and inspect build logs. |
| Raw upload request/file limit | Keep `--archive=tgz`; document benchmark. |
| Dirty worktree | Continue only if user asked to ship local changes; otherwise stage with `--skip-domain` or stop before production traffic. |
| Custom domain not on Vercel | Verify generated deployment URL; explain that Vercel deployment may not affect live domain traffic. |
| Post-deploy gate fails | Roll back if production was promoted; preserve logs and timing report. |

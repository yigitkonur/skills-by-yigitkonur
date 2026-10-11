# scaffold-kernel-app.sh

Generate a minimal TypeScript Kernel project without writing secrets.

```bash
bash scripts/scaffold-kernel-app.sh --mode embed --dir ./kernel-embed-demo
bash scripts/scaffold-kernel-app.sh --mode deploy --dir ./kernel-deploy-demo
```

## Modes

- `--mode embed` creates `src/index.ts`, an embedded SDK script that creates a browser, connects through Playwright CDP, writes `shot.png`, and deletes the browser in `finally`.
- `--mode deploy` creates `app.ts` at the project root (next to `package.json`, because `kernel deploy` uploads the entrypoint's directory), a Kernel App with one `analyze` action. The action tags browsers with `invocation_id`, returns a small JSON result, and deletes the browser in `finally`.

Deploy flow: `npm install` (creates the lockfile the deploy needs), `npm run deploy`, then `npm run invoke` (an async invocation that follows logs until it finishes). Both modes depend on `playwright-core` (the browser runs on Kernel, so no local browser download).

## Files created

- `package.json` with package ranges pinned from npm at generation time, not `latest`.
- `tsconfig.json` for strict NodeNext TypeScript.
- `.gitignore` that excludes `.env`, `node_modules/`, build output, and the screenshot artifact.
- `.env.example` with placeholders only. The script never creates `.env` and never writes a real `KERNEL_API_KEY`.
- `src/index.ts` for embed mode or `app.ts` (project root) for deploy mode.

## Flags

- `--dir DIR`: target directory. Defaults to `kernel-app`.
- `--mode embed|deploy`: output shape. Defaults to `embed`.
- `--force`: allow writing scaffold-managed files into a non-empty directory. Without this flag, the script refuses non-empty directories.

## Cleanup expectations

Embed mode deletes the created browser session before exit and prints the deleted `session_id`.

Deploy mode deletes browser sessions inside the action. After deploying, report the deployment ID/version, invocation ID, terminal status, and whether logs/events were consumed. If an invocation is stopped early, use the invocation cleanup APIs for browsers tagged with `invocation_id`.

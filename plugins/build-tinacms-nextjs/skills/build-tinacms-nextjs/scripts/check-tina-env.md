# check-tina-env.sh

Read-only inspection for TinaCMS environment variables, config files, generated client state, preview wiring, and likely backend lane.

## Run

```bash
bash scripts/check-tina-env.sh /path/to/project
```

Omit the argument to inspect the current directory.

## What It Checks

- Common TinaCloud env var names: `NEXT_PUBLIC_TINA_CLIENT_ID`, `TINA_TOKEN`, and `NEXT_PUBLIC_TINA_BRANCH`.
- Common self-hosted env var names for local mode, Auth.js, GitHub, Vercel KV, MongoDB, and Clerk.
- Presence of `tina/config.*`, `tina/database.*`, generated client files, admin route, preview route, `proxy.ts`, legacy `middleware.ts`, and self-hosted Tina API routes.
- A rough TinaCloud vs self-hosted lane guess based on env/config signals.

## Expected Output

The script prints whether each signal is present in process env, declared in an env file, or missing. It never prints secret values.

## Limitations

- It does not validate that secret values are correct.
- It does not read hosting-provider environment variables unless they are exported into the current shell.
- Lane detection is heuristic. Treat it as a routing aid, then verify against `tina/config.*` and the deployment target.

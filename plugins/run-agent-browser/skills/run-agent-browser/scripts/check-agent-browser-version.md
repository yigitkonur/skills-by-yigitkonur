# `check-agent-browser-version.sh`

Use this non-mutating helper before relying on the skill's current command examples:

```bash
bash scripts/check-agent-browser-version.sh
bash scripts/check-agent-browser-version.sh 0.31.1
```

It verifies that:

- the resolved installed CLI runs;
- its parsed version meets the requested minimum (default `0.31.1`);
- `agent-browser skills get core` is available;
- the local managed CDP pool is reported when present.

It uses `npx --no-install` only when no binary is on `PATH`. It never installs a package or Chrome. Pool absence is informational because the upstream CLI remains usable; missing core skill or an older/unparseable CLI is a failure.

# check-agent-browser-version.sh

Use this helper before browser work when the installed `agent-browser` surface may be stale or missing.

```bash
bash scripts/check-agent-browser-version.sh
bash scripts/check-agent-browser-version.sh 0.17.1
bash scripts/check-agent-browser-version.sh v0.17.1
```

Behavior:
- uses `agent-browser` when installed
- otherwise tries `npx --no-install agent-browser`
- prints the resolved command, raw version output, parsed semver, and minimum-version result
- exits non-zero only when the command cannot run or the parsed installed version is below the requested minimum
- accepts minimum versions as `MAJOR`, `MAJOR.MINOR`, `MAJOR.MINOR.PATCH`, or the same forms prefixed with `v`
- never runs `npm install`, `npx` package installation, or `agent-browser install`

If the installed version or minimum version cannot be parsed, inspect the printed output manually before relying on version-gated command examples.

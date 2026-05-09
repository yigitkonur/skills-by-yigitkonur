# launch-debug-session.sh

Use this script as a canonical opener for a live browser debugging session.

```bash
bash skills/run-playwright/skills/run-playwright/scripts/launch-debug-session.sh https://example.com debug-session --headed
```

From inside the installed skill directory:

```bash
bash scripts/launch-debug-session.sh https://example.com debug-session --headed
```

Arguments:

- first argument: URL to open
- optional positional argument: session name
- optional flag: `--headed`

The script:

- verifies a global or local `playwright-cli` exists and exposes current commands
- opens the URL with current command syntax
- supports `-s=<session>` and `open --headed`
- prints follow-up commands: `snapshot`, `show`, `console error`, `requests`, `tracing-start`, `tracing-stop`

It does not install packages, launch via `npx -y`, close sessions, delete data, or clean up. Cleanup must be explicit after evidence is collected.

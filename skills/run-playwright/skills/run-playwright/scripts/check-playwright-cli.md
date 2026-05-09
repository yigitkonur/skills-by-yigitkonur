# check-playwright-cli.sh

Run this script before relying on command examples when the installed `playwright-cli` version is unknown.

```bash
bash skills/run-playwright/skills/run-playwright/scripts/check-playwright-cli.sh
```

From inside the installed skill directory:

```bash
bash scripts/check-playwright-cli.sh
```

The script is read-only. It does not install packages globally, launch browsers, close sessions, or delete data.

It checks:

- global `playwright-cli`, then local `npx --no-install playwright-cli`, then fallback `npx -y @playwright/cli@latest`
- stale global binaries that lack the current command surface
- npm metadata for `@playwright/cli`
- binary version and top-level help
- required current commands: `install-browser`, `state-save`, `list`, `show`
- old unsupported command names still mentioned in the skill docs

If a docs/help conflict appears, prefer `playwright-cli --help` and command-specific help for examples that must execute.

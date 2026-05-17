# Version Drift

Use this file when the user asks for the latest or current Railway CLI behavior, or when a command in the official docs does not exist in the local live-help snapshot.

## Local baseline

- Local binary checked in this workspace: `railway 4.29.0`
- Local command surface captured from recursive help output on `2026-04-17`
- Local extraction artifacts:
  - `references/cli/railway-cli-command-reference.md`
  - `references/cli/railway-cli-command-tree.json`
  - `references/cli/railway-cli-live-help-snapshot.md`

## First-party upstream signals

Scraped on `2026-04-17`.

### Official docs index

Source:

- `https://docs.railway.com/cli`

Signals:

- The docs index currently lists command pages for:
  - `bucket`
  - `starship`
  - `functions`
  - `volume`
  - `deployment`
  - `scale`
- The docs index is broader than the local `4.29.0` top-level help snapshot.

### Official releases

Source:

- `https://github.com/railwayapp/cli/releases`

Signals:

| Release | Date | Relevant change |
|---|---|---|
| `v4.39.0` | `2026-04-17` | added `railway skills` |
| `v4.38.0` | `2026-04-16` | added `railway agent` |
| `v4.36.0` | `2026-03-31` | added `environment list` |
| `v4.37.3` | `2026-04-15` | fixed `railway docs` in non-interactive mode |

### Official repo landing page

Source:

- `https://github.com/railwayapp/cli`

Signals:

- Latest visible release: `v4.39.0`
- Latest release date shown: `Apr 17, 2026`
- Railway now also promotes official agent skills from the CLI repo README.

## What this means in practice

### If the user asks about the installed CLI

Use the local extracted reference as the source of truth.

Examples:

- exact flags for `railway add`
- nested subcommands under `railway volume`
- whether `railway scale` exists locally

### If the user asks for latest or current Railway CLI behavior

Do not answer from the local `4.29.0` snapshot alone.

Use current first-party sources and state the version split explicitly, for example:

- "Your local CLI is `4.29.0`, but Railway’s latest visible release on GitHub was `v4.39.0` on `April 17, 2026`."
- "The official releases page shows `railway skills` was added in `v4.39.0`, so it is newer than your local snapshot."

### If the docs mention a command missing from the local snapshot

Say both facts:

1. the command is documented upstream
2. it is not present in the captured local `4.29.0` help output

This avoids falsely claiming the command is available in the installed binary.

## Safe wording patterns

- "In the local `railway 4.29.0` help snapshot, ..."
- "In current first-party Railway sources scraped on `2026-04-17`, ..."
- "This appears to be newer than the installed local CLI."
- "Verify again after upgrading with `railway upgrade` or by regenerating the local help snapshot."

## Refresh workflow after an upgrade

After the user upgrades Railway CLI, regenerate the local reference:

```bash
node scripts/extract-railway-cli-help.mjs
```

Then re-check:

```bash
railway --version
```

If the user specifically wants "latest", re-check the official docs and releases instead of assuming the earlier scrape is still current.

# Installation and prerequisites

Install the skill, locate its bundled runner, and verify only the dependencies required by the selected target.

## Supported installation paths

### Claude Code plugin

```text
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install test-martool-cli@yigitkonur
```

### Codex plugin

```bash
codex plugin marketplace add yigitkonur/skills-by-yigitkonur
codex plugin add test-martool-cli@yigitkonur
```

### Skills CLI

Install only this skill:

```bash
npx -y skills add -y -g \
  yigitkonur/skills-by-yigitkonur/skills/test-martool-cli
```

Install the complete pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

The installation provides instructions and the combined runner. It does not install martool, create SSH access, deploy an image, or grant Docker permissions.

## Locate the runner

The active agent runtime determines the installation root. Common personal-scope locations include:

| Runtime | Typical root |
|---|---|
| Claude Code | `~/.claude/skills/test-martool-cli/` |
| `skills` CLI global install | `~/.agents/skills/test-martool-cli/` |
| Codex plugin | `$CODEX_HOME/plugins/cache/yigitkonur/test-martool-cli/<version>/skills/test-martool-cli/` |
| Manual Codex skill | `~/.codex/skills/test-martool-cli/` |
| Cursor/compatible skills runtime | Its configured skills directory |

Resolve the directory that directly contains this skill's `SKILL.md`:

```bash
export MARTOOL_CLI_SKILL_DIR=/absolute/path/to/test-martool-cli
test -f "$MARTOOL_CLI_SKILL_DIR/SKILL.md"
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" --help
```

Do not assume the runner is under the martool checkout. Plugin installers may copy or symlink it elsewhere.

## Shared prerequisites

- Node.js capable of running ESM `.mjs` files; use martool's supported Node version when source mode is selected.
- Write access to the chosen report directory.
- Enough time and CPU for thousands of isolated black-box cases during a full run.
- No DataForSEO credentials are required for these audits.

The runner accepts no credential flags and does not read or print remote environment variables.

## Source-mode prerequisites

Source mode requires:

- a martool Git checkout containing `package.json`;
- `pnpm` matching the checkout's `packageManager` declaration;
- installed dependencies; and
- martool's two authoritative audit scripts.

The runner calls `pnpm build` by default, then audits `dist/cli/main.js`. Use `--no-build` only when the intended target is an existing built artifact and its provenance is already known.

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target source \
  --repo /absolute/path/to/martool \
  --report-dir /tmp/martool-cli-source-proof
```

Source mode runs Node processes directly. It does not start Docker.

## Coolify-mode prerequisites

Coolify mode requires:

- OpenSSH client available locally;
- non-interactive SSH access to the Docker host;
- remote permission to run `docker ps`, `docker inspect`, and `docker exec`;
- one running, healthy container matching the requested Coolify project/service labels; and
- a deployed image containing `dist/cli/main.js` plus both audit scripts.

Verify access without dumping environment values:

```bash
ssh -o BatchMode=yes hetzner 'docker version --format "{{.Server.Version}}"'
```

Then run:

```bash
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify \
  --ssh-host hetzner \
  --coolify-project martool \
  --service martool
```

The runner never calls local Docker in this mode. See [Coolify remote verification](coolify-remote.md) for discovery and pinning details.

## Report directory

Without `--report-dir`, the runner creates a timestamped `martool-cli-audit-*` directory under the current directory. For reproducible automation, pass an absolute owned path:

```bash
--report-dir /tmp/martool-cli-proof-2026-07-17
```

The directory contains:

- `generated-flags.json` when the generated matrix runs;
- `platform-flags.json` when the platform matrix runs; and
- `combined.json` for the compact verdict and hashes.

Protect reports according to their environment. They contain command arguments and target identifiers, but the runner deliberately excludes secrets and environment dumps.

# test-martool-cli

Exhaustively test or release-gate martool CLI commands in a source checkout or deployed Coolify container over SSH, without local Docker or provider spend.

The bundled Node runner combines martool's generated-command and platform-command audit harnesses, saves raw evidence, verifies exact coverage and zero provider calls, and pins remote proof to one healthy container image.

**Category:** testing

## Install

**As a Claude Code plugin:**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install test-martool-cli@yigitkonur
```

**As a Codex plugin:**

```bash
codex plugin marketplace add yigitkonur/skills-by-yigitkonur
codex plugin add test-martool-cli@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/test-martool-cli
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Quick start

Find the installed directory containing this skill's `SKILL.md`, then run:

```bash
export MARTOOL_CLI_SKILL_DIR=/path/to/test-martool-cli
node "$MARTOOL_CLI_SKILL_DIR/scripts/run-martool-cli-audit.mjs" \
  --target coolify \
  --ssh-host hetzner
```

Use `--target source --repo /path/to/martool` for a source checkout. Run `--help` for all options and read [`references/installation.md`](references/installation.md) for prerequisites.

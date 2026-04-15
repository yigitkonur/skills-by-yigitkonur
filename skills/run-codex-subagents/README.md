# run-codex-subagents

Orchestrate Codex work through the released `codex-worker` CLI with file-backed prompts, explicit thread/turn control, request-response handling, runtime inspection, and recovery patterns.

**Category:** orchestration

## Requirements

- `codex-worker` available on `PATH`
- `codex` CLI installed and authenticated
- `jq` recommended for JSON-based shell flows

Install `codex-worker` itself if needed:

```bash
sudo -v ; curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | sudo bash
```

Or user-local:

```bash
curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | bash -s -- --install-dir "$HOME/.local/bin"
```

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-subagents
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

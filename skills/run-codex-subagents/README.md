# run-codex-subagents

Orchestrate Codex coding agents with the `codex-worker` CLI: create threads, launch turns from Markdown prompts, answer pending requests, recover partial work, and run parallel or sequential execution waves.

**Category:** orchestration

## Install Skill

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-subagents
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## Install codex-worker

Three options. The global install is canonical — every shell, subagent, and editor can call the binary by name.

```bash
# 1. Global install:
npm install -g codex-worker
which codex-worker
#   macOS with Homebrew-managed node: /opt/homebrew/bin/codex-worker
#   Other:  $(npm prefix -g)/bin/codex-worker
codex-worker --version

# 2. Throwaway, no install:
npx -y codex-worker --help
```

If `which codex-worker` is empty, your npm global bin is not on PATH. Run `npm prefix -g` and add the resulting `bin/` to `PATH` in `~/.zshrc`.

## Run codex-worker

Start a new thread from a Markdown task:

```bash
codex-worker run task.md
```

Continue an existing thread with a follow-up prompt:

```bash
codex-worker send <thread-id> followup.md
```

## Env Vars (inline or exported)

```bash
# Raise the idle watchdog from 30 min to 1 h for a single run:
CODEX_WORKER_TURN_TIMEOUT_MS=3600000 codex-worker run task.md

# Persistent in ~/.zshrc:
export CODEX_WORKER_TURN_TIMEOUT_MS=3600000
```

Full list: the installed skill's `references/tool-reference.md`.

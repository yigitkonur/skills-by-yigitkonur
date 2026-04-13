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

Run it without a global install:

```bash
npx -y codex-worker --help
```

Or install it globally:

```bash
npm install -g codex-worker
codex-worker --help
```

## Run codex-worker

Start a new thread from a Markdown task:

```bash
npx -y codex-worker run task.md
```

Or, after a global install:

```bash
codex-worker run task.md
```

Continue an existing thread with a follow-up prompt:

```bash
npx -y codex-worker send <thread-id> followup.md
```

Or:

```bash
codex-worker send <thread-id> followup.md
```

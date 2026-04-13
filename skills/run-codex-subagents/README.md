# run-codex-subagents

Orchestrate Codex coding agents with the `cli-codex-subagent` CLI. This skill is for file-backed task dispatch, async monitoring, blocked-request handling, session reuse, prompt-bundle handoff, and multi-wave CLI orchestration.

**Category:** workflow automation

## Focus

- CLI-only task orchestration with `run`, `task`, `session`, `request`, and `prompt`
- file-backed prompts with resolved `AGENTS.md` and `--context-file` inputs
- async-by-default execution with explicit `--wait` and `--follow`
- recovery from local artifacts such as rendered prompts, event logs, timeline logs, summary logs, and stderr logs
- handoff bundles for other coding agents

This skill does not cover MCP tools, MCP resource URIs, or `mcpc` testing.

## Requirements

- `cli-codex-subagent` available in `PATH`, or
- local-dev fallback: `node --import tsx src/cli.ts`

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-codex-subagents
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

# orchestrate-codex

Orchestrating codex CLI for parallel worktree fleets, batched template runs, single-mission monitoring, per-branch review loops, or resuming a partial prior run.

**Category:** orchestration

## Install

Install this skill individually:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/orchestrate-codex
```

Or install the full pack:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

## What it does

One skill, five modes, one entry point. The agent classifies the user's intent, runs the right pre-flight, spawns codex workers, emits a Monitor tool hint, and exits — leaving the workers running detached. Every spawn carries the same flag set (`--dangerously-bypass-approvals-and-sandbox`, `gpt-5.5`, `xhigh`). Every failure routes through the same taxonomy. Every destructive action is gated.

The five modes:
- **exec** — parallel `codex exec` agents in git worktrees with auto-commit and post-verify.
- **batch** — template × N inputs with bounded concurrency, idempotent skip-existing, output-size audit.
- **single** — one mission with JSONL streaming through the Monitor tool.
- **review** — per-branch `codex exec review` convergence loop with major/minor classifier.
- **rescue** — resume a partial prior run; redo failures or never-started entries.

## Prerequisites

- `codex-cli` 0.129.0 or later, authenticated (`codex login status` exits 0).
- `node` 22+ (for the dispatcher).
- `python3` 3.10+ (for the helpers).
- `jq` (for the bash manifest helper).
- `gh` 2.x with `gh auth status` succeeding (review mode only).

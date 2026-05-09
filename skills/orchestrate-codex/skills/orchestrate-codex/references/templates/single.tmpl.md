# Single mode prompt template

A single mission is a focused, observable, one-shot codex invocation. The template carries the same six sections as exec mode but does not need the SUBAGENT-STOP prefix unless the task is coding work in a repo where codex's installed meta-skills would interfere.

Use this template for: large refactors with live observability needed; research tasks too big for a single web search; one-shot code generations that benefit from JSONL event streaming via `codex-json-filter.sh`.

---

## Template

```
# Intent

<one sentence: the end-state to reach>

# Discovery — read first

- <path 1> — <reason>
- <path 2> — <reason>

# Constraints

- <hard facts the agent must respect>
- <out-of-scope items>

# Success criteria

- <specific deliverables>
- <verification commands the agent should run before finishing>

# Failure protocol

If blocked: stop, summarize what was tried and what was discovered, exit non-zero with the summary in the last-message file.
```

## When to add the SUBAGENT-STOP prefix

Add the prefix from `references/templates/exec.tmpl.md` if the user's task is coding work AND the cwd is a repo where codex has loaded meta-skills (visible in the early JSONL events as long `agent_message` items about planning before any `command_execution` event). For research / non-repo missions, skip the prefix — meta-skills don't fire in non-coding contexts.

## What single mode unlocks vs exec mode

- One worktree (or no worktree) instead of N. Lower setup cost.
- Live JSONL stream piped through `codex-json-filter.sh` — the user sees `[CMD>]`, `[CMD✓]`, `[THINK]`, `[SAID]` lines as they happen.
- Pairs `--json` with `-o <file>`. The `-o` file is the source of truth for "did codex produce output" even if MCP servers cause JSONL events to drop silently.

## Sizing

Single-mission prompts can run longer (100–300 lines) because there's only one. The token cost per word is the same as exec mode but you only pay it once. The Discovery and Constraints sections often grow because the agent has more autonomy and needs more guardrails.

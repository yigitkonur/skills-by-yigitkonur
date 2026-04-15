# Prompt bundles

Use this file when you need to understand how the CLI resolves and passes prompts to the Codex runtime.

## The task file is the contract

`codex-worker` is file-first. Every task or follow-up message starts from a markdown file.

The prompt file should contain:

- a non-empty markdown body
- any reusable context inline or in the prompt text itself

## How the CLI handles prompts

The CLI reads the markdown file content and passes it directly to the Codex app-server runtime. The runtime handles all prompt processing, context resolution, and `AGENTS.md` discovery.

Key points:

- The CLI does **not** parse frontmatter — it sends raw file content
- `AGENTS.md` auto-loading is handled by the Codex runtime, not the CLI
- Developer instructions are generated from CLI flags (like `--plan`, `--effort`, `--label`) and prepended to the prompt content

## Flag-based prompt enrichment

The CLI enriches prompt content based on flags before sending:

| Flag | What gets prepended |
|---|---|
| `--plan` | "Start by creating a plan before making any changes..." |
| `--skip-plan` | "Skip planning and proceed directly with implementation." |
| `--effort <level>` | "Reasoning effort level: {level}." |
| `--label <text>` | "Task label: {text}." |

These are prepended as developer hints to the raw prompt body.

## Working directory resolution

The `--cwd` flag determines the working directory for the Codex runtime. If not set, it defaults to `process.cwd()`.

```bash
codex-worker run task.md --cwd /absolute/path/to/project
codex-worker task start task.md --cwd ./relative/path
```

## Session continuity

When you use `--session <threadId>`, the CLI sends the prompt to an existing thread instead of creating a new one. This preserves:

- the existing thread context
- the model selection from the original thread
- the working directory from the original thread

```bash
codex-worker task start followup.md --session thr_abc123 --follow --compact
```

## Task steer vs new task

`task steer` sends a follow-up to a completed/failed thread, reusing its turn history:

```bash
codex-worker task steer thr_abc123 followup.md --follow --compact
```

A new `task start` with `--session` creates a fresh turn in the same thread:

```bash
codex-worker task start task.md --session thr_abc123
```

Both achieve session continuity, but `task steer` also carries forward the specific turn context.

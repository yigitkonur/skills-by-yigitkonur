# Prompt writing

Use this file when you are writing the markdown task file that `codex-worker` will execute.

## Core rule

Tighter prompts beat higher effort settings.

Before raising `--effort`, make the task file more concrete.

## Every task file should answer five questions

1. What exactly should the worker do?
2. Which files or directories matter?
3. What must it not touch?
4. What counts as success?
5. Which commands prove success?

## Good task structure

Recommended sections:

- objective
- scope
- constraints
- required checks
- deliverable

You do not need all headings in every file, but the content should exist somewhere in the prompt body.

## Useful frontmatter

The CLI itself does not parse frontmatter — it passes raw markdown to the Codex runtime. The runtime may process frontmatter keys. If you use frontmatter, treat it as runtime-level configuration:

```md
---
cwd: .
model: gpt-5.4
---
```

Keep behavioral instructions in the prompt body, not in frontmatter.

For CLI-level control, use command flags:

```bash
codex-worker run task.md --cwd . --model gpt-5.4 --effort medium --label auth-refactor
```

## Delegation rules

When the worker is another coding agent:

- name the exact files or modules it owns
- say whether it may create new files
- say what to ignore
- define the final verification command
- say whether it should stop at diagnosis or carry through the change

## Good patterns

- exact file paths
- exact acceptance criteria
- exact commands to run
- explicit non-goals
- explicit handoff expectations

## Weak patterns

- broad goals with no file scope
- “fix this” without telling the agent what success looks like
- relying on the agent to discover the verification command
- mixing several unrelated tasks into one prompt file

## File-backed context strategy

If the task needs long context, include it in the prompt file itself or as part of the `AGENTS.md` discovery that the Codex runtime handles automatically.

Do not paste large reference blocks into shell commands when the prompt file can carry them durably.

## When to split work

Create separate task files when:

- tasks can run independently
- one task is implementation and another is verification
- one task is research and another is coding
- you need different effort levels or models

See the templates for copy-ready starting points.

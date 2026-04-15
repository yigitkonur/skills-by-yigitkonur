# Prompt writing

Use this file when writing the Markdown prompt file that `codex-worker` will execute.

## Core rule

Tighter prompts beat clever flag combinations.

Before adding more runtime knobs, make the prompt file more concrete.

## Every prompt file should answer five questions

1. What exactly should the worker do?
2. Which files or directories matter?
3. What must it not touch?
4. What counts as success?
5. Which commands prove success?

## Good prompt structure

Recommended sections:
- objective
- scope
- constraints
- required checks
- deliverable

You do not need all headings every time, but the content should exist somewhere in the prompt body.

## CLI flags vs prompt content

Behavioral control that exists in the released CLI belongs in CLI flags:

```bash
codex-worker run task.md --cwd . --model gpt-5.4 --timeout 240000
```

Prompt-file content should describe the work, not replace those flags.

## Strong prompt patterns

- exact file paths
- explicit non-goals
- concrete acceptance criteria
- concrete verification commands
- clear ownership when the worker is another coding agent

## Weak prompt patterns

- “fix this” without success criteria
- unrelated tasks mixed into one file
- vague scope with no file boundaries
- relying on the worker to invent verification commands

## Split work when

- two prompts can run independently
- one prompt is implementation and another is verification
- one prompt is research and another is coding
- one prompt needs a different model or effort level

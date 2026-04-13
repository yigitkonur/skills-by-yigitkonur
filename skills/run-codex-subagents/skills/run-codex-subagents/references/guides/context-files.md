# Context Lives In The Markdown Prompt

The current CLI takes one Markdown file per `run`, `send`, `turn start`, or `turn steer` call. There is no supported `--context-file` flag on `codex-worker`.

## Preferred Pattern

Put the needed context directly in the prompt file:

```markdown
## Context

- Repo root: `/abs/project`
- Read first: `src/auth.ts`, `src/session.ts`
- Existing failure: `npm test` fails in `AuthGuard`

## Mission

Fix the auth regression without changing billing code.

## Definition Of Done

- [ ] `npm test` passes
- [ ] only `src/auth.ts` and `src/session.ts` changed
```

## Shared Context Across Many Turns

If every turn in a thread needs the same standing rules, create the thread explicitly:

```bash
codex-worker thread start \
  --cwd /abs/project \
  --developer-instructions "Prefer rg over grep. Keep patches minimal."
```

Then use `turn start` or `send` for the task-specific Markdown files.

## When To Inline Paths

Inline relative or absolute paths when:
- the next turn must read exact files first
- you want deterministic recovery after a failed turn
- multiple threads run in the same repo and you need different scopes

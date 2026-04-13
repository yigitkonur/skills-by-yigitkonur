# Thread-Level Instructions

Use thread-level instructions when every future turn in the thread should inherit the same operating constraints.

## Supported Flags

```bash
codex-worker thread start \
  --cwd /abs/project \
  --developer-instructions "Prefer rg over grep. Run tests before claiming success." \
  --base-instructions "Do not edit generated files."
```

## When To Use `--developer-instructions`

Use it for:
- repo-specific workflow rules
- tool preferences
- verification requirements
- safety constraints that apply to the whole thread

## When To Use `--base-instructions`

Use it for:
- standing background context
- non-negotiable global rules you want loaded before the first turn

## Operational Advice

- Create the thread once with these instructions, then use `turn start` or `send`.
- Keep them short and operational.
- Put task-specific goals in the Markdown prompt, not in the thread bootstrap text.

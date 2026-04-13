# Coder Mission Template

Save a prompt like this to `task.md`, then run:

```bash
codex-worker run task.md
```

## Template

```markdown
## Context

What exists now. What changed recently. Which files to read first.

## Mission

Describe the observable end-state. Name concrete files, exports, routes,
commands, or tests that should exist after success.

## Constraints

- Which files may change
- Which files must not change
- Architecture, style, or dependency constraints

## Definition Of Done

- [ ] Binary, verifiable result
- [ ] Binary, verifiable result

## Verification Commands

- `npm test`
- `npm run build`
```

## Use `send` For Recovery

If the first turn gets close but misses, keep the same thread:

```bash
codex-worker send <thread-id> fix-only.md
```

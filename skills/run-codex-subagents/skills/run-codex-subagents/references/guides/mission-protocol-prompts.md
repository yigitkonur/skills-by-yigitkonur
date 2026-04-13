# Mission-Style Prompt Files

`codex-worker` runs Markdown files. Use a consistent mission structure so threads are easy to recover, steer, and review.

## Preferred Shape

```markdown
## Context

What exists now. What changed recently. Which files to read first.

## Mission

Describe the observable end-state, not the implementation steps.

## Constraints

- File scope
- Safety constraints
- What must not change

## Definition Of Done

- [ ] Binary, verifiable outcome
- [ ] Binary, verifiable outcome

## Verification Commands

- `npm test`
- `npm run build`
```

## Why This Works

- `Context` reduces needless clarification requests.
- `Mission` keeps the worker outcome-focused.
- `Constraints` make recovery safer after partial progress.
- `Definition Of Done` gives you a crisp steer/fix prompt if the first turn misses.

## Template Routing

- Use `../templates/coder-mission.md` for implementation work.
- Use `../templates/planning-mission.md` for planning-only work.
- Use `../templates/research-mission.md` for audits and exploration.
- Use `../templates/quick-diagnostic.md` for one-command checks.
- Use `../templates/test-runner.md` for pure test execution.

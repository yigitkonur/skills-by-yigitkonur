# batch wave template

Use this as the parent-agent planning document when you want to dispatch several independent markdown task files in waves.

~~~~md
# Wave Plan

## Wave 1 goal

What can run independently right now?

## Wave 1 tasks

| Prompt file | Ownership | Label | Expected verification |
|---|---|---|---|
| prompts/wave-1/a.md | area A | wave-1 | npm test -- a |
| prompts/wave-1/b.md | area B | wave-1 | npm test -- b |
| prompts/wave-1/c.md | area C | wave-1 | npm test -- c |

## Launch commands

```bash
for file in prompts/wave-1/*.md; do
  codex-worker task start "$file" --label wave-1 --output json
done
```

## Completion gate

Do not start wave 2 until:

- all wave 1 tasks are terminal
- `codex-worker task list` shows no failed tasks with wave-1 label
- any blocked requests have been answered

## Wave 2 goal

What depends on wave 1 being complete?

## Recovery plan

If one task fails:

1. inspect `task read`
2. inspect `task events`
3. rerun only the failed branch or hand it off with a bundle
~~~~

Use one shared label per wave so `task list --label ...` stays useful.

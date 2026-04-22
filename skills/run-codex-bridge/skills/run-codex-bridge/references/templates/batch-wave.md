# batch wave template

Use this as the parent-agent planning document when you want to dispatch several independent Markdown prompt files in waves.

~~~~md
# Wave Plan

## Wave 1 goal

What can run independently right now?

## Wave 1 tasks

| Prompt file | Ownership | Expected verification |
|---|---|---|
| prompts/wave-1/a.md | area A | npm test -- a |
| prompts/wave-1/b.md | area B | npm test -- b |
| prompts/wave-1/c.md | area C | npm test -- c |

## Launch commands

```bash
> state/threads.tsv
for file in prompts/wave-1/*.md; do
  start_json="$(codex-worker --output json run "$file" --async)"
  thread_id="$(printf '%s' "$start_json" | jq -r '.threadId')"
  printf '%s\t%s\n' "$file" "$thread_id" >> state/threads.tsv
done
```

## Completion gate

Do not start wave 2 until:

- every thread in `state/threads.tsv` is terminal
- `references/scripts/batch-status.sh --status failed --cwd "$PWD"` reports no failures
- any blocked requests have been answered

## Recovery plan

If one branch fails:

1. inspect `read`
2. inspect `logs`
3. rerun only the failed branch or send a focused follow-up
~~~~

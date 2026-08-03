# Tool Filtering

Use native `grep` first, then JSON filtering.

## Native discovery first

```bash
mcpc grep search
mcpc @research-test grep evidence
mcpc grep config --tools --prompts
```

## Then filter JSON when needed

```bash
mcpc --json @research-test tools-list | jq '.[] | {name, taskSupport: .execution.taskSupport}'
mcpc --json @everything-http tools-list | jq '.[] | select(.execution.taskSupport == "required") | .name'
mcpc --json @research-test tools-list | jq '.[] | select(.annotations.readOnlyHint == true) | .name'
```

## Notes

- default grep scope is tools plus instructions; exit `1` means no matches (grep convention), not a CLI failure
- `--full` is mainly about richer human-mode output; JSON already carries the schema detail
- filtering by `.execution.taskSupport` is useful in `0.6.0` because task support is now public CLI surface

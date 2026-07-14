# Discovery Checklist

Use this file when the command does not appear in Raycast or does not seem to be recognized.

## Symptom Table

| Symptom | Likely cause | Fix |
|---|---|---|
| Command never appears | Script directory is not added to Raycast | Open Raycast Settings -> Script Commands -> Add Script Directory and select the folder containing the script. |
| Command never appears | Filename still contains `.template.` | Duplicate or rename the file and remove `.template.` after required user-specific edits are filled in. |
| Command is not recognized | Missing `@raycast.schemaVersion`, `@raycast.title`, or `@raycast.mode` | Add the required metadata directly below the shebang. |
| Metadata is ignored | Metadata is too far from the top | Move the metadata block near the top, before runnable code. |
| Metadata is ignored | Wrong comment style for Python/Bash | Use `# @raycast.*` comments. |
| Command appears but mode is wrong | `@raycast.mode` is missing or unsupported | Use one of `fullOutput`, `compact`, `silent`, or `inline`. |
| Command appears but will not run | Shebang or runtime is wrong | Run the file from Terminal with its shebang path; fix the shebang or install the runtime. |
| Command appears under an odd package label | `packageName` omitted and inferred from directory | Add `@raycast.packageName` when the package label matters. |

## Fast Fix Pattern

Start from a minimal known-good top block:

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example
# @raycast.mode fullOutput
# @raycast.packageName Examples
```

Then add other fields back only as needed.

## What not to chase first

Do not start by rewriting the whole script. Discovery failures are usually simpler:

- bad filename
- missing metadata
- metadata comment syntax problem
- script directory not added in Raycast

## Escalation

If the command appears but behaves strangely, switch to:

- `references/troubleshooting/runtime-and-output-issues.md`
- `references/metadata/mode-selection.md`

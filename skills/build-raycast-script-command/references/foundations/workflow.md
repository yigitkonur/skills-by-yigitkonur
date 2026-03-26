# Build Workflow

Use this file when creating or converting a Raycast Script Command.

## Branch 1: Create From Scratch

1. Decide whether Python or Bash is the better fit.
2. Choose the output mode based on how much text the command should show.
3. Start from the matching template in `assets/templates/`.
4. Add required metadata first.
5. Add optional metadata only when it changes behavior or clarity.
6. Implement the command logic.
7. Add dependency notes if the command relies on extra packages or CLIs.
8. Validate argument handling, output shape, and failure behavior.

## Branch 2: Convert An Existing Script

1. Read the script first without rewriting it.
2. Determine whether it already behaves like a one-shot command, a status widget, or a report.
3. Add the metadata block directly below the shebang.
4. Choose the correct mode from actual output shape, not guesswork.
5. If the script is not safe to run as-is, add `needsConfirmation true` or convert it to a `.template.` file when appropriate.
6. Tighten failure messages so Raycast gets a readable final error line.
7. Add dependency instructions at the top if the script is shareable.

## Branch 3: Repair An Existing Command

Work from symptom to cause:

- not showing up -> check file name and metadata
- wrong amount of output -> check mode
- broken arguments -> check metadata JSON and positional access
- inline not refreshing -> check `refreshTime`
- ugly or noisy failure -> check final printed line and exit code

## Validation Checklist

- the shebang matches the implementation language
- metadata is top-of-file and uses `# @raycast.*`
- required fields exist
- chosen mode matches output shape
- optional arguments are read safely
- non-zero exits produce human-readable error output
- dependency requirements are documented if needed

## Default Language Heuristic

- Python for APIs, JSON, text transforms, richer logic
- Bash for tiny wrappers around existing CLIs or OS actions

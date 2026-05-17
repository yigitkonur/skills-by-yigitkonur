# preview-script.sh

Run a Script Command locally and preview the stdout line Raycast will surface for the selected output mode.

This is a display-contract preview. It does not render Raycast UI.

## Usage

```bash
scripts/preview-script.sh path/to/command.py
scripts/preview-script.sh path/to/command.sh "argument one" "argument two"
```

The script reads `@raycast.mode`, runs the command with optional arguments, captures stdout, stderr, and exit code, then prints the Raycast-relevant display line.

## Mode Mapping

| Mode | Preview output |
|---|---|
| `fullOutput` | full stdout |
| `compact` | last stdout line |
| `silent` | last stdout line if present |
| `inline` | first stdout line |

## Non-Zero Exits

A non-zero exit is reported explicitly. For `compact` and `inline`, Raycast uses the last output line as the error message, so make failure paths print a readable final line before exiting.

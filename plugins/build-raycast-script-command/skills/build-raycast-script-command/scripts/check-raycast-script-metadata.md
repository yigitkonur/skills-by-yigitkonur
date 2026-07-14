# check-raycast-script-metadata.sh

Validate the metadata contract for a Python or Bash Raycast Script Command.

## Usage

```bash
scripts/check-raycast-script-metadata.sh path/to/command.py
scripts/check-raycast-script-metadata.sh path/to/command.sh
```

Run it before previewing the command. It does not execute the command.

## Checks

- file exists and has a `.py` or `.sh` extension
- first line is a shebang
- `@raycast.schemaVersion`, `@raycast.title`, and `@raycast.mode` appear near the top
- `@raycast.schemaVersion` is `1`
- mode is one of `fullOutput`, `compact`, `silent`, `inline`
- `inline` has `@raycast.refreshTime`
- `@raycast.argument1`, `@raycast.argument2`, and `@raycast.argument3` values parse as JSON
- argument types are only `text`, `password`, or `dropdown`
- dropdown `data` entries include `title` and `value`
- no argument beyond `@raycast.argument3` is used

## Result

The script prints `PASS` with the detected mode and argument count, or `FAIL` with actionable errors.

# diff-cli-help.sh

Compare two captured CLI help snapshots without invoking a live CLI.

## Inputs

```bash
scripts/diff-cli-help.sh OLD_HELP_SNAPSHOT NEW_HELP_SNAPSHOT
```

Both inputs are plain text files. Capture them with a separate read-only process such as:

```bash
mycli --help > /tmp/mycli-help-old.txt
mycli --help > /tmp/mycli-help-new.txt
```

For larger CLIs, concatenate top-level and subcommand help into each snapshot before diffing.

## Output

The script emits Markdown with:

- command additions
- command removals
- flag additions
- flag removals
- likely breaking changes

Removed commands, removed flags, and changed `Usage:` lines are reported as likely breaking changes.

## Safe Usage

The script reads files only. It does not execute the CLI under audit.

## Example

```bash
scripts/diff-cli-help.sh snapshots/v1-help.txt snapshots/v2-help.txt
```

## Limitations

- Command extraction is heuristic and works best with conventional `Commands:` or `Subcommands:` sections.
- It does not understand aliases, hidden commands, or command-specific flag scopes unless those appear in the snapshot.
- It cannot prove runtime compatibility; pair it with real stdout/stderr and exit-code checks before declaring a CLI agent-ready.

# audit-cli-help.sh

Read-only helper for a first-pass CLI discoverability audit.

## Inputs

- `CLI`: binary name or path.
- `--subcommands FILE`: optional newline-delimited list of subcommands to inspect. Blank lines and `#` comments are ignored.

Subcommand examples:

```text
repo view
issue list
deploy
```

## Commands Run

The script only runs help/version-style commands:

```bash
CLI --help
CLI --version
CLI <subcommand...> --help
```

It does not run list, get, create, update, delete, deploy, login, or any domain command.

## Output

The script emits Markdown with:

- top-level help and version status
- standard agent flag coverage: `--json`, `--output`, `--quiet`, `--yes`, `--dry-run`, `--force`, `--no-input`, `--timeout`
- subcommand help availability for listed commands
- whether help appears to document examples and exit codes
- missing or suspicious affordances

## Example

```bash
printf '%s\n' 'repo view' 'issue list' > /tmp/gh-subcommands.txt
scripts/audit-cli-help.sh --subcommands /tmp/gh-subcommands.txt gh
```

## Limitations

- This is a discoverability scan, not a full agent-readiness proof.
- It does not validate stdout/stderr separation, parse real JSON, or exercise failure paths.
- Flag detection is text-based; false positives and false negatives are possible when help text is unusual.
- Subcommand lines are split on shell whitespace; avoid quoted arguments in the subcommand file.

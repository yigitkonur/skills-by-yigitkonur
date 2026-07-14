# Shell Advanced

The shell is session-only in `mcpc 0.2.4`.

## Start it

```bash
mcpc shell @research-test
# or
mcpc @research-test shell
```

Do not document direct-URL shell commands.

## Useful commands inside the shell

- `help`
- `tools-list`
- `tools-get <name>`
- `tools-call <name> ...`
- `tools-call <name> --task ...`
- `tools-call <name> --detach ...`
- `prompts-list`
- `resources-list`
- `tasks-list`
- `tasks-get <taskId>`
- `tasks-cancel <taskId>`

## History location

Shell history is stored in `~/.mcpc/shell-history`.
That matches the released package even if older docs mention `~/.mcpc/history`.

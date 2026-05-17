# preview-makefile-wipe.sh

Read-only candidate discovery for the scaffold wipe step.

## Use

Run from this skill directory and pass the downstream project root. If already in the downstream project root, `.` is acceptable.

```bash
bash scripts/preview-makefile-wipe.sh /path/to/project
bash scripts/preview-makefile-wipe.sh /path/to/project --paths-only
```

The script prints:

- exact candidate path
- why the path matched
- whether Git tracks it
- current `git status --porcelain` state for that path

`--paths-only` prints the candidate path list to stdout for a deletion manifest. It still writes nothing.

## Read-only contract

The script never writes, stages, commits, deletes, chmods, moves, or edits files. It only runs `find`, `git ls-files`, and `git status`.

It excludes `.git/`, `node_modules/`, package-manager caches, vendored caches, framework caches, build output, coverage output, and language build directories.

## How the wipe step uses it

1. Run the preview script and inspect the table.
2. Read every candidate file before classifying it as scaffold.
3. Write a deletion manifest containing only approved paths.
4. Create a targeted snapshot commit that stages only manifest paths.
5. Print the recovery command.
6. Delete only paths listed in the manifest.

Never pipe `--paths-only` directly into `rm`. The manifest is an explicit review artifact, not a shortcut.

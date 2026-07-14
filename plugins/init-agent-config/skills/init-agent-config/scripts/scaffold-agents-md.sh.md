# scaffold-agents-md.sh

After-discovery helper for emitting one minimal `AGENTS.md` or `REVIEW.md` skeleton.

## Usage

```bash
sh scripts/scaffold-agents-md.sh --type root-agents --title "Project Name"
sh scripts/scaffold-agents-md.sh --type folder-agents --title "src/api"
sh scripts/scaffold-agents-md.sh --type review --title "Project Name"
```

Write to a file only when the file plan is known:

```bash
sh scripts/scaffold-agents-md.sh --type root-agents --title "Project Name" --write AGENTS.md
```

## Types

- `root-agents` emits a root `AGENTS.md` skeleton.
- `folder-agents` emits a folder-local `AGENTS.md` skeleton.
- `review` emits a root `REVIEW.md` skeleton.

## Safety

By default, the script writes to stdout. With `--write`, it requires an explicit target path, refuses to create missing directories, and refuses to overwrite an existing file. It does not invent commands, folders, project type, or review rules.

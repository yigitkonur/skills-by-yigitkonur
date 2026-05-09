# read-tree.sh

Purpose: recursively print a GitHub Issue sub-issue tree as markdown.

Mutates: no.

Arguments:

```bash
bash read-tree.sh OWNER/REPO ROOT_ISSUE [DEPTH]
```

Environment:

- `FULL=1` includes issue bodies.
- `MAX_DEPTH=N` caps recursion, default `8`.
- `VERIFY_PARENTS=0` skips the REST parent check.

Examples:

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" yigitkonur/example 42
FULL=1 MAX_DEPTH=4 bash "$SKILL_DIR/scripts/read-tree.sh" yigitkonur/example 42
```

Failure modes:

- Missing `gh` or `jq`.
- Root issue, sub-issue list, or parent lookup cannot be fetched.
- A child issue reports a different parent than the tree edge being read.

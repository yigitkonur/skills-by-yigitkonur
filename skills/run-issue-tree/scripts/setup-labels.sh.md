# setup-labels.sh

Purpose: create or update the standard wave, type, priority, and status labels for an issue tree.

Mutates: yes, it creates or updates GitHub labels.

Arguments:

```bash
bash setup-labels.sh OWNER/REPO
```

Environment:

- `MAX_WAVE=N` creates `wave:1` through `wave:N`; default is `5`.

Examples:

```bash
bash "$SKILL_DIR/scripts/setup-labels.sh" yigitkonur/example
MAX_WAVE=8 bash "$SKILL_DIR/scripts/setup-labels.sh" yigitkonur/example
```

Failure modes:

- Missing `gh`.
- `MAX_WAVE` is not an integer greater than or equal to `1`.
- GitHub auth, permission, or rate-limit errors while creating labels.

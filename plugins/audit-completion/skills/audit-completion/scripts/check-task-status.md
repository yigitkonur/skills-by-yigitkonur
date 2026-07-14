# check-task-status.sh

Deterministic checker for markdown audit tables and completion reports produced by `audit-completion`.

## Usage

```bash
bash scripts/check-task-status.sh audit.md
bash scripts/check-task-status.sh completion-report.md
```

Run it from the skill directory (`skills/audit-completion/skills/audit-completion/`) or pass the script path explicitly from elsewhere.

## Input

The script scans markdown tables with either shape:

```markdown
| # | Task | Status | Evidence | Blocking? | Action Required |
|---|------|--------|----------|-----------|-----------------|
```

```markdown
| # | Task | Started | Ended | Evidence |
|---|------|---------|-------|----------|
```

It ignores other markdown tables.

## Output

The report includes:

- count per audit `Status` or completion `Ended` status
- invented / unknown statuses
- audit rows with non-`Implemented` status and missing `Action Required`
- completion-report rows whose `Ended` value is non-terminal

`Blocked — unresolvable` is accepted as the terminal form of `Blocked`, not as a 23rd base status. `Superseded` may include a canonical-row note such as `Superseded (canonical: #3)`.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | No unknown statuses, no missing audit actions, and no non-terminal completion endings |
| `1` | At least one table integrity failure was found |
| `2` | Usage error, missing file, or no audit/completion table found |

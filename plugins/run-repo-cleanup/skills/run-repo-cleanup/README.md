# run-repo-cleanup

When you finish work on a project, sweep the repo clean: review and merge every live branch and worktree into the main branch locally (no PRs), retire all dangling branches (local and remote), and move non-essential files into a gitignored trash — with a report you can trust on re-run.

**Category:** productivity

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-repo-cleanup@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-repo-cleanup
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

# run-babysitter

Run an autonomous maintenance loop over one git repo, reading commits, issues, and persistent memory, then filing one deduplicated GitHub issue per cycle via gh.

**Category:** automation

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-babysitter@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/run-babysitter
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

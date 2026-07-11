# update-agent-config

Auditing AGENTS.md/CLAUDE.md/REVIEW.md hierarchies for drift after refactors: stale file:line refs, frequency-table recounts, invalidated rules, or missing AGENTS.md for code-bearing gap folders.

**Category:** configuration

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install update-agent-config@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/update-agent-config
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

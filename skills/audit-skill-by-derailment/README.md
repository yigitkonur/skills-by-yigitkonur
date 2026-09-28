# audit-skill-by-derailment

Harden and upgrade any skill by analyzing real execution friction traces. Supports synthetic subagents (Mode A), live multi-pane Herdr fleet audits (Mode B), and the native two-tier Herdr worker ➔ forensic auditor subagent loop (Mode C) with physical disk evidence verification and `Ctrl+O` verbose mode support.

**Category:** productivity

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install audit-skill-by-derailment@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/audit-skill-by-derailment -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/audit-skill-by-derailment/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/audit-skill-by-derailment -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

# run-testsprite-frontend

Creating, running, debugging, or release-gating TestSprite frontend browser tests, including public-target CLI or localhost MCP routing; not backend, load, security, or local-unit testing.

**Category:** testing

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-testsprite-frontend@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-testsprite-frontend -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/run-testsprite-frontend/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-testsprite-frontend -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

## Plan auditor

Resolve the installed/loaded skill directory to an absolute path; never pass `{baseDir}` literally. Use `--json` for machine-readable errors and warnings:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json "<PLAN_FILE>"
```

`--authorized-outward-step INDEX` is repeatable and zero-based. It changes only that detected step from an error to a warning; it does not grant authorization. `--self-test` is for maintainers/CI only and does not validate a plan.

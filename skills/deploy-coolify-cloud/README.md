# deploy-coolify-cloud

Deploying or updating a docker-compose service on Coolify Cloud via the API — wiring project/server, custom domains + TLS, cross-service networking, env-var secrets, and verifying the container actually came up.

**Category:** platform

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install deploy-coolify-cloud@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/deploy-coolify-cloud -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/deploy-coolify-cloud/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/deploy-coolify-cloud -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

# run-astro-audit

Enterprise-grade end-to-end Astro audits, deterministic AST & contract linting with **Astro Sentinel**, modern ESLint Flat Config & Prettier alignment, multi-wave subagent remediation in isolated Git worktrees, PR review comment harvesting, and conflict-free serial merge queues.

**Category:** Frontend / Architecture & Quality Engineering

## Key Capabilities

- **Astro Sentinel Linter Engine**: Deterministic AST static analysis via `@astrojs/compiler` catching virtual DOM leaks, secret prop serialization, unoptimized images, and Content Layer contract violations in sub-seconds.
- **Modern ESLint & Prettier Blueprint**: Production Flat Config aligning `eslint-plugin-astro`, 34 WCAG 2.2 accessibility rules (`astro/jsx-a11y-recommended`), and strict Tailwind v4 plugin ordering.
- **Knowledge Base**: 170 atomic Astro architectural rule cards across 10 domains and 70 modular workload briefs across 7 thematic layers.
- **Autonomous Remediation Lifecycle**: Multi-wave subagent dispatching, isolated worktree provisioning (`.worktrees/wt-*`), GitHub issue hierarchy, and parent-controlled serial rebase/merge queues.

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-astro-audit@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-astro-audit -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/run-astro-audit/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-astro-audit -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

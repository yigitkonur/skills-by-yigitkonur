# init-jean-json

Onboarding a repo to Jean (the worktree-based agent dev environment) — explore the repo, author `jean.json` (setup/run/teardown/ports) plus a `.worktreeinclude` manifest, prove them in a throwaway test worktree, document the bootstrap in AGENTS.md, and retire every test artifact. Covers `.env*`/`.claude` copying, APFS clonefile for instant `node_modules`, shared build caches, and port strategy for parallel worktrees.

**Category:** config

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install init-jean-json@yigitkonur
```

**Or with the `skills` CLI — this skill only:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/init-jean-json
```

**Or the full pack:**

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
```

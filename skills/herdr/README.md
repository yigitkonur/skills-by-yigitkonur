# herdr

Controlling interactive coding agents, tabs, worktrees, or session lifecycle through Herdr CLI.

Simple is the default; Advanced adds one Codex/Claude Engineering Manager only when explicitly selected.

**Category:** orchestration

## Install

**As a plugin (easy install / uninstall via `/plugin`):**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install herdr@yigitkonur
```

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs directly into `./.agents/skills` for your active project, keeping your workspace self-contained and avoiding global collisions. Fully compatible with project-scoped tools like PromptScript:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can also import directly via `prs`:
   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/herdr/SKILL.md
   ```

2. **Global install (user-level):**
   Installs globally into `~/.agents/skills` for all universal agents (Claude Code, Cursor, Codex, Antigravity, Amp, etc.) cleanly without triggering project-scoped agent warnings:

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/herdr -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

## Run

Install the skill per project; a global skill install is optional. The Herdr CLI
and the chosen interactive agent CLI must also be available on `PATH`. Installing
this documentation does not install those runtimes or authenticate an account.
Select your harness when it uses a separate skill directory. The tested project
install with `-a universal` populated `.agents/skills/herdr`; selecting
`-a claude-code` installed a separate project copy under `.claude/skills/herdr`.
Resolve the actual selected harness's copy; updating one did not refresh the
earlier Universal copy in the tested installer.
For example, append `-a claude-code` to the skill-only project command above.

Open a terminal pane inside Herdr, then verify:

```bash
herdr --help
herdr pane current --current
```

Require `HERDR_ENV=1` and successful live pane lookup. If lookup says
`pane_not_found`, follow the read-only identity diagnosis in [SKILL.md](SKILL.md);
do not target another focused terminal. That file also provides the Simple route.
New tasks reference the
resolved absolute skill path, so project installation works across worker
checkouts without requiring a global copy.

- Codex invocation: `$herdr`; worker brief: `$herdr (/absolute/path/herdr/SKILL.md)`.
- AGY/Claude invocation: `/herdr`; worker brief includes the same absolute path.
- Nontrivial AGY briefs begin `/teamwork-preview /herdr (absolute path)`.
- To request Advanced, say so explicitly and choose Codex/Claude plus effort for
  its one manager. Parallel work alone stays in Simple.

Fixed model profiles are pack defaults, subject to the installed runtime/account.
A rejected profile is reported rather than silently replaced. Live TUI behavior,
including optional Codex Tab queueing, needs verification on the installed build.

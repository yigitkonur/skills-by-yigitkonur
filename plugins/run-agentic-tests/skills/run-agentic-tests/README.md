# run-agentic-tests

Orchestrating multi-agent E2E campaigns with independent evidence review, isolated runtimes, and defect fix/retest loops.

**Category:** testing

One self-contained skill provides twelve focused roles, a Node.js bookkeeping
CLI, strict YAML records, immutable evidence, and a static HTML report. It uses
your host's native isolated agents and available browser, CLI, MCP, or mobile
tools. Node.js 22 or newer is required; `yq` is an optional query tool.

## Install

**As a Claude Code plugin:**

```
/plugin marketplace add yigitkonur/skills-by-yigitkonur
/plugin install run-agentic-tests@yigitkonur
```

**As a Codex plugin:**

```bash
codex plugin marketplace add yigitkonur/skills-by-yigitkonur
```

Then install `run-agentic-tests@yigitkonur` from `/plugins`.

**With the `skills` CLI:**

1. **Project-level install (recommended & PromptScript-compatible):**
   Installs into `./.agents/skills` for your active project.

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-agentic-tests -y

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y
   ```

   PromptScript projects can import directly:

   ```bash
   prs skills add github.com/yigitkonur/skills-by-yigitkonur/skills/run-agentic-tests/SKILL.md
   ```

2. **Global install (user-level):**
   Installs into `~/.agents/skills` for universal agents.

   ```bash
   # This skill only
   npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-agentic-tests -y -g -a universal

   # Or the full pack
   npx -y skills add yigitkonur/skills-by-yigitkonur -y -g -a universal
   ```

## Use

Ask your agent to use `run-agentic-tests` for an E2E campaign, or to resume an
existing campaign directory. Read [SKILL.md](SKILL.md) for the role router and
[CLI instructions](references/cli-and-yq.md) for setup. Existing approved
scenarios are imported before new scope is proposed. Submission acceptance,
evidence review, and current-target PASS are distinct results.

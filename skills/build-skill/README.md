# build-skill

Synthesize, refactor, and audit Agent Skills adhering strictly to the open [Agent Skills Specification](https://agentskills.io/specification). Built on empirical research, progressive disclosure, deterministic Node.js (`.mjs`) / Python scripting, and verified domain context.

**Category:** productivity

## Prerequisites & Installation

Quality skills require verified ground truth. This skill works alongside and requires **`run-research`**:
- **Companion Skill**: [`skills/run-research`](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/run-research)
- **Install both skills:**

```bash
# Project-level install (recommended)
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/build-skill -y
npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-research -y

# Or install the complete collection
npx -y skills add yigitkonur/skills-by-yigitkonur -y
```

## Core Operational Modes

1. **Discovery Mode**: Search `skills.sh` registry via `scripts/skill-dl.mjs`, delegate parallel sub-agents to summarize candidate skills, form a consortium of patterns, and build a pre-implementation comparison table.
2. **Creation & Distillation Mode**: Synthesize findings into repo-fit conventions, draft clean progressive disclosure boundaries (`SKILL.md` < 500 lines, bulky content in `references/`), and implement deterministic logic in `scripts/`.
3. **Conversation-Driven Mode**: Ingest in-flight high-token sessions (e.g. 200k–400k tokens), extract reusable patterns, produce a 5-level nested list of actions/confessions linking to agent memory, and script-ify deterministic steps.
4. **Pure Documentation / Framework Mode**: Ingest an external repo or framework via `run-research` and generate hundreds of atomic reference blocks with actionable "do this, do that" instructions.

## Included Scripts

- **`scripts/skill-dl.mjs`**: Portable Node.js ES Module for multi-query consensus discovery, batch skill downloading, and specification compliance auditing.
- **`scripts/skill-research.mjs`**: End-to-end automated research pipeline runner.

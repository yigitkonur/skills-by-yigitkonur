# Research Workflow for Skill Synthesis

Research is mandatory before skill synthesis. You cannot create a qualified skill without verified domain context.

## Mandatory Prerequisite: `run-research`

This workflow strictly requires the **`run-research`** skill to be installed and available:
- **Repository URL**: [skills/run-research](https://github.com/yigitkonur/skills-by-yigitkonur/tree/main/skills/run-research)
- **Install command**: `npx -y skills add yigitkonur/skills-by-yigitkonur/skills/run-research -y`

> **Standing Invariant**: Never draft a skill based on LLM memory, assumptions, or generic training data alone. When non-trivial APIs, frameworks, or workflows are involved, invoke `run-research` to gather authoritative documentation, code examples, and verified quotes. If `run-research` is not available, install it before proceeding.

## When Remote Research is Mandatory

Run the research phase when any of these conditions are met:
1. Creating a new skill from scratch
2. Substantially redesigning or refactoring an existing skill
3. Merging patterns from multiple skills or disparate source corpora
4. The local workspace has thin, unverified, or outdated documentation
5. The user asks for a skill covering an external library, framework, or CLI

## Phase 1 — Inspect the Local Workspace First

Before looking outward, capture the local baseline:
1. Generate a tree-style directory listing of the target workspace.
2. Read project config files (`package.json`, `tsconfig.json`, `pyproject.toml`, etc.).
3. Identify existing skills in `.agents/skills/` or `skills/` to inherit repository naming and formatting conventions.

## Phase 2 — Discovery Mode & Consortium Gathering

1. **Multi-Query Consensus Search**:
   Run discovery across the canonical `skills.sh` registry using `scripts/skill-dl.mjs`:
   ```bash
   node scripts/skill-dl.mjs search "typescript" "mcp" "testing" --top 10
   ```
2. **Subagent Consortium Delegation**:
   For complex topics, delegate exploration across up to 3–5 parallel subagents:
   - *Subagent 1 (Specification & Standards)*: Verify official schemas, RFCs, and API docs via `run-research`.
   - *Subagent 2 (Registry & Ecosystem)*: Inspect top-ranked skills on `skills.sh` for existing patterns.
   - *Subagent 3 (Edge Cases & Failure Modes)*: Investigate known issues, migration traps, and gotchas via GitHub / web search.
3. **Download Selected Candidates**:
   Download high-signal skills to an isolated corpus:
   ```bash
   node scripts/skill-dl.mjs download anthropics/skills/mcp-builder -o ./research-corpus
   ```

## Phase 3 — Corpus Inspection & Evidence Extraction

For each downloaded skill:
1. Run `node scripts/skill-dl.mjs inspect ./research-corpus/<skill>` to audit line counts, frontmatter spec compliance, and structure.
2. Read the `SKILL.md` body to understand its decision rules and workflow structure.
3. Check `scripts/` to identify deterministic automation that can be inherited as `.mjs` or `.py` scripts.
4. Tree `references/` to study progressive disclosure depth.

## Phase 4 — The Comparison Table

Construct a structured comparison table before drafting the target skill:

| Source | Focus | Strengths | Gaps & Pitfalls | Inherit / Avoid Decisions |
|---|---|---|---|---|
| `anthropics/mcp-builder` | MCP server construction | Clean FastMCP & TS SDK patterns | Missing automated client test loop | Inherit: FastMCP defaults. Avoid: inline XML prompt templates |

Every row must culminate in a concrete decision, not merely an observation.

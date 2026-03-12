# Steering Experiences

Common mistakes agents make when executing the `init-agent-config` skill, observed during structured derailment testing on real repositories. Each pattern includes the trigger condition, the mistake, why it happens, and the correct behavior.

## How to use this file

Read this file when you notice yourself doing something that feels uncertain or template-like. Each steering pattern has a trigger condition -- if the trigger matches your situation, follow the corrective action.

---

## S-01 -- Phantom directory references

**Trigger:** You are writing a CLAUDE.md thin wrapper.

**Mistake:** Referencing `.claude/rules/` in the thin wrapper even though the directory does not exist and you are not creating any rules files.

**Why it happens:** Templates and examples show `.claude/rules/` as a standard part of the thin wrapper. Agents copy the line without checking if the directory exists.

**Correct behavior:** Only reference `.claude/rules/` if (a) the directory already exists in the repo, or (b) you are creating rule files as part of this session. The canonical thin wrapper in Step 3 of SKILL.md includes a conditional comment -- follow it.

---

## S-02 -- Over-inspection

**Trigger:** You are in Step 2 (inspection) and have already found commands, stack info, and conventions.

**Mistake:** Continuing to read every file in the repo looking for more evidence, reading deep into source code, or exploring test files extensively.

**Why it happens:** "Read only enough to ground the config" does not define when "enough" is reached. Agents default to exhaustive reading.

**Correct behavior:** Stop after Tier 3 if you have (1) verified commands, (2) identified non-obvious conventions, and (3) found architecture boundaries. Only proceed to Tier 4 if a specific convention needs code-level evidence. The stopping condition is: "no new actionable facts from the last tier."

---

## S-03 -- Template-first drafting

**Trigger:** You are about to start drafting and find yourself opening `project-templates.md` before finishing inspection.

**Mistake:** Selecting a template first, then trying to fill it in with repo facts. This leads to including template sections that do not apply and missing sections that do.

**Correct behavior:** Complete Steps 1-2 (scope + inspect) first. Only then consult `project-templates.md` to find the closest match. Customize the template to fit the repo -- strip sections that do not apply, add sections for repo-specific concerns.

---

## S-04 -- Monorepo false positive

**Trigger:** The repo has a single `package.json` without workspaces, but has multiple directories.

**Mistake:** Applying monorepo rules (nested AGENTS.md, workspace protocol, per-package instructions) to a single-package project just because it has a `src/` and `tests/` directory.

**Why it happens:** The monorepo rule does not explicitly gate on workspace configuration. Agents see multiple directories and assume monorepo.

**Correct behavior:** Check for workspace config (`workspaces` in package.json, `pnpm-workspace.yaml`, `nx.json`, `lerna.json`) before applying monorepo rules. A single package.json without workspaces is a standard project, not a monorepo.

---

## S-05 -- README content copying

**Trigger:** You found useful context in README.md.

**Mistake:** Copying README sections (project description, installation steps, architecture diagrams) into AGENTS.md. This wastes context budget and duplicates content.

**Why it happens:** README has good information and agents want to be thorough.

**Correct behavior:** Reference README -- `"See README.md for project overview"`. Only extract facts that agents would not reliably infer from reading the README themselves: non-obvious conventions, commands with specific flags, or WHY context behind decisions.

---

## S-06 -- Missing WHY for non-obvious decisions

**Trigger:** You are documenting a non-obvious technical choice (e.g., using sessions instead of JWT, choosing a specific ORM, preferring a non-standard directory layout).

**Mistake:** Documenting only WHAT (the choice) without WHY (the reasoning). This causes agents to "improve" the decision by suggesting the more common alternative.

**Correct behavior:** Pair every non-obvious WHAT with a brief WHY:

```markdown
## Auth
Sessions, not JWT -- SSR requires server-readable auth state, no mobile clients planned.
```

---

## S-07 -- Scope creep in file creation

**Trigger:** You are working on a simple project (single service, no monorepo, straightforward stack).

**Mistake:** Creating `.claude/commands/`, `.claude/agents/`, `agent_docs/`, nested AGENTS.md files, or elaborate `.claude/rules/` hierarchies for a project that only needs a single AGENTS.md and maybe a thin CLAUDE.md wrapper.

**Why it happens:** Agents want to demonstrate knowledge of the full feature set. The skill does not explicitly gate file creation on project complexity.

**Correct behavior:** Match file complexity to project complexity. For simple projects: root AGENTS.md + thin CLAUDE.md wrapper is usually sufficient. Add `.claude/rules/` only if the project has genuinely distinct code areas needing path-scoped instructions (3+ rules for a specific path).

---

## S-08 -- Invented commands

**Trigger:** You need to document build/test/lint commands but are not sure of exact syntax.

**Mistake:** Guessing at commands based on the framework (e.g., writing `npm test` when the project uses `pnpm`, or `pytest` when tests use a custom runner).

**Correct behavior:** Verify every command against `package.json` scripts, `Makefile` targets, `pyproject.toml` scripts, or CI workflows. If you cannot verify a command, write `"Test: see package.json scripts"` or mark it as `[unverified]`. Never invent commands.

---

## S-09 -- Generic best practices

**Trigger:** You are writing conventions for the config file.

**Mistake:** Including generic advice like "write clean code", "follow SOLID principles", "use meaningful variable names". These are noise -- agents ignore them because they are too vague to act on.

**Correct behavior:** Every convention must be specific, measurable, and project-specific:

- Bad: "Write clean code"
- Good: "No `any` types without justification comment"
- Bad: "Follow best practices for error handling"
- Good: "Use Result type, not exceptions -- see `src/lib/result.ts`"

---

## S-10 -- Linter rule duplication

**Trigger:** You see the project has ESLint, Prettier, Ruff, Clippy, or similar tooling.

**Mistake:** Documenting linter-enforced rules in AGENTS.md (e.g., "use semicolons", "indent with 2 spaces", "no unused variables").

**Why it happens:** These feel like important conventions, and agents think documenting them is helpful.

**Correct behavior:** If a linter enforces a rule, do not document it in AGENTS.md -- the linter will catch violations regardless. Exception: document only if agents might disable the rule: `"Never disable ESLint rules inline without justification"`.

---

## S-11 -- Audit step on new setups

**Trigger:** You are creating config for a repo that has no existing agent configuration.

**Mistake:** Running Step 6 (Audit or migrate) on a greenfield project, which wastes time looking for existing config to audit.

**Correct behavior:** Skip Step 6 entirely for new setups. Go directly from Step 5 (scope and disclosure) to Step 7 (validate). Step 6 is only for repos with existing config that needs improvement.

---

## S-12 -- Unknowns buried in files

**Trigger:** You have unresolved questions or unverified assumptions about the repo.

**Mistake:** Embedding unknowns as comments or notes inside the generated AGENTS.md or CLAUDE.md files, cluttering the config with non-actionable content.

**Correct behavior:** Call out unknowns in your response to the user, not in the generated files. Agent config files should contain only verified, actionable instructions. Your response text is the right place for caveats, questions, and follow-up suggestions.

---

## S-13 -- Thin wrapper template conflicts

**Trigger:** You see different thin wrapper examples in SKILL.md, writing-guidelines.md, and project-templates.md.

**Mistake:** Using a thin wrapper template from a reference file that conflicts with the canonical template in Step 3.

**Why it happens:** Multiple files show thin wrapper examples with slightly different content (some include `.claude/rules/` unconditionally, some add different Claude-specific lines).

**Correct behavior:** Step 3 of SKILL.md is the canonical thin wrapper template. Reference file examples are project-type customizations, not replacements. When in doubt, use Step 3's template and customize from there.

---

## Summary table

| ID | Pattern | Trigger | Key correction |
|----|---------|---------|----------------|
| S-01 | Phantom directory refs | Writing thin wrapper | Only ref `.claude/rules/` if it exists or you create it |
| S-02 | Over-inspection | Still reading after Tier 3 | Stop when no new actionable facts |
| S-03 | Template-first drafting | Opening templates before inspecting | Inspect first, then match template |
| S-04 | Monorepo false positive | Single package.json, no workspaces | Check for workspace config first |
| S-05 | README copying | Found useful README content | Reference README, don't copy |
| S-06 | Missing WHY | Documenting non-obvious choice | Pair WHAT with WHY |
| S-07 | Scope creep | Simple project, many files | Match file complexity to project complexity |
| S-08 | Invented commands | Unsure of exact syntax | Verify or mark `[unverified]` |
| S-09 | Generic best practices | Writing conventions | Specific, measurable, project-specific |
| S-10 | Linter rule duplication | Project has linter | Don't document linter-enforced rules |
| S-11 | Audit on new setup | No existing config | Skip Step 6 for greenfield |
| S-12 | Unknowns in files | Unresolved questions | Call out in response, not in files |
| S-13 | Template conflicts | Multiple thin wrapper examples | Step 3 is canonical |

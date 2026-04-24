---
name: init-agent-config
description: "Use skill if you are creating, auditing, or migrating AGENTS.md-first repo instructions, REVIEW.md standards, folder-scoped guidance, and companion agent entrypoints for multi-agent coding workflows."
---

# Init Agent Config

Build AGENTS-first instruction systems from repo evidence. `AGENTS.md` is the source of truth for how agents should work. `REVIEW.md` is the standardization layer for what changes should be scrutinized or blocked during review. Explore the repository in waves, write root plus folder-scoped `AGENTS.md` files, then finish with a repo-grounded review context layer and any needed native adapters.

Default Claude compatibility model: every finalized `AGENTS.md` gets a sibling `CLAUDE.md` symlink. If the environment cannot preserve symlinks, fall back to a one-line wrapper and call out the exception in your response.

## Use this skill for

- creating new root and folder-scoped `AGENTS.md` files from real repo evidence
- creating or tightening a repo-grounded `REVIEW.md` standardization layer after the AGENTS hierarchy is done
- auditing or tightening existing agent instructions before rewriting them
- migrating `CLAUDE.md`, `.cursorrules`, Copilot, Gemini, or mixed agent config into an AGENTS-first layout
- building nested instruction boundaries for `src/`, packages, apps, services, or docs areas
- coordinating multi-agent exploration before instruction writing

## Do not use this skill for

- reviewing a PR directly
- writing generic "AI coding guidelines" without inspecting a real repository
- runtime subagent orchestration unrelated to repo instruction files -> use the matching orchestration skill

## Review context and native adapters

The main job is still AGENTS standardization, but every finished repo should also get a review-context layer. Treat `REVIEW.md` as mandatory. Treat platform-native review adapters as configurable last-step outputs driven by the completed `AGENTS.md` + `REVIEW.md` pair.

Keep the split clear:

| Surface | Purpose | Default status |
|---------|---------|----------------|
| `AGENTS.md` | How agents should work, where code lives, what local boundaries exist | Required |
| `REVIEW.md` | What diffs should be flagged, protected, or held to a higher bar | Required |
| Copilot files | GitHub Copilot review-specific adapters | Configurable final step |
| Devin files | Devin Bug Catcher review adapters and scoped review surfaces | Configurable final step |
| Greptile files | Greptile review adapters and context files | Configurable final step |

Quick boundary:
- `AGENTS.md` = how to work
- `REVIEW.md` = what to scrutinize in changes
- native review adapters = platform-specific translations of the review context

## Non-negotiables

- Inspect the repository before drafting anything.
- `AGENTS.md` comes first. Agent-specific files come after the AGENTS hierarchy exists.
- `REVIEW.md` comes after the AGENTS hierarchy, not before it.
- Do not ask about Copilot, Devin, or Greptile adapters until both the `AGENTS.md` hierarchy and `REVIEW.md` are complete.
- Every project should leave this skill with a useful review-context layer, even if it never adopts a PR review tool.
- Native review adapters are configurable last-step outputs, not the default deliverable.
- Use wave-based discovery: broad architecture first, folder architecture second, writing only after both waves are merged.
- If the environment supports explorer subagents, use up to 10 across the discovery waves.
- Explorer prompts must be substantive: minimum 500 words, maximum 2500 words.
- Writer prompts may be more detailed, but cap them at 5000 words.
- Default folder rule: create root `AGENTS.md` plus a local `AGENTS.md` for each meaningful `src` subfolder discovered in Wave 2. If a `src` tree has first-level folders, each first-level folder should end with its own `AGENTS.md` unless repo evidence proves there is no distinct workflow there.
- Every folder-level `AGENTS.md` must answer the question: `What does a coder working in this folder need to know to avoid mistakes here?`
- The root `REVIEW.md` must answer: `What kinds of changes should be flagged or scrutinized because they break this repo's intended standards or risk boundaries?`
- After each `AGENTS.md` is finalized, create sibling `CLAUDE.md` as a symlink to it. If symlinks are impossible in the target environment, fall back to a one-line wrapper and call out the exception in your response.
- Verify commands and paths against real files; never invent them.
- Keep universal guidance in `AGENTS.md`. Keep agent-native syntax and features out of `AGENTS.md`.
- Keep review criteria in `REVIEW.md`. Do not hide diff-review rules inside `AGENTS.md` unless the repo already uses that pattern and you are preserving it intentionally.
- Complement existing config; do not blindly replace it.
- Preserve existing `Always`, `Ask`, `Never`, `WARNING`, `CRITICAL`, and `DO NOT` rules unless the repo proves they are obsolete.
- Prefer high-signal directives over long prose. If a line would not prevent a mistake, cut it from the config file (the instruction, not the repo).
- For existing files, output the audit/quality report before applying updates unless the user explicitly skips the audit phase.

## Anti-derail guardrails

- Do not write from templates before discovery is complete.
- Do not skip Wave 2 just because Wave 1 already found the stack.
- Do not let writer agents start from partial findings.
- Do not duplicate root rules in child `AGENTS.md` files.
- Do not let `REVIEW.md` turn into a second copy of `AGENTS.md`.
- Do not keep universal content trapped inside `CLAUDE.md` or any other agent-native file.
- Do not grow `CLAUDE.md` into a second source of truth. Keep Claude-only behavior in `.claude/` or other native surfaces.
- Do not create support files only because an agent supports them; create them only when discovery proves they are useful.
- Do not create shared defaults in `AGENTS.override.md` or `CLAUDE.local.md`; those are override/personal layers.
- If existing config is already mostly correct, switch from rewrite mode to audit/tighten mode.

## Workflow

### 1) Scope the request and current instruction surfaces

Classify the job before reading deeply.

| Request type | What to produce |
|-------------|-----------------|
| New setup | Fresh root and folder `AGENTS.md` hierarchy, then companion entrypoints |
| Audit | Quality report first, then targeted edits |
| Migration | Extract universal content into `AGENTS.md`, then re-home agent-specific behavior |
| Extension | Add missing folder files or companion entrypoints without rewriting everything |

Check which instruction surfaces already exist:
- `AGENTS.md`, nested `AGENTS.md`, `AGENTS.override.md`
- `REVIEW.md`, nested `REVIEW.md`
- `CLAUDE.md`, `.claude/`, `GEMINI.md`, `.gemini/`
- `.cursor/rules/`, `.cursorrules`, `.windsurfrules`
- `.github/copilot-instructions.md`
- `.greptile/`, `greptile.json`
- `README.md`, `CONTRIBUTING.md`, architecture docs

### 2) Build the folder map locally

Use the filesystem before dispatching explorers.

- Run `tree -d .` or `tree -dL 2 .` to map top-level and `src` folders.
- Mark candidate instruction boundaries: repo root, each `src/*`, each app/package/service root, and any docs/standards subtree with separate workflows.
- Decide which folders will get dedicated exploration coverage.
- Do not draft yet. This step exists so Wave 2 can be assigned cleanly.

### 3) Wave 1 exploration: broad architecture

Wave 1 answers the repo-wide questions before folder specialization begins.

**Goal**
- identify architecture shape, command sources, critical workflows, major boundaries, and existing instruction debt

**Agent count**
- 2 to 10 explorer agents, depending on repo size and how many independent questions exist

**Required outputs**
- repo-wide command sources and verified entrypoints
- top-level architecture map
- existing instruction files and conflicts
- candidate folders that need their own `AGENTS.md`
- candidate folders that may need scoped `REVIEW.md`
- risks, unknowns, and questions to resolve in Wave 2

**Wave 1 prompt template**
Use a 500-2500 word prompt built from this scaffold:
```text
You are Wave 1 of an AGENTS-first repo-instruction discovery pass.

Mission:
Map the repository at a broad architectural level so the main agent can design an AGENTS.md hierarchy before any writing begins.

Repository:
- Root: <repo path>
- Current tree snapshot: <paste `tree -dL 2 .` or equivalent>
- Existing instruction surfaces: <list any AGENTS.md, CLAUDE.md, .claude, Copilot, Cursor, Gemini, README, CONTRIBUTING files already found>

What you must discover:
1. The repo's real command sources and which commands are verified versus missing.
2. The top-level architecture, major folders, and which areas appear to have distinct workflows or risks.
3. Existing agent-instruction files, duplicated guidance, stale guidance, or CLAUDE-first anti-patterns.
4. Which folders are strong candidates for local AGENTS.md files, especially under `src/`, `apps/`, `packages/`, `services/`, or similar roots.
5. What a future folder-level writer would need to know before drafting local instructions.
6. Which review-critical areas should later become the backbone of `REVIEW.md`.

How to work:
- Read only enough repo evidence to support claims.
- Separate documented facts from inference.
- Cite exact file paths for every important claim.
- Call out conflicts between files.
- Do not write AGENTS.md yet.
- Do not propose generic best practices.
- Focus on information that prevents mistakes.

Deliverable:
Produce a concise architecture brief with:
- verified commands and their sources
- repo-wide boundaries
- candidate AGENTS.md folders
- candidate review-critical areas
- missing information that must be resolved in Wave 2
- risks if the main agent writes before deeper folder exploration
```

Wait for all Wave 1 findings. Compare overlap, contradictions, and gaps before moving on.

### 4) Wave 2 exploration: folder-specific deep dives

Wave 2 uses the folder map plus Wave 1 findings to inspect the inner folders that will actually receive local instructions.

**Trigger**
- launch only after Wave 1 has been merged and the main agent knows which folders need local coverage

**Assignment model**
- base assignments on `tree -d .` or `tree -dL 2 .`
- give each explorer one folder or one tightly-related cluster
- default coverage includes every meaningful `src` first-level subfolder

**Required outputs**
- folder-local commands or workflows
- local architecture and entry points
- conventions, risks, boundaries, and non-obvious WHY context
- exact recommendation for that folder's `AGENTS.md`
- exact recommendation for whether that folder needs scoped review guidance
- whether the folder needs additional agent-native files beyond the default `CLAUDE.md` symlink

**Wave 2 prompt template**
Use a 500-2500 word prompt built from this scaffold:
```text
You are Wave 2 of an AGENTS-first repo-instruction discovery pass.

Mission:
Investigate one subtree deeply enough that the main agent can write a local AGENTS.md for that folder without guessing.

Assigned subtree:
- Folder: <folder path>
- Parent/root context: <one paragraph from Wave 1 summary>
- Tree excerpt: <paste relevant lines from `tree -d .` or `tree -dL 2 .`>

What you must answer for this folder:
1. What does a coder working in this folder need to know before making changes here?
2. Which commands, entry points, or test workflows are local to this folder?
3. Which patterns are non-obvious and would cause mistakes if omitted?
4. Which rules belong in the parent AGENTS.md instead of this folder file?
5. Which changes in this folder deserve special scrutiny in review?
6. Should this folder also receive a sibling `CLAUDE.md` symlink and any extra native agent files?

How to work:
- Read only files that materially improve the folder brief.
- Ground every rule in repo evidence.
- Prefer local conventions over generic advice.
- Distinguish facts from inference.
- Avoid repeating parent-level instructions unless the folder overrides them.
- Do not write the final AGENTS.md file. Hand the main agent the evidence needed to write it.

Deliverable:
Return a folder brief with:
- the folder's purpose
- local commands and boundaries
- non-obvious patterns plus WHY
- content that must appear in this folder's AGENTS.md
- content that must stay in the parent file
- content that should later shape the review-context layer
- unresolved unknowns that still block writing
```

Wait for all Wave 2 findings. Merge overlaps and resolve contradictions before writing.

### 5) Synthesize the AGENTS hierarchy before writing

Translate the discovery findings into a file plan.

- Root `AGENTS.md` carries repo-wide commands, architecture, shared conventions, and top-level boundaries.
- Each folder `AGENTS.md` carries only what is local to that subtree.
- Child files may assume the parent already provided global rules.
- If a folder needs only a small local delta, keep that file short rather than folding it back into the root.
- If a `src` folder has first-level subfolders, default to one local `AGENTS.md` per first-level subfolder.
- Each planned file should have a one-sentence purpose before writing begins.

### 6) Audit existing files before rewriting them

Use `references/audit-and-migration.md` when the repo already has agent instructions.

- find all existing instruction and wrapper files
- score them before editing
- show the report first
- then propose targeted changes, migrations, or deletions

Use this output structure for audit work:
1. `## Agent Instructions Quality Report`
2. summary counts and average score
3. file-by-file scores with concrete evidence
4. recommended changes
5. apply edits only after the report step unless the user explicitly waives it

### 7) Draft AGENTS.md files

Write the hierarchy from the top down.

- Use the WHAT / WHY / HOW filter from `references/agents-md-format.md`.
- Prefer direct instructions and measurable boundaries.
- Keep root and child files lean.
- Create a section only when 3+ repo-specific facts justify it.
- Ask while drafting: `Would a coder editing this folder make a mistake if this line were missing?`
- If the answer is no, cut the line.

### 8) Create companion entrypoints after AGENTS.md exists

After the AGENTS hierarchy is stable:

- create sibling `CLAUDE.md` as a symlink to the corresponding `AGENTS.md`
- if symlink creation is impossible, use a one-line wrapper:
  ```markdown
  @AGENTS.md
  ```
- keep Claude-only behavior in `.claude/` rather than expanding `CLAUDE.md`
- point Gemini, Copilot, Aider, Cursor, or other agent-native surfaces back to the AGENTS source of truth unless they genuinely need agent-only behavior

See `references/agent-entrypoints.md`.

### 9) Writer-agent pass

After both discovery waves are merged, the main agent may dispatch writers.

**Rules**
- writers get disjoint folder ownership
- writer prompts may be longer than explorer prompts, but must stay under 5000 words
- a writer prompt must include the relevant wave findings for that folder, the target file path, the parent-child boundary, and the question `What does a coder working in this folder need to know?`
- do not send a writer until the main agent has all needed context from both discovery waves

**Writer prompt scaffold**
Expand this scaffold with repo-specific findings, up to 5000 words:
```text
You are the writer for one folder in an AGENTS-first instruction hierarchy.

Ownership:
- Target file: <path/to/AGENTS.md>
- Folder scope: <folder>
- Parent instruction file: <parent AGENTS path>
- Companion entrypoint policy: create `CLAUDE.md` as a symlink to this AGENTS.md after the content is finalized

Context you must use:
- Repo summary from Wave 1: <insert synthesized summary>
- Folder brief from Wave 2: <insert subtree findings>
- Existing files to preserve or tighten: <list>
- Verified commands and paths: <list>

Writing objective:
Produce the smallest high-signal AGENTS.md that tells a coder working in this folder exactly what they need to know here and nothing they already know from the parent file.

Requirements:
- Keep only folder-local instructions.
- Preserve valid warnings and boundary rules.
- Ground every rule in evidence.
- Include commands only if they are verified and local to this folder.
- Do not duplicate parent instructions.
- Prefer imperative, measurable language.
- Call out non-obvious WHY context where it prevents mistakes.
- If the folder truly has minimal unique guidance, write a short local AGENTS.md rather than skipping the file.

Deliverable:
Return the final AGENTS.md content plus any notes the main agent needs before creating the companion `CLAUDE.md` symlink.
```

### 10) Generate the review-context layer

After the AGENTS hierarchy is written, draft the review-context layer from the same repo evidence.

**Purpose**
- standardize what kinds of diffs should be flagged
- encode repo-specific code standards that matter during review
- capture the places where AI agents may act outside intended architectural or safety bounds
- strengthen future AGENTS updates by forcing the repo's risk model to be explicit

**Default outputs**
- root `REVIEW.md`
- scoped `REVIEW.md` files only when a subtree has review risks or standards that diverge materially from the root

**Split of responsibility**
- `AGENTS.md` = how to work and where things belong
- `REVIEW.md` = what to flag, protect, or verify in diffs

**Review-writing rules**
- use repo evidence, not generic best practices
- keep rules specific, measurable, actionable, and semantic
- put highest-risk rules first
- skip anything already enforced by lint, format, or deterministic tooling
- prefer 5-10 strong rules over a long checklist
- use scoped `REVIEW.md` only when the root file would become contradictory or bloated

**Suggested section order for root `REVIEW.md`**
- `## Critical Areas`
- `## Security`
- `## Conventions`
- `## Performance`
- `## Patterns`
- `## Ignore`
- `## Testing`

**After drafting review context**
- compare it back against the AGENTS hierarchy
- if the review pass exposed missing boundaries or safety rules, update the relevant `AGENTS.md` files
- keep the two surfaces complementary rather than duplicative

### 11) Validate before finalizing

Check all of the following:

- root and folder `AGENTS.md` files exist where the wave plan said they should
- each created `CLAUDE.md` points to the correct sibling `AGENTS.md`, or the fallback wrapper is documented as an exception
- root `REVIEW.md` exists and reflects the repo's real risk areas
- scoped `REVIEW.md` files exist only where the repo truly needs them
- commands and paths are verified
- child `AGENTS.md` files do not restate root rules unnecessarily
- `REVIEW.md` rules are specific, reviewable, and not duplicates of linter rules
- agent-specific files do not become a second source of truth
- unresolved unknowns are called out in your response, not buried in the files

### 12) Final configurable step: ask which native review adapters to generate

Only after Step 11 passes, ask one concise question about platform adapters.

Use this exact question pattern:
`The AGENTS.md and REVIEW.md hierarchy is complete. Which native review adapters should also be generated for this repo: Copilot, Devin, Greptile, or none?`

Rules for this step:
- ask only after both AGENTS and REVIEW are done
- the generic review-context layer is not optional; only the platform adapters are configurable
- if the user says `none`, stop
- if the user names one or more platforms, generate the matching native adapter files in this same skill
- if the user says `all`, still confirm the repo actually uses them before writing files
- treat platform-native review files as translations of the completed review context, not as a separate source of truth

Adapter defaults:
- Copilot -> generate `.github/copilot-instructions.md` plus scoped `.github/instructions/*.instructions.md`; keep files below the platform limit and note base-branch behavior
- Devin -> keep `REVIEW.md` as the main review surface, add scoped `REVIEW.md` only where needed, and reuse the completed `AGENTS.md` hierarchy for coding behavior
- Greptile -> generate `.greptile/config.json` plus optional `rules.md` and `files.json`; keep `scope` as arrays, `ignorePatterns` as a newline string, and note source-branch behavior

## Steering experiences

These are common mistakes observed during real-world execution. See `references/agents-md-format.md` for the detailed authoring and derailment guidance behind them.

| ID | Pattern | Key correction |
|----|---------|----------------|
| S-01 | AGENTS-second drafting | Write `AGENTS.md` first, agent-native files second |
| S-02 | One-wave exploration | Complete both waves before writing |
| S-03 | Weak explorer prompts | Use 500-2500 word prompts with concrete deliverables |
| S-04 | Writer starts too early | Merge Wave 1 and Wave 2 before dispatching writers |
| S-05 | Missing folder coverage | Give each meaningful `src` subtree local instruction ownership |
| S-06 | Root duplication in child files | Keep child files local and lean |
| S-07 | Invented commands | Verify or mark `[unverified]` -- never guess |
| S-08 | Generic best practices | Every convention must be specific, measurable, project-specific |
| S-09 | Missing WHY for non-obvious decisions | Pair every non-obvious WHAT with a brief WHY |
| S-10 | Missing `CLAUDE.md` companion | Create the sibling symlink or call out the fallback exception |
| S-11 | Unknowns in files | Call out unknowns in response text, not inside config files |
| S-12 | Over-nesting without signal | Add local files only where the folder scope is real |

## Do this, not that

| Do this | Not that |
|--------|----------|
| Ground every rule in repo evidence | Paste a generic best-practices template |
| Verify commands in manifests, makefiles, or CI | Invent `test`, `lint`, or `build` commands |
| Put shared rules in `AGENTS.md` | Put agent-native syntax in `AGENTS.md` |
| Create `CLAUDE.md` after `AGENTS.md` is stable | Hand-maintain duplicate instructions in both files |
| Preserve existing warning/boundary rules during migration | Drop `Never` / `CRITICAL` rules because they feel repetitive |
| Use local `AGENTS.md` files for meaningful `src` subfolders | Stuff every package-specific rule into the root file |
| Point to existing docs for bulky detail | Copy `README.md` or API docs into agent config |
| Use templates only after both discovery waves | Fill a template before you know the repo shape |
| Build platform adapters from the completed `REVIEW.md` | Treat review tooling as disconnected from the repo's standardization layer |
| Mark unverified commands as `[unverified]` | Guess at command syntax |
| Create sections only when 3+ facts justify them | Add single-bullet sections to match a template |
| Call out unknowns in your response to the user | Embed unknowns as comments inside generated config files |

## Reference routing

Read the smallest reference set that unblocks the current decision:

| Need | Reference |
|-----|-----------|
| AGENTS authoring, folder scoping, WHAT/WHY/HOW, and derailments | `references/agents-md-format.md` |
| Companion entrypoints, review-context adapters, setup gotchas, cross-agent surfaces | `references/agent-entrypoints.md` |
| Auditing existing files, report format, and migrations | `references/audit-and-migration.md` |
| Starter templates for root and folder files | `references/project-templates.md` |

**Quick-start mapping**

| Situation | Start with | Then read |
|----------|------------|-----------|
| New repo with no agent files | `project-templates.md` | `agents-md-format.md` |
| Existing `CLAUDE.md`-only repo | `audit-and-migration.md` | `agent-entrypoints.md` |
| Monorepo or large `src/` tree | `agents-md-format.md` | `project-templates.md`, `agent-entrypoints.md` |
| Multi-agent team | `agent-entrypoints.md` | `agents-md-format.md` |
| Folder-level instruction writing | `agents-md-format.md` | `project-templates.md` |
| Existing noisy config | `audit-and-migration.md` | `agents-md-format.md` |
| AGENTS and REVIEW are done and the user wants Copilot, Devin, or Greptile adapters | `agent-entrypoints.md` | stay in this skill and generate them |

Start with one or two references. Expand only if the current task truly needs more detail.

## Final output expectations

When you generate or revise files, provide:

1. the chosen AGENTS hierarchy and why it fits the repo
2. the folder map or tree excerpt that drove the hierarchy
3. the audit report first when existing files were present
4. the review-context outputs and how they complement the AGENTS hierarchy
5. the created or updated files, including any symlinked companion entrypoints and configured review adapters
6. remaining unknowns or follow-up checks in your response text, not inside the instruction files

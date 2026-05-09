---
name: init-agent-config
description: "Use skill if you are creating, auditing, or migrating AGENTS.md-first repo instructions, review-context decisions, folder-scoped guidance, and companion entrypoints for multi-agent coding workflows."
---

# Init Agent Config

Build AGENTS-first instruction systems from repo evidence. `AGENTS.md` is the source of truth for how agents should work. `REVIEW.md` is the optional review-standardization layer for what changes should be scrutinized or blocked during review. Explore the repository in waves, write root plus folder-scoped `AGENTS.md` files, create companion entrypoints, decide the review-context layer, then finish with any requested native adapters.

Default Claude compatibility model: every finalized `AGENTS.md` gets a sibling `CLAUDE.md` symlink. If the environment cannot preserve symlinks, fall back to a one-line wrapper and call out the exception in your response.

## Use this skill for

- creating new root and folder-scoped `AGENTS.md` files from real repo evidence
- creating or tightening a repo-grounded `REVIEW.md` standardization layer after the AGENTS hierarchy is done
- auditing or tightening existing agent instructions before rewriting them
- migrating `CLAUDE.md`, `.cursorrules`, Copilot, Gemini, or mixed agent config into an AGENTS-first layout
- building nested instruction boundaries for `src/`, packages, apps, services, or docs areas
- coordinating multi-agent exploration before instruction writing

## Do not use this skill for

- creating or revising skills, frontmatter, reference routing, or skill packaging -> use `synthesize-skills`
- checking whether planned work is actually complete -> use `check-completion`
- reviewing a PR directly -> use `do-review`
- writing generic "AI coding guidelines" without inspecting a real repository
- runtime multi-agent orchestration unrelated to repo instruction files -> use `orchestrate-codex`

## Review context and native adapters

The main job is AGENTS standardization. Generate `REVIEW.md` by default for review-standardization runs or when repo evidence exposes review-critical risks. Skip it when the user requested only AGENTS migration or no shared review standard exists to encode. Treat platform-native review adapters as configurable final-stage outputs.

Keep the split clear:

| Surface | Purpose | Default status |
|---------|---------|----------------|
| `AGENTS.md` | How agents should work, where code lives, what local boundaries exist | Required |
| `CLAUDE.md` | Compatibility companion for each finalized `AGENTS.md` | Required symlink or wrapper |
| `REVIEW.md` | What diffs should be flagged, protected, or held to a higher bar | Default when in scope or evidence warrants it |
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
- Create or repair sibling `CLAUDE.md` companions after each finalized `AGENTS.md`.
- `REVIEW.md` comes after AGENTS and CLAUDE decisions, not before them.
- Create `REVIEW.md` by default for review-standardization work or when discovery finds repo-specific review risks; otherwise document why it was skipped.
- Do not ask about Copilot, Devin, or Greptile adapters until the `AGENTS.md` hierarchy and review-context decision are complete.
- Native review adapters are configurable last-step outputs, not the default deliverable.
- Use wave-based discovery: broad architecture first, folder architecture second, writing only after both waves are merged.
- If the environment supports explorer subagents, use up to 10 across the discovery waves.
- Explorer prompts must be substantive: minimum 500 words, maximum 2500 words.
- Writer prompts may be more detailed, but cap them at 5000 words.
- Default folder rule: treat each meaningful first-level `src/*` folder as a local `AGENTS.md` candidate. Create the file unless Wave 2 proves there is no distinct workflow, risk, or convention; then skip or collapse the guidance into the parent.
- Every folder-level `AGENTS.md` must answer the question: `What does a coder working in this folder need to know to avoid mistakes here?`
- When generated, the root `REVIEW.md` must answer: `What kinds of changes should be flagged or scrutinized because they break this repo's intended standards or risk boundaries?`
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

## Scripts

Resolve script paths relative to this skill directory.

| Script | Use when | Mutates |
|--------|----------|---------|
| `scripts/audit-agents-md.sh` | Step 1 audits existing instruction surfaces, line counts, companion status, native adapters, and duplicate-source risks. See `scripts/audit-agents-md.sh.md`. | No |
| `scripts/scaffold-agents-md.sh` | After discovery and file planning, emit one minimal root/folder `AGENTS.md` or `REVIEW.md` skeleton. See `scripts/scaffold-agents-md.sh.md`. | Only with explicit `--write` |

## Workflow

### 1) Scope the request and current instruction surfaces

Classify the job before reading deeply.

| Request type | Output contract |
|-------------|-----------------|
| New setup | Root and evidence-gated folder `AGENTS.md` hierarchy, sibling `CLAUDE.md` companions, review-context decision/output, then optional adapter question |
| Audit | Quality report first, then targeted edits to unstable files, companion status, and review-context gaps |
| Migration | Extract shared rules into `AGENTS.md`, move agent-native behavior out, preserve critical warnings, repair companions, and decide review context |
| Extension | Add missing folder files or entrypoints without rewriting stable root files; touch review context only when the new scope warrants it |

Check which instruction surfaces already exist:
- `AGENTS.md`, nested `AGENTS.md`, `AGENTS.override.md`
- `REVIEW.md`, nested `REVIEW.md`
- `CLAUDE.md`, `.claude/`, `GEMINI.md`, `.gemini/`
- `.cursor/rules/`, `.cursorrules`, `.windsurfrules`
- `.github/copilot-instructions.md`
- `.greptile/`, `greptile.json`
- `README.md`, `CONTRIBUTING.md`, architecture docs

For existing repositories, run `scripts/audit-agents-md.sh` or perform equivalent read-only checks before editing.

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

**Prompt scaffold**
Use the Wave 1 scaffold in `references/discovery-prompts.md`. Fill it with the repo path, tree snapshot, and existing instruction surfaces before dispatch.

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

**Prompt scaffold**
Use the Wave 2 scaffold in `references/discovery-prompts.md`. Fill it with the assigned subtree, parent context, and relevant tree excerpt.

Wait for all Wave 2 findings. Merge overlaps and resolve contradictions before writing.

### 5) Synthesize the AGENTS hierarchy before writing

Translate the discovery findings into a file plan.

- Root `AGENTS.md` carries repo-wide commands, architecture, shared conventions, and top-level boundaries.
- Each folder `AGENTS.md` carries only what is local to that subtree.
- Child files may assume the parent already provided global rules.
- If a folder needs only a small local delta, keep that file short rather than folding it back into the root.
- If a `src` folder has first-level subfolders, default to one local `AGENTS.md` per meaningful subfolder unless Wave 2 proves the local delta is empty.
- Each planned file should have a one-sentence purpose before writing begins.
- Use `scripts/scaffold-agents-md.sh` only after this file plan is known; never use it to invent structure before discovery.

### 6) Produce the audit report before rewriting existing files

Use `references/audit-and-migration.md` when the repo already has agent instructions.

- use the Step 1 surface audit as input
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

**Prompt scaffold**
Use the writer scaffold in `references/discovery-prompts.md`. Include the target file path, parent-child boundary, Wave 1 summary, Wave 2 folder brief, and verified commands.

### 10) Generate the review-context layer

After the AGENTS hierarchy is written, decide whether the same repo evidence warrants a review-context layer.

- Default to root `REVIEW.md` for review-standardization work or when discovery finds repo-specific risks worth encoding.
- Use scoped `REVIEW.md` only when a subtree has distinct review risks that would bloat or contradict the root.
- Keep `AGENTS.md` as operating guidance and `REVIEW.md` as diff scrutiny.
- If review drafting exposes a missing work boundary, update the relevant `AGENTS.md`.
- If `REVIEW.md` is intentionally skipped, state the reason in the final response.

See `references/review-context.md` for purpose, exceptions, section order, scoped review rules, and adapter relationships.

### 11) Validate before finalizing

Check all of the following:

- root and folder `AGENTS.md` files exist where the wave plan said they should
- each created `CLAUDE.md` points to the correct sibling `AGENTS.md`, or the fallback wrapper is documented as an exception
- root `REVIEW.md` exists and reflects the repo's real risk areas, or the skip reason is documented
- scoped `REVIEW.md` files exist only where the repo truly needs them
- commands and paths are verified
- child `AGENTS.md` files do not restate root rules unnecessarily
- `REVIEW.md` rules are specific, reviewable, and not duplicates of linter rules
- agent-specific files do not become a second source of truth
- unresolved unknowns are called out in your response, not buried in the files

### 12) Final configurable step: ask which native review adapters to generate

Only after Step 11 passes, ask one concise question about platform adapters.

Use this exact question pattern:
`The AGENTS.md hierarchy is complete and the REVIEW.md decision is recorded. Which native review adapters should also be generated for this repo: Copilot, Devin, Greptile, or none?`

Rules for this step:
- ask only after AGENTS is done and the review-context decision is complete
- if the user says `none`, stop
- if the user names one or more platforms, generate the matching native adapter files in this same skill
- if the user says `all`, still confirm the repo actually uses them before writing files
- treat platform-native review files as translations of the completed review context, not as a separate source of truth

Adapter defaults:
- Copilot -> generate `.github/copilot-instructions.md` plus scoped `.github/instructions/*.instructions.md`; keep files below the platform limit and note base-branch behavior
- Devin -> keep `REVIEW.md` as the main review surface, add scoped `REVIEW.md` only where needed, and reuse the completed `AGENTS.md` hierarchy for coding behavior
- Greptile -> generate `.greptile/config.json` plus optional `rules.md` and `files.json`; keep `scope` as arrays, `ignorePatterns` as a newline string, and note source-branch behavior

## Anti-Derail Table

Keep this short. Read `references/agents-md-format.md` for the full authoring, bloat, and derailment catalog.

| Derail | Correction |
|--------|------------|
| AGENTS-second drafting | Write `AGENTS.md` first, then companion/native files |
| One-wave exploration | Complete Wave 2 before writing folder files |
| Writer starts from partial findings | Merge both discovery waves before dispatch |
| Child file repeats root | Keep child files local and lean |
| Invented commands | Verify or mark `[unverified]` |
| `REVIEW.md` duplicates `AGENTS.md` | Keep operating guidance and diff scrutiny separate |
| Native file becomes source of truth | Symlink, wrap, or point back to AGENTS |

## Reference routing

Read the smallest reference set that unblocks the current decision:

| Need | Reference |
|-----|-----------|
| Wave 1, Wave 2, or writer prompt scaffolds | `references/discovery-prompts.md` |
| REVIEW.md purpose, exceptions, root/scoped split, and adapter relationships | `references/review-context.md` |
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

1. instruction hierarchy created or changed
2. repo evidence that drove the hierarchy
3. audit report before edits when existing files were present
4. review-context output or explicit reason it was not generated
5. companion entrypoint status for each finalized `AGENTS.md`
6. verification rung reached
7. unresolved unknowns outside generated files

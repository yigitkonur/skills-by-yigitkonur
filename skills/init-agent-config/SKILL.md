---
name: init-agent-config
description: "Use if creating, auditing, or migrating CLAUDE.md/AGENTS.md/REVIEW.md instruction files."
---

# Init Agent Config

AGENTS-first instruction hierarchies, built from real repo evidence. `AGENTS.md` is the source of truth for how agents work. `CLAUDE.md` is its sibling companion. `REVIEW.md` is the optional review-standardization layer. Native review adapters (Copilot, Devin, Greptile) are configurable last-stage outputs.

Default Claude compatibility: every finalized `AGENTS.md` gets a sibling `CLAUDE.md` symlink. If symlinks are impossible in the target environment, fall back to a one-line `@AGENTS.md` wrapper and call out the exception in your response.

## When to use

- *"set up CLAUDE.md / AGENTS.md for this repo"*
- *"init agent instructions"* / *"bootstrap agent config"*
- *"write a REVIEW.md"* / *"add review standardization"*
- *"migrate .cursorrules / Copilot / Gemini config to AGENTS.md"*
- *"audit our existing agent instructions"*
- *"add folder-scoped AGENTS.md under src/ / apps/ / packages/"*
- *"generate Copilot / Devin / Greptile review adapters"* (after AGENTS+REVIEW are done)
- *"clean up CLAUDE.md so Codex and Cursor can read it too"*

## Do NOT use for

- creating or revising **skills** themselves -> use `build-skill`
- checking whether planned work is actually complete -> use `audit-completion`
- reviewing a specific PR -> use `run-review` Mode A
- runtime multi-agent orchestration unrelated to instruction files -> use a multi-agent runtime orchestrator

## File responsibilities

Keep the split clear. One file = one purpose.

| Surface | Purpose | Default status |
|---------|---------|----------------|
| `AGENTS.md` | How agents should work, where code lives, what local boundaries exist | Required |
| `CLAUDE.md` | Compatibility companion for each finalized `AGENTS.md` | Required symlink or `@AGENTS.md` wrapper |
| `REVIEW.md` | What diffs should be flagged, protected, or held to a higher bar | Default when in scope or evidence warrants |
| Folder `AGENTS.md` | Local delta only — never restate root | Conditional on Wave 2 evidence |
| `.github/copilot-instructions.md` | Copilot review adapter | Configurable final step |
| Devin review files | Devin Bug Catcher adapters | Configurable final step |
| `.greptile/config.json` | Greptile review adapter | Configurable final step |

Quick boundary:

- `AGENTS.md` = how to work
- `REVIEW.md` = what to scrutinize in changes
- Native adapters = platform-specific translations of the review context

## Non-negotiables

Read these every run. They are the hard guardrails.

1. **Inspect the repo before drafting anything.** No template-first writing.
2. **AGENTS.md comes first.** Companion files (`CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*`) come after the AGENTS hierarchy exists.
3. **Sibling `CLAUDE.md` after each finalized `AGENTS.md`.** Symlink by default; `@AGENTS.md` wrapper only when symlinks are unsupported (call it out).
4. **`REVIEW.md` decision comes after AGENTS+CLAUDE.** Generate by default for review-standardization runs or when discovery exposes repo-specific risks; otherwise document why it was skipped.
5. **Native review adapters are the LAST step.** Do not ask about Copilot/Devin/Greptile until AGENTS+CLAUDE+REVIEW are complete.
6. **Wave-based discovery.** Wave 1 (broad architecture) → Wave 2 (folder deep dives) → write. Never skip Wave 2 just because Wave 1 found the stack.
7. **Folder rule.** Treat each meaningful first-level `src/*`, `apps/*`, `packages/*`, `services/*` folder as a local `AGENTS.md` candidate. Skip only when Wave 2 proves the local delta is empty.
8. **Verify commands and paths against real files.** Never invent. Mark `[unverified]` when you cannot confirm.
9. **Complement existing config; do not blind-replace it.** Preserve `Always`, `Ask`, `Never`, `WARNING`, `CRITICAL`, `DO NOT` rules unless the repo proves them obsolete.
10. **High-signal directives over prose.** If a line would not prevent a mistake, cut it.
11. **Audit report before edits** when existing files are present, unless the user explicitly waives it.

## Anti-derail guardrails

| Derail | Correction |
|--------|------------|
| Writing from templates before discovery is complete | Run Wave 1 + Wave 2; templates load only after the file plan exists |
| Skipping Wave 2 because Wave 1 found the stack | Wave 2 is mandatory before folder files |
| Writers start from partial findings | Merge both waves before writer dispatch |
| Child `AGENTS.md` repeats root rules | Keep child files lean — local delta only |
| `REVIEW.md` becomes a second copy of `AGENTS.md` | Operating guidance vs diff scrutiny — separate concerns |
| `CLAUDE.md` grows into a second source of truth | Symlink to `AGENTS.md`; Claude-only behavior lives in `.claude/` |
| Universal content trapped in `CLAUDE.md` or `GEMINI.md` | Promote it to `AGENTS.md` |
| Native adapter generated as the default deliverable | Adapters are configurable last-step outputs only |
| Shared defaults written into `AGENTS.override.md` or `CLAUDE.local.md` | Those are override/personal layers — not for shared defaults |
| Existing config is mostly correct and you rewrote it anyway | Switch to audit/tighten mode |

## Scripts

Resolve script paths relative to this skill directory.

| Script | Use when | Mutates |
|--------|----------|---------|
| `scripts/audit-agents-md.sh` | Step 1 audit of existing instruction surfaces, line counts, companion status, native adapters, duplicate-source risks. See `scripts/audit-agents-md.sh.md`. | No |
| `scripts/scaffold-agents-md.sh` | After discovery and file planning, emit one minimal root/folder `AGENTS.md` or `REVIEW.md` skeleton. See `scripts/scaffold-agents-md.sh.md`. | Only with explicit `--write` |

## Workflow

### 1. Scope the request

Classify before reading deeply.

| Request type | Output contract |
|-------------|-----------------|
| New setup | Root + evidence-gated folder `AGENTS.md` hierarchy, sibling `CLAUDE.md` companions, review-context decision/output, then optional adapter question |
| Audit | Quality report first, then targeted edits to unstable files, companion status, review-context gaps |
| Migration | Extract shared rules into `AGENTS.md`, move agent-native behavior out, preserve critical warnings, repair companions, decide review context |
| Extension | Add missing folder files or entrypoints without rewriting stable root files; touch review context only if new scope warrants |

Inventory existing instruction surfaces:

- `AGENTS.md`, nested `AGENTS.md`, `AGENTS.override.md`
- `REVIEW.md`, nested `REVIEW.md`
- `CLAUDE.md`, `.claude/`, `GEMINI.md`, `.gemini/`
- `.cursor/rules/`, `.cursorrules`, `.windsurfrules`
- `.github/copilot-instructions.md`
- `.greptile/`, `greptile.json`
- `README.md`, `CONTRIBUTING.md`, architecture docs

Run `scripts/audit-agents-md.sh` (or equivalent read-only checks) before editing anything.

### 2. Build the folder map locally

Use the filesystem before dispatching explorers.

- `tree -d .` or `tree -dL 2 .` to map top-level and `src` folders.
- Mark candidate instruction boundaries: repo root, each `src/*`, each app/package/service root, any docs/standards subtree with separate workflows.
- Decide which folders will get dedicated exploration coverage.
- Do not draft yet. This step exists so Wave 2 can be assigned cleanly.

### 3. Wave 1 — broad architecture

Goal: identify architecture shape, command sources, critical workflows, major boundaries, and existing instruction debt.

- Agents: 2 to 10 explorers depending on repo size and number of independent questions.
- Required outputs: repo-wide command sources, top-level architecture map, existing instruction conflicts, candidate folders for local `AGENTS.md`, candidate folders for scoped `REVIEW.md`, risks and unknowns to resolve in Wave 2.
- Prompt scaffold: Wave 1 section in `references/discovery-prompts.md`. Fill placeholders with repo path, tree snapshot, and existing instruction surfaces before dispatch.
- Explorer prompts: 500–2500 words.

Wait for all Wave 1 findings. Compare overlap, contradictions, gaps before moving on.

### 4. Wave 2 — folder-specific deep dives

Trigger only after Wave 1 is merged.

- Assignments: based on `tree -dL 2 .` plus Wave 1. Give each explorer one folder or one tightly-related cluster. Default coverage: every meaningful `src/` first-level subfolder.
- Required outputs: folder-local commands or workflows, local architecture and entrypoints, conventions and risks, exact recommendation for that folder's `AGENTS.md`, exact recommendation for whether the folder needs scoped review guidance, whether it needs additional native files beyond the default `CLAUDE.md` symlink.
- Prompt scaffold: Wave 2 section in `references/discovery-prompts.md`.

Wait for all Wave 2 findings. Merge overlaps and resolve contradictions before writing.

### 5. Synthesize the AGENTS hierarchy before writing

Translate findings into a file plan:

- Root `AGENTS.md` carries repo-wide commands, architecture, shared conventions, and top-level boundaries.
- Each folder `AGENTS.md` carries only what is local to that subtree.
- Child files may assume the parent already provided global rules.
- If a folder needs only a small local delta, keep that file short rather than folding back into root.
- Each planned file gets a one-sentence purpose before writing.
- Use `scripts/scaffold-agents-md.sh` only after the plan is set; never to invent structure.

### 6. Audit report before rewriting existing files

When the repo already has agent instructions, output the audit before edits.

Use `references/audit-and-migration.md`. Output structure:

1. `## Agent Instructions Quality Report`
2. summary counts and average score
3. file-by-file scores with concrete evidence
4. recommended changes
5. apply edits only after the report — unless the user explicitly waives it

### 7. Draft AGENTS.md files

Top-down. Use the WHAT / WHY / HOW filter from `references/agents-md-format.md`.

- Direct instructions, measurable boundaries.
- Keep root and child files lean.
- Create a section only when 3+ repo-specific facts justify it.
- Ask while drafting: *"Would a coder editing this folder make a mistake if this line were missing?"* If no, cut it.

### 8. Create companion entrypoints

After the AGENTS hierarchy is stable:

- Create sibling `CLAUDE.md` as a symlink to the corresponding `AGENTS.md`.
- If symlink creation is impossible, use a one-line wrapper: `@AGENTS.md`.
- Keep Claude-only behavior in `.claude/`, never expand `CLAUDE.md` into a second source of truth.
- Point Gemini, Copilot, Aider, Cursor, or other native surfaces back to the AGENTS source unless they genuinely need agent-only behavior.

See `references/agent-entrypoints.md` for the full support matrix and per-agent rules.

### 9. Writer-agent pass (optional)

After both discovery waves are merged, dispatch writers if the file plan is wide.

- Writers get disjoint folder ownership.
- Writer prompts may exceed explorer prompts but stay under 5000 words.
- Each writer prompt includes: target file path, parent-child boundary, Wave 1 summary, Wave 2 folder brief, verified commands, and the question *"What does a coder working in this folder need to know?"*
- Prompt scaffold: writer section in `references/discovery-prompts.md`.

### 10. Generate the review-context layer

After AGENTS is written, decide whether the same evidence warrants `REVIEW.md`.

- Default to root `REVIEW.md` for review-standardization work or when discovery finds repo-specific risks worth encoding.
- Use scoped `REVIEW.md` only when a subtree has distinct review risks that would bloat or contradict the root.
- Keep `AGENTS.md` as operating guidance and `REVIEW.md` as diff scrutiny.
- If review drafting exposes a missing work boundary, update the relevant `AGENTS.md`.
- If `REVIEW.md` is intentionally skipped, state the reason in the final response.

See `references/review-context.md` for purpose, exceptions, section order, scoped review rules, and adapter relationships.

### 11. Validate before finalizing

- Root and folder `AGENTS.md` files exist where the wave plan said they should.
- Each created `CLAUDE.md` points to the correct sibling `AGENTS.md`, or the fallback wrapper is documented as an exception.
- Root `REVIEW.md` exists and reflects real risk areas, or the skip reason is recorded.
- Scoped `REVIEW.md` files exist only where the repo truly needs them.
- Commands and paths verified.
- Child `AGENTS.md` files do not restate root rules unnecessarily.
- `REVIEW.md` rules are specific and reviewable, not duplicates of linter rules.
- Companion files do not become a second source of truth.
- Unresolved unknowns are called out in your response, not buried in the files.

### 12. Final configurable step — native review adapters

Only after Step 11 passes, ask one concise question:

> *The AGENTS.md hierarchy is complete and the REVIEW.md decision is recorded. Which native review adapters should also be generated for this repo: Copilot, Devin, Greptile, or none?*

- If the user says `none`, stop.
- If the user names platforms, generate the matching native adapter files in this same skill.
- If `all`, confirm the repo actually uses them before writing files.
- Treat platform-native review files as translations of the completed review context, not as a separate source of truth.

Adapter defaults:

- **Copilot** -> `.github/copilot-instructions.md` plus scoped `.github/instructions/*.instructions.md`; keep files below the platform limit and note base-branch behavior.
- **Devin** -> keep `REVIEW.md` as the main review surface; add scoped `REVIEW.md` only where needed; reuse the completed `AGENTS.md` hierarchy for coding behavior.
- **Greptile** -> `.greptile/config.json` plus optional `rules.md` and `files.json`; keep `scope` as arrays, `ignorePatterns` as a newline string, note source-branch behavior.

## Reference routing

Read the smallest reference set that unblocks the current decision.

| Need | Reference |
|------|-----------|
| Wave 1, Wave 2, or writer prompt scaffolds | `references/discovery-prompts.md` |
| `REVIEW.md` purpose, exceptions, root/scoped split, adapter relationships | `references/review-context.md` |
| AGENTS authoring, folder scoping, WHAT/WHY/HOW, derailment catalog | `references/agents-md-format.md` |
| Companion entrypoints, native review adapters, setup gotchas, cross-agent surfaces | `references/agent-entrypoints.md` |
| Auditing existing files, report format, migrations | `references/audit-and-migration.md` |
| Starter templates for root and folder files | `references/project-templates.md` |

### Quick-start mapping

| Situation | Start with | Then read |
|-----------|------------|-----------|
| New repo with no agent files | `references/project-templates.md` | `references/agents-md-format.md` |
| Existing `CLAUDE.md`-only repo | `references/audit-and-migration.md` | `references/agent-entrypoints.md` |
| Monorepo or large `src/` tree | `references/agents-md-format.md` | `references/project-templates.md`, `references/agent-entrypoints.md` |
| Multi-agent team (Codex + Cursor + Claude + Gemini) | `references/agent-entrypoints.md` | `references/agents-md-format.md` |
| Folder-level instruction writing | `references/agents-md-format.md` | `references/project-templates.md` |
| Existing noisy / duplicated config | `references/audit-and-migration.md` | `references/agents-md-format.md` |
| AGENTS+REVIEW done, user wants Copilot/Devin/Greptile adapters | `references/agent-entrypoints.md` | stay in this skill and generate them |

Start with one or two references. Expand only if the task truly needs more.

## Final output expectations

When you generate or revise files, return:

1. instruction hierarchy created or changed
2. repo evidence that drove the hierarchy
3. audit report before edits when existing files were present
4. review-context output, or explicit reason it was not generated
5. companion entrypoint status for each finalized `AGENTS.md`
6. verification rung reached
7. unresolved unknowns called out outside the generated files

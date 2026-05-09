# Prompt discipline — what every per-task prompt must carry

The prompt is the single lever between dispatch and result. A vague prompt with N parallel jobs becomes N times the waste. Every per-task prompt — exec, batch, single, or review — carries six sections. The four templates in `references/templates/` instantiate this skeleton; this file documents the contract.

## The six sections

```
# Intent

<one sentence; the gravitational center>

# Discovery — read first

- <path or concept 1> — <one-line reason>
- <path or concept 2> — <one-line reason>

# Constraints

- <hard fact 1>
- <hard fact 2>

# Success criteria

- <BSV criterion 1>
- <BSV criterion 2>

# Out-of-scope

- <explicit non-goal 1>
- <explicit non-goal 2>

# Failure protocol

If you cannot satisfy success criteria: <exact recovery instruction>.
```

The order matters. The agent reads top-down; placing Intent first keeps every subsequent section calibrated to it.

## Why each section

### Intent — one sentence, gravitational center

The agent self-corrects toward this throughout the task. If exploration drifts (codex starts refactoring adjacent files, reading meta-skills, or planning instead of doing), the Intent line pulls it back.

Bad: "Improve the auth subsystem." (too abstract; no clear stop signal)
Good: "Replace the legacy session-token format with the new prefixed-id format across the auth module." (specific; observable; a clear "done" exists)

### Discovery — concept, not query

Hint at understanding goals, not search queries. The agent picks the right grep / Glob / Read pattern.

Bad: "grep for `getUserSession` and read every match."
Good: "Trace the full auth lifecycle: how sessions are created, validated, refreshed, and expired. Pay attention to the per-tenant isolation in `lib/tenants.ts`."

Include AGENTS.md / CLAUDE.md / CONTRIBUTING.md (if present at repo root) — the agent reads these as the authority for repo-local conventions.

### Constraints — hard facts

These are walls. The agent treats Constraints as non-negotiable. Use Constraints for:
- Language strictness (`TypeScript strict + exactOptionalPropertyTypes`).
- Framework conventions (`use TanStack Query, follow existing return shapes`).
- Scope fences (`do NOT touch X`). Out-of-scope items also go in the dedicated section, but high-leverage scope fences belong here too.
- Multi-agent fences (`do NOT modify shared files in this fleet: prisma/schema.prisma, lib/query-keys.ts`).

Avoid:
- Soft language ("be careful", "use best practices", "make it clean") — these don't survive translation into code.
- Method prescriptions ("first do X, then Y, then Z") — caps quality at your imagination.

### Success criteria — BSV (binary, specific, verifiable)

Every line should be runnable as a check, not interpretable as "good enough."

Compliant:
- `tsc --noEmit` exits 0.
- `pnpm test` all pass.
- ≥ 3 commits on the branch.
- File `db/migrations/<timestamp>_add_users.sql` exists.
- Function `getUserSession()` in `lib/auth.ts` accepts `tenantId: string` as a parameter.
- `[ "$(wc -l < FILE)" -le 30 ]` is true (size-budget ceiling).
- Output file has exactly N lines (verify: `wc -l <file>` reports N).
- `grep -c '<pattern>' FILE` returns exactly N (presence-count ceiling/floor).

Non-compliant (banned):
- "Code is clean."
- "Performance is acceptable."
- "Error handling is good."
- "Tests are comprehensive."
- "Aim for ~20 lines" (soft target; codex anchors on the soft number and ignores the hard ceiling).
- "Keep it short" / "around N entries" (interpretable, not binary).

Size-budget anti-patterns (count-once is fragile):
- **Stating a count once is fragile.** If the deliverable is "exactly N rows", restate N in Constraints AND Success criteria AND Failure protocol. Single-shot LLMs lose count over long outputs; redundancy across three sections is cheap insurance.
- **Mixing soft target with hard ceiling.** Codex anchors on the soft target. State only the hard ceiling, e.g. `≤30 lines`, never `aim for 20`. Pick one number. State it three times.
- **Pair counts with executable checks.** `wc -l`, `awk NF` count, `grep -c` — give codex the exact command it must run before declaring success, and require the output in the success report.

### Out-of-scope — explicit non-goals

Codex defaults to "while I'm here, also fix...". Out-of-scope items prevent that drift. Two distinct patterns:

**Scope-fence** ("do NOT touch existing X"):
- Do NOT refactor unrelated functions in the same file.
- Do NOT update doc files unless explicitly asked.
- Do NOT add new dependencies.
- Do NOT modify the existing public API shape.
- Canonical test-fence (copy-paste when source edits should not touch tests): `Do NOT modify any file matching test/**, *.test.ts, *.spec.ts, __tests__/**, jest.config.*, vitest.config.*, *.test.go, *_test.py.`

**Categorical-exclusion** ("do NOT use language/feature Y at all"):
- Do NOT use any `<script>` tag. Do NOT use inline JavaScript event handlers. Do NOT use `javascript:` URLs. Do NOT use any framework — pure HTML+CSS only.
- Do NOT use `eval`, `Function`, or any dynamic code execution.
- Do NOT use external CDN imports — every byte of the deliverable must be in the file.

These two patterns read differently to codex. Scope-fence says "don't touch what already exists"; categorical-exclusion says "don't use this technique anywhere in the new work". Treating them as equivalent risks under-armed prompts for "build X without Y" missions. For categorical-exclusion, list every plausible loophole (`<script>` AND inline handlers AND `javascript:` URLs) — a single line is weaker than a triple-redundant ban.

The Out-of-scope section is the single most underrated leverage in the prompt. Skip it and codex inflates the diff 2-3x.

### Failure protocol — clean exit when stuck

The agent gets a deterministic recovery path:

```
If you cannot satisfy success criteria: stop, write a `.fleet-failure-<task-id>.md` in the worktree root with the reason, exit non-zero. Do not improvise. Do not partial-commit.
```

The `.fleet-failure-*.md` marker is read by `audit-fleet-state.py` and surfaces in the manifest as `last_error`. This makes failure observable without ambiguity.

**Failure protocol — mode-specific shapes.** The example above is exec-mode shape. Each mode has its own clean-exit signal that downstream tooling reads. **The per-mode template is authoritative for this section.** Do not generalize across modes:

| Mode | Failure signal | Reader |
|---|---|---|
| exec | `.fleet-failure-<task-id>.md` in the worktree root, exit non-zero | `audit-fleet-state.py` → manifest `last_error` |
| single | summary in the last-message (`-o`) file, exit non-zero | manifest `exit_code` + `-o` content |
| batch | 5-line "could not research" output (no marker file) | `audit-sizes.sh` flags below-floor outputs |
| review | single line `REVIEW_BLOCKED: <reason>` to stdout | `classify-review-feedback.py` |

When writing a prompt, copy the Failure protocol verbatim from the matching template; do not rewrite it from this doc's exec-mode example.

## SUBAGENT-STOP prefix (exec mode only)

Codex loads its own installed skills on every `codex exec`. Many of those skills (e.g. `superpowers:using-superpowers`) push agents toward planning meta-skills before any code is written. The SUBAGENT-STOP prefix is a hard signal that short-circuits this:

```
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES. DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY. THE TASK:
```

Use it for:
- Coding tasks in repos where codex's installed skills include planning skills.
- Any exec-mode task where you've seen agents waste 20+k tokens on rumination.

Skip it for:
- Research / non-coding tasks (the meta-skills aren't usually triggered).
- Non-repo cwd (codex doesn't load coding meta-skills there).

## Sizing

| Mode | Typical prompt length | Upper bound |
|---|---|---|
| exec | 30–80 lines | 150 lines |
| batch (per-template; per-input renders are similar size) | 30–80 lines | 100 lines |
| single | 50–200 lines (more autonomy → more guardrails) | 400 lines |
| review (round focus) | 30–60 lines | 100 lines |

If a prompt is over the upper bound, the task is probably two tasks; split.

## Anti-patterns

- "Be thorough" / "Use best practices" / "Make it clean" — banned. Soft language evaporates in code.
- Method prescriptions — `Use grep to find X, then modify Y, then run Z.` Caps quality at your imagination.
- Multiple Intent statements. One task, one Intent.
- Implicit Out-of-scope. Make it explicit; codex defaults to broad.
- Floor-style language ("at minimum N tests"). Use ceilings or specifics ("≥ 3 commits", not "minimum 5").
- Method-prescriptive Success criteria ("write the function in X style"). Specify what exists at the end, not how.

## Forensics

If a fleet's output quality is uneven across N parallel tasks, inspect the prompts:

```bash
# Are all prompts using the same template? (They should.)
for f in prompts/*.md; do head -3 "$f"; echo; done

# Are Intent lines specific? (They should be.)
grep -A 1 '^# Intent' prompts/*.md

# Are Out-of-scope sections present? (They should be.)
for f in prompts/*.md; do
    if ! grep -q '^# Out-of-scope' "$f"; then echo "MISSING: $f"; fi
done
```

A pattern of weak Intent lines or missing Out-of-scope sections explains uneven output. Re-render with the template explicitly enforced; the next run is cleaner.

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
- <out-of-scope: do NOT touch X / Y / Z>

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

Non-compliant (banned):
- "Code is clean."
- "Performance is acceptable."
- "Error handling is good."
- "Tests are comprehensive."

### Out-of-scope — explicit non-goals

Codex defaults to "while I'm here, also fix...". Out-of-scope items prevent that drift:

- Do NOT refactor unrelated functions in the same file.
- Do NOT update doc files unless explicitly asked.
- Do NOT add new dependencies.
- Do NOT modify the existing public API shape.

The Out-of-scope section is the single most underrated leverage in the prompt. Skip it and codex inflates the diff 2-3x.

### Failure protocol — clean exit when stuck

The agent gets a deterministic recovery path:

```
If you cannot satisfy success criteria: stop, write a `.fleet-failure-<task-id>.md` in the worktree root with the reason, exit non-zero. Do not improvise. Do not partial-commit.
```

The `.fleet-failure-*.md` marker is read by `audit-fleet-state.py` and surfaces in the manifest as `last_error`. This makes failure observable without ambiguity.

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

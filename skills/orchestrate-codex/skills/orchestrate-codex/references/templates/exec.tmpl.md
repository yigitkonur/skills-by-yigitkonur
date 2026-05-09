# Exec mode prompt template

Every task in an exec-mode fleet ships a prompt file shaped like this. The dispatcher reads `tasks.json`; for each entry the bash runner reads the prompt file at `entries[i].mode_state.prompt_file` and pipes it to `codex exec` via stdin.

The template prefix below is non-negotiable. Codex loads its own installed skills on every `codex exec`. Many of those skills push agents toward planning meta-skills before any code is written. The `SUBAGENT-STOP` prefix neutralizes that pull and saves 20–80k tokens of rumination per agent.

---

## Template

```
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES. DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY. THE TASK:

# Intent

<one sentence: what state should the codebase be in after this run>

# Discovery — read first

- <absolute or repo-relative path 1> — <one-line reason>
- <absolute or repo-relative path 2> — <one-line reason>
- AGENTS.md / CLAUDE.md / CONTRIBUTING.md (if present at the repo root)

# Constraints (hard facts, not preferences)

- <language strictness, e.g. TypeScript strict + exactOptionalPropertyTypes>
- <framework conventions, e.g. TanStack Query, follow existing return shapes>
- <out-of-scope: do NOT touch X / Y / Z>
- <one concern per commit>

# Success criteria

- `tsc --noEmit` exits 0
- `pnpm test` (or `vitest run`) all pass
- ≥ <N> commits on the worktree's branch
- <specific file/function exists with the documented shape>

# Failure protocol

If you cannot satisfy success criteria: stop, write a `.fleet-failure-<task-id>.md` in the worktree root with the reason, exit non-zero. Do not improvise. Do not partial-commit.
```

## Why each section

- **SUBAGENT-STOP prefix** — short-circuits codex's installed meta-skills (e.g. `superpowers:using-superpowers`) which would otherwise burn tokens on planning before the agent writes a line. The prefix is a hard signal; codex respects it across versions.
- **Intent** — the gravitational center. One sentence. The agent self-corrects toward this when exploration drifts.
- **Discovery** — concept-level guidance, not search-query guidance. The agent picks the right grep.
- **Constraints** — hard facts the agent treats as walls. Use this for "do NOT" rules.
- **Success criteria** — BSV (binary, specific, verifiable). Every line should be runnable as a check, not interpretable as "good enough."
- **Failure protocol** — gives the agent a clean exit when blocked. The `.fleet-failure-*.md` marker is read by `audit-fleet-state.py` and surfaces in the manifest as `last_error`.

## What to leave OUT

- "Be careful." "Use best practices." "Make it clean." None of these survive translation into code.
- Method prescriptions ("first do X, then run Y, then refactor Z"). Cap quality at the prompter's imagination.
- Multi-mission prompts. One task, one prompt file. If the work has two concerns, write two tasks.

## Sizing

Aim for under 50 lines per prompt. If a prompt is over 100 lines, the task is probably two tasks. Split.

# render-task-prompts.sh

Wrap raw description files (Linear tickets, GitHub issue bodies, design briefs, audit specs) into prompt files shaped for run-codex-1 `exec` or `single` mode. The runner pipes prompt files VERBATIM to `codex exec`; without the SUBAGENT-STOP prefix and the 6-section skeleton (Intent / Discovery / Constraints / Success criteria / Out-of-scope / Failure protocol), codex burns 20–80k tokens on meta-skill rumination before doing useful work. This helper performs that wrap once so operators stop hand-rewriting tickets.

## Inputs

```bash
bash render-task-prompts.sh INPUT_DIR OUTPUT_DIR \
  [--mode exec|single] [--prefix on|off] [--force]
```

| Arg / flag | Notes |
|---|---|
| `INPUT_DIR` | Directory containing one `*.md` file per task (raw content). |
| `OUTPUT_DIR` | Destination for rendered prompts. Created if missing. Same basename per file. |
| `--mode` | `exec` (default) or `single`. Drives prefix default + audit-style success-criteria addendum. |
| `--prefix` | `on` \| `off`. Force-toggle the SUBAGENT-STOP prefix. Defaults below. |
| `--force` | Overwrite existing `OUTPUT_DIR/<basename>.md` instead of emitting `[skip]`. |

### Prefix defaults

| Mode | Default | Override notes |
|---|---|---|
| `exec` | prefix **on** | `--prefix off` to skip (rare; almost always wanted in exec). |
| `single` | prefix **on**, except inputs containing `research` / `analysis` / `audit` (case-insensitive) → prefix **off** | `--prefix on` to force; `--prefix off` to force off regardless of content. |

### Audit-style addendum (exec only)

When `--mode exec` and the input file mentions `audit` / `report` / `findings` / `review` (case-insensitive), the rendered Success criteria appends the canonical commit instruction so the ≥1-commit success gate fires on findings-only tasks. Cross-referenced from `references/modes/exec.md` §"Audit-style / findings-only tasks".

## Outputs

- One file `OUTPUT_DIR/<basename>.md` per input.
- Stdout: `[render] <input> → <output>` per file written, `[skip] <output> (exists)` per existing file (no `--force`).

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Every file rendered or skipped |
| 1 | INPUT_DIR is missing / unreadable / contains no `*.md` files |
| 2 | Usage error (bad flag, missing arg, unknown mode/prefix value) |

## Common cases

### Case 1 — 5 Linear tickets in `tickets/`, exec fleet

```bash
bash scripts/render-task-prompts.sh tickets/ prompts/ --mode exec
# → 5 prompts/<ticket>.md files, each with SUBAGENT-STOP prefix + 6 sections.
# Edit any prompt to fill in Discovery / Constraints / Out-of-scope details
# the ticket body did not capture. Then dispatch:
node scripts/run-codex-1.mjs exec --tasks tasks.json
# (where tasks.json points at the rendered prompts via `prompt_file` per entry)
```

### Case 2 — 8 audit briefs, findings-only exec with auto-commit

```bash
bash scripts/render-task-prompts.sh briefs/ prompts/ --mode exec
# Inputs that mention "audit" / "report" / "findings" / "review" automatically
# get the canonical commit instruction appended to Success criteria. The
# fleet success gate (≥1 commit) now fires when codex writes the report
# AND commits it, instead of tripping `codex_exit_0_no_changes`.
```

## Transformation example

### BEFORE — `tickets/ticket-202.md`

```
LIN-202: audit the payment-retry queue for stuck items.

Look for jobs that have been retried >5 times. Produce a findings report
listing affected job ids, age, and last error class.
```

### AFTER — `prompts/ticket-202.md`

```
YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES. DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY. THE TASK:

# Intent

LIN-202: audit the payment-retry queue for stuck items.

Look for jobs that have been retried >5 times. Produce a findings report
listing affected job ids, age, and last error class.

# Discovery — read first

- <path 1> — <one-line reason>
- <path 2> — <one-line reason>
- AGENTS.md / CLAUDE.md / CONTRIBUTING.md (if present at the repo root)

# Constraints

- <hard fact the agent must respect>

# Success criteria

- <one verifiable check, e.g. `tsc --noEmit` exits 0>
- <one verifiable check, e.g. `pnpm test` passes>
- Write the findings/report to `audit/ticket-202.md` (or repo-appropriate path) and commit it with `git add audit/ticket-202.md && git commit -m '<descriptive subject>'` before exiting.

# Out-of-scope

- Do NOT touch unrelated files
- Do NOT add new dependencies unless explicitly requested

# Failure protocol

If you cannot satisfy success criteria: stop, write a `.fleet-failure-ticket-202.md` in the worktree root with the reason, exit non-zero. Do not improvise. Do not partial-commit.
```

The original ticket text lands inside `# Intent`. The other five sections start as one-line placeholders the operator can either edit or leave as defaults. The SUBAGENT-STOP prefix is the verbatim string from `references/templates/exec.tmpl.md`.

## When NOT to use it

- You already authored the prompts from scratch using the templates. Re-running this script over hand-authored prompts would produce double-wrapping / collisions; the script's `[skip]` guard prevents accidental overwrite, but `--force` would clobber. Don't.
- Your "tickets" are actually batch-mode template inputs (one prompt template fanned over N rows). That's `scripts/render-prompts.sh` (placeholder substitution), not this script (per-file wrapping). See `references/modes/batch.md`.
- The work is review mode — review uses native `codex exec review` with hardcoded flags; per-branch prompts are not configurable through the dispatcher (see SKILL.md "Known limitations" §review prompt-injection).

## Cross-links

- `references/templates/exec.tmpl.md` — canonical exec-mode template (the SUBAGENT-STOP prefix is lifted verbatim from here).
- `references/templates/single.tmpl.md` — single-mode template, including the "When to add the SUBAGENT-STOP prefix" decision rules this script encodes by default.
- `references/universal/prompt-discipline.md` — the 6-section skeleton in detail; what to fill in once the wrap exists.
- `references/modes/exec.md` §"Audit-style / findings-only tasks" — the canonical commit instruction the audit addendum injects.

## Idempotency

Re-running over an existing `OUTPUT_DIR` skips files (`[skip]` line). Use `--force` to overwrite. The script never deletes; it only writes new files or overwrites with `--force`.

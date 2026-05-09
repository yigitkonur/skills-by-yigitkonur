# Single mode prompt template

A single mission is a focused, observable, one-shot codex invocation. The template carries the same six sections as exec mode but does not need the SUBAGENT-STOP prefix unless the task is coding work in a repo where codex's installed meta-skills would interfere.

Use this template for: large refactors with live observability needed; research tasks too big for a single web search; one-shot code generations that benefit from JSONL event streaming via `codex-json-filter.sh`.

---

## Template

```
# Intent

<one sentence: the end-state to reach>

# Discovery — read first

- <path 1> — <reason>
- <path 2> — <reason>

# Constraints

- <hard facts the agent must respect>

# Output format (parseable deliverables only — JSON / YAML / CSV / fixed-shape markdown)

- The `-o` answer file's first byte must be the canonical opener (`<`, `{`, `---`, header row, first table row).
- The `-o` answer file's last byte must be the canonical closer (`>`, `}`, the final data row, EOF after the last value).
- No code fences (no triple-backticks, no ```json / ```yaml).
- No prose preamble or trailing commentary — output ONLY the artifact.
- Restate this in BOTH Constraints AND Success criteria; a single mention is fragile.

# Success criteria

- <specific deliverables>
- <verification commands the agent should run before finishing>

# Out-of-scope

- <explicit non-goals — Do NOT touch X / Y / Z>
- <categorical exclusions if any — Do NOT use language/feature Y at all>

# Failure protocol

If blocked: stop, summarize what was tried and what was discovered, exit non-zero with the summary in the last-message file.
```

## Structured-deliverable callout (JSON / YAML / CSV / fixed-shape markdown)

Single mode is the natural mode for one-shot structured outputs (config files, parseable tables, fixed-schema JSON). Codex writes its **final assistant message verbatim** to `-o`, so for parseable deliverables the prompt MUST forbid the natural reply pattern:

- Output ONLY the artifact. NO prose preamble. NO trailing prose. NO commentary.
- NO markdown fences (no triple-backticks, no ```json, no ```yaml).
- NO leading/trailing blank lines.
- The first byte of `-o` must be the first byte of the artifact (`{` for JSON, `---` or first key for YAML, header row for CSV, first table row for markdown).
- Validate post-run with the appropriate parser; the parser's exit code is the actual success rung, not byte count.

For fixed-N deliverables (10 rows, 30-line file, 5 entries), see `references/universal/prompt-discipline.md` §"Size-budget anti-patterns" — restate the count in Constraints AND Success criteria AND Failure protocol; a single mention is fragile.

## When the deliverable is N source-file edits, not a parseable artifact

Multi-file source refactors (instrument `lib/db.ts`, `lib/cache.ts`, `lib/queue.ts` with OTel spans; rename a symbol across 12 files; migrate a config call site) do NOT produce a single parseable artifact. The "first byte / canonical opener" structure above does not apply — there is no JSON / YAML / CSV to validate.

For these missions:

- Skip the canonical-opener and code-fence rules in the Output format section. They are noise here.
- Success is `(N target files modified) AND (post-verify cmd exit 0)`. Encode this as binary checks in Success criteria — e.g. `grep -l 'tracer.startSpan' lib/db.ts lib/cache.ts lib/queue.ts | wc -l` reports `3`; `pnpm typecheck` exits 0; `pnpm test` exits 0.
- The `-o` answer file is the agent's *summary* of what changed (which files, what shape), not the deliverable itself. Treat it as a hand-off log, not as a parseable contract. The operator reads it before merging.
- The actual deliverable is the diff on the worktree's branch — use `references/modes/exec.md` semantics: codex commits, post-verify runs, the success gate fires on (codex exit 0) ∧ (≥ 1 commit) ∧ (`-o` non-empty) ∧ (post-verify pass-or-not-run).

If the mission has both a parseable deliverable AND source edits (rare — e.g. "generate `openapi.yaml` AND wire it into the express app"), split into two missions; single mode runs each cleaner than one bundled prompt.

## When to add the SUBAGENT-STOP prefix

Add the prefix from `references/templates/exec.tmpl.md` when ALL of these hold:
- The task is coding work (writing/modifying source files), not research or analysis.
- The cwd is a git repo (`git rev-parse --is-inside-work-tree` exits 0).
- Codex's installed meta-skills include planning skills (visible in the early JSONL events as long `agent_message` items about planning before any `command_execution` event).

Skip the prefix when ANY of these hold:
- The mission is research, summarization, or non-coding.
- The cwd is not a git repo (codex doesn't load coding meta-skills there — confirmed by inspection of installed skill triggers).
- The deliverable is a single structured artifact (JSON config, markdown table, CSS file) where meta-skill triggers don't fire.

## What single mode unlocks vs exec mode

- One worktree (or no worktree) instead of N. Lower setup cost.
- Live JSONL stream piped through `codex-json-filter.sh` — the user sees `[CMD>]`, `[CMD✓]`, `[THINK]`, `[SAID]` lines as they happen.
- Pairs `--json` with `-o <file>`. The `-o` file is the source of truth for "did codex produce output" even if MCP servers cause JSONL events to drop silently.

## Sizing

Single-mission prompts can run longer (100–300 lines) because there's only one. The token cost per word is the same as exec mode but you only pay it once. The Discovery and Constraints sections often grow because the agent has more autonomy and needs more guardrails.

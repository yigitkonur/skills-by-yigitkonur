# run-codex-review.py

Wrapper around `node codex-companion.mjs review --json` (or `adversarial-review --json`) for one branch in one worktree. Runs the review synchronously, normalizes output to the JSON schema in `references/codex-review-contract.md`, writes the round log, and updates the manifest.

**This is the single entry point for "do one round of review on this branch".** Subagents call it once per round.

The wrapper invokes the OpenAI Codex Claude Code plugin's companion script — it discovers `codex-companion.mjs` automatically (version-agnostic), so no per-environment adjustment is required.

## Usage

```bash
# Default: native review (free-form text parsed via regex)
python3 scripts/run-codex-review.py --branch feat/foo --worktree /Users/.../wt-feat-foo

# Pick base branch
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --base canary

# Wall-clock cap (Codex review can hang on remote tools)
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --timeout 1500

# Adversarial mode — structured findings with severities critical|high|medium|low
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --mode adversarial

# Dry-run prints the resolved codex-companion.mjs path + the planned invocation
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --dry-run
```

## Behavior

1. Pre-flight: verify `--worktree` exists and is on `--branch`.
2. Discover `codex-companion.mjs` (env-var first, then `~/.claude/plugins/cache/openai-codex/codex/<latest>/`).
3. Invoke `node codex-companion.mjs <review|adversarial-review> --base <ref> --scope branch --json` synchronously inside the worktree.
4. Parse the JSON envelope:
   - **`review` mode**: extract `codex.stdout` (free-form text) and regex-parse `[severity] Title — file:line` items.
   - **`adversarial` mode**: read `result.findings[]` directly (structured; no regex).
5. Write `<rounds-dir>/<slug>.<round>.json` with the round-log schema.
6. Update the manifest entry's `last_review_id`, `last_review_at`, `last_status`, `rounds`, `head_sha_current`, and append a `round_history` entry.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--branch <b>` | required | Branch under review. Must match the worktree's HEAD. |
| `--worktree <path>` | required | Worktree directory; codex runs from here. |
| `--base <ref>` | `main` | Base ref for the diff. |
| `--mode review\|adversarial` | `review` | `review` = native (free-form text parsed); `adversarial` = adversarial-review (structured `findings[]`). |
| `--manifest <path>` | `<repo-root>/.codex-review-manifest.json` | Manifest to update. Defaults to repo-local (no `/tmp` cross-repo collisions). |
| `--rounds-dir <path>` | `<repo-root>/.codex-review-rounds/` | Round-log directory. Same defaulting logic. |
| `--output <path>` | (computed) | Override the round-log output path. If unset, computed from `<rounds-dir>` + branch slug + round number. |
| `--timeout <n>` | `1500` (25 min) | Wall-clock cap. On hang, exit 1 with `last_status: "timeout"` and `terminal_reason: "review-hang past wall-clock cap"`. |
| `--dry-run` | off | Resolve `codex-companion.mjs` path, validate worktree state, print the intended invocation. Don't run codex. |

## Exit codes

| Code | Meaning | Caller (subagent) action |
|---|---|---|
| `0` | Review available; round log written | Run `classify-review-feedback.py` next. |
| `1` | Timeout (wall-clock cap; manifest marked `timeout`) | Retry the round once; else mark FAILED. |
| `2` | Codex CLI failed (manifest marked `failed`) | Retry the round once; else mark FAILED. |
| `127` | Codex plugin not installed | Surface to user; install via Claude Code plugin manager. |

## Plugin discovery

The wrapper discovers `codex-companion.mjs` automatically:

1. **`${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs`** — set by Claude Code when the plugin is loaded in a live session.
2. **Latest version under `~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs`** — fallback for when the env var isn't set. Versions are sorted semver-ascending; the latest installed wins. Non-semver directory names sort first (so `1.0.4` beats `dev`).

If neither path resolves, the wrapper exits with code 127 and a message pointing at https://github.com/openai/codex-plugin-cc.

## Schema of the round-log JSON

Per `references/codex-review-contract.md`:

```json
{
  "review_id": "<codex thread id>",
  "branch": "feat/foo",
  "head_sha": "deadbeef1234...",
  "started_at": "2026-04-26T10:00:00Z",
  "finished_at": "2026-04-26T10:04:32Z",
  "raw_text": "<full Codex output verbatim>",
  "items": [
    { "id": "cdx-0", "severity_raw": "P1", "file": "src/foo.ts", "line": 42, "body": "..." }
  ]
}
```

In `review` mode, `items[]` is populated by regex-parsing `codex.stdout`. Token recognized in the severity slot: `P1` / `P2` / `P3` / `P4` / `critical` / `high` / `medium` / `low` (case-insensitive).

In `adversarial` mode, `items[]` is populated by mapping `result.findings[]`:
- `severity_raw` ← `severity` (`critical | high | medium | low`)
- `file` ← `file`
- `line` ← `line_start`
- `body` ← `title + body + recommendation` joined with blank lines

## codex-companion.mjs JSON shapes

`review --json`:
```json
{
  "review": "Review",
  "target": { "mode": "branch", "label": "...", "baseRef": "main" },
  "threadId": "...",
  "codex": { "status": 0, "stdout": "<free-form text>", "stderr": "...", "reasoning": null }
}
```

`adversarial-review --json`:
```json
{
  "review": "Adversarial Review",
  "result": {
    "verdict": "approve|needs-attention",
    "summary": "...",
    "findings": [
      { "severity": "critical|high|medium|low", "title": "...", "body": "...",
        "file": "src/foo.ts", "line_start": 42, "line_end": 42,
        "confidence": 0.0, "recommendation": "..." }
    ],
    "next_steps": [...]
  },
  "rawOutput": "...",
  "parseError": null
}
```

## Concurrency safety

`run-codex-review.py` is invoked **once per round per branch** by exactly **one subagent**. No file-locking on the round-log write (each round-log filename is unique by `slug.round.json`). Manifest updates use `tempfile + os.replace` for atomicity, but the protocol assumes one subagent per branch — concurrent invocations on the same branch are an error.

Multiple branches can be reviewed in parallel: each branch's invocation is independent. Parallelism comes from concurrent subprocesses, not from a `--background` flag (the companion's `review` and `adversarial-review` subcommands ignore `--background` — they always run synchronously).

## Sample output (success, native review)

```
running codex-companion review (sync) in /Users/.../wt-feat-foo ... timeout=1500s
  ✓ round log written: /Users/.../repo/.codex-review-rounds/feat-foo.03.json (items=4)
  ✓ manifest updated: rounds=3
```

## Sample output (timeout)

```
running codex-companion review (sync) in /Users/.../wt-feat-foo ... timeout=1500s
✗ codex review timed out after 1500s
```

(exit 1; manifest `last_status: "timeout"`, `terminal_reason: "review-hang past wall-clock cap"`)

## Sample output (plugin missing)

```
codex-companion.mjs not found. Install the OpenAI Codex Claude Code plugin
(https://github.com/openai/codex-plugin-cc) — expected at $CLAUDE_PLUGIN_ROOT/scripts/codex-companion.mjs
or at ~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs.
```

(exit 127; manifest `last_status: "plugin-missing"`)

## Failure modes

| Failure | Wrapper behavior | Recovery |
|---|---|---|
| Plugin not installed | Exit 127; `last_status: "plugin-missing"` | Install plugin; resume. |
| Worktree not on the right branch | Exit 2 with stderr; no manifest update | `git -C <wt> checkout <branch>`; retry. |
| codex-companion ran but exited non-zero with no stdout | Exit 2; `last_status: "failed"` | Subagent retries once. |
| codex-companion ran with non-zero exit but stdout has parseable JSON | Wrapper logs warning, normalizes anyway | Round log written; loop continues. |
| Wall-clock timeout | Exit 1; `last_status: "timeout"` | Subagent retries once OR mark FAILED. |
| Output doesn't match expected JSON envelope | Exit 0 with `items: []`, raw text in `raw_text` | Classifier falls back to regex over `raw_text`. |
| Branch HEAD changed mid-review | Not detected by wrapper; review may be stale | Subagent discards round, retries from current HEAD. |

## When to run

- Per round, by exactly one subagent per branch.
- Never invoke twice in parallel on the same branch (use a different worktree if you need parallel branches).

## Read/write surface

- **Reads**: `<worktree>/...`, manifest, the codex-companion script.
- **Writes**: `<rounds-dir>/<slug>.<round>.json` (new each round), manifest entry for this branch.
- **Does NOT**: push, commit, modify the worktree, open PRs, edit other branches' entries.

## See also

- `scripts/trigger-codex-rescue.py` — the Phase 6 sibling that wraps `codex-companion.mjs task --background` for the rescue review on an open PR.
- `references/codex-review-contract.md` — the round-log schema this wrapper produces.
- `references/event-driven-orchestration.md` — how main agent dispatches this wrapper in parallel across N branches via `Bash run_in_background`.

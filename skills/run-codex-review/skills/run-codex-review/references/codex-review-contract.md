# Codex Review Contract

`/codex:review` is the per-branch reviewer in this skill. It is a Claude Code slash command from the OpenAI Codex plugin (`openai-codex/codex`, source: https://github.com/openai/codex-plugin-cc). This file is the **single pinned spec** for how the skill invokes it, parses it, and decides "no major feedback".

## How callers invoke a codex review

**Always through the wrapper, never directly.**

```bash
python3 <this-skill>/scripts/run-codex-review.py \
  --branch <branch> \
  --base <base> \
  --worktree <worktree-path>
```

The wrapper does:
1. Discover `codex-companion.mjs` automatically — env-var first (`${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs`), version-glob fallback (`~/.claude/plugins/cache/openai-codex/codex/<latest>/scripts/codex-companion.mjs`).
2. Spawn `node codex-companion.mjs review --base <ref> --scope branch --json` synchronously inside the worktree.
3. Parse the JSON envelope.
4. Normalize to the round-log schema below.
5. Write `<rounds-dir>/<slug>.<round>.json`.
6. Update the manifest entry's `last_review_id`, `last_review_at`, `last_status`, `rounds`, `head_sha_current`, and append a `round_history` entry.

Sub-agents call the wrapper. Main agent (in programmatic loops) calls the wrapper. The wrapper is the contract; the underlying `codex-companion.mjs` invocation is the wrapper's implementation detail.

### Why the wrapper matters

`/codex:review` is `disable-model-invocation: true` in the plugin manifest — sub-agents physically cannot dispatch the slash command via `Skill(...)`. The slash itself runs `node codex-companion.mjs review` internally. Instead of every brief reinventing the discovery + invocation + parse + normalize chain (production traces showed agents writing 245-line `/tmp/codex-review-runner.py` shims session-after-session), `scripts/run-codex-review.py` does it once, version-agnostically, with a stable CLI surface.

### Adversarial mode (structured findings, opt-in)

`/codex:review` emits free-form text in `codex.stdout`; the wrapper regex-parses it. For projects that want pre-parsed findings with explicit severities (`critical | high | medium | low`), the wrapper supports `--mode adversarial`, which invokes `node codex-companion.mjs adversarial-review --json` instead. The `result.findings[]` array maps directly to round-log `items[]` — no regex needed.

Default is `--mode review` (matches existing skill semantics). Switch to `--mode adversarial` when the regex parser misses items because Codex emitted unusual formatting.

### Forbidden invocation paths

| Forbidden | Why |
|---|---|
| `codex review …` from Bash | No such CLI surface — the underlying `codex` binary has no `--background` review flag. |
| `Skill(skill="codex:review", ...)` from a sub-agent | `disable-model-invocation: true` in the plugin manifest. Will fail. |
| `node …/codex-companion.mjs review …` directly from a sub-agent brief | The wrapper does that, plus discovery + normalization + manifest update + round-log path computation. Calling the companion script directly bypasses all of that. |
| Inventing a "shim" because `codex --help` doesn't list `--background` | The flag belongs to the slash command, not the CLI. The wrapper handles it. |
| Re-running `/codex:review` as user-typed text from a sub-agent | Sub-agents cannot type slash commands. They use the wrapper. |
| Writing a parallel `/tmp/codex-review-runner.py` | That's what the production wrapper now does. Don't duplicate it. |

### Plugin missing → surface, do not fabricate

If the wrapper's discovery returns 127 (`codex-companion.mjs` not found at `${CLAUDE_PLUGIN_ROOT}/scripts/` or `~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/`), the codex plugin is missing. The wrapper exits 127 with install instructions. Sub-agent hands back FAILED with `terminal_reason: "codex plugin unavailable"`. Main agent surfaces to the user and stops the skill. **Never** substitute a free-form `codex` Bash call or any other plugin's reviewer.

## Synchronous execution (not background)

Despite the legacy "—background" framing in earlier versions of this skill, the codex-companion `review` and `adversarial-review` subcommands ALWAYS run synchronously — `--background` is parsed but ignored. The wrapper invokes them with a wall-clock cap (default 1500s = 25 min) and returns when codex returns. Per-branch parallelism comes from concurrent subprocess invocations across branches, not from a background flag.

If a single review hangs past the wall-clock cap (Codex can stall on remote tools like codebase-search APIs), the wrapper exits 1 with `terminal_reason: "review-hang past wall-clock cap"`. Caller retries once, then marks the round FAILED.

(Note: `task --background` is different — it DOES honor the flag and runs out-of-band. That's how Phase 6 codex rescue works. See `scripts/trigger-codex-rescue.py` and `references/post-pr-review-protocol.md`.)

## Normalized JSON schema (round-log)

Every round emits one file at `<rounds-dir>/<slug>.<round>.json`:

```json
{
  "review_id": "<codex thread id>",
  "branch": "feat/foo",
  "head_sha": "deadbeef1234...",
  "started_at": "2026-04-26T10:00:00Z",
  "finished_at": "2026-04-26T10:04:32Z",
  "raw_text": "<full Codex output verbatim>",
  "items": [
    {
      "id": "cdx-1",
      "severity_raw": "P1",
      "file": "src/foo.ts",
      "line": 42,
      "body": "Off-by-one in the slice — drops the last element."
    }
  ]
}
```

`severity_raw` is whatever Codex emits — the regex parser accepts `P1` / `P2` / `P3` / `P4` / `critical` / `high` / `medium` / `low` (case-insensitive). The adversarial-review path emits `critical | high | medium | low` directly. The classifier (`classify-review-feedback.py`) maps these onto major/minor per `major-vs-minor-policy.md`. **Don't pre-classify here** — keep the wrapper's normalization mechanical.

If Codex's `codex.stdout` doesn't match the expected `[severity] Title — file:line` pattern (free-form prose with no item headers, or fully unrecognized format), `items` is `[]` and the classifier falls back to regex over `raw_text`.

## codex-companion JSON envelopes (wrapper input)

What `codex-companion.mjs review --json` emits to stdout:

```json
{
  "review": "Review",
  "target": { "mode": "branch", "label": "...", "baseRef": "main" },
  "threadId": "...",
  "sourceThreadId": "...",
  "codex": {
    "status": 0,
    "stderr": "",
    "stdout": "<free-form review text — `[Px] title — file:line` items>",
    "reasoning": "<optional>"
  }
}
```

What `codex-companion.mjs adversarial-review --json` emits:

```json
{
  "review": "Adversarial Review",
  "result": {
    "verdict": "approve|needs-attention",
    "summary": "...",
    "findings": [
      {
        "severity": "critical|high|medium|low",
        "title": "...",
        "body": "...",
        "file": "src/foo.ts",
        "line_start": 42,
        "line_end": 42,
        "confidence": 0.9,
        "recommendation": "..."
      }
    ],
    "next_steps": ["..."]
  },
  "rawOutput": "...",
  "parseError": null,
  "reasoningSummary": null
}
```

The wrapper handles both shapes; callers don't need to care which mode produced the round-log.

## Detecting "no major feedback"

The subagent decides DONE-vs-continue from the classifier's output, not from the raw artifact:

```bash
python3 <this-skill>/scripts/classify-review-feedback.py --review-json <round-json>
```

Exit code:
- `0` = at least one major item → **continue the loop**.
- `1` = no major items (only minor / unclassified-but-no-major triggers) → **mark branch DONE**.
- `2` = parse failure → mark round `failed`, retry once (caps at 3).

Never decide DONE by eyeballing the raw text. The classifier is the single arbiter so the loop terminates the same way every time.

## Failure modes and what the wrapper does

| Failure | Wrapper behavior | Caller (subagent) action |
|---|---|---|
| Codex plugin not installed | Exit 127 with install instructions; manifest `last_status: "plugin-missing"` | Hand back FAILED with `terminal_reason: "codex plugin unavailable"`; main surfaces to user. |
| Worktree not on the right branch | Exit 2; no manifest update | `git -C <wt> checkout <branch>`; retry. |
| `codex-companion.mjs` exits non-zero with no stdout | Exit 2; manifest `last_status: "failed"` | Retry the round once. |
| `codex-companion.mjs` exits non-zero but stdout has parseable JSON | Wrapper logs warning, normalizes anyway, exit 0 | Round log written; loop continues. |
| Wall-clock timeout (Codex hung on a tool) | Exit 1; manifest `last_status: "timeout"`, `terminal_reason: "review-hang past wall-clock cap"` | Retry once; else mark FAILED. |
| Output doesn't match expected JSON envelope | Exit 0 with `items: []`, raw text in `raw_text` | Classifier falls back to regex over `raw_text`. |
| Branch HEAD changed mid-review (someone else pushed) | Not detected by wrapper; review may be stale | Discard the round, retry from current HEAD. |

## Read-only invariants

`run-codex-review.py` is read-only on the repo's content (no git mutations: no push, no commit, no checkout). Its only writes are:
- `<rounds-dir>/<slug>.<round>.json` — the round log.
- `<repo-root>/.codex-review-manifest.json` (or `--manifest <path>`) — the manifest entry update.

Pushing fix commits is the Applier sub-agent's job in Phase 3, not the wrapper's.

## Adjusting the contract

If a future Codex plugin version changes the JSON shape:

1. Update `normalize_review()` in `scripts/run-codex-review.py` to match the new shape.
2. Update this doc's Schema section in lock-step.
3. Run `scripts/classify-review-feedback.py` against a sample normalized JSON to confirm the classifier still partitions correctly.

The wrapper's external CLI surface (`--branch`, `--base`, `--worktree`, `--mode`, `--output`, `--manifest`, `--rounds-dir`, `--timeout`, `--dry-run`) is stable across plugin upgrades — callers don't change.

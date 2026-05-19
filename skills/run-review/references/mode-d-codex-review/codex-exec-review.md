# `codex exec review` — when and how to use it

The nested `codex exec review` subcommand inherits the broader `codex exec` flag surface. Pick it over root `codex review` when any of the broader features are required.

## When to switch from root `codex review` to `codex exec review`

Switch if **any** of these are true for the user's request:

| Need | Flag that triggers the switch |
|---|---|
| Machine-readable / JSONL events for downstream parsing | `--json` |
| Persist last-message to disk | `-o <file>` |
| Pin a specific model for the run | `-m <model>` |
| Bypass interactive approvals (CI / sandbox already in place) | `--dangerously-bypass-approvals-and-sandbox` |
| Skip the git work-tree precondition | `--skip-git-repo-check` |
| Do not persist session files | `--ephemeral` |
| The caller is a fleet driver (multi-branch codex review orchestration) | always — fleet path uses `codex exec review` exclusively |

Everything else (a quick human-readable review, custom prompt, base/uncommitted/commit target, `-c` config overrides, `--title`, `--enable`/`--disable`) works on root `codex review` and stays there.

## Inherited `codex exec` flag table

`codex exec --help` (verbatim from `codex-cli 0.130.0`):

| Flag | Effect |
|---|---|
| `-c, --config <key=value>` | Override config value (TOML-parsed; dotted paths). |
| `--enable <FEATURE>` | Enable feature (repeatable). `-c features.<name>=true`. |
| `--disable <FEATURE>` | Disable feature. `-c features.<name>=false`. |
| `-i, --image <FILE>...` | Attach image(s) to the initial prompt. |
| `-m, --model <MODEL>` | Model the agent should use. |
| `--oss` | Use open-source provider. |
| `--local-provider <OSS_PROVIDER>` | `lmstudio` or `ollama`. |
| `-p, --profile <CONFIG_PROFILE>` | Profile from `config.toml`. |
| `-s, --sandbox <SANDBOX_MODE>` | `read-only` / `workspace-write` / `danger-full-access`. |
| `--dangerously-bypass-approvals-and-sandbox` | Skip confirmations and sandbox. EXTREMELY DANGEROUS — only inside externally-sandboxed environments. |
| `-C, --cd <DIR>` | Working root for the agent. |
| `--add-dir <DIR>` | Additional writable directories. |
| `--skip-git-repo-check` | Run outside a git repo. |
| `--ephemeral` | Do not persist session files. |
| `--ignore-user-config` | Do not load `$CODEX_HOME/config.toml`. |
| `--ignore-rules` | Do not load `.rules` execpolicy files. |
| `--output-schema <FILE>` | JSON Schema for the final response shape. |
| `--color <COLOR>` | `always` / `never` / `auto`. |
| `--json` | Print events to stdout as JSONL. |
| `-o, --output-last-message <FILE>` | Write the last message to a file. |

`codex exec review` itself accepts these flags (subcommand-specific):

| Flag | Effect |
|---|---|
| `--uncommitted` | Review staged, unstaged, untracked changes. |
| `--base <BRANCH>` | Review against base branch. |
| `--commit <SHA>` | Review the changes from a commit. |
| `--title <TITLE>` | Title for the summary header. |
| `[PROMPT]` | Initial instructions; `-` reads from stdin. |

The combination above is what makes `codex exec review` strictly broader than root `codex review`.

## Canonical invocations

### Quick second opinion, capture machine-readable output

```bash
mkdir -p /tmp/codex-review
ts=$(date +%Y%m%dT%H%M%SZ)
codex exec review \
  --json \
  -o "/tmp/codex-review/${ts}-last.md" \
  --base main \
  "Review for auth and session safety."
```

`--json` streams JSONL events to stdout; `-o` writes the final message to disk.

### Bypass approvals (only inside an already-sandboxed worker)

```bash
codex exec review \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  --json \
  -o /tmp/codex-review/last.md \
  --base main
```

Only safe inside a CI worker, container, or other externally-sandboxed context. Never on a developer laptop unattended.

### Pin model + raise reasoning effort

```bash
codex exec review \
  -m gpt-5.5 \
  -c model_reasoning_effort="xhigh" \
  --base main
```

### Ephemeral run (no session files persisted)

```bash
codex exec review --ephemeral --base main
```

### Brief on stdin + JSON capture

```bash
cat brief.md | codex exec review --json -o /tmp/codex-review/last.md --base main -
```

### Switch working directory before reviewing

```bash
codex exec review -C /path/to/repo --base main
```

## Output parsing — `--json` event stream

`codex exec --json` writes one JSON object per line. Each event has a `type` (e.g. `agent.message`, `agent.tool_call`, `agent.thought`). For review use:

- skim for `type == "agent.message"` to extract findings text;
- the final agent message — also written by `-o <file>` — is the structured review summary.

When wiring downstream parsers, capture `-o <file>` rather than parsing JSONL line-by-line. The `-o` file is a single markdown document; JSONL is a stream of intermediate events.

## When `codex exec review` is **not** the right path

- For a casual human-readable review, stay with root `codex review`. The extra flags are noise.
- For multi-branch convergence loops, do **not** wire `codex exec review` by hand — route to multi-branch codex review orchestration by writing a thin orchestrator that fans out `codex exec review --base <ref>` calls per branch (the dedicated dispatcher skill was retired). The fleet path adds manifest seeding, monitor wiring, classification, and rescue — all things `codex exec review` alone does not provide.
- For "review my PR with three different model configs and compare", run `codex exec review` three times sequentially, each with a different `-m` or `-c` override, and capture each `-o` to a distinct file. Do not try to fan out via `--profile` only; multiple model identities need multiple invocations.

## Recovery and failure modes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `--json` output is empty | Run exited before producing the final message. | Check stderr; re-run without `--json` to see the human-readable error. |
| `-o` file is empty after a 0-exit run | The agent did not produce a final message (rare). | Re-run with `--json` and inspect the last events. |
| `--dangerously-bypass-approvals-and-sandbox` refused | Codex is configured to deny that flag in this environment. | Do not work around it. Ask the user; this is intentional. |
| `--ephemeral` plus `--output-schema` interaction | Ephemeral runs still honor schema; the schema file remains on disk. | Expected. The session-file ephemerality does not affect input files. |
| Mid-stream JSONL truncation | Process killed or pipe broken. | Re-run; do not try to repair the JSONL by hand. |

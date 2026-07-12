# jean.json + .worktreeinclude — verified contracts

All Jean claims verified against `coollabsio/jean` source, main branch, 2026-07-11:
`src-tauri/src/projects/types.rs` (schema), `src-tauri/src/projects/git.rs:1912-2050` (reader + runner), `src-tauri/src/projects/commands.rs:2184,2295,2976,3481` (call sites), `src-tauri/src/terminal/commands.rs:88-103` (run/ports), `src/services/projects.ts:2099-2215` (TS mirror).

## jean.json schema (canonical)

Location: **repo root**, must be **tracked** (one call site reads it from the project root path when creating the worktree — a gitignored file also silently vanishes for teammates).

```jsonc
{
  "scripts": {
    "setup":    "string | null",            // runs AFTER worktree creation
    "teardown": "string | null",            // runs BEFORE worktree deletion/archival
    "run":      "string | string[] | null"  // launched via toolbar Run; array = multiple selectable commands
  },
  "ports": [
    { "port": 8000, "label": "App UI", "host": "localhost" }  // host optional, defaults localhost
  ]
}
```

Rust source of truth:

```rust
struct JeanConfig { scripts: JeanScripts, ports: Option<Vec<PortEntry>> }   // scripts has #[serde(default)]
struct JeanScripts { setup: Option<String>, teardown: Option<String>, run: Option<RunScript> }
enum RunScript { Single(String), Multiple(Vec<String>) }                    // untagged: "x" or ["x","y"]
struct PortEntry { port: u16, label: String, host: Option<String> }
```

- Unknown keys are ignored by serde; **a parse error makes Jean ignore the whole file** (logged warning, no UI error) — always `jq . jean.json` before shipping.
- `ports[]` powers ⌘+O open-in-browser per worktree. `run`/`ports` are re-read live (30s frontend cache) — editing jean.json applies to existing worktrees; `setup` only affects *new* worktrees.

## Execution contract (setup & teardown)

| Aspect | Behavior |
|---|---|
| Shell | User's login shell, interactive+login mode when supported: `zsh -l -i -c <script>` / `bash -l -i -c`; else `sh -c`. Your rc-file PATH (nvm, bun, brew) is available. No TTY — any prompt hangs. |
| CWD | The worktree directory. Relative paths are worktree-relative. |
| Env | `JEAN_WORKSPACE_PATH` (worktree abs path), `JEAN_ROOT_PATH` (main repo abs path), `JEAN_BRANCH` (branch name). Jean **refuses to run** if any is empty or the paths are non-absolute — this guards `rm -rf $JEAN_WORKSPACE_PATH/x` against empty-var expansion. |
| Timing | Setup runs **in background after** `worktree:created` is emitted — the user/agent can start typing immediately; slow setup doesn't block the session. |
| Failure | Non-zero exit → `setup_success=false`, stdout+stderr captured and shown in the Setup card. Worktree is **not** rolled back. Teardown output surfaces as a toast/event. |
| Both scripts | Must therefore be idempotent, non-interactive, and safe on partial state. |

Setup runs on all three worktree-creation paths (manual, from-branch, from-issue/PR) — same contract.

## .worktreeinclude semantics

Verified from `satococoa/git-worktreeinclude` (Go, Homebrew tap) and `ReubenBeeler/WorktreeCreate-hook` (Claude Code hook); real-world examples: `openai/codex` (`user.bazelrc`), `PostHog/posthog` (`.env`, `.env.local`, `.envrc`), `DataDog/browser-sdk` (`.claude/settings.local.json`, `.env`).

- Location: repo root of the **source** (main) worktree. Syntax: **gitignore-compatible** (`#` comments, `!` negation, `/` anchors, `**`, nested files scope to their dir).
- **Intersection rule:** a path copies only if it is (a) matched by `.worktreeinclude` AND (b) classified as *ignored* by git. **Tracked files never copy.** Untracked-but-not-ignored files also don't copy.
- Plain `git worktree add` does **not** read it. Consumers: Claude Code WorktreeCreate hooks, Roo Code ("Create from .gitignore"), standalone `git-worktreeinclude apply`, various wrappers.
- **Jean does NOT read it** (zero references in source). That is why this skill pairs it with equivalent copy lines in `scripts.setup`.

Keeping the pair in sync — the setup copy-block is generated from the include list:

```bash
# copy-block pattern for jean.json setup (one line per include entry)
cp "$JEAN_ROOT_PATH/.env" . 2>/dev/null || true
cp "$JEAN_ROOT_PATH/.env.local" . 2>/dev/null || true
mkdir -p .claude && cp "$JEAN_ROOT_PATH/.claude/settings.local.json" .claude/ 2>/dev/null || true
```

`|| true` per line: a missing optional file must not fail the whole setup — but list what was skipped by echoing, so the Setup card shows it (pattern inherited from git-worktree-manager's "continue with warning + explicit missing-file list" contract).

## Reference dogfood examples

`coollabsio/coolify/jean.json` (the maintainer's own):

```json
{
  "scripts": {
    "setup": "cp $JEAN_ROOT_PATH/.env . && mkdir -p .claude && cp $JEAN_ROOT_PATH/.claude/settings.local.json .claude/settings.local.json",
    "teardown": null,
    "run": "docker rm -f coolify coolify-realtime coolify-minio coolify-redis coolify-db coolify-mail; spin up; spin down"
  },
  "ports": [{ "port": 8000, "label": "Coolify UI" }]
}
```

`coollabsio/jean/jean.json`:

```json
{ "scripts": { "setup": "bun install", "run": "bun run tauri:dev" } }
```

## Compatibility note — jean-tui

The sibling terminal client `coollabsio/jean-tui` parses `scripts` as a free-form `map[string]string` (any named script; no `ports`, no `run` array). Sticking to string values for `setup`/`teardown` and only using the array form for `run` keeps the desktop app fully served while degrading gracefully in the TUI (which will simply expose whatever named string scripts it finds).

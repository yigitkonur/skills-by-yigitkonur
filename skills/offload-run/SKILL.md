---
name: offload-run
description: Use skill if you are running a project's npm/pnpm install, tests, builds, tsc, eslint, pytest, macOS/Xcode builds, or a dev server in a remote Sprites cloud sandbox instead of locally.
---

# offload-run

Drive a remote **Sprite** (Fly.io stateful sandbox) so build / test / serve work never burns local
CPU/RAM. `offload <subcommand>`. Default is `run`, so `offload -- npm test` runs your command in the
cloud, streams stdout/stderr, and returns the **exit code unchanged** — it behaves like a local run.

Per project, everything maps to one **ephemeral run sprite** `offload-<type>` keyed to a
dependency-warm **golden checkpoint** (deps installed once, restored each run in seconds — no
reinstall). Servers get a **separate persistent sprite** `offload-srv-<dir>` so a `run` never wipes them.

## Subcommands
| Command | What it does |
|---|---|
| `offload -- CMD` / `offload run -- CMD` | run CMD in the run sprite; stream output; return its exit code. Flags: `--quiet`, `--root R`, `--type T`, `--backend B` |
| `offload serve [--port N] [--public] [--name S] -- CMD` | run CMD as a persistent **Service** on its own sprite and print the public URL |
| `offload status [--serve]` | live state (running/warm/cold), URL, and **billing posture** |
| `offload url [--public\|--private]` | show or change the sprite's public-URL auth |
| `offload sync` | push the worktree into the sprite (no run) |
| `offload shell` | interactive console in the sprite |
| `offload proxy <port[:local]>...` | forward a sprite port to localhost (DB/dev) |
| `offload checkpoints` / `offload prune [--keep N]` | list / delete accumulated `pre-restore` safety checkpoints |
| `offload keepalive --seconds N` | hold the sprite awake N s (bounded; billed while held) |
| `offload nuke [--yes]` | **destroy** the sprite — the only way to stop ALL billing |
| `offload mcp [--add]` | print/add the optional Sprites remote MCP (see MCP below) |
| `offload doctor` | check CLI + auth + print the in-sprite official agent docs |

Add `--sprite NAME` to any op to target an explicit sprite; `--serve` to target the server sprite.

## Feedback fidelity
`run` streams the remote stdout/stderr live and exits with the remote command's exact code (verified:
pass→0, forced fail→7, shell operators preserved). `--quiet` suppresses the `[offload]` log lines so
output is byte-for-byte the program's — drop it into scripts / pre-commit / CI transparently.

## Billing & lifecycle (the cost model)
- **Idle = $0 compute.** When you stop using a sprite it auto-suspends (warm → cold); CPU & memory
  billing stops on its own. There is **no** stop/sleep command — and you don't need one.
- **Only storage bills while idle** — ~`$0.027/GB-month` (a 10 GB box ≈ $0.20/mo). Rates: CPU
  `$0.07/CPU-hr`, mem `$0.04375/GB-hr`, storage `$0.000027/GB-hr`.
- **`offload nuke` is the only path to $0** (destroys files + golden + checkpoints — irreversible).
- **Cost trap:** a forgotten keep-alive heartbeat keeps it *running* (billing). `keepalive` is bounded
  and auto-releases; never leave a bare refresh loop.
- `offload status` prints this live for the current project.

## Servers & sync (no constant rsync)
The ext4 filesystem is **persistent + checkpointed**, so you **don't** rsync continuously — sync once,
then incrementally. `offload serve` registers your command as a Sprites **Service** (survives
hibernation, auto-starts on the next request), routes the public URL to `--port` (default 8080), and
prints the real URL (read from the API). First request wakes it in ~0.1–2 s; idle costs $0. For live
two-way editing of a running server, use `offload proxy` (or an SSHFS mount) — see references.

## MCP (optional; CLI-first by Fly's own recommendation)
Sprites ships a hosted remote MCP (`https://sprites.dev/mcp`, OAuth). But Fly state plainly that for
agents that can run shell, **CLI/skills are the better default** ("MCP is the wrong way… command line
tools and discoverable APIs are the Right Way"). So this skill is CLI-first; add MCP only for chat
agents that cannot run commands: `offload mcp --add` → `claude mcp add --transport http sprites https://sprites.dev/mcp`.

## First-time setup
1. **Get a token, then install + auth the CLI in one step.** At https://sprites.dev create an org token (the dashboard hands you a ready one-liner) and run it — it installs the `sprite` CLI **and** authenticates:
   `curl -fsSL https://sprites.dev/install.sh | SETUP_SPRITE_TOKEN="<your-token>" bash`
   Already have the CLI? `sprite auth setup --token <your-token>` (or `sprite login` for a browser flow). The token is stored by the CLI under `~/.config` — **this skill never reads a key from env/config; it only shells out to an already-authed `sprite`.** The sprites backend also needs `jq` (`brew install jq`) for JSON parsing. Stuck? `offload doctor` prints exactly what to fix.
2. `cp config.example.sh ~/.config/offload-run/config.sh` (optional; defaults: linux=sprites, macos=tart).
3. `ln -s "$PWD/scripts/offload.sh" ~/bin/offload`. Verify: `offload doctor`.

## Backends
node/python/generic → **Sprites** (default, **verified end-to-end**). macOS/Xcode/Swift → **Tart** on a
remote Mac host (scaffold — see references). E2B (`--backend e2b`) for parallel fork (scaffold).

## References
- `references/sprites-power.md` — lifecycle/billing, serve+URL, sync/mount, prune, keepalive, MCP — full detail.
- `references/setup.md` — provision backends + build golden images (the one-time work).
- `references/backends.md` — backend comparison + macOS host options.
- `references/troubleshooting.md` — gotchas found while verifying the Sprites backend.

# Sprites power features — lifecycle, serving, sync, checkpoints, MCP

All facts below verified against sprite CLI v0.0.1-rc43 + docs.sprites.dev + fly.io (2026-05-29), and
exercised live (status/prune/serve/run on a real account). Sprites = Fly.io stateful sandboxes.

## Lifecycle & billing (three states)
| State | Compute billed? | Wake | RAM/processes |
|---|---|---|---|
| running (active exec/console, open URL connection, live Service, Task hold) | YES — CPU + mem + storage | — | live |
| warm (just went idle) | NO (compute removed) | 100–500 ms | frozen/preserved |
| cold (idle longer) | NO | 1–2 s | dropped |

- Transition is **automatic** — there is **no `sprite stop/sleep/pause`**. Stop using it → it suspends.
- Only **durable storage** bills 24/7: `$0.000027/GB-hr` (~$0.027/GB-month). Compute: CPU `$0.07/CPU-hr`
  (min 6.25%/s), mem `$0.04375/GB-hr` (min 0.25 GB/s). Hot NVMe cache `$0.000683/GB-hr` only during active use.
- **Only `sprite destroy` (`offload nuke`) zeroes the bill** — it deletes files, deps, and ALL checkpoints. No "keep data, stop paying" option.
- **#1 cost trap:** a refreshing Tasks-API heartbeat keeps it running "until you notice." `offload keepalive`
  is a bounded `sprite exec sleep N` that auto-releases — safe. For self-managing in-sprite processes that
  must hold outbound connections (websockets/queues, which drop on every pause), use the Tasks API with a
  trap-EXIT cleanup: `curl --unix-socket /.sprite/api.sock -X POST http://sprite/v1/tasks -d '{"name":"x","expire":"5m"}'`, refresh via PUT every ~60 s, `DELETE` on exit (max 1 h/task).

## Serving an app (`offload serve`)
- Runs your command as an in-sprite **Service** (`/.sprite/bin/sprite-env services create <name> --cmd <bin> --args "a,b,c" --http-port <port> --dir /work`). `--cmd` is the binary only; args are comma-separated. Only one service may hold `--http-port`.
- Services **survive hibernation** (frozen on warm, restarted on cold/boot) and **auto-start on the next request** — unlike `sprite exec`/`console` processes, which die when the sprite sleeps.
- The URL is read from the API (`/v1/sprites` → `.url`), shape `https://<name>-<id>.sprites.app` — **never hand-construct it**. Default route is port 8080 or the service's `http_port`.
- Auth: `sprite` (org/token only, default) or `public` (open). `offload url --public|--private` (`sprite url update --auth …`, deprecated alias but works; also `sprite update --url-auth`). **Never** combine `--public` with secrets in env.
- Serve uses a **separate persistent sprite** `offload-srv-<dir>` so the ephemeral `offload run` (which restores the golden) never wipes the server. Deps install once on that box and persist.
- Cost-optimal pattern: Service + public URL + wake-on-request = $0 while idle. For zero cold-start or held connections, add a Task heartbeat (pays continuously).

## Sync / file transfer (no continuous rsync)
The fs is persistent + checkpointed, so: **upload once, then incremental** — not a daemon rsync. Confirmed mechanisms only:
- `offload sync` / the run path: git-aware tar over stdin (`git ls-files -co --exclude-standard | tar | sprite exec -- tar -x`), honoring `.gitignore`, never `node_modules`. macOS AppleDouble stripped (`COPYFILE_DISABLE=1 --no-mac-metadata`).
- `sprite exec --file src:dest` — single-file upload before exec (repeatable).
- **Live two-way editing of a running server:** mount via SSHFS over `offload proxy` (install openssh-server as a Service, `offload proxy -W :22`, sshfs-mount) — use this instead of a rsync loop. There is **no** `sprite cp/push/pull/mount` command.

## Checkpoints & pruning
- `sprite checkpoint create -s NAME [--comment …]` (ids v0,v1,…); `list`; `info <id>`; `delete <id>` (CLI only — **REST has no delete**); `restore <id>` (replaces the fs, restarts services, seconds-scale — not the marketing "ms").
- **Every restore auto-creates a `pre-restore-*` safety checkpoint** (platform behavior) → they accumulate. `offload prune [--keep N]` deletes them (keeps newest N + the golden + Current). Copy-on-write makes each cheap, but they hold storage quota until deleted.
- The golden is a normal checkpoint commented `golden-<type>-<lockfilehash>`; rebuilt only when the lockfile changes.

## Official agent convention
There is **no** Fly-published skill; the official pattern is to point the agent at the in-sprite docs and let it drive the CLI. `offload doctor` prints `/.sprite/llm.txt` (the in-sprite agent manifest: services, checkpoints, URL, network policy, layout under `/.sprite/`). Treat that file (and `/.sprite/docs/agent-context.md`) as the in-sprite source of truth; this skill wraps the same CLI it documents.

## Programmatic (herder / orchestrator)
- REST `https://api.sprites.dev/v1` (Bearer `$SPRITES_TOKEN`); `sprite api -s NAME <path>` for raw JSON from the CLI.
- SDKs: JS `@fly/sprites` (SpritesClient: createSprite/sprite(name).execFile/.spawn), Go `sprites-go`, Python `sprites-py`, Elixir. Checkpoints/services/network are REST/SDK; prune is CLI-only.

## Network/security
- Egress is policy-controlled (DNS-based allow/deny via `sprite api POST /v1/sprites/<name>/policy/network`, deny-by-default with a trailing `{deny *}`). Inbound = URL auth (sprite|public). Secrets via `--env` are discouraged for long-lived tokens; prefer Connectors. Isolation = Firecracker + restartable inner container.

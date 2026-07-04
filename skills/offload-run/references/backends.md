# Backends — comparison & when to use which

Distilled from the 23-platform corpus at `~/research/agent-build-sandboxes-2026/`. The skill routes
by project type; this is how to choose/configure the backend behind each.

## Decision tree
```
macOS / Xcode / Swift / Pods?  ── yes ──► Tart  (only Apple HW can build macOS)
        │ no
node / python / generic?
        ├─ want persistent machine + checkpoint, idle-free, simplest ──► Sprites   (default)
        ├─ want to FORK one warm env into many parallel sandboxes  ──► E2B
        └─ already running a Tart host & want one engine for all     ──► Tart (Linux image)
```

## Linux backends (node / python / generic)
| | Sprites (default) | E2B (alt) |
|---|---|---|
| Model | persistent sprite + filesystem **checkpoint/restore** (~ms) | ephemeral microVM, **snapshot warm-FORK** (`create(snapId)`) |
| Warm deps | node_modules in golden checkpoint | node_modules in lockfile-keyed template |
| Parallel fan-out | pool of sprites (no fork) | **fork one template → N sandboxes** (best) |
| Idle cost | **pay nothing when idle** | full wall-clock; pause=free |
| Agents prebuilt | bake yourself (`OFFLOAD_INSTALL_AGENTS=1`) | **prebuilt Codex/Claude Code templates** |
| Isolation | Firecracker + inner container | Firecracker |
| Pricing | $0.07/CPU-hr, $0.04375/GB-hr, idle-free | $0.0504/vCPU-hr, $0.0162/GiB-hr, $150/mo base |
| Self-host | no (Fly.io managed) | no |
| Use when | the default — checkpoint, cheap idle, persistent | parallel test fan-out or want agent templates |

Honorable mentions for Linux (in the corpus, not wired here): Daytona (no base fee + best dashboard
+ AGPL self-host), Morph/CodeSandbox (memory warm-fork), Northflank/Fly (cheapest), GCP Cloud Run
Jobs / AWS (IAM-native). Adding one = a new `backends/<name>.sh` with the same function signature.

## macOS backend (Tart)
Tart is the engine; the **host** is your choice (set `OFFLOAD_TART_HOST` so your own Mac stays free):

| Host option | Own hardware? | Notes |
|---|---|---|
| Spare Apple Silicon Mac you own | yes | cheapest if you have one; `OFFLOAD_TART_HOST=you@that-mac` |
| Orchard cluster (cirruslabs/orchard) | yes (several Macs) | REST scheduler for a real farm; 2 macOS VMs/host cap |
| Cirrus Runners (managed Tart) | **no** | managed macOS — closest to "not my resources" |
| MacStadium Orka / AWS EC2 Mac / Namespace macOS / Depot macOS | **no** | managed Mac hosts; point SSH/endpoint at them |

Key facts: `tart clone` = instant CoW copy (the macOS "checkpoint"); Apple license caps **2 macOS VMs
per host**; Linux VMs on the same Tart have no cap (so `OFFLOAD_LINUX_BACKEND=tart` is viable if you
already run a Tart host). macOS golden = a Tart image with Xcode + your toolchain baked in.

## The honest gap
There is **no fully-managed, serverless, checkpoint-capable macOS sandbox** equivalent to Sprites for
Linux. macOS always means "a Mac somewhere" — the only lever is whether that Mac is yours (spare/
Orchard) or rented (Cirrus/Orka/EC2 Mac). For Linux, Sprites/E2B are genuinely zero-own-hardware.

## Adding a backend
Implement `backends/<name>.sh` exposing `<name>_backend TYPE HASH ROOT CMD...` that: restores/forks a
golden keyed to HASH, syncs `worktree_tar ROOT` into `$OFFLOAD_WORKDIR`, runs CMD, returns its exit
code. Then add a `case` arm in `offload.sh` and document it here.

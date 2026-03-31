---
name: build-hcom-systems
description: >-
  Use skill if you are building applications or automation systems on hcom — multi-agent architectures, custom workflow scripts, CI/CD integration, or understanding hcom internals like hooks, SQLite, relay, and events.
---

# Build hcom-Based Systems

Design and build applications that use hcom as the multi-agent communication backbone.

## Decision tree

1. **Need to understand hcom architecture** → Read `references/architecture/core-architecture.md`
2. **Need to understand the hook system** → Read `references/internals/hook-system.md`
3. **Need to understand cross-device relay** → Read `references/internals/relay-system.md`
4. **Need to understand terminal/PTY management** → Read `references/internals/pty-system.md`
5. **Need to understand the event system** → Read `references/internals/event-system.md`
6. **Building a custom workflow script engine** → Read `references/architecture/scripting-engine.md`
7. **Need configuration details** → Read `references/architecture/config-system.md`
8. **Need TUI/dashboard details** → Read `references/architecture/tui-architecture.md`
9. **Need tool integration details** → Read `references/internals/tool-integration.md`
10. **Need bootstrap/injection details** → Read `references/internals/bootstrap-injection.md`
11. **Looking for multi-agent pattern ideas** → Read `references/patterns/multi-agent-research.md`
12. **Designing a new multi-agent application** → Follow the Design Workflow below

## Design workflow for new hcom-based systems

Before you start, choose the output path. Default to `./design.md` in the current working directory unless the user gave a different target. If the user wants runnable orchestration, confirm `hcom` is available with `command -v hcom` before promising executable steps. If `hcom` is unavailable, stay at architecture/design level and state that the plan is not executable in the current environment. The design is not complete until that file contains:

- target topology and agent responsibilities
- communication primitives, thread model, and event/wait strategy
- a minimal script skeleton or launch plan
- external integration points
- verification steps, cleanup plan, and open risks/assumptions

### Step 1: Define your agent topology

| Topology | When to use | hcom primitives |
|----------|-------------|-----------------|
| Hub-spoke | One coordinator, N workers | Coordinator uses `@tag-` to broadcast, workers report back |
| Pipeline | Sequential stages | Each stage reads previous via `hcom transcript`, signals via thread |
| Ensemble | N independent, 1 aggregator | Workers answer independently, judge reads all via `hcom events --sql` |
| Peer-to-peer | Agents message freely | Direct `@name` messaging with intent system |
| Reactive | Event-driven triggers | `hcom events sub` subscriptions trigger agent actions |

### Step 2: Choose communication primitives

| Need | hcom primitive | Latency |
|------|---------------|---------|
| Send message to agent | `hcom send @name --thread T --intent X -- "msg"` | under 1s (Claude), 1-3s (Codex) |
| Wait for signal | `hcom events --wait N --sql "..."` | under 1s after match |
| Read agent's full work | `hcom transcript @name --full --detailed` | under 1s |
| React to file changes | `hcom events sub --file "*.py"` | under 2s |
| React to agent idle | `hcom events sub --idle name` | under 2s |
| Cross-device messaging | `hcom send @name:DEVICE -- "msg"` | 1-5s (MQTT relay) |
| Structured context handoff | `hcom send --title X --transcript N-M:full --files a.py` | under 1s |

### Step 3: Design the script

If the user only wants architecture/design, write the script skeleton directly in `design.md` and stop after the completion checklist below. If the user wants executable orchestration beyond the skeleton below, open `skills/run-hcom-agents/SKILL.md` and then read `skills/run-hcom-agents/references/cli-reference.md` plus `skills/run-hcom-agents/references/gotchas.md` for the exact launch and cleanup patterns.

Treat launch grouping and message threading as separate design choices: `--batch-id` groups related launches, while `--thread` belongs on `hcom send` and `hcom events`.

Minimal launch skeleton to include in the design when agent execution is part of the plan:

```bash
thread="workflow-$(date +%s)"
batch_id="$thread"
launch_output="$(hcom 2 claude --tag researcher --go --headless --batch-id "$batch_id" \
  --hcom-prompt "Wait for work on thread $thread and report back on the same thread.")"
names_csv="$(printf '%s\n' "$launch_output" | sed -n 's/^Names: //p')"

if [ -z "$names_csv" ]; then
  echo "Could not capture agent names from hcom launch output" >&2
  exit 1
fi

mapfile -t agent_names < <(
  printf '%s\n' "$names_csv" |
    tr ',' '\n' |
    sed 's/^[[:space:]]*//; s/[[:space:]]*$//' |
    sed '/^$/d'
)

if [ "${#agent_names[@]}" -eq 0 ]; then
  echo "Launch output did not contain any usable agent names" >&2
  exit 1
fi

for name in "${agent_names[@]}"; do
  hcom events --wait 30 --idle "$name" >/dev/null
done

echo "Thread: $thread"
echo "Agents: ${agent_names[*]}"
```

Router-level launch flags such as `--go`, `--headless`, and `--batch-id` are valid even if `hcom 1 claude --help` does not list them. Use `references/internals/tool-integration.md` as the source of truth for launch mechanics.

Key decisions:

| Decision | Options |
|----------|---------|
| Agent tool | `claude` (better reasoning), `codex` (sandboxed execution), mixed |
| Launch mode | `--headless` (scripts), interactive (user-facing) |
| Coordination | Thread-based messaging + `events --wait` (simple), event subscription (reactive), transcript handoff (pipeline) |
| Launch grouping | Standalone launches, shared `--batch-id` for coordinated spawn |
| Error handling | `trap cleanup ERR` + `hcom kill`, timeout-based fallbacks |
| State management | Thread messages (ephemeral), bundles (structured), transcripts (persistent) |

### Step 4: Integrate with external systems

```bash
# CI/CD integration
hcom 1 claude --tag ci --go --headless \
  --hcom-prompt "Run tests. If failing, send failures to @fixer-"
hcom events --wait 300 --sql "msg_text LIKE '%ALL TESTS PASS%'"

# External sender (non-agent)
hcom send @worker- --from "github-actions" -- "PR #42 merged, deploy needed"
```

### Completion checklist and stop condition

Stop when `design.md` (or the user-specified output path) exists and includes:

- the chosen topology and why it fits
- the hcom primitives for launch, wait, transcript handoff, and cleanup
- a concrete thread naming rule and a launch-output capture rule for agent names
- either a minimal script skeleton or an explicit note that execution is out of scope
- verification steps and a clear cleanup/termination plan

If the user asked for design only, do not keep expanding into execution details after this point.

## hcom architecture overview

```
┌─────────────────────────────────────────────────┐
│                   hcom CLI (Rust)                │
├─────────┬───────────┬──────────┬────────────────┤
│  Claude │  Codex    │  Gemini  │   OpenCode     │
│  Hooks  │  Hooks    │  Hooks   │   Plugin       │
├─────────┴───────────┴──────────┴────────────────┤
│              SQLite Database (WAL)               │
│  instances | events | notify_endpoints | kv      │
├─────────────────────────────────────────────────┤
│         MQTT Relay (cross-device sync)           │
│  Push/Pull every 5s | TCP notify for instant     │
└─────────────────────────────────────────────────┘
```

**Key tables:** `instances` (one row per agent), `events` (immutable log with `events_v` view), `notify_endpoints` (TCP wake ports), `kv` (relay state, subscriptions)

**Hook cycle (~20ms):** SessionStart → PreToolUse → PostToolUse → Stop (primary delivery)

**Bundled scripts:** debate (structured debate), confess (honesty eval), fatcow (codebase oracle)

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Codex stale_cleanup | Wait for idle: `hcom events --wait 30 --idle $name` |
| No thread isolation | Use a unique message thread like `thread="workflow-$(date +%s)"` and carry it through `hcom send`/`hcom events` |
| Polling with sleep | Use `hcom events --wait --sql` |
| Putting `--thread` on launch | Keep `--thread` on `send`/`events`; use `--batch-id` only to group launches |
| Hardcoded agent names | Capture the `Names:` line, normalize commas/whitespace, then wait for idle before follow-up messages |
| Missing --go flag | Always include `--go` on scripted launch, kill, or stop |
| Launch flags seem invalid | `--go`, `--headless`, and `--batch-id` are hcom-level launch flags even when tool-specific help omits them |
| No cleanup trap | `trap cleanup ERR` with `hcom kill $name --go` |

## Guardrails

- Do not build directly on the SQLite database — use hcom CLI as the interface
- Do not assume agent names — always capture from launch output
- Do not skip thread isolation — every workflow needs a unique thread ID
- Do not put `--thread` on `hcom [N] <tool>` launch commands — threads belong to message and wait operations
- Do not use sleep — hcom events --wait is the correct primitive
- Do not send messages to agents that haven't bound yet — wait for idle
- Do not trust tool-specific launch help alone for router-level flags — `--go`, `--headless`, and `--batch-id` are valid hcom launch flags
- Do not forget cleanup — orphan headless agents consume resources indefinitely

## Reference files

| File | When to read |
|------|-------------|
| `references/architecture/core-architecture.md` | Full DB schema, instance lifecycle, 3-tier identity, delivery pipeline, bootstrap |
| `references/architecture/scripting-engine.md` | Script discovery, execution flow, debate/confess/fatcow analysis |
| `references/architecture/config-system.md` | All 20 config keys, TOML structure, env var mapping, per-agent config |
| `references/architecture/tui-architecture.md` | Ratatui rendering, inline vs fullscreen, ejector, RPC, command palette |
| `references/internals/hook-system.md` | All 10 Claude hooks, 7 Gemini, Codex/OpenCode, timing, collision detection |
| `references/internals/relay-system.md` | MQTT topic layout, push/pull algorithm, control messages, daemon watchdog |
| `references/internals/pty-system.md` | 24 terminal presets, screen tracker, gate conditions, injection protocol |
| `references/internals/event-system.md` | events_v columns, all filter flags, subscription lifecycle, FTS5, bundles |
| `references/internals/tool-integration.md` | Tool enum, per-tool arg parsers, launch mechanics, session binding |
| `references/internals/bootstrap-injection.md` | Full bootstrap template, per-tool delivery rules, subagent bootstrap |
| `references/patterns/multi-agent-research.md` | 35-repo research findings adapted as hcom patterns |

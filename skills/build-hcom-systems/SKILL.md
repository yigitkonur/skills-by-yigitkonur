---
name: build-hcom-systems
description: Use skill if you are building applications or automation systems on top of hcom — designing multi-agent architectures, extending hcom with custom workflow scripts, integrating hcom into CI/CD pipelines, or understanding hcom internals like its hook system, SQLite schema, relay networking, and event subscriptions.
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

Use the `run-hcom-agents` skill for script template and execution patterns. Key decisions:

| Decision | Options |
|----------|---------|
| Agent tool | `claude` (better reasoning), `codex` (sandboxed execution), mixed |
| Launch mode | `--headless` (scripts), interactive (user-facing) |
| Coordination | Thread-based (simple), event subscription (reactive), transcript handoff (pipeline) |
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
| No thread isolation | Use unique `--thread "workflow-$(date +%s)"` |
| Polling with sleep | Use `hcom events --wait --sql` |
| Hardcoded agent names | Parse from `grep '^Names: '` in launch output |
| Missing --go flag | Always include `--go` on launch and kill |
| No cleanup trap | `trap cleanup ERR` with `hcom kill $name --go` |

## Guardrails

- Do not build directly on the SQLite database — use hcom CLI as the interface
- Do not assume agent names — always capture from launch output
- Do not skip thread isolation — every workflow needs a unique thread ID
- Do not use sleep — hcom events --wait is the correct primitive
- Do not send messages to agents that haven't bound yet — wait for idle
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

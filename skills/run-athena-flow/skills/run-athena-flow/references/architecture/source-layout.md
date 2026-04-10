# Source Code Layout

Athena Flow CLI is a TypeScript project built with React + Ink for the terminal UI, better-sqlite3 for persistence, and tsup for bundling (ESM only).

## Repository

- **GitHub:** github.com/lespaceman/athena-flow-cli
- **Package:** `@athenaflow/cli`
- **License:** MIT
- **Language:** TypeScript 98.3%, JavaScript 1.7%
- **Node:** 20+
- **Target:** ES2022

## Binary Entry Points

| Binary | Source | Purpose |
|--------|--------|---------|
| `athena` / `athena-flow` | `dist/cli.js` | Main CLI |
| `athena-hook-forwarder` | `dist/hook-forwarder.js` | Claude Code hook bridge |

## Directory Structure

```
src/
  app/                          # Application layer
    bootstrap/                  # Config merging, workflow/plugin resolution
    commands/                   # Slash command system
      builtins/                 # /help, /clear, /quit, /stats, /sessions, etc.
      executor.ts               # Routes parsed commands
      parser.ts                 # Parses slash commands vs prompts
      registry.ts               # Map-backed command registry
      types.ts                  # Command type hierarchy
    entry/                      # CLI entry points
      cli.tsx                   # Main entry: flag parsing, command routing
      execCommand.ts            # `athena exec` handler
      interactiveSession.ts     # Session resolution for interactive mode
      workflowCommand.ts        # `athena workflow <sub>` handler
      marketplaceCommand.ts     # `athena marketplace <sub>` handler
    exec/                       # Non-interactive execution engine
      runner.ts                 # Core exec loop
      types.ts                  # ExecRunOptions, exit codes
      policies.ts               # Permission & question policies
      output.ts                 # JSONL output writer
      finalMessage.ts           # Final assistant message resolution
    process/                    # Harness process lifecycle
    providers/                  # React context providers
    runtime/                    # Runtime factory
    shell/                      # Interactive terminal UI
      AppShell.tsx              # Root Ink component
      useShellInput.ts          # Input handling
      useGlobalKeyboard.ts      # Keyboard shortcuts
    workflow/                   # Workflow picker UI
    setup/                      # First-run setup wizard

  core/                         # Domain logic (harness-neutral)
    controller/                 # Event routing & decision logic
      runtimeController.ts      # Event processing, rule matching
      rules.ts                  # HookRule matching (deny-first)
      permission.ts             # Permission queue management
    feed/                       # Event feed system (observability)
      types.ts                  # FeedEvent discriminated union (27 kinds)
      entities.ts               # Session, Run, Actor entities
      mapper.ts                 # RuntimeEvent → FeedEvent[] transformation
      feedStore.ts              # In-memory feed state
      timeline.ts               # Timeline projection
      filter.ts                 # Event filtering
      toolDisplay.ts            # Tool call rendering
      todo.ts                   # TodoWrite extraction
      agentChain.ts             # Agent chain tracking
    runtime/                    # Runtime boundary types
      types.ts                  # Runtime interface, RuntimeEvent, RuntimeDecision
      events.ts                 # RuntimeEventKind union (28 kinds)
      connector.ts              # RuntimeConnector alias
      process.ts                # HarnessProcess, TurnContinuation
    workflows/                  # Workflow engine
      types.ts                  # WorkflowConfig, LoopConfig
      registry.ts               # Workflow CRUD
      applyWorkflow.ts          # Template substitution
      plan.ts                   # WorkflowPlan compilation
      sessionPlan.ts            # Lifecycle management
      loopManager.ts            # Loop execution
      installer.ts              # Plugin marketplace resolution

  harnesses/                    # Harness adapter layer
    adapter.ts                  # HarnessAdapter interface
    registry.ts                 # Adapter resolution
    claude/                     # Claude Code harness
      adapter.ts                # claudeHarnessAdapter
      hook-forwarder.ts         # Standalone UDS forwarder script
      config/                   # Isolation, flags, model resolution
      hooks/                    # Hook settings generation
      process/                  # claude -p spawning
      protocol/                 # Wire types, event types
      runtime/                  # UDS server, event translation
      session/                  # Session controller
      system/                   # Binary detection, version
    codex/                      # OpenAI Codex harness
      adapter.ts                # codexHarnessAdapter
      protocol/                 # JSON-RPC types, methods
      runtime/                  # App server manager, event translation
      session/                  # Session controller

  infra/                        # Infrastructure layer
    plugins/                    # Plugin loading, marketplace, MCP merging
    sessions/                   # SQLite store, schema, registry
    telemetry/                  # PostHog client

  shared/                       # Shared types and utilities
  ui/                           # Theme system
```

## Build System

```bash
npm run build        # tsup (ESM, code splitting)
npm test             # vitest run
npm run typecheck    # tsc --noEmit
npm run lint         # prettier + eslint
npm run dev          # tsup --watch
npm run protocol:codex  # Regenerate Codex protocol bindings
```

## CI/CD

- GitHub Actions (`ci.yml`, `release.yml`)
- release-please for automated releases
- Conventional commits enforced via commitlint

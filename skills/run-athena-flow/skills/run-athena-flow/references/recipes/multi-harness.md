# Multi-Harness Setup: Claude Code + Codex

Athena supports both Claude Code and OpenAI Codex as production harnesses. The same workflows run on both — the harness abstraction normalizes events so plugins and the UI behave identically.

## Feature Comparison

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Session persistence | Yes | Yes |
| MCP servers | Yes | Yes |
| Workflows + loops | Yes | Yes |
| Isolation presets | Yes | Yes |
| Ephemeral sessions | Yes | Yes |
| Skills / commands | Yes | Yes |

## Switching Harnesses

Set the harness in your config:

```json
// ~/.config/athena/config.json
{
  "harness": "openai-codex"
}
```

Or select it during the setup wizard:

```bash
athena-flow setup
```

## Integration Differences

**Claude Code** — Uses hook-forwarding over a Unix Domain Socket. The `athena-hook-forwarder` binary receives hook events from Claude Code's hooks system and streams NDJSON to the runtime.

**OpenAI Codex** — Uses a JSON-RPC app-server protocol. Events from Codex are translated to Athena's `RuntimeEvent` schema via a comprehensive event translation layer. Codex uses a persistent thread conversation model with turn-based session management.

Both produce the same normalized event stream. The UI, plugins, and workflows see identical `RuntimeEvent` objects.

## Same Workflow, Two Harnesses

A workflow runs identically on both:

```json
{
  "name": "e2e-test-builder",
  "plugins": ["e2e-test-builder@lespaceman/athena-workflow-marketplace"],
  "promptTemplate": "Add E2E tests...",
  "loop": { "enabled": true, "completionMarker": "ATHENA_COMPLETE", "maxIterations": 10 },
  "isolation": "minimal"
}
```

No workflow changes needed when switching harnesses.

## Prerequisites

**Claude Code:**
- `claude` binary on PATH
- Authenticated (run `claude` to verify)

**OpenAI Codex:**
- `codex` binary on PATH (minimum version 0.37.0)
- Authenticated

## Recommendation

Both harnesses are production-ready. Choose based on your preferred agent runtime. Workflow definitions are portable across harnesses — you can switch at any time without modifying your workflows or plugins.

## Planned Harnesses

| Harness | Status |
|---------|--------|
| `opencode` | Coming soon — adapter placeholder exists but not yet enabled |

---
name: build-agent-cli
description: "Use skill if you are building CLI tools that AI agents will invoke, designing structured output formats, exit codes, non-interactive modes, or deciding between MCP servers and CLIs."
---

# build-agent-cli

> Build CLI tools that AI agents can reliably invoke, parse, and compose.

## Quick Reference Checklist

```
□ --json flag outputs structured data to stdout
□ Logs/progress go to stderr, never stdout
□ Exit codes: 0=ok, 2=usage, 3=not-found, 4=auth, 5=conflict, 6=validation, 7=transient
□ --non-interactive / --yes flags for headless execution
□ --help shows examples, not just flag descriptions
□ Commands are idempotent where semantically possible
□ Error responses include: class, code, message, retryable, suggestion
□ Noun-verb grammar: mycli <resource> <action>
□ Consistent field names across all commands
□ --dry-run for destructive operations
```

---

## MCP vs CLI Decision Tree

```
START: Does the operation need state across calls?
  │
  ├─ YES (browser session, DB connection, auth flow)
  │     └─→ MCP SERVER
  │
  └─ NO (stateless, one-shot)
        │
        Does it need enterprise governance (OAuth, audit, RBAC)?
        │
        ├─ YES → MCP SERVER
        │
        └─ NO
              │
              Is shell access available?
              │
              ├─ NO → MCP SERVER
              │
              └─ YES
                    │
                    Is token efficiency critical? (CLI is ~50x cheaper)
                    │
                    ├─ YES → CLI
                    │
                    └─ NO
                          │
                          Does a well-known CLI exist? (gh, kubectl, aws, docker)
                          │
                          ├─ YES → CLI (better LLM training data)
                          │
                          └─ NO
                                │
                                Is tool surface large with progressive disclosure needs?
                                │
                                ├─ YES → MCP SERVER
                                └─ NO → CLI
```

**Rule of thumb**: Prefer CLI for simple CRUD. Use MCP for sessions, enterprise, or complex tool surfaces.

---

## Core Patterns

### 1. Output Contract

#### JSON Envelope

```json
// Success
{
  "ok": true,
  "command": "resource create",
  "schema_version": "1.0",
  "result": {
    "id": "res_abc123",
    "status": "created",
    "url": "https://..."
  }
}

// Error
{
  "ok": false,
  "command": "resource create",
  "schema_version": "1.0",
  "error": {
    "class": "validation",
    "code": "INVALID_NAME",
    "message": "Resource name must be alphanumeric",
    "retryable": false,
    "suggestion": "Use --name with only a-z, 0-9, hyphens",
    "details": {
      "field": "name",
      "provided": "my resource!",
      "pattern": "^[a-z0-9-]+$"
    }
  }
}
```

#### Exit Code Table

| Code | Class | When to Use | Agent Action |
|------|-------|-------------|--------------|
| 0 | success | Operation completed | Continue |
| 1 | unknown | Unexpected error | Report to user |
| 2 | usage | Bad flags/args, malformed input | Fix invocation |
| 3 | not_found | Resource doesn't exist | Create or skip |
| 4 | auth | Auth failed/expired/forbidden | Re-auth or escalate |
| 5 | conflict | Resource state conflict | Resolve or force |
| 6 | validation | Business rule violation | Fix input data |
| 7 | transient | Network, rate limit, timeout | Retry with backoff |

#### Stream Rules

- **stdout**: JSON data only (parseable)
- **stderr**: Logs, progress, human messages
- **Never mix**: An agent must `cmd --json 2>/dev/null` and get clean JSON

→ Deep dive: [references/output-contracts.md](references/output-contracts.md)

---

### 2. Command Grammar

#### Noun-Verb Hierarchy

```bash
mycli user create --name alice
mycli user list --limit 10 --json
mycli job status JOB_ID
mycli job cancel JOB_ID --force
mycli config set key=value
```

#### Standard Global Flags

| Flag | Purpose |
|------|---------|
| `--json` | Output structured JSON |
| `--quiet` / `-q` | Suppress non-essential output |
| `--non-interactive` | Fail rather than prompt |
| `--yes` / `-y` | Auto-confirm destructive actions |
| `--dry-run` | Show what would happen |
| `--profile NAME` | Use named credential profile |
| `--verbose` / `-v` | Increase log verbosity |

#### Help Must Include Examples

```bash
$ mycli user create --help
Create a new user account.

USAGE:
  mycli user create --name NAME --email EMAIL [--role ROLE]

FLAGS:
  --name     User display name (required)
  --email    Email address (required)
  --role     One of: admin, member, viewer (default: member)
  --json     Output result as JSON

EXAMPLES:
  # Create admin user
  mycli user create --name "Alice" --email alice@co.com --role admin

  # Create member and capture ID
  ID=$(mycli user create --name "Bob" --email bob@co.com --json | jq -r '.result.id')
```

→ Deep dive: [references/discovery-and-auth.md](references/discovery-and-auth.md)

---

### 3. Execution Semantics

#### Idempotency Verbs

| Verb | Semantics | Idempotent? |
|------|-----------|-------------|
| `create` | Fail if exists | No |
| `ensure` | Create if missing, noop if exists | Yes |
| `apply` | Create or update to match spec | Yes |
| `delete` | Fail if missing | No |
| `remove` | Delete if exists, noop if missing | Yes |
| `sync` | Reconcile to desired state | Yes |

#### Non-Interactive Mode

```bash
# Detect headless environment
if [ -z "$TERM" ] || [ "$CI" = "true" ]; then
  INTERACTIVE=false
fi

# Never prompt in non-interactive
if ! $INTERACTIVE && needs_confirmation; then
  echo "Error: Destructive action requires --yes flag" >&2
  exit 2
fi
```

#### Dry Run Contract

```json
{
  "ok": true,
  "dry_run": true,
  "command": "resource delete",
  "would_affect": [
    {"id": "res_1", "action": "delete"},
    {"id": "res_2", "action": "delete"}
  ],
  "warnings": ["This will delete 2 resources permanently"]
}
```

→ Deep dive: [references/execution-patterns.md](references/execution-patterns.md)

---

### 4. Long-Running Operations

#### JSONL Streaming Progress

```bash
$ mycli deploy apply --json
{"type": "progress", "phase": "validating", "pct": 10}
{"type": "progress", "phase": "building", "pct": 30}
{"type": "progress", "phase": "deploying", "pct": 70}
{"type": "result", "ok": true, "result": {"deployment_id": "dep_xyz"}}
```

#### Async Job Pattern

```bash
# Start async
$ mycli job start --json
{"ok": true, "result": {"job_id": "job_123", "status": "pending"}}

# Poll status
$ mycli job status job_123 --json
{"ok": true, "result": {"job_id": "job_123", "status": "running", "progress": 45}}

# Wait for completion (blocks)
$ mycli job wait job_123 --timeout 300 --json
{"ok": true, "result": {"job_id": "job_123", "status": "completed", "output": {...}}}

# Cancel if needed
$ mycli job cancel job_123 --json
{"ok": true, "result": {"job_id": "job_123", "status": "cancelled"}}
```

→ Deep dive: [references/execution-patterns.md](references/execution-patterns.md)

---

### 5. Batch Operations

#### Chunking Pattern

```bash
# Process items in batches, output per-item results
$ mycli item process --batch items.json --json
{"type": "item", "id": "a", "ok": true}
{"type": "item", "id": "b", "ok": false, "error": {"code": "INVALID"}}
{"type": "item", "id": "c", "ok": true}
{"type": "summary", "total": 3, "succeeded": 2, "failed": 1}
```

#### Partial Failure Handling

```json
{
  "ok": false,
  "partial": true,
  "command": "batch create",
  "results": [
    {"id": "item_1", "ok": true, "result": {...}},
    {"id": "item_2", "ok": false, "error": {"code": "DUPLICATE"}},
    {"id": "item_3", "ok": true, "result": {...}}
  ],
  "summary": {
    "total": 3,
    "succeeded": 2,
    "failed": 1
  }
}
```

Exit code for partial failure: Use **highest severity** error code from failed items.

---

## Anti-Patterns

### ❌ Output Anti-Patterns

```bash
# BAD: Progress mixed with JSON
{"status": "creating"}
Creating resource... done!  # ← Human text breaks parsing
{"id": "res_123"}

# GOOD: Progress to stderr, JSON to stdout
$ cmd 2>&1 | head -1
Creating resource... done!
$ cmd 2>/dev/null
{"ok": true, "result": {"id": "res_123"}}
```

### ❌ Exit Code Anti-Patterns

```bash
# BAD: Exit 1 for everything
exit 1  # Auth failure? Validation? Not found? Who knows!

# GOOD: Semantic exit codes
case $error_type in
  auth) exit 4 ;;
  not_found) exit 3 ;;
  validation) exit 6 ;;
esac
```

### ❌ Interactivity Anti-Patterns

```bash
# BAD: Mandatory prompt
read -p "Are you sure? [y/N] " confirm

# GOOD: Flag-controlled with CI detection
if [ "$YES_FLAG" = "true" ] || [ "$CI" = "true" ]; then
  confirm="y"
else
  read -p "Are you sure? [y/N] " confirm
fi
```

### ❌ Help Anti-Patterns

```
# BAD: Flags only, no examples
FLAGS:
  --name    The name
  --email   The email

# GOOD: Examples show real usage patterns
EXAMPLES:
  mycli user create --name "Alice" --email a@b.com --json
  mycli user create --name "Bob" --role admin
```

### ❌ Error Anti-Patterns

```json
// BAD: Unhelpful error
{"error": "failed"}

// BAD: Human-only error
{"error": "Something went wrong! Please try again later."}

// GOOD: Machine-parseable with recovery hints
{
  "error": {
    "class": "auth",
    "code": "TOKEN_EXPIRED",
    "message": "Access token expired",
    "retryable": true,
    "suggestion": "Run 'mycli auth refresh' or 'mycli auth login'"
  }
}
```

---

## References

Detailed documentation:

- **[references/output-contracts.md](references/output-contracts.md)** — JSON schemas, exit codes, streaming formats, error shapes
- **[references/execution-patterns.md](references/execution-patterns.md)** — Idempotency, dry-run, batch ops, transactions, async jobs
- **[references/discovery-and-auth.md](references/discovery-and-auth.md)** — Self-documentation, auth flows, credential management
- **[references/mcp-vs-cli-decision.md](references/mcp-vs-cli-decision.md)** — When to build MCP vs CLI, hybrid patterns
- **[references/examples.md](references/examples.md)** — Reference implementations in Go, Python, Node.js

---

## Summary

Build CLIs that agents can trust:

1. **Structured output** — JSON to stdout, logs to stderr
2. **Semantic exit codes** — Agents route on code, not message parsing
3. **Non-interactive default** — Prompt only when TTY and no `--yes`
4. **Self-documenting** — `--help` is the API spec
5. **Idempotent operations** — Safe to retry, safe to rerun
6. **Clear error contracts** — Class, code, retryable, suggestion

When in doubt: **Can an agent invoke this command, parse the output, and decide what to do next without human intervention?** If yes, you've built an agent-friendly CLI.

# Output Contracts Reference

This document defines the output standards that make CLIs agent-friendly. Following these contracts ensures AI agents can reliably parse responses, handle errors, and orchestrate complex workflows.

---

## 1. Structured Output Standards

### JSON Output Requirements

Every agent-friendly CLI must support structured JSON output:

| Requirement | Implementation |
|-------------|----------------|
| Flag | `--json` or `--output json` |
| stdout | Data ONLY — no logs, no progress, no warnings |
| stderr | Logs, progress indicators, warnings, debug info |
| Structure | Prefer flat over deeply nested |
| Types | Consistent — numbers stay numbers, dates as ISO 8601 |

### Success Envelope

All successful operations return this structure:

```json
{
  "ok": true,
  "command": "deploy apply",
  "schema_version": "1.0",
  "result": {
    "id": "deploy_123",
    "status": "succeeded",
    "resources_created": 3
  },
  "meta": {
    "truncated": false,
    "total_count": 3,
    "duration_ms": 1234
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Always `true` for success |
| `command` | string | The command that was executed |
| `schema_version` | string | Output schema version for forward compatibility |
| `result` | object | The actual operation result |
| `meta` | object | Metadata about the response |

### Error Envelope

All failures return this structure:

```json
{
  "ok": false,
  "error": {
    "class": "conflict",
    "code": "RESOURCE_EXISTS",
    "message": "Resource 'foo' already exists",
    "retryable": false,
    "suggestion": "Use --force to overwrite or choose a different name",
    "details": {
      "existing_id": "res_abc123",
      "created_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Always `false` for errors |
| `error.class` | string | Error category (see Error Classes) |
| `error.code` | string | Machine-readable error code |
| `error.message` | string | Human-readable description |
| `error.retryable` | boolean | Whether the operation can be retried |
| `error.suggestion` | string | Actionable fix suggestion |
| `error.details` | object | Additional context-specific information |

---

## 2. Exit Code Taxonomy

Exit codes enable agents to make retry decisions without parsing output.

| Code | Name | Meaning | Retry? |
|------|------|---------|--------|
| 0 | SUCCESS | Operation completed successfully | N/A |
| 1 | ERROR | General/unknown error | Maybe |
| 2 | USAGE_ERROR | Bad arguments, invalid syntax | No |
| 3 | NOT_FOUND | Resource doesn't exist | No |
| 4 | AUTH_DENIED | Permission/authentication failed | No |
| 5 | CONFLICT | Resource already exists, version mismatch | No (but check) |
| 6 | VALIDATION | Input validation failed | No |
| 7 | TRANSIENT | Network, timeout, rate limit | Yes |
| 8 | PARTIAL | Some operations succeeded, some failed | Check details |

> **Critical:** Document your exit codes explicitly in `--help` output and man pages!

### Exit Code Constants

Define constants to avoid magic numbers:

```go
// exitcodes.go
const (
    ExitSuccess     = 0
    ExitError       = 1
    ExitUsageError  = 2
    ExitNotFound    = 3
    ExitAuthDenied  = 4
    ExitConflict    = 5
    ExitValidation  = 6
    ExitTransient   = 7
    ExitPartial     = 8
)
```

```python
# exitcodes.py
class ExitCode:
    SUCCESS = 0
    ERROR = 1
    USAGE_ERROR = 2
    NOT_FOUND = 3
    AUTH_DENIED = 4
    CONFLICT = 5
    VALIDATION = 6
    TRANSIENT = 7
    PARTIAL = 8
```

```typescript
// exitcodes.ts
export const ExitCode = {
  SUCCESS: 0,
  ERROR: 1,
  USAGE_ERROR: 2,
  NOT_FOUND: 3,
  AUTH_DENIED: 4,
  CONFLICT: 5,
  VALIDATION: 6,
  TRANSIENT: 7,
  PARTIAL: 8,
} as const;
```

---

## 3. Error Classes

Standard error classes enable agents to reason about failures semantically:

| Class | Description | Example |
|-------|-------------|---------|
| `not_found` | Resource doesn't exist | File, user, project not found |
| `conflict` | Already exists or version mismatch | Duplicate name, stale ETag |
| `validation` | Input doesn't pass validation | Invalid email, bad format |
| `auth` | Authentication/authorization failed | Expired token, no permission |
| `rate_limit` | Rate limited | Too many requests |
| `timeout` | Operation timed out | API didn't respond |
| `network` | Network connectivity issue | DNS failure, connection refused |
| `internal` | Internal error (bug) | Unexpected nil pointer |

### Mapping Classes to Exit Codes

```go
func errorClassToExitCode(class string) int {
    switch class {
    case "not_found":
        return ExitNotFound
    case "conflict":
        return ExitConflict
    case "validation":
        return ExitValidation
    case "auth":
        return ExitAuthDenied
    case "rate_limit", "timeout", "network":
        return ExitTransient
    case "internal":
        return ExitError
    default:
        return ExitError
    }
}
```

---

## 4. JSONL Streaming

For long-running operations, use JSON Lines (newline-delimited JSON) to stream progress:

```jsonl
{"type":"progress","phase":"downloading","percent":25,"message":"Downloading dependencies..."}
{"type":"progress","phase":"downloading","percent":50}
{"type":"progress","phase":"building","percent":75}
{"type":"completed","status":"succeeded","result":{"id":"build_123"}}
```

### Event Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `progress` | Incremental progress update | `type`, `phase` |
| `log` | Log message | `type`, `level`, `message` |
| `completed` | Operation finished successfully | `type`, `status`, `result` |
| `error` | Operation failed | `type`, `error` |

### Streaming Requirements

1. **Include `type` field** — Enables event discrimination
2. **UTC ISO 8601 timestamps** — e.g., `2024-01-15T10:30:00Z`
3. **Flush after each line** — Unbuffered output for real-time processing
4. **One JSON object per line** — No pretty-printing in stream mode

### Implementation Examples

**Go:**
```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "time"
)

type ProgressEvent struct {
    Type      string    `json:"type"`
    Phase     string    `json:"phase"`
    Percent   int       `json:"percent,omitempty"`
    Message   string    `json:"message,omitempty"`
    Timestamp time.Time `json:"timestamp"`
}

type CompletedEvent struct {
    Type   string      `json:"type"`
    Status string      `json:"status"`
    Result interface{} `json:"result"`
}

func emitProgress(phase string, percent int, message string) {
    event := ProgressEvent{
        Type:      "progress",
        Phase:     phase,
        Percent:   percent,
        Message:   message,
        Timestamp: time.Now().UTC(),
    }
    data, _ := json.Marshal(event)
    fmt.Fprintln(os.Stdout, string(data))
    os.Stdout.Sync() // Flush immediately
}

func emitCompleted(result interface{}) {
    event := CompletedEvent{
        Type:   "completed",
        Status: "succeeded",
        Result: result,
    }
    data, _ := json.Marshal(event)
    fmt.Fprintln(os.Stdout, string(data))
}
```

**Python:**
```python
import json
import sys
from datetime import datetime, timezone


def emit_progress(phase: str, percent: int, message: str = None):
    event = {
        "type": "progress",
        "phase": phase,
        "percent": percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if message:
        event["message"] = message
    print(json.dumps(event), flush=True)


def emit_completed(result: dict):
    event = {
        "type": "completed",
        "status": "succeeded",
        "result": result,
    }
    print(json.dumps(event), flush=True)


def emit_error(error_class: str, code: str, message: str):
    event = {
        "type": "error",
        "error": {
            "class": error_class,
            "code": code,
            "message": message,
        },
    }
    print(json.dumps(event), flush=True)
    sys.exit(1)
```

**Node.js:**
```typescript
interface ProgressEvent {
  type: 'progress';
  phase: string;
  percent?: number;
  message?: string;
  timestamp: string;
}

interface CompletedEvent {
  type: 'completed';
  status: string;
  result: unknown;
}

function emitProgress(phase: string, percent?: number, message?: string): void {
  const event: ProgressEvent = {
    type: 'progress',
    phase,
    percent,
    message,
    timestamp: new Date().toISOString(),
  };
  console.log(JSON.stringify(event));
}

function emitCompleted(result: unknown): void {
  const event: CompletedEvent = {
    type: 'completed',
    status: 'succeeded',
    result,
  };
  console.log(JSON.stringify(event));
}
```

---

## 5. Field Selection

Allow agents to request only the fields they need:

```bash
# Select specific fields
mycli list resources --json --fields id,name,status

# Use jq expressions
mycli get resource foo --json --jq '.status'

# Combine with other filters
mycli list resources --json --fields id,status --filter "status=active"
```

### Implementation

```go
func filterFields(data map[string]interface{}, fields []string) map[string]interface{} {
    if len(fields) == 0 {
        return data
    }
    result := make(map[string]interface{})
    for _, field := range fields {
        if val, ok := data[field]; ok {
            result[field] = val
        }
    }
    return result
}
```

```python
def filter_fields(data: dict, fields: list[str]) -> dict:
    if not fields:
        return data
    return {k: v for k, v in data.items() if k in fields}
```

---

## 6. Pagination

For list operations that may return many results:

```json
{
  "ok": true,
  "result": [
    {"id": "res_001", "name": "Resource 1"},
    {"id": "res_002", "name": "Resource 2"}
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzfQ=="
  }
}
```

### Pagination Fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of items (if known) |
| `page` | integer | Current page number (1-indexed) |
| `per_page` | integer | Items per page |
| `has_more` | boolean | Whether more pages exist |
| `next_cursor` | string | Opaque cursor for next page |

### CLI Flags

```bash
# Page-based pagination
mycli list resources --page 2 --per-page 50

# Cursor-based pagination
mycli list resources --cursor "eyJpZCI6MTIzfQ=="

# Get all pages (use with caution)
mycli list resources --all
```

### Implementation

```go
type PaginationInfo struct {
    Total      int    `json:"total,omitempty"`
    Page       int    `json:"page"`
    PerPage    int    `json:"per_page"`
    HasMore    bool   `json:"has_more"`
    NextCursor string `json:"next_cursor,omitempty"`
}

type ListResponse struct {
    OK         bool            `json:"ok"`
    Result     []Resource      `json:"result"`
    Pagination *PaginationInfo `json:"pagination,omitempty"`
}
```

---

## 7. Quiet Mode

`--quiet` or `-q` produces minimal, pipeline-friendly output:

```bash
# List: Just IDs, one per line
$ mycli list resources --quiet
res_001
res_002
res_003

# Create: Just the new ID
$ mycli create resource --name foo --quiet
res_004

# Delete: No output on success
$ mycli delete resource res_001 --quiet
```

### When to Use Quiet Mode

- Piping to other commands: `mycli list --quiet | xargs mycli delete`
- Capturing IDs in variables: `ID=$(mycli create --quiet)`
- Counting results: `mycli list --quiet | wc -l`

### Implementation

```go
var quietFlag bool

func init() {
    rootCmd.PersistentFlags().BoolVarP(&quietFlag, "quiet", "q", false, 
        "Minimal output suitable for pipelines")
}

func outputResult(id string, full interface{}) {
    if quietFlag {
        fmt.Println(id)
        return
    }
    if jsonFlag {
        data, _ := json.MarshalIndent(full, "", "  ")
        fmt.Println(string(data))
        return
    }
    // Human-readable output
    fmt.Printf("Created resource: %s\n", id)
}
```

---

## 8. Stream Separation Best Practices

Proper stream separation is critical for agent consumption.

### The Rule

| Stream | Content |
|--------|---------|
| **stdout** | Machine-parseable results ONLY |
| **stderr** | Progress, warnings, debug info, prompts, spinners |

### Never Do This

```go
// BAD: Mixing human text with JSON in stdout
fmt.Println("Creating resource...")  // Goes to stdout
data, _ := json.Marshal(result)
fmt.Println(string(data))            // Also stdout — can't parse!
```

### Do This Instead

```go
// GOOD: Separate streams
fmt.Fprintln(os.Stderr, "Creating resource...")  // Human text to stderr
data, _ := json.Marshal(result)
fmt.Fprintln(os.Stdout, string(data))            // JSON to stdout
```

### Verbose Mode

Use `--verbose` / `-v` to increase stderr detail, **never** stdout:

```go
var verboseLevel int

func log(level int, msg string) {
    if level <= verboseLevel {
        fmt.Fprintln(os.Stderr, msg)
    }
}

// Usage:
// -v     → verboseLevel 1 (info)
// -vv    → verboseLevel 2 (debug)
// -vvv   → verboseLevel 3 (trace)
```

### Complete Example

**Go:**
```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
)

func main() {
    // Progress to stderr
    fmt.Fprintln(os.Stderr, "Connecting to server...")
    
    // Simulate work
    result, err := doOperation()
    if err != nil {
        // Error JSON to stdout (for --json mode)
        response := map[string]interface{}{
            "ok": false,
            "error": map[string]interface{}{
                "class":   "network",
                "code":    "CONNECTION_FAILED",
                "message": err.Error(),
            },
        }
        json.NewEncoder(os.Stdout).Encode(response)
        os.Exit(7) // TRANSIENT
    }
    
    // Success JSON to stdout
    response := map[string]interface{}{
        "ok":     true,
        "result": result,
    }
    json.NewEncoder(os.Stdout).Encode(response)
    os.Exit(0)
}
```

**Python:**
```python
import json
import sys


def main():
    # Progress to stderr
    print("Connecting to server...", file=sys.stderr)
    
    try:
        result = do_operation()
    except NetworkError as e:
        # Error JSON to stdout
        response = {
            "ok": False,
            "error": {
                "class": "network",
                "code": "CONNECTION_FAILED",
                "message": str(e),
            },
        }
        print(json.dumps(response))
        sys.exit(7)  # TRANSIENT
    
    # Success JSON to stdout
    response = {
        "ok": True,
        "result": result,
    }
    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Node.js:**
```typescript
import { exit } from 'process';

async function main() {
  // Progress to stderr
  console.error('Connecting to server...');

  try {
    const result = await doOperation();
    
    // Success JSON to stdout
    console.log(JSON.stringify({
      ok: true,
      result,
    }));
    exit(0);
    
  } catch (error) {
    // Error JSON to stdout
    console.log(JSON.stringify({
      ok: false,
      error: {
        class: 'network',
        code: 'CONNECTION_FAILED',
        message: error.message,
      },
    }));
    exit(7); // TRANSIENT
  }
}

main();
```

---

## Quick Reference

### Output Mode Flags

| Flag | Output Type | Use Case |
|------|-------------|----------|
| (none) | Human-readable | Interactive terminal use |
| `--json` | JSON envelope | Agent/script consumption |
| `--quiet` | Bare IDs/values | Pipelines, variable capture |
| `--verbose` | Detailed stderr | Debugging |

### Exit Code Quick Reference

| Code | Retry? | Action |
|------|--------|--------|
| 0 | N/A | Success |
| 2 | No | Fix command syntax |
| 3 | No | Resource doesn't exist |
| 4 | No | Check credentials |
| 5 | No | Handle conflict |
| 6 | No | Fix input |
| 7 | Yes | Retry with backoff |
| 8 | Check | Inspect partial results |

### Checklist

- [ ] `--json` flag outputs structured JSON to stdout
- [ ] Errors include `class`, `code`, `message`, `retryable`
- [ ] Exit codes match the taxonomy
- [ ] Progress/logs go to stderr only
- [ ] Streaming operations use JSONL with `type` field
- [ ] Pagination includes `has_more` and cursor
- [ ] `--quiet` mode outputs bare values
- [ ] Exit codes are documented in `--help`

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

## 2. JSON Schema Definitions (Draft-07)

Formal schemas enable compile-time validation and IDE support for agent integrations.

### Success Response Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/success-response.json",
  "title": "SuccessResponse",
  "description": "Standard envelope for successful CLI operations",
  "type": "object",
  "required": ["ok", "result"],
  "properties": {
    "ok": {
      "type": "boolean",
      "const": true,
      "description": "Always true for success responses"
    },
    "command": {
      "type": "string",
      "description": "The command that was executed",
      "examples": ["deploy apply", "resource create", "config set"]
    },
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "Semantic version of the output schema",
      "default": "1.0"
    },
    "result": {
      "description": "The operation result payload (type varies by command)"
    },
    "meta": {
      "type": "object",
      "description": "Response metadata",
      "properties": {
        "truncated": {
          "type": "boolean",
          "description": "Whether the result was truncated",
          "default": false
        },
        "total_count": {
          "type": "integer",
          "minimum": 0,
          "description": "Total items available (for list operations)"
        },
        "duration_ms": {
          "type": "integer",
          "minimum": 0,
          "description": "Operation duration in milliseconds"
        },
        "request_id": {
          "type": "string",
          "description": "Unique request identifier for debugging"
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

### Error Response Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/error-response.json",
  "title": "ErrorResponse",
  "description": "Standard envelope for failed CLI operations",
  "type": "object",
  "required": ["ok", "error"],
  "properties": {
    "ok": {
      "type": "boolean",
      "const": false,
      "description": "Always false for error responses"
    },
    "error": {
      "type": "object",
      "required": ["class", "code", "message"],
      "properties": {
        "class": {
          "type": "string",
          "enum": [
            "not_found",
            "conflict",
            "validation",
            "auth",
            "rate_limit",
            "timeout",
            "network",
            "internal",
            "dependency_failed",
            "partial_success"
          ],
          "description": "Error category for semantic handling"
        },
        "code": {
          "type": "string",
          "pattern": "^[A-Z][A-Z0-9_]*$",
          "description": "Machine-readable error code (SCREAMING_SNAKE_CASE)",
          "examples": ["RESOURCE_EXISTS", "TOKEN_EXPIRED", "RATE_EXCEEDED"]
        },
        "message": {
          "type": "string",
          "minLength": 1,
          "description": "Human-readable error description"
        },
        "retryable": {
          "type": "boolean",
          "description": "Whether the operation can be retried",
          "default": false
        },
        "suggestion": {
          "type": "string",
          "description": "Actionable guidance for resolution"
        },
        "retry_after": {
          "type": "integer",
          "minimum": 0,
          "description": "Seconds to wait before retrying (for rate_limit)"
        },
        "details": {
          "type": "object",
          "description": "Additional context-specific information",
          "additionalProperties": true
        },
        "failed_operations": {
          "type": "array",
          "description": "List of failed items (for partial_success)",
          "items": {
            "type": "object",
            "required": ["id", "error"],
            "properties": {
              "id": { "type": "string" },
              "error": { "type": "string" }
            }
          }
        },
        "succeeded_operations": {
          "type": "array",
          "description": "List of succeeded items (for partial_success)",
          "items": {
            "type": "object",
            "required": ["id"],
            "properties": {
              "id": { "type": "string" },
              "result": {}
            }
          }
        }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

### Pagination Envelope Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/pagination.json",
  "title": "PaginationEnvelope",
  "description": "Pagination metadata for list operations",
  "type": "object",
  "required": ["has_more"],
  "properties": {
    "total": {
      "type": "integer",
      "minimum": 0,
      "description": "Total number of items (omit if unknown/expensive)"
    },
    "page": {
      "type": "integer",
      "minimum": 1,
      "description": "Current page number (1-indexed)"
    },
    "per_page": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "description": "Items per page",
      "default": 20
    },
    "has_more": {
      "type": "boolean",
      "description": "Whether additional pages exist"
    },
    "next_cursor": {
      "type": "string",
      "description": "Opaque cursor for fetching the next page"
    },
    "prev_cursor": {
      "type": "string",
      "description": "Opaque cursor for fetching the previous page"
    }
  },
  "additionalProperties": false
}
```

### Schema Validation Example

**TypeScript with Ajv:**
```typescript
import Ajv from 'ajv';
import successSchema from './schemas/success-response.json';
import errorSchema from './schemas/error-response.json';

const ajv = new Ajv({ allErrors: true });
const validateSuccess = ajv.compile(successSchema);
const validateError = ajv.compile(errorSchema);

function parseCliOutput(stdout: string): SuccessResponse | ErrorResponse {
  const data = JSON.parse(stdout);
  
  if (data.ok === true) {
    if (!validateSuccess(data)) {
      throw new Error(`Invalid success response: ${ajv.errorsText(validateSuccess.errors)}`);
    }
    return data as SuccessResponse;
  } else {
    if (!validateError(data)) {
      throw new Error(`Invalid error response: ${ajv.errorsText(validateError.errors)}`);
    }
    return data as ErrorResponse;
  }
}
```

---

## 3. Exit Code Taxonomy

Exit codes enable agents to make retry decisions without parsing output.

### Standard Exit Code Table

| Code | Name | When to Use | Retry? | Error Classes |
|------|------|-------------|--------|---------------|
| 0 | `success` | Operation completed successfully | N/A | — |
| 1 | `crash` | Unexpected error, internal failure, panic | Maybe | `internal` |
| 2 | `usage` | Bad flags, invalid arguments, wrong syntax | No | — |
| 3 | `not_found` | Requested resource does not exist | No | `not_found` |
| 4 | `auth` | Authentication or authorization failed | No | `auth` |
| 5 | `conflict` | Resource already exists, version mismatch, lock contention | No (check details) | `conflict` |
| 6 | `validation` | Input validation failed (schema, format, constraints) | No | `validation` |
| 7 | `transient` | Retry-able error (network, timeout, rate limit, dependency) | Yes | `rate_limit`, `timeout`, `network`, `dependency_failed` |
| 8 | `partial` | Some operations succeeded, some failed | No (check details) | `partial_success` |

> **Critical:** Document your exit codes explicitly in `--help` output and man pages!

### Exit Code Decision Tree

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Did the operation succeed?                    │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
            FULLY           PARTIALLY          NO
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────────────┐
        │ Exit 0   │    │ Exit 8   │    │ What went wrong? │
        │ success  │    │ partial  │    └──────────────────┘
        └──────────┘    └──────────┘             │
                        ┌───────────────────────┼───────────────────────┐
                        │                       │                       │
                   User's fault            Our fault             External fault
                        │                       │                       │
           ┌────────────┴────────┐              │              ┌────────┴────────┐
           │                     │              │              │                 │
     Bad arguments?        Bad input?           │         Retryable?        Not retryable?
           │                     │              │              │                 │
           ▼                     ▼              ▼              ▼                 ▼
      ┌──────────┐        ┌──────────┐    ┌──────────┐   ┌──────────┐      ┌──────────┐
      │ Exit 2   │        │ Exit 6   │    │ Exit 1   │   │ Exit 7   │      │ Exit 4/5 │
      │ usage    │        │validation│    │ crash    │   │transient │      │auth/conf │
      └──────────┘        └──────────┘    └──────────┘   └──────────┘      └──────────┘
```

### Exit Code Constants

Define constants to avoid magic numbers:

```go
// exitcodes.go
const (
    ExitSuccess    = 0  // Operation completed successfully
    ExitCrash      = 1  // Unexpected error, internal failure
    ExitUsage      = 2  // Bad flags, invalid arguments
    ExitNotFound   = 3  // Resource does not exist
    ExitAuth       = 4  // Authentication/authorization failed
    ExitConflict   = 5  // Resource conflict (exists, version mismatch)
    ExitValidation = 6  // Input validation failed
    ExitTransient  = 7  // Retryable error (network, timeout, rate limit)
    ExitPartial    = 8  // Partial success (some operations failed)
)
```

```python
# exitcodes.py
class ExitCode:
    SUCCESS = 0     # Operation completed successfully
    CRASH = 1       # Unexpected error, internal failure
    USAGE = 2       # Bad flags, invalid arguments
    NOT_FOUND = 3   # Resource does not exist
    AUTH = 4        # Authentication/authorization failed
    CONFLICT = 5    # Resource conflict (exists, version mismatch)
    VALIDATION = 6  # Input validation failed
    TRANSIENT = 7   # Retryable error (network, timeout, rate limit)
    PARTIAL = 8     # Partial success (some operations failed)
```

```typescript
// exitcodes.ts
export const ExitCode = {
  SUCCESS: 0,     // Operation completed successfully
  CRASH: 1,       // Unexpected error, internal failure
  USAGE: 2,       // Bad flags, invalid arguments
  NOT_FOUND: 3,   // Resource does not exist
  AUTH: 4,        // Authentication/authorization failed
  CONFLICT: 5,    // Resource conflict (exists, version mismatch)
  VALIDATION: 6,  // Input validation failed
  TRANSIENT: 7,   // Retryable error (network, timeout, rate limit)
  PARTIAL: 8,     // Partial success (some operations failed)
} as const;

export type ExitCodeValue = typeof ExitCode[keyof typeof ExitCode];
```

```rust
// exitcodes.rs
pub enum ExitCode {
    Success = 0,    // Operation completed successfully
    Crash = 1,      // Unexpected error, internal failure
    Usage = 2,      // Bad flags, invalid arguments
    NotFound = 3,   // Resource does not exist
    Auth = 4,       // Authentication/authorization failed
    Conflict = 5,   // Resource conflict (exists, version mismatch)
    Validation = 6, // Input validation failed
    Transient = 7,  // Retryable error (network, timeout, rate limit)
    Partial = 8,    // Partial success (some operations failed)
}
```

---

## 4. Error Classes

Standard error classes enable agents to reason about failures semantically:

| Class | Description | Example | Retryable |
|-------|-------------|---------|-----------|
| `not_found` | Resource doesn't exist | File, user, project not found | No |
| `conflict` | Already exists or version mismatch | Duplicate name, stale ETag | No |
| `validation` | Input doesn't pass validation | Invalid email, bad format | No |
| `auth` | Authentication/authorization failed | Expired token, no permission | No |
| `rate_limit` | Rate limited by server | Too many requests | Yes (with backoff) |
| `timeout` | Operation timed out | API didn't respond in time | Yes |
| `network` | Network connectivity issue | DNS failure, connection refused | Yes |
| `internal` | Internal error (bug) | Unexpected nil pointer | Maybe |
| `dependency_failed` | Upstream service unavailable | Database down, external API error | Yes |
| `partial_success` | Some operations succeeded, some failed | Batch with mixed results | No (check details) |

### Error Class Examples

#### rate_limit

```json
{
  "ok": false,
  "error": {
    "class": "rate_limit",
    "code": "RATE_EXCEEDED",
    "message": "Rate limit exceeded: 100 requests per minute",
    "retryable": true,
    "retry_after": 45,
    "suggestion": "Wait 45 seconds or use --rate-limit 50 to throttle requests",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "current_count": 102,
      "reset_at": "2024-01-15T10:31:00Z"
    }
  }
}
```

#### timeout

```json
{
  "ok": false,
  "error": {
    "class": "timeout",
    "code": "OPERATION_TIMEOUT",
    "message": "Operation timed out after 30 seconds",
    "retryable": true,
    "suggestion": "Retry with --timeout 60 or check service health",
    "details": {
      "timeout_ms": 30000,
      "operation": "api_call",
      "endpoint": "https://api.example.com/deploy",
      "last_status": "in_progress"
    }
  }
}
```

#### dependency_failed

```json
{
  "ok": false,
  "error": {
    "class": "dependency_failed",
    "code": "DATABASE_UNAVAILABLE",
    "message": "PostgreSQL connection failed: connection refused",
    "retryable": true,
    "suggestion": "Check database status with 'mycli db status' or retry in 30 seconds",
    "details": {
      "dependency": "postgresql",
      "host": "db.example.com:5432",
      "connection_attempts": 3,
      "last_error": "connection refused"
    }
  }
}
```

#### partial_success

```json
{
  "ok": false,
  "error": {
    "class": "partial_success",
    "code": "BATCH_PARTIAL_FAILURE",
    "message": "3 of 5 operations succeeded",
    "retryable": false,
    "suggestion": "Retry failed items with: mycli batch retry --failed-only",
    "details": {
      "total": 5,
      "succeeded": 3,
      "failed": 2
    },
    "succeeded_operations": [
      { "id": "res_001", "result": { "status": "created" } },
      { "id": "res_002", "result": { "status": "created" } },
      { "id": "res_003", "result": { "status": "created" } }
    ],
    "failed_operations": [
      { "id": "res_004", "error": "VALIDATION_FAILED", "message": "Invalid format" },
      { "id": "res_005", "error": "CONFLICT", "message": "Already exists" }
    ]
  }
}
```

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

### Stream Event Schema (Draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schemas.cli-agents.dev/stream-event.json",
  "title": "StreamEvent",
  "description": "Base schema for streaming JSONL events",
  "type": "object",
  "required": ["type"],
  "oneOf": [
    { "$ref": "#/definitions/ProgressEvent" },
    { "$ref": "#/definitions/LogEvent" },
    { "$ref": "#/definitions/CompletedEvent" },
    { "$ref": "#/definitions/ErrorEvent" },
    { "$ref": "#/definitions/HeartbeatEvent" },
    { "$ref": "#/definitions/PhaseEvent" }
  ],
  "definitions": {
    "ProgressEvent": {
      "type": "object",
      "required": ["type", "phase"],
      "properties": {
        "type": { "const": "progress" },
        "phase": { "type": "string", "description": "Current operation phase" },
        "percent": { "type": "integer", "minimum": 0, "maximum": 100 },
        "message": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "eta_seconds": { "type": "integer", "minimum": 0 },
        "items_processed": { "type": "integer", "minimum": 0 },
        "items_total": { "type": "integer", "minimum": 0 }
      }
    },
    "LogEvent": {
      "type": "object",
      "required": ["type", "level", "message"],
      "properties": {
        "type": { "const": "log" },
        "level": { "enum": ["debug", "info", "warn", "error"] },
        "message": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "context": { "type": "object", "additionalProperties": true }
      }
    },
    "CompletedEvent": {
      "type": "object",
      "required": ["type", "status", "result"],
      "properties": {
        "type": { "const": "completed" },
        "status": { "enum": ["succeeded", "failed", "cancelled"] },
        "result": { "description": "Operation result payload" },
        "duration_ms": { "type": "integer", "minimum": 0 }
      }
    },
    "ErrorEvent": {
      "type": "object",
      "required": ["type", "error"],
      "properties": {
        "type": { "const": "error" },
        "error": {
          "type": "object",
          "required": ["class", "code", "message"],
          "properties": {
            "class": { "type": "string" },
            "code": { "type": "string" },
            "message": { "type": "string" },
            "retryable": { "type": "boolean" }
          }
        }
      }
    },
    "HeartbeatEvent": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": { "const": "heartbeat" },
        "timestamp": { "type": "string", "format": "date-time" },
        "uptime_ms": { "type": "integer", "minimum": 0 }
      }
    },
    "PhaseEvent": {
      "type": "object",
      "required": ["type", "phase", "status"],
      "properties": {
        "type": { "const": "phase" },
        "phase": { "type": "string" },
        "status": { "enum": ["started", "completed", "skipped", "failed"] },
        "timestamp": { "type": "string", "format": "date-time" },
        "duration_ms": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```

### Event Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `progress` | Incremental progress update | `type`, `phase` |
| `log` | Log message | `type`, `level`, `message` |
| `completed` | Operation finished successfully | `type`, `status`, `result` |
| `error` | Operation failed | `type`, `error` |
| `heartbeat` | Keep-alive signal for long operations | `type` |
| `phase` | Phase transition marker | `type`, `phase`, `status` |

### Progress Event Patterns

#### Percentage-based Progress
```jsonl
{"type":"progress","phase":"upload","percent":0,"message":"Starting upload...","timestamp":"2024-01-15T10:30:00Z"}
{"type":"progress","phase":"upload","percent":25,"message":"Uploading file 1/4","timestamp":"2024-01-15T10:30:05Z"}
{"type":"progress","phase":"upload","percent":50,"message":"Uploading file 2/4","timestamp":"2024-01-15T10:30:10Z"}
{"type":"progress","phase":"upload","percent":75,"message":"Uploading file 3/4","timestamp":"2024-01-15T10:30:15Z"}
{"type":"progress","phase":"upload","percent":100,"message":"Upload complete","timestamp":"2024-01-15T10:30:20Z"}
```

#### Item-based Progress (Unknown Total)
```jsonl
{"type":"progress","phase":"scan","items_processed":0,"message":"Starting scan..."}
{"type":"progress","phase":"scan","items_processed":150,"message":"Scanning files..."}
{"type":"progress","phase":"scan","items_processed":423,"message":"Scanning files..."}
{"type":"completed","status":"succeeded","result":{"files_scanned":423,"issues_found":12}}
```

#### Multi-Phase Progress
```jsonl
{"type":"phase","phase":"download","status":"started","timestamp":"2024-01-15T10:30:00Z"}
{"type":"progress","phase":"download","percent":50}
{"type":"phase","phase":"download","status":"completed","duration_ms":5000}
{"type":"phase","phase":"extract","status":"started"}
{"type":"progress","phase":"extract","percent":30}
{"type":"phase","phase":"extract","status":"completed","duration_ms":2000}
{"type":"phase","phase":"install","status":"started"}
{"type":"progress","phase":"install","percent":80}
{"type":"phase","phase":"install","status":"completed","duration_ms":8000}
{"type":"completed","status":"succeeded","result":{"installed":"package@1.2.3"}}
```

#### Long-Running Operations with Heartbeat
```jsonl
{"type":"progress","phase":"training","percent":0,"eta_seconds":3600}
{"type":"heartbeat","timestamp":"2024-01-15T10:30:30Z","uptime_ms":30000}
{"type":"progress","phase":"training","percent":5,"eta_seconds":3420}
{"type":"heartbeat","timestamp":"2024-01-15T10:31:00Z","uptime_ms":60000}
{"type":"progress","phase":"training","percent":10,"eta_seconds":3240}
```

### Streaming Requirements

1. **Include `type` field** — Enables event discrimination
2. **UTC ISO 8601 timestamps** — e.g., `2024-01-15T10:30:00Z`
3. **Flush after each line** — Unbuffered output for real-time processing
4. **One JSON object per line** — No pretty-printing in stream mode
5. **Heartbeats for long operations** — Emit every 30s to prevent timeout detection
6. **Monotonic progress** — Percent should never decrease within a phase

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
| `--stream` / `--follow` | JSONL events | Real-time progress monitoring |

### Exit Code Quick Reference

| Code | Name | Retry? | Action |
|------|------|--------|--------|
| 0 | success | N/A | Operation succeeded |
| 1 | crash | Maybe | Internal error — check logs |
| 2 | usage | No | Fix command syntax |
| 3 | not_found | No | Resource doesn't exist |
| 4 | auth | No | Check credentials |
| 5 | conflict | No | Handle conflict (force/rename) |
| 6 | validation | No | Fix input format/values |
| 7 | transient | Yes | Retry with exponential backoff |
| 8 | partial | Check | Inspect succeeded/failed lists |

### Error Class Quick Reference

| Class | Exit Code | Retryable | Common Causes |
|-------|-----------|-----------|---------------|
| `not_found` | 3 | No | Missing resource, invalid ID |
| `auth` | 4 | No | Expired token, missing permissions |
| `conflict` | 5 | No | Duplicate resource, stale version |
| `validation` | 6 | No | Invalid format, constraint violation |
| `rate_limit` | 7 | Yes | Too many requests |
| `timeout` | 7 | Yes | Operation exceeded time limit |
| `network` | 7 | Yes | Connection failed, DNS error |
| `dependency_failed` | 7 | Yes | Upstream service unavailable |
| `internal` | 1 | Maybe | Bug, unexpected state |
| `partial_success` | 8 | No | Batch with mixed results |

### Checklist

- [ ] `--json` flag outputs structured JSON to stdout
- [ ] Errors include `class`, `code`, `message`, `retryable`
- [ ] Exit codes match the taxonomy (0-8)
- [ ] Progress/logs go to stderr only
- [ ] Streaming operations use JSONL with `type` field
- [ ] Stream events include timestamps (ISO 8601 UTC)
- [ ] Pagination includes `has_more` and cursor
- [ ] `--quiet` mode outputs bare values
- [ ] Exit codes are documented in `--help`
- [ ] Long operations emit heartbeat events every 30s

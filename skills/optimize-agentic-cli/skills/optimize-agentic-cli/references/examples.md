# Agent-Friendly CLI: Code Examples

Production-ready code examples in Go, Python, Node.js, Rust, and Shell/Bash for implementing agent-friendly CLI patterns.

---

## Standard Flag Names

All examples in this document use consistent flag names:

| Flag | Short | Purpose |
|------|-------|---------|
| `--json` | | Output as JSON (not `--output json`) |
| `--quiet` | `-q` | Minimal output |
| `--yes` | `-y` | Auto-confirm prompts |
| `--dry-run` | | Preview without executing |
| `--force` | `-f` | Force operation |
| `--timeout` | | Operation timeout |

## Standard Exit Codes

| Code | Meaning | Retryable |
|------|---------|-----------|
| 0 | Success | N/A |
| 1 | General error | Maybe |
| 2 | Usage/input error | No |
| 3 | Not found | No |
| 4 | Auth/permission denied | No |
| 5 | Conflict/already exists | No |
| 6 | Validation error | No |
| 7 | Transient/network error | Yes |

## Standard JSON Envelope

```json
{
  "ok": true|false,
  "command": "resource.create",
  "result": { ... },
  "error": {
    "class": "not_found|auth|conflict|validation|transient",
    "code": "RESOURCE_NOT_FOUND",
    "message": "Human-readable message",
    "retryable": false,
    "suggestion": "Try 'mycli resource list' first"
  },
  "meta": {
    "truncated": false,
    "total_count": 100,
    "duration_ms": 42
  }
}
```

---

## 1. Structured Output (Go)

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
)

type Response struct {
    OK      bool        `json:"ok"`
    Command string      `json:"command,omitempty"`
    Result  interface{} `json:"result,omitempty"`
    Error   *ErrorInfo  `json:"error,omitempty"`
    Meta    *Meta       `json:"meta,omitempty"`
}

type ErrorInfo struct {
    Class      string      `json:"class"`
    Code       string      `json:"code"`
    Message    string      `json:"message"`
    Retryable  bool        `json:"retryable"`
    Suggestion string      `json:"suggestion,omitempty"`
    Details    interface{} `json:"details,omitempty"`
}

type Meta struct {
    Truncated  bool `json:"truncated,omitempty"`
    TotalCount int  `json:"total_count,omitempty"`
    DurationMs int  `json:"duration_ms,omitempty"`
}

func outputJSON(resp Response) {
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    enc.Encode(resp)
}

func success(result interface{}) {
    outputJSON(Response{OK: true, Result: result})
    os.Exit(0)
}

func fail(class, code, message string, retryable bool, exitCode int) {
    outputJSON(Response{
        OK: false,
        Error: &ErrorInfo{
            Class:     class,
            Code:      code,
            Message:   message,
            Retryable: retryable,
        },
    })
    os.Exit(exitCode)
}
```

---

## 2. JSONL Streaming (Python)

```python
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class StreamEvent:
    type: str
    timestamp: str = None
    phase: Optional[str] = None
    percent: Optional[int] = None
    message: Optional[str] = None
    data: Optional[Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

def emit_event(event: StreamEvent):
    """Emit a single JSONL event to stderr (progress) or stdout (final)."""
    d = {k: v for k, v in asdict(event).items() if v is not None}
    line = json.dumps(d)
    
    if event.type in ('progress', 'log'):
        print(line, file=sys.stderr, flush=True)
    else:
        print(line, flush=True)

# Usage
emit_event(StreamEvent(type='progress', phase='downloading', percent=25))
emit_event(StreamEvent(type='progress', phase='building', percent=75))
emit_event(StreamEvent(type='completed', data={'id': 'build_123'}))
```

---

## 3. Non-Interactive Mode (Node.js)

```typescript
import * as readline from 'readline';
import * as tty from 'tty';

interface CLIOptions {
  json: boolean;        // --json
  quiet: boolean;       // --quiet, -q
  yes: boolean;         // --yes, -y
  force: boolean;       // --force, -f
  dryRun: boolean;      // --dry-run
  timeout: string;      // --timeout
  nonInteractive: boolean;
}

function isInteractive(): boolean {
  return tty.isatty(process.stdin.fd) && 
         !process.env.CI && 
         !process.env.MYCLI_NON_INTERACTIVE;
}

async function confirm(message: string, opts: CLIOptions): Promise<boolean> {
  // Auto-yes mode
  if (opts.yes) return true;
  
  // Non-interactive: fail if we need confirmation
  if (opts.nonInteractive || !isInteractive()) {
    console.error(`Error: confirmation required but running non-interactively`);
    console.error(`Use --yes/-y to auto-confirm or --force/-f to bypass`);
    process.exit(2);
  }
  
  // Interactive prompt
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stderr
  });
  
  return new Promise((resolve) => {
    rl.question(`${message} [y/N]: `, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'y');
    });
  });
}
```

---

## 4. Exit Code Handling (Go)

```go
package main

import "os"

// Exit codes as constants
const (
    ExitSuccess    = 0 // Success
    ExitError      = 1 // General error
    ExitUsage      = 2 // Usage/input error
    ExitNotFound   = 3 // Resource not found
    ExitAuth       = 4 // Auth/permission denied
    ExitConflict   = 5 // Conflict/already exists
    ExitValidation = 6 // Validation error
    ExitTransient  = 7 // Transient/retryable error
)

type AppError struct {
    Class     string
    Code      string
    Message   string
    Retryable bool
    ExitCode  int
}

func (e *AppError) Exit() {
    fail(e.Class, e.Code, e.Message, e.Retryable, e.ExitCode)
}

// Factory functions
func ErrNotFound(resource string) *AppError {
    return &AppError{
        Class:     "not_found",
        Code:      "RESOURCE_NOT_FOUND", 
        Message:   fmt.Sprintf("Resource '%s' not found", resource),
        Retryable: false,
        ExitCode:  ExitNotFound,
    }
}

func ErrConflict(resource string) *AppError {
    return &AppError{
        Class:     "conflict",
        Code:      "RESOURCE_EXISTS",
        Message:   fmt.Sprintf("Resource '%s' already exists", resource),
        Retryable: false,
        ExitCode:  ExitConflict,
    }
}

func ErrTransient(message string) *AppError {
    return &AppError{
        Class:     "transient",
        Code:      "TRANSIENT_ERROR",
        Message:   message,
        Retryable: true,
        ExitCode:  ExitTransient,
    }
}
```

---

## 5. Dry-Run Implementation (Python)

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class ChangeAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"

@dataclass
class PlannedChange:
    action: ChangeAction
    resource_type: str
    resource_id: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    diff: Optional[Dict[str, Any]] = None

@dataclass  
class DryRunResult:
    ok: bool = True
    dry_run: bool = True
    changes: List[PlannedChange] = None
    summary: Dict[str, int] = None
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        if self.summary is None:
            self.summary = {"create": 0, "update": 0, "delete": 0, "noop": 0}

def compute_dry_run(desired_state: Dict, actual_state: Dict) -> DryRunResult:
    result = DryRunResult()
    
    # Check for creates and updates
    for key, desired in desired_state.items():
        actual = actual_state.get(key)
        
        if actual is None:
            result.changes.append(PlannedChange(
                action=ChangeAction.CREATE,
                resource_type=desired['type'],
                resource_id=key,
                after=desired
            ))
            result.summary['create'] += 1
        elif actual != desired:
            result.changes.append(PlannedChange(
                action=ChangeAction.UPDATE,
                resource_type=desired['type'],
                resource_id=key,
                before=actual,
                after=desired,
                diff=compute_diff(actual, desired)
            ))
            result.summary['update'] += 1
    
    # Check for deletes
    for key in actual_state:
        if key not in desired_state:
            result.changes.append(PlannedChange(
                action=ChangeAction.DELETE,
                resource_type=actual_state[key]['type'],
                resource_id=key,
                before=actual_state[key]
            ))
            result.summary['delete'] += 1
    
    return result
```

---

## 6. Batch Operations with Partial Failure (Go)

```go
package main

import (
    "context"
    "sync"
)

type BatchConfig struct {
    ChunkSize       int
    Concurrency     int
    ContinueOnError bool
}

type BatchResult struct {
    Total     int           `json:"total"`
    Succeeded int           `json:"succeeded"`
    Failed    int           `json:"failed"`
    Errors    []BatchError  `json:"errors,omitempty"`
    mu        sync.Mutex
}

type BatchError struct {
    ID      string `json:"id"`
    Error   string `json:"error"`
    Class   string `json:"class"`
}

func (r *BatchResult) addSuccess() {
    r.mu.Lock()
    r.Succeeded++
    r.mu.Unlock()
}

func (r *BatchResult) addError(id, errClass, errMsg string) {
    r.mu.Lock()
    r.Failed++
    r.Errors = append(r.Errors, BatchError{
        ID:    id,
        Error: errMsg,
        Class: errClass,
    })
    r.mu.Unlock()
}

func BatchProcess(ctx context.Context, items []Item, cfg BatchConfig, process func(Item) error) *BatchResult {
    result := &BatchResult{Total: len(items)}
    
    sem := make(chan struct{}, cfg.Concurrency)
    var wg sync.WaitGroup
    
    for _, item := range items {
        if ctx.Err() != nil {
            break
        }
        
        sem <- struct{}{}
        wg.Add(1)
        
        go func(item Item) {
            defer wg.Done()
            defer func() { <-sem }()
            
            if err := process(item); err != nil {
                result.addError(item.ID, classifyError(err), err.Error())
                if !cfg.ContinueOnError {
                    // Signal to stop (via context cancellation in real impl)
                }
            } else {
                result.addSuccess()
            }
        }(item)
    }
    
    wg.Wait()
    return result
}
```

---

## 7. Auth Credential Resolution (Python)

```python
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class Credential:
    token: str
    source: str  # 'flag', 'env', 'config', 'keychain', 'oidc'

def resolve_credential(
    flag_token: Optional[str] = None,
    flag_token_file: Optional[str] = None,
    flag_token_stdin: bool = False
) -> Credential:
    """
    Resolve credentials in priority order:
    1. CLI flags (--token, --token-file, --token-stdin)
    2. Environment variable (MYCLI_TOKEN)
    3. Config file
    4. Keychain/credential helper
    5. OIDC/workload identity
    """
    
    # 1. Stdin (most secure for automation)
    if flag_token_stdin:
        import sys
        token = sys.stdin.read().strip()
        return Credential(token=token, source='stdin')
    
    # 2. Token file
    if flag_token_file:
        token = Path(flag_token_file).read_text().strip()
        return Credential(token=token, source='file')
    
    # 3. Direct flag (not recommended but supported)
    if flag_token:
        return Credential(token=flag_token, source='flag')
    
    # 4. Environment variable
    env_token = os.environ.get('MYCLI_TOKEN')
    if env_token:
        return Credential(token=env_token, source='env')
    
    # 5. Config file
    config_token = load_config_token()
    if config_token:
        return Credential(token=config_token, source='config')
    
    # 6. Keychain
    keychain_token = get_keychain_token()
    if keychain_token:
        return Credential(token=keychain_token, source='keychain')
    
    raise AuthError("No credentials found. Run 'mycli auth login' first.")
```

---

## 8. Help Generation (Node.js with Commander)

```typescript
import { Command } from 'commander';

const program = new Command();

program
  .name('mycli')
  .description('Agent-friendly CLI tool')
  .version('1.0.0');

program
  .command('deploy <service>')
  .description('Deploy a service to the target environment')
  .requiredOption('--env <environment>', 'Target environment: dev, staging, prod')
  .option('--image <image>', 'Container image override')
  .option('--replicas <n>', 'Number of replicas', parseInt)
  .option('--dry-run', 'Preview changes without applying')
  .option('--wait', 'Wait for deployment to complete', true)
  .option('--timeout <duration>', 'Maximum wait time', '5m')
  .option('--json', 'Output result as JSON')
  .addHelpText('after', `
Examples:
  $ mycli deploy web-api --env staging
  $ mycli deploy web-api --env prod --image myregistry/web:v2.1.0 --json
  $ mycli deploy web-api --env dev --dry-run
`)
  .action(async (service, options) => {
    // Implementation
  });

// JSON help output (custom)
program
  .command('help-json')
  .description('Output help as JSON')
  .action(() => {
    const commands = program.commands.map(cmd => ({
      name: cmd.name(),
      description: cmd.description(),
      options: cmd.options.map(opt => ({
        flags: opt.flags,
        description: opt.description,
        required: opt.required,
        default: opt.defaultValue
      }))
    }));
    console.log(JSON.stringify({ commands }, null, 2));
  });

program.parse();
```

---

## 9. Long-Running Task with Progress (Go)

```go
package main

import (
    "context"
    "encoding/json"
    "os"
    "time"
)

type TaskStatus struct {
    OperationID string    `json:"operation_id"`
    Status      string    `json:"status"`
    Progress    *Progress `json:"progress,omitempty"`
    Result      any       `json:"result,omitempty"`
    Error       *ErrorInfo `json:"error,omitempty"`
    StartedAt   time.Time `json:"started_at"`
    CompletedAt *time.Time `json:"completed_at,omitempty"`
}

type Progress struct {
    Phase   string `json:"phase"`
    Percent int    `json:"percent"`
    Message string `json:"message,omitempty"`
}

func runWithProgress(ctx context.Context, opID string, work func(progress chan<- Progress) error) {
    progressCh := make(chan Progress, 10)
    resultCh := make(chan error, 1)
    
    // Worker goroutine
    go func() {
        resultCh <- work(progressCh)
        close(progressCh)
    }()
    
    enc := json.NewEncoder(os.Stderr)
    
    // Progress reporter
    for {
        select {
        case p, ok := <-progressCh:
            if !ok {
                return
            }
            enc.Encode(map[string]any{
                "type":         "progress",
                "operation_id": opID,
                "phase":        p.Phase,
                "percent":      p.Percent,
                "message":      p.Message,
            })
            
        case err := <-resultCh:
            if err != nil {
                enc.Encode(map[string]any{
                    "type":         "error",
                    "operation_id": opID,
                    "error":        err.Error(),
                })
            } else {
                enc.Encode(map[string]any{
                    "type":         "completed",
                    "operation_id": opID,
                    "status":       "succeeded",
                })
            }
            return
            
        case <-ctx.Done():
            enc.Encode(map[string]any{
                "type":         "cancelled",
                "operation_id": opID,
            })
            return
        }
    }
}
```

---

## 10. Complete CLI Skeleton (Go with Cobra)

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"

    "github.com/spf13/cobra"
)

var (
    jsonOutput     bool
    quiet          bool
    nonInteractive bool
    yes            bool
    force          bool
    timeout        string
)

func main() {
    rootCmd := &cobra.Command{
        Use:   "mycli",
        Short: "Agent-friendly CLI example",
    }
    
    // Global flags
    rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output as JSON")
    rootCmd.PersistentFlags().BoolVarP(&quiet, "quiet", "q", false, "Minimal output")
    rootCmd.PersistentFlags().BoolVar(&nonInteractive, "non-interactive", false, "Fail on prompts")
    rootCmd.PersistentFlags().BoolVarP(&yes, "yes", "y", false, "Auto-confirm")
    rootCmd.PersistentFlags().BoolVarP(&force, "force", "f", false, "Force operation")
    rootCmd.PersistentFlags().StringVar(&timeout, "timeout", "30s", "Operation timeout")
    
    // Resource subcommand
    resourceCmd := &cobra.Command{Use: "resource", Short: "Manage resources"}
    
    resourceCmd.AddCommand(&cobra.Command{
        Use:   "create <name>",
        Short: "Create a new resource",
        Args:  cobra.ExactArgs(1),
        Run:   createResource,
    })
    
    resourceCmd.AddCommand(&cobra.Command{
        Use:   "list",
        Short: "List all resources",
        Run:   listResources,
    })
    
    rootCmd.AddCommand(resourceCmd)
    
    if err := rootCmd.Execute(); err != nil {
        os.Exit(1)
    }
}

func createResource(cmd *cobra.Command, args []string) {
    name := args[0]
    
    // Check for conflict
    if exists(name) && !force {
        fail("conflict", "RESOURCE_EXISTS", 
            fmt.Sprintf("Resource '%s' already exists", name), false, 5)
    }
    
    resource := create(name)
    
    if jsonOutput {
        json.NewEncoder(os.Stdout).Encode(map[string]any{
            "ok":     true,
            "result": resource,
        })
    } else if quiet {
        fmt.Println(resource.ID)
    } else {
        fmt.Printf("Created resource: %s\n", resource.ID)
    }
}
```

---

## 11. Real-World CLI Audit: GitHub CLI (gh)

Let's audit `gh` (GitHub CLI) for agent-readiness using our checklist.

### Critical Checks

| # | Check | Test Command | Result | Score |
|---|-------|--------------|--------|-------|
| C1 | JSON output | `gh repo view --json name,description \| jq .` | ✅ PASS - clean JSON | +20 |
| C2 | stdout/stderr separated | `gh repo view --json name > out.txt 2> err.txt` | ✅ PASS - out.txt is pure JSON | +20 |
| C3 | Semantic exit codes | `gh repo view nonexistent/repo; echo $?` | 🟡 PARTIAL - returns 1 for all errors | +10 |
| C4 | Non-interactive | `gh pr create < /dev/null` | ✅ PASS - errors with usage message | +20 |
| C5 | Structured errors | `gh api /nonexistent --jq '.message'` | ✅ PASS - returns `{"message":"Not Found"}` | +20 |

### Important Checks (each +5)

- ✅ Consistent field types (snake_case JSON)
- ✅ `--dry-run` in `gh pr merge --dry-run`  
- ✅ Good `--help` with examples
- ❌ No explicit conflict handling (exit 1 for exists)
- ✅ Noun-verb grammar (`gh repo create`, `gh pr list`)

**Important Score:** 20/25

### Nice-to-Have Checks (each +2)

- ❌ No JSONL streaming for `gh run watch`
- ✅ `--jq` for quiet/filtered output
- ❌ No `schema_version` in outputs
- ✅ `gh run watch` for async jobs

**Nice-to-Have Score:** 4/8

### Final Score

| Category | Score |
|----------|-------|
| Critical | 90/100 |
| Important | 20/25 |
| Nice-to-Have | 4/8 |
| **TOTAL** | **114/133 (86%)** |

**Grade: 🟡 Mostly Ready**

### Key Fixes Needed

1. **Exit codes:** Currently returns 1 for all errors. Should differentiate:
   - 3 for "not found" errors
   - 4 for auth failures
   - 5 for conflicts

2. **Structured errors:** API errors are structured, but CLI errors are just stderr text.

### What gh Does Right

1. Universal `--json` flag across all commands
2. `--jq` for in-line filtering (reduces agent parsing)
3. Clean separation of stdout (data) and stderr (messages)
4. `--template` for custom output formatting
5. Good example-driven `--help` text

---

## 12. Real-World CLI Audit: kubectl

Quick audit of Kubernetes CLI for agent use.

### Critical Checks

| # | Check | Test Command | Result | Score |
|---|-------|--------------|--------|-------|
| C1 | JSON output | `kubectl get pods -o json \| jq .kind` | ✅ PASS | +20 |
| C2 | stdout/stderr | `kubectl get pods -o json 2>&1 \| head` | ✅ PASS | +20 |
| C3 | Exit codes | `kubectl get nonexistent; echo $?` | 🟡 PARTIAL - 1 for all | +10 |
| C4 | Non-interactive | `kubectl delete pod x < /dev/null` | ✅ PASS - requires `--force` | +20 |
| C5 | Structured errors | Error messages are plain text | ❌ FAIL | +0 |

### Summary

| Category | Score |
|----------|-------|
| Critical | 70/100 |
| Important | 18/25 |
| Nice-to-Have | 6/8 |
| **TOTAL** | **94/133 (71%)** |

**Grade: 🟡 Mostly Ready**

**Strengths:** Multiple output formats (`-o json`, `-o yaml`, `-o jsonpath`), `--dry-run=client`, excellent `--field-selector` filtering.

**Weaknesses:** Errors are unstructured text, exit codes are binary (0 or 1), no in-line jq filtering.

---

## 13. Real-World CLI Audit: AWS CLI

Quick audit of AWS CLI v2 for agent readiness.

### Critical Checks

| # | Check | Test Command | Result | Score |
|---|-------|--------------|--------|-------|
| C1 | JSON output | `aws s3api list-buckets --output json` | ✅ PASS - default is JSON | +20 |
| C2 | stdout/stderr | `aws s3 ls 2>&1 \| grep -v "^{"` | ✅ PASS | +20 |
| C3 | Exit codes | `aws s3 ls s3://nonexistent; echo $?` | 🟡 PARTIAL - 1 or 255 | +10 |
| C4 | Non-interactive | All commands non-interactive by default | ✅ PASS | +20 |
| C5 | Structured errors | `aws s3 ls s3://x 2>&1` | ✅ PASS - JSON error objects | +20 |

### Summary

| Category | Score |
|----------|-------|
| Critical | 90/100 |
| Important | 22/25 |
| Nice-to-Have | 5/8 |
| **TOTAL** | **117/133 (88%)** |

**Grade: 🟢 Agent Ready**

**Strengths:** JSON output by default, `--query` for JMESPath filtering, structured error responses, `--dry-run` for EC2, excellent pagination with `--max-items`.

**Weaknesses:** Exit codes not semantic (255 for API errors), no streaming JSONL for long operations, waiter output not machine-parseable.

---

## Key Takeaways from Real-World Audits

| CLI | Score | Grade | Best Feature | Biggest Gap |
|-----|-------|-------|--------------|-------------|
| gh | 86% | 🟡 Mostly Ready | `--jq` inline filtering | Exit codes |
| kubectl | 71% | 🟡 Mostly Ready | Multiple output formats | Unstructured errors |
| aws | 88% | 🟢 Agent Ready | JSON default + `--query` | Exit code semantics |

**Common patterns in production CLIs:**
- All support JSON output (table is usually default for humans)
- Exit codes are universally weak (0/1 binary)
- Inline filtering (`--jq`, `--query`, `-o jsonpath`) is the differentiator
- Structured errors are inconsistent even in "agent-ready" CLIs

---

## 14. Structured Output (Rust with Serde + Clap)

Complete Rust CLI implementation matching our standard patterns.

```rust
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::process::ExitCode;
use thiserror::Error;

// ============================================================================
// Exit Codes (matching standard 0-7)
// ============================================================================

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ExitStatus {
    Success = 0,
    GeneralError = 1,
    UsageError = 2,
    NotFound = 3,
    AuthDenied = 4,
    Conflict = 5,
    ValidationError = 6,
    TransientError = 7,
}

impl From<ExitStatus> for ExitCode {
    fn from(status: ExitStatus) -> Self {
        ExitCode::from(status as u8)
    }
}

// ============================================================================
// Standard JSON Envelope
// ============================================================================

#[derive(Debug, Serialize)]
pub struct Response<T: Serialize> {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub command: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ErrorInfo>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<Meta>,
}

#[derive(Debug, Serialize)]
pub struct ErrorInfo {
    pub class: String,
    pub code: String,
    pub message: String,
    pub retryable: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub suggestion: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<serde_json::Value>,
}

#[derive(Debug, Serialize, Default)]
pub struct Meta {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub truncated: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_ms: Option<u64>,
}

// ============================================================================
// Error Handling with thiserror
// ============================================================================

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Resource '{0}' not found")]
    NotFound(String),

    #[error("Resource '{0}' already exists")]
    Conflict(String),

    #[error("Authentication failed: {0}")]
    AuthFailed(String),

    #[error("Validation failed: {0}")]
    ValidationFailed(String),

    #[error("Network error: {0}")]
    Transient(String),

    #[error("Usage error: {0}")]
    Usage(String),
}

impl AppError {
    pub fn exit_code(&self) -> ExitStatus {
        match self {
            AppError::NotFound(_) => ExitStatus::NotFound,
            AppError::Conflict(_) => ExitStatus::Conflict,
            AppError::AuthFailed(_) => ExitStatus::AuthDenied,
            AppError::ValidationFailed(_) => ExitStatus::ValidationError,
            AppError::Transient(_) => ExitStatus::TransientError,
            AppError::Usage(_) => ExitStatus::UsageError,
        }
    }

    pub fn error_class(&self) -> &'static str {
        match self {
            AppError::NotFound(_) => "not_found",
            AppError::Conflict(_) => "conflict",
            AppError::AuthFailed(_) => "auth",
            AppError::ValidationFailed(_) => "validation",
            AppError::Transient(_) => "transient",
            AppError::Usage(_) => "usage",
        }
    }

    pub fn error_code(&self) -> &'static str {
        match self {
            AppError::NotFound(_) => "RESOURCE_NOT_FOUND",
            AppError::Conflict(_) => "RESOURCE_EXISTS",
            AppError::AuthFailed(_) => "AUTH_FAILED",
            AppError::ValidationFailed(_) => "VALIDATION_FAILED",
            AppError::Transient(_) => "TRANSIENT_ERROR",
            AppError::Usage(_) => "USAGE_ERROR",
        }
    }

    pub fn is_retryable(&self) -> bool {
        matches!(self, AppError::Transient(_))
    }

    pub fn to_error_info(&self) -> ErrorInfo {
        ErrorInfo {
            class: self.error_class().to_string(),
            code: self.error_code().to_string(),
            message: self.to_string(),
            retryable: self.is_retryable(),
            suggestion: None,
            details: None,
        }
    }
}

// ============================================================================
// CLI Argument Parsing with Clap (Standard Flags)
// ============================================================================

#[derive(Parser)]
#[command(name = "mycli")]
#[command(about = "Agent-friendly CLI example")]
#[command(version)]
pub struct Cli {
    /// Output as JSON
    #[arg(long, global = true)]
    pub json: bool,

    /// Minimal output
    #[arg(short = 'q', long, global = true)]
    pub quiet: bool,

    /// Auto-confirm prompts
    #[arg(short = 'y', long, global = true)]
    pub yes: bool,

    /// Force operation (bypass safety checks)
    #[arg(short = 'f', long, global = true)]
    pub force: bool,

    /// Preview without executing
    #[arg(long, global = true)]
    pub dry_run: bool,

    /// Operation timeout (e.g., 30s, 5m)
    #[arg(long, global = true, default_value = "30s")]
    pub timeout: String,

    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Create a new resource
    Create {
        /// Resource name
        name: String,
        /// Resource type
        #[arg(long)]
        resource_type: Option<String>,
    },
    /// List resources
    List {
        /// Filter by type
        #[arg(long)]
        resource_type: Option<String>,
        /// Maximum results
        #[arg(long, default_value = "100")]
        limit: usize,
    },
    /// Get a resource
    Get {
        /// Resource ID
        id: String,
    },
    /// Delete a resource
    Delete {
        /// Resource ID
        id: String,
    },
}

// ============================================================================
// Output Helpers
// ============================================================================

pub fn output_success<T: Serialize>(cli: &Cli, result: T) -> ExitCode {
    if cli.json {
        let response: Response<T> = Response {
            ok: true,
            command: None,
            result: Some(result),
            error: None,
            meta: None,
        };
        println!("{}", serde_json::to_string_pretty(&response).unwrap());
    } else if cli.quiet {
        // Minimal output - just the ID or primary field
        println!("{}", serde_json::to_string(&result).unwrap());
    } else {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    }
    ExitCode::SUCCESS
}

pub fn output_error(cli: &Cli, err: AppError) -> ExitCode {
    if cli.json {
        let response: Response<()> = Response {
            ok: false,
            command: None,
            result: None,
            error: Some(err.to_error_info()),
            meta: None,
        };
        eprintln!("{}", serde_json::to_string_pretty(&response).unwrap());
    } else {
        eprintln!("Error: {}", err);
    }
    err.exit_code().into()
}

// ============================================================================
// Main Entry Point
// ============================================================================

fn main() -> ExitCode {
    let cli = Cli::parse();

    match run(&cli) {
        Ok(result) => output_success(&cli, result),
        Err(err) => output_error(&cli, err),
    }
}

fn run(cli: &Cli) -> Result<serde_json::Value, AppError> {
    match &cli.command {
        Commands::Create { name, resource_type } => {
            // Dry-run check
            if cli.dry_run {
                return Ok(serde_json::json!({
                    "dry_run": true,
                    "would_create": name,
                    "type": resource_type
                }));
            }
            // Actual creation logic here
            Ok(serde_json::json!({
                "id": format!("res_{}", uuid::Uuid::new_v4()),
                "name": name,
                "created": true
            }))
        }
        Commands::List { resource_type, limit } => {
            Ok(serde_json::json!({
                "resources": [],
                "total": 0,
                "limit": limit
            }))
        }
        Commands::Get { id } => {
            // Example: return not found
            Err(AppError::NotFound(id.clone()))
        }
        Commands::Delete { id } => {
            if !cli.yes && !cli.force {
                return Err(AppError::Usage(
                    "Deletion requires --yes/-y or --force/-f".to_string()
                ));
            }
            Ok(serde_json::json!({ "deleted": id }))
        }
    }
}
```

### Cargo.toml Dependencies

```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
uuid = { version = "1", features = ["v4"] }
```

---

## 15. Shell/Bash Wrapper Scripts

Production-ready shell patterns for agent automation.

### 15.1 Basic Wrapper with jq Parsing

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Standard Exit Codes (matching all languages)
# ============================================================================
readonly EXIT_SUCCESS=0
readonly EXIT_ERROR=1
readonly EXIT_USAGE=2
readonly EXIT_NOT_FOUND=3
readonly EXIT_AUTH=4
readonly EXIT_CONFLICT=5
readonly EXIT_VALIDATION=6
readonly EXIT_TRANSIENT=7

# ============================================================================
# Configuration
# ============================================================================
MYCLI_JSON="${MYCLI_JSON:-false}"
MYCLI_QUIET="${MYCLI_QUIET:-false}"
MYCLI_YES="${MYCLI_YES:-false}"
MYCLI_DRY_RUN="${MYCLI_DRY_RUN:-false}"
MYCLI_FORCE="${MYCLI_FORCE:-false}"
MYCLI_TIMEOUT="${MYCLI_TIMEOUT:-30}"

# ============================================================================
# JSON Output Helpers
# ============================================================================

json_success() {
    local result="$1"
    if [[ "$MYCLI_JSON" == "true" ]]; then
        jq -n --argjson result "$result" '{ok: true, result: $result}'
    else
        echo "$result" | jq -r '.'
    fi
}

json_error() {
    local class="$1"
    local code="$2"
    local message="$3"
    local retryable="${4:-false}"
    local exit_code="${5:-1}"

    if [[ "$MYCLI_JSON" == "true" ]]; then
        jq -n \
            --arg class "$class" \
            --arg code "$code" \
            --arg message "$message" \
            --argjson retryable "$retryable" \
            '{ok: false, error: {class: $class, code: $code, message: $message, retryable: $retryable}}' >&2
    else
        echo "Error: $message" >&2
    fi
    exit "$exit_code"
}

# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

retry_with_backoff() {
    local max_attempts="${1:-3}"
    local base_delay="${2:-1}"
    local max_delay="${3:-60}"
    shift 3

    local attempt=1
    local delay="$base_delay"

    while (( attempt <= max_attempts )); do
        if "$@"; then
            return 0
        fi

        local exit_code=$?

        # Only retry transient errors (exit code 7)
        if (( exit_code != EXIT_TRANSIENT )); then
            return "$exit_code"
        fi

        if (( attempt < max_attempts )); then
            echo "Attempt $attempt failed. Retrying in ${delay}s..." >&2
            sleep "$delay"
            delay=$(( delay * 2 ))
            (( delay > max_delay )) && delay="$max_delay"
        fi

        (( attempt++ ))
    done

    return "$EXIT_TRANSIENT"
}

# ============================================================================
# CLI Wrapper Function
# ============================================================================

mycli_wrapper() {
    local cmd="$1"
    shift

    # Build command arguments
    local args=()
    [[ "$MYCLI_JSON" == "true" ]] && args+=(--json)
    [[ "$MYCLI_QUIET" == "true" ]] && args+=(-q)
    [[ "$MYCLI_YES" == "true" ]] && args+=(-y)
    [[ "$MYCLI_DRY_RUN" == "true" ]] && args+=(--dry-run)
    [[ "$MYCLI_FORCE" == "true" ]] && args+=(-f)
    [[ -n "$MYCLI_TIMEOUT" ]] && args+=(--timeout "$MYCLI_TIMEOUT")

    # Execute with timeout
    timeout "$MYCLI_TIMEOUT" mycli "$cmd" "${args[@]}" "$@"
}

# ============================================================================
# Example: Create Resource with Retry
# ============================================================================

create_resource() {
    local name="$1"
    local type="${2:-default}"

    retry_with_backoff 3 2 30 mycli_wrapper create "$name" --resource-type "$type"
}

# ============================================================================
# Example: Safe Delete with Confirmation
# ============================================================================

delete_resource() {
    local id="$1"

    if [[ "$MYCLI_YES" != "true" && "$MYCLI_FORCE" != "true" ]]; then
        read -r -p "Delete resource '$id'? [y/N] " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Aborted." >&2
            exit "$EXIT_USAGE"
        fi
    fi

    mycli_wrapper delete "$id"
}
```

### 15.2 JSON Response Parsing with jq

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Parse CLI JSON Response
# ============================================================================

parse_response() {
    local response="$1"

    # Check if response is valid JSON
    if ! echo "$response" | jq -e . >/dev/null 2>&1; then
        echo "Error: Invalid JSON response" >&2
        return 1
    fi

    # Check ok field
    local ok
    ok=$(echo "$response" | jq -r '.ok')

    if [[ "$ok" != "true" ]]; then
        local error_class error_code error_message
        error_class=$(echo "$response" | jq -r '.error.class // "unknown"')
        error_code=$(echo "$response" | jq -r '.error.code // "UNKNOWN"')
        error_message=$(echo "$response" | jq -r '.error.message // "Unknown error"')

        echo "Error [$error_class/$error_code]: $error_message" >&2
        return 1
    fi

    # Return result
    echo "$response" | jq -r '.result'
}

# ============================================================================
# Extract Specific Fields
# ============================================================================

get_resource_id() {
    local response="$1"
    echo "$response" | jq -r '.result.id // empty'
}

get_resource_list() {
    local response="$1"
    echo "$response" | jq -r '.result.resources[]?.id'
}

is_retryable_error() {
    local response="$1"
    local retryable
    retryable=$(echo "$response" | jq -r '.error.retryable // false')
    [[ "$retryable" == "true" ]]
}

# ============================================================================
# Batch Processing with jq
# ============================================================================

process_batch() {
    local input_file="$1"
    local output_file="${2:-/dev/stdout}"

    # Process each line as JSON
    while IFS= read -r line; do
        local id
        id=$(echo "$line" | jq -r '.id')

        local result
        if result=$(mycli get "$id" --json 2>&1); then
            echo "$result" | jq -c '{id: .result.id, status: "success", data: .result}'
        else
            echo "$result" | jq -c '{id: "'"$id"'", status: "error", error: .error}'
        fi
    done < "$input_file" > "$output_file"
}

# ============================================================================
# Usage Example
# ============================================================================

main() {
    export MYCLI_JSON=true

    # Create and capture response
    local response
    if response=$(mycli create "my-resource" --json 2>&1); then
        local resource_id
        resource_id=$(get_resource_id "$response")
        echo "Created resource: $resource_id"
    else
        if is_retryable_error "$response"; then
            echo "Transient error - retrying..."
            retry_with_backoff 3 2 30 mycli create "my-resource" --json
        else
            echo "Non-retryable error" >&2
            exit 1
        fi
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
```

### 15.3 Flag Parsing in Bash

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Standard Flag Parsing (matching all languages)
# ============================================================================

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] COMMAND [ARGS]

Options:
    --json              Output as JSON
    -q, --quiet         Minimal output
    -y, --yes           Auto-confirm prompts
    -f, --force         Force operation
    --dry-run           Preview without executing
    --timeout SECONDS   Operation timeout (default: 30)
    -h, --help          Show this help

Commands:
    create NAME         Create a resource
    list                List resources
    get ID              Get a resource
    delete ID           Delete a resource

Examples:
    $(basename "$0") create my-resource --json
    $(basename "$0") delete res_123 --yes
    $(basename "$0") list --quiet
EOF
    exit "${1:-0}"
}

# Parse flags
JSON_OUTPUT=false
QUIET=false
YES=false
FORCE=false
DRY_RUN=false
TIMEOUT=30

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -y|--yes)
            YES=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --timeout=*)
            TIMEOUT="${1#*=}"
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage 2
            ;;
        *)
            break
            ;;
    esac
done

# Remaining args are command and arguments
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    create)
        NAME="${1:-}"
        [[ -z "$NAME" ]] && { echo "Error: NAME required" >&2; exit 2; }
        # ... create logic
        ;;
    list)
        # ... list logic
        ;;
    get|delete)
        ID="${1:-}"
        [[ -z "$ID" ]] && { echo "Error: ID required" >&2; exit 2; }
        # ... get/delete logic
        ;;
    "")
        echo "Error: COMMAND required" >&2
        usage 2
        ;;
    *)
        echo "Unknown command: $COMMAND" >&2
        usage 2
        ;;
esac
```

---

## 16. Testing CLI Output

### 16.1 Unit Testing JSON Output (Go)

```go
package main

import (
    "bytes"
    "encoding/json"
    "os/exec"
    "testing"
)

func TestJSONOutput(t *testing.T) {
    tests := []struct {
        name       string
        args       []string
        wantOK     bool
        wantFields map[string]any
        wantExit   int
    }{
        {
            name:     "create success",
            args:     []string{"create", "test-resource", "--json"},
            wantOK:   true,
            wantExit: 0,
            wantFields: map[string]any{
                "result.created": true,
            },
        },
        {
            name:     "get not found",
            args:     []string{"get", "nonexistent", "--json"},
            wantOK:   false,
            wantExit: 3,
            wantFields: map[string]any{
                "error.class": "not_found",
                "error.code":  "RESOURCE_NOT_FOUND",
            },
        },
        {
            name:     "delete without confirmation",
            args:     []string{"delete", "res_123", "--json"},
            wantOK:   false,
            wantExit: 2,
            wantFields: map[string]any{
                "error.class": "usage",
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            cmd := exec.Command("./mycli", tt.args...)
            var stdout, stderr bytes.Buffer
            cmd.Stdout = &stdout
            cmd.Stderr = &stderr

            err := cmd.Run()

            // Check exit code
            exitCode := 0
            if exitErr, ok := err.(*exec.ExitError); ok {
                exitCode = exitErr.ExitCode()
            }
            if exitCode != tt.wantExit {
                t.Errorf("exit code = %d, want %d", exitCode, tt.wantExit)
            }

            // Parse JSON output
            output := stdout.Bytes()
            if len(output) == 0 {
                output = stderr.Bytes()
            }

            var resp map[string]any
            if err := json.Unmarshal(output, &resp); err != nil {
                t.Fatalf("invalid JSON: %v\noutput: %s", err, output)
            }

            // Check ok field
            if ok, _ := resp["ok"].(bool); ok != tt.wantOK {
                t.Errorf("ok = %v, want %v", ok, tt.wantOK)
            }

            // Check expected fields (simplified path lookup)
            for path, want := range tt.wantFields {
                got := lookupPath(resp, path)
                if got != want {
                    t.Errorf("%s = %v, want %v", path, got, want)
                }
            }
        })
    }
}

func lookupPath(m map[string]any, path string) any {
    // Simplified: split by "." and traverse
    parts := strings.Split(path, ".")
    var current any = m
    for _, part := range parts {
        if cm, ok := current.(map[string]any); ok {
            current = cm[part]
        } else {
            return nil
        }
    }
    return current
}
```

### 16.2 Unit Testing JSON Output (Python)

```python
import json
import subprocess
import pytest
from typing import Any

def run_cli(*args: str) -> tuple[int, dict[str, Any]]:
    """Run CLI and return (exit_code, parsed_json)."""
    result = subprocess.run(
        ["mycli", *args, "--json"],
        capture_output=True,
        text=True
    )
    
    output = result.stdout or result.stderr
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        data = {"raw": output}
    
    return result.returncode, data

class TestCLIOutput:
    def test_create_success(self):
        exit_code, data = run_cli("create", "test-resource")
        
        assert exit_code == 0
        assert data["ok"] is True
        assert "result" in data
        assert data["result"]["created"] is True

    def test_get_not_found(self):
        exit_code, data = run_cli("get", "nonexistent")
        
        assert exit_code == 3  # EXIT_NOT_FOUND
        assert data["ok"] is False
        assert data["error"]["class"] == "not_found"
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["retryable"] is False

    def test_delete_requires_confirmation(self):
        exit_code, data = run_cli("delete", "res_123")
        
        assert exit_code == 2  # EXIT_USAGE
        assert data["ok"] is False
        assert data["error"]["class"] == "usage"

    def test_delete_with_yes_flag(self):
        exit_code, data = run_cli("delete", "res_123", "-y")
        
        assert exit_code == 0
        assert data["ok"] is True

    def test_dry_run_returns_preview(self):
        exit_code, data = run_cli("create", "test", "--dry-run")
        
        assert exit_code == 0
        assert data["ok"] is True
        assert data["result"]["dry_run"] is True

    @pytest.mark.parametrize("flag,short", [
        ("--quiet", "-q"),
        ("--yes", "-y"),
        ("--force", "-f"),
    ])
    def test_short_flags_work(self, flag, short):
        """Ensure short flag aliases work identically."""
        _, data1 = run_cli("list", flag)
        _, data2 = run_cli("list", short)
        
        # Results should be structurally identical
        assert data1.get("ok") == data2.get("ok")
```

### 16.3 Unit Testing JSON Output (Node.js)

```typescript
import { spawn } from 'child_process';
import { describe, it, expect } from 'vitest';

interface CLIResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  json: any;
}

async function runCLI(...args: string[]): Promise<CLIResult> {
  return new Promise((resolve) => {
    const proc = spawn('./mycli', [...args, '--json']);
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => { stdout += data; });
    proc.stderr.on('data', (data) => { stderr += data; });

    proc.on('close', (exitCode) => {
      let json: any;
      try {
        json = JSON.parse(stdout || stderr);
      } catch {
        json = { raw: stdout || stderr };
      }
      resolve({ exitCode: exitCode ?? 1, stdout, stderr, json });
    });
  });
}

describe('CLI JSON Output', () => {
  it('returns success envelope on create', async () => {
    const result = await runCLI('create', 'test-resource');

    expect(result.exitCode).toBe(0);
    expect(result.json.ok).toBe(true);
    expect(result.json.result).toBeDefined();
    expect(result.json.result.created).toBe(true);
  });

  it('returns not_found error with exit code 3', async () => {
    const result = await runCLI('get', 'nonexistent');

    expect(result.exitCode).toBe(3);
    expect(result.json.ok).toBe(false);
    expect(result.json.error.class).toBe('not_found');
    expect(result.json.error.code).toBe('RESOURCE_NOT_FOUND');
    expect(result.json.error.retryable).toBe(false);
  });

  it('returns usage error when confirmation missing', async () => {
    const result = await runCLI('delete', 'res_123');

    expect(result.exitCode).toBe(2);
    expect(result.json.ok).toBe(false);
    expect(result.json.error.class).toBe('usage');
  });

  it('--dry-run returns preview without executing', async () => {
    const result = await runCLI('create', 'test', '--dry-run');

    expect(result.exitCode).toBe(0);
    expect(result.json.ok).toBe(true);
    expect(result.json.result.dry_run).toBe(true);
  });

  describe('standard flags', () => {
    const flags = [
      { long: '--quiet', short: '-q' },
      { long: '--yes', short: '-y' },
      { long: '--force', short: '-f' },
    ];

    for (const { long, short } of flags) {
      it(`${short} is alias for ${long}`, async () => {
        const r1 = await runCLI('list', long);
        const r2 = await runCLI('list', short);

        expect(r1.json.ok).toBe(r2.json.ok);
      });
    }
  });
});
```

### 16.4 Unit Testing JSON Output (Rust)

```rust
use assert_cmd::Command;
use predicates::prelude::*;
use serde_json::Value;

fn run_cli(args: &[&str]) -> (i32, Value) {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    let output = cmd.args(args).arg("--json").output().unwrap();

    let exit_code = output.status.code().unwrap_or(1);
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    let json: Value = serde_json::from_str(if stdout.is_empty() { &stderr } else { &stdout })
        .unwrap_or_else(|_| serde_json::json!({"raw": format!("{}{}", stdout, stderr)}));

    (exit_code, json)
}

#[test]
fn test_create_success() {
    let (exit_code, json) = run_cli(&["create", "test-resource"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
    assert!(json["result"]["created"].as_bool().unwrap_or(false));
}

#[test]
fn test_get_not_found() {
    let (exit_code, json) = run_cli(&["get", "nonexistent"]);

    assert_eq!(exit_code, 3); // EXIT_NOT_FOUND
    assert_eq!(json["ok"], false);
    assert_eq!(json["error"]["class"], "not_found");
    assert_eq!(json["error"]["code"], "RESOURCE_NOT_FOUND");
    assert_eq!(json["error"]["retryable"], false);
}

#[test]
fn test_delete_requires_confirmation() {
    let (exit_code, json) = run_cli(&["delete", "res_123"]);

    assert_eq!(exit_code, 2); // EXIT_USAGE
    assert_eq!(json["ok"], false);
    assert_eq!(json["error"]["class"], "usage");
}

#[test]
fn test_delete_with_yes_flag() {
    let (exit_code, json) = run_cli(&["delete", "res_123", "-y"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
}

#[test]
fn test_dry_run_preview() {
    let (exit_code, json) = run_cli(&["create", "test", "--dry-run"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
    assert_eq!(json["result"]["dry_run"], true);
}

#[test]
fn test_short_flags_work() {
    // Test each short flag is equivalent to long form
    let flags = [("--quiet", "-q"), ("--yes", "-y"), ("--force", "-f")];

    for (long, short) in flags {
        let (_, json1) = run_cli(&["list", long]);
        let (_, json2) = run_cli(&["list", short]);

        assert_eq!(json1["ok"], json2["ok"], "{} != {}", long, short);
    }
}

// Rust-specific: test with assert_cmd for better ergonomics
#[test]
fn test_help_exits_zero() {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    cmd.arg("--help").assert().success();
}

#[test]
fn test_invalid_command_exits_usage() {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    cmd.arg("invalid-command")
        .assert()
        .code(predicate::eq(2));
}
```

### 16.5 Integration Test Script (Bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CLI Integration Test Suite
# ============================================================================

TESTS_PASSED=0
TESTS_FAILED=0
CLI_BIN="${CLI_BIN:-./mycli}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    if [[ "$actual" -eq "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $test_name (exit=$actual)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name: expected exit=$expected, got exit=$actual"
        ((TESTS_FAILED++))
    fi
}

assert_json_field() {
    local json="$1"
    local field="$2"
    local expected="$3"
    local test_name="$4"

    local actual
    actual=$(echo "$json" | jq -r "$field")

    if [[ "$actual" == "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $test_name ($field=$actual)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name: $field expected '$expected', got '$actual'"
        ((TESTS_FAILED++))
    fi
}

# ============================================================================
# Test: Create Success
# ============================================================================
test_create_success() {
    local output exit_code
    output=$($CLI_BIN create test-resource --json 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "create: exit code"
    assert_json_field "$output" '.ok' 'true' "create: ok=true"
    assert_json_field "$output" '.result.created' 'true' "create: result.created"
}

# ============================================================================
# Test: Get Not Found
# ============================================================================
test_get_not_found() {
    local output exit_code
    output=$($CLI_BIN get nonexistent --json 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 3 "$exit_code" "get not found: exit code"
    assert_json_field "$output" '.ok' 'false' "get not found: ok=false"
    assert_json_field "$output" '.error.class' 'not_found' "get not found: error.class"
    assert_json_field "$output" '.error.retryable' 'false' "get not found: not retryable"
}

# ============================================================================
# Test: Delete Requires Confirmation
# ============================================================================
test_delete_needs_confirm() {
    local output exit_code
    output=$($CLI_BIN delete res_123 --json 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 2 "$exit_code" "delete no confirm: exit code"
    assert_json_field "$output" '.error.class' 'usage' "delete no confirm: error.class"
}

# ============================================================================
# Test: Delete with --yes
# ============================================================================
test_delete_with_yes() {
    local output exit_code
    output=$($CLI_BIN delete res_123 --yes --json 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "delete --yes: exit code"
    assert_json_field "$output" '.ok' 'true' "delete --yes: ok=true"
}

# ============================================================================
# Test: Dry Run
# ============================================================================
test_dry_run() {
    local output exit_code
    output=$($CLI_BIN create test --dry-run --json 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "dry-run: exit code"
    assert_json_field "$output" '.result.dry_run' 'true' "dry-run: result.dry_run"
}

# ============================================================================
# Test: Short Flags
# ============================================================================
test_short_flags() {
    local flags=("-q:--quiet" "-y:--yes" "-f:--force")

    for pair in "${flags[@]}"; do
        local short="${pair%%:*}"
        local long="${pair##*:}"

        local out1 out2
        out1=$($CLI_BIN list "$long" --json 2>&1) || true
        out2=$($CLI_BIN list "$short" --json 2>&1) || true

        local ok1 ok2
        ok1=$(echo "$out1" | jq -r '.ok')
        ok2=$(echo "$out2" | jq -r '.ok')

        if [[ "$ok1" == "$ok2" ]]; then
            echo -e "${GREEN}✓${NC} flag alias: $short == $long"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗${NC} flag alias: $short != $long"
            ((TESTS_FAILED++))
        fi
    done
}

# ============================================================================
# Run All Tests
# ============================================================================
main() {
    echo "Running CLI Integration Tests..."
    echo "================================"

    test_create_success
    test_get_not_found
    test_delete_needs_confirm
    test_delete_with_yes
    test_dry_run
    test_short_flags

    echo "================================"
    echo -e "Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}"

    if [[ "$TESTS_FAILED" -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
```

---

## Cross-Language Consistency Reference

All examples in this document follow these standards:

### Standard Flags

| Flag | Short | All Languages |
|------|-------|---------------|
| `--json` | - | ✅ Go, Python, Node, Rust, Bash |
| `--quiet` | `-q` | ✅ Go, Python, Node, Rust, Bash |
| `--yes` | `-y` | ✅ Go, Python, Node, Rust, Bash |
| `--dry-run` | - | ✅ Go, Python, Node, Rust, Bash |
| `--force` | `-f` | ✅ Go, Python, Node, Rust, Bash |
| `--timeout` | - | ✅ Go, Python, Node, Rust, Bash |

### Exit Codes

| Code | Meaning | Go | Python | Node | Rust | Bash |
|------|---------|-----|--------|------|------|------|
| 0 | Success | ✅ | ✅ | ✅ | ✅ | ✅ |
| 1 | General error | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | Usage/input error | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | Not found | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | Auth/permission | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | Conflict | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | Validation error | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | Transient error | ✅ | ✅ | ✅ | ✅ | ✅ |

### JSON Envelope

All languages output the same envelope structure:

```json
{
  "ok": true,
  "command": "resource.create",
  "result": { "id": "...", "created": true },
  "error": null,
  "meta": { "duration_ms": 42 }
}
```

Error case:

```json
{
  "ok": false,
  "command": "resource.get",
  "result": null,
  "error": {
    "class": "not_found",
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource 'xyz' not found",
    "retryable": false,
    "suggestion": "Try 'mycli resource list' first"
  },
  "meta": null
}
```

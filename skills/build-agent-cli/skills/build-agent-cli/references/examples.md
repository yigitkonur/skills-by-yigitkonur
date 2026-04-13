# Agent-Friendly CLI: Code Examples

Production-ready code examples in Go, Python, and Node.js for implementing agent-friendly CLI patterns.

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
  nonInteractive: boolean;
  yes: boolean;
  force: boolean;
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
    console.error(`Use --yes to auto-confirm or --force to bypass`);
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
    jsonOutput bool
    quiet      bool
    nonInteractive bool
    yes        bool
    force      bool
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

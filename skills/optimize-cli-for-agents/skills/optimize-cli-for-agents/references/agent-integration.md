# Agent Integration Guide

> Patterns for calling agent-ready CLIs from AI systems

## 1. Basic CLI Invocation Pattern

```python
import subprocess
import json
from typing import TypedDict, Optional

class CLIResult(TypedDict):
    ok: bool
    result: Optional[dict]
    error: Optional[dict]

def invoke_cli(cmd: list[str], timeout: int = 30) -> CLIResult:
    """Invoke CLI with JSON output, proper error handling."""
    try:
        result = subprocess.run(
            cmd + ["--json"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Parse JSON from stdout
        if result.stdout.strip():
            return json.loads(result.stdout)
        
        # No output = check exit code
        if result.returncode == 0:
            return {"ok": True, "result": None, "error": None}
        
        # Error without JSON body
        return {
            "ok": False,
            "result": None,
            "error": {
                "code": f"exit_{result.returncode}",
                "message": result.stderr.strip() or "Unknown error"
            }
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "result": None, "error": {"code": "timeout", "retryable": True}}
    except json.JSONDecodeError as e:
        return {"ok": False, "result": None, "error": {"code": "invalid_json", "message": str(e)}}
```

## 2. Exit Code Routing

```python
EXIT_CODE_ACTIONS = {
    0: "success",      # Proceed with result
    1: "crash",        # Log error, escalate to human
    2: "usage",        # Fix command syntax
    3: "not_found",    # Resource doesn't exist
    4: "auth",         # Re-authenticate
    5: "conflict",     # Resolve conflict, retry
    6: "validation",   # Fix input data
    7: "transient",    # Retry with backoff
}

def route_exit_code(code: int) -> str:
    """Map exit code to appropriate action."""
    return EXIT_CODE_ACTIONS.get(code, "unknown")
```

## 3. Retry Logic with Exponential Backoff

```python
import time
import random

def invoke_with_retry(
    cmd: list[str],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> CLIResult:
    """Invoke CLI with intelligent retry for transient errors."""
    
    for attempt in range(max_retries + 1):
        result = invoke_cli(cmd)
        
        # Success - return immediately
        if result["ok"]:
            return result
        
        error = result.get("error", {})
        
        # Not retryable - fail fast
        if not error.get("retryable", False):
            return result
        
        # Last attempt - return error
        if attempt == max_retries:
            return result
        
        # Calculate backoff with jitter
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
        
        # Honor Retry-After header if present
        if "retry_after" in error:
            delay = max(delay, error["retry_after"])
        
        time.sleep(delay)
    
    return result
```

## 4. Error Recovery Flow

```python
def handle_cli_error(result: CLIResult, context: dict) -> str:
    """Generate recovery action from CLI error."""
    
    error = result.get("error", {})
    error_class = error.get("class", "unknown")
    
    RECOVERY_ACTIONS = {
        "authentication": "Re-run auth: mycli auth login",
        "not_found": f"Resource {context.get('resource')} does not exist. Create it first.",
        "conflict": f"Conflict detected. Use --force or resolve: {error.get('suggestion', '')}",
        "validation": f"Invalid input: {error.get('message')}. Fix: {error.get('suggestion', '')}",
        "transient": "Temporary failure. Retry automatically handled.",
        "rate_limit": f"Rate limited. Wait {error.get('retry_after', 60)}s before retry.",
    }
    
    return RECOVERY_ACTIONS.get(error_class, f"Unknown error: {error.get('message')}")
```

## 5. Batch Processing with Partial Failure

```python
def batch_invoke(
    items: list[dict],
    cmd_template: list[str],
    batch_size: int = 10
) -> dict:
    """Process items in batches, handle partial failures."""
    
    results = {"succeeded": [], "failed": [], "total": len(items)}
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        for item in batch:
            cmd = [c.format(**item) for c in cmd_template]
            result = invoke_with_retry(cmd)
            
            if result["ok"]:
                results["succeeded"].append({
                    "item": item,
                    "result": result["result"]
                })
            else:
                results["failed"].append({
                    "item": item,
                    "error": result["error"]
                })
    
    return results
```

## 6. Agent System Prompt Template

```markdown
## CLI Usage Guidelines

When using CLI tools, follow these patterns:

1. **Always use --json flag** for structured output
2. **Check exit codes** before parsing output:
   - 0 = success, parse result
   - 3 = not found, resource missing
   - 4 = auth error, re-authenticate
   - 7 = transient, retry with backoff
3. **Read error.suggestion** field for recovery hints
4. **Use --yes flag** to skip confirmations
5. **Handle timeouts** - set reasonable limits

Example invocation:
```bash
mycli resource get RESOURCE_ID --json --yes
```

Parse response:
```json
{"ok": true, "result": {"id": "...", "status": "active"}}
```
```

## 7. Function Calling Schema (Claude/GPT)

```json
{
  "name": "invoke_cli",
  "description": "Execute CLI command and return structured result",
  "parameters": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "Base CLI command (e.g., 'mycli resource create')"
      },
      "args": {
        "type": "object",
        "description": "Named arguments as key-value pairs"
      },
      "flags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Boolean flags (e.g., ['--json', '--yes'])"
      }
    },
    "required": ["command"]
  }
}
```

## 8. Integration Test Script

```bash
#!/bin/bash
# test-agent-integration.sh
# Validates CLI is agent-ready

CLI="mycli"
PASS=0
FAIL=0

test_json_output() {
    echo "Test: JSON output..."
    $CLI version --json | jq -e '.ok' > /dev/null 2>&1
    [ $? -eq 0 ] && ((PASS++)) && echo "  ✅ JSON output works" || ((FAIL++)) && echo "  ❌ JSON output broken"
}

test_exit_codes() {
    echo "Test: Exit codes..."
    $CLI nonexistent-resource --json 2>/dev/null
    [ $? -eq 3 ] && ((PASS++)) && echo "  ✅ Not-found returns 3" || ((FAIL++)) && echo "  ❌ Wrong exit code"
}

test_error_structure() {
    echo "Test: Error structure..."
    $CLI fail --json 2>/dev/null | jq -e '.error.code and .error.retryable != null' > /dev/null
    [ $? -eq 0 ] && ((PASS++)) && echo "  ✅ Error structure correct" || ((FAIL++)) && echo "  ❌ Error structure missing fields"
}

test_non_interactive() {
    echo "Test: Non-interactive mode..."
    echo "" | timeout 5 $CLI dangerous-cmd --yes --json > /dev/null 2>&1
    [ $? -ne 124 ] && ((PASS++)) && echo "  ✅ Non-interactive works" || ((FAIL++)) && echo "  ❌ Command hangs"
}

# Run tests
test_json_output
test_exit_codes
test_error_structure
test_non_interactive

# Summary
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

## 9. Debugging Agent CLI Failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent loops infinitely | No exit code differentiation | Implement semantic exit codes |
| Parser errors | Mixed stdout/stderr | Separate streams properly |
| Timeouts | Interactive prompts | Add `--yes` / `--no-input` flags |
| Retry storms | No Retry-After header | Add header to rate limit responses |
| Partial data | Pagination not handled | Return cursor, implement `--all` |

---

## 10. TypeScript/JavaScript Integration

### Basic child_process Invocation

```typescript
import { spawn, exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface CLIResult {
  ok: boolean;
  result?: Record<string, unknown>;
  error?: { code: string; message: string; retryable?: boolean };
}

/**
 * Invoke CLI with JSON output and proper timeout handling.
 */
async function invokeCLI(
  cmd: string[],
  options: { timeout?: number; cwd?: string } = {}
): Promise<CLIResult> {
  const { timeout = 30000, cwd } = options;
  const fullCmd = [...cmd, '--json', '--quiet'];

  try {
    const { stdout, stderr } = await execAsync(fullCmd.join(' '), {
      timeout,
      cwd,
      env: { ...process.env, NO_COLOR: '1' },
    });

    if (stdout.trim()) {
      return JSON.parse(stdout);
    }
    return { ok: true };
  } catch (error: unknown) {
    if (error instanceof Error && 'killed' in error) {
      return { ok: false, error: { code: 'timeout', message: 'Command timed out', retryable: true } };
    }
    const execError = error as { code?: number; stderr?: string };
    return {
      ok: false,
      error: {
        code: `exit_${execError.code ?? 1}`,
        message: execError.stderr?.trim() || 'Unknown error',
      },
    };
  }
}

// Usage
const result = await invokeCLI(['mycli', 'task', 'start', 'prompt.md'], { timeout: 60000 });
```

### Async/Await with Retry

```typescript
import { setTimeout } from 'timers/promises';

async function invokeWithRetry(
  cmd: string[],
  options: { maxRetries?: number; baseDelay?: number } = {}
): Promise<CLIResult> {
  const { maxRetries = 3, baseDelay = 1000 } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const result = await invokeCLI(cmd);

    if (result.ok) return result;
    if (!result.error?.retryable) return result;
    if (attempt === maxRetries) return result;

    const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
    await setTimeout(delay);
  }

  return { ok: false, error: { code: 'exhausted', message: 'Max retries exceeded' } };
}
```

### JSONL Streaming with spawn

```typescript
import { spawn } from 'child_process';
import { createInterface } from 'readline';

interface TaskEvent {
  type: 'status' | 'output' | 'approval' | 'complete' | 'error';
  task_id?: string;
  data?: unknown;
}

/**
 * Stream JSONL events from CLI task follow command.
 */
async function* streamTaskEvents(
  taskId: string,
  options: { signal?: AbortSignal } = {}
): AsyncGenerator<TaskEvent> {
  const proc = spawn('mycli', ['task', 'follow', taskId, '--json'], {
    stdio: ['ignore', 'pipe', 'pipe'],
    signal: options.signal,
  });

  const rl = createInterface({ input: proc.stdout });

  try {
    for await (const line of rl) {
      if (!line.trim()) continue;
      try {
        yield JSON.parse(line) as TaskEvent;
      } catch {
        console.error('Invalid JSONL:', line);
      }
    }
  } finally {
    rl.close();
    proc.kill();
  }
}

// Usage with async iteration
async function runTask(promptFile: string): Promise<void> {
  const start = await invokeCLI(['mycli', 'task', 'start', promptFile, '--json']);
  if (!start.ok) throw new Error(start.error?.message);

  const taskId = (start.result as { task_id: string }).task_id;

  for await (const event of streamTaskEvents(taskId)) {
    switch (event.type) {
      case 'approval':
        // Handle approval request
        await invokeCLI(['mycli', 'request', 'answer', event.data?.req_id, '--yes', '--json']);
        break;
      case 'complete':
        console.log('Task completed:', event.data);
        return;
      case 'error':
        throw new Error(`Task failed: ${JSON.stringify(event.data)}`);
    }
  }
}
```

### Class-based CLI Wrapper

```typescript
import { EventEmitter } from 'events';

class CLIAgent extends EventEmitter {
  private baseCmd: string[];
  private defaultFlags: string[];

  constructor(cli: string, defaultFlags: string[] = ['--json', '--quiet']) {
    super();
    this.baseCmd = [cli];
    this.defaultFlags = defaultFlags;
  }

  async invoke(subcommand: string[], extraFlags: string[] = {}): Promise<CLIResult> {
    const cmd = [...this.baseCmd, ...subcommand, ...this.defaultFlags, ...extraFlags];
    const result = await invokeWithRetry(cmd);
    this.emit('invocation', { cmd, result });
    return result;
  }

  async taskStart(promptFile: string, opts: { session?: string; timeout?: number } = {}) {
    const flags = [];
    if (opts.session) flags.push('--session', opts.session);
    if (opts.timeout) flags.push('--timeout', String(opts.timeout));
    return this.invoke(['task', 'start', promptFile], flags);
  }

  async taskWait(taskId: string, timeoutMs = 300000) {
    return this.invoke(['task', 'wait', taskId, '--timeout', String(timeoutMs / 1000)]);
  }
}
```

---

## 11. Go Integration

### Basic os/exec Invocation

```go
package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"time"
)

// CLIResult represents structured CLI output
type CLIResult struct {
	OK     bool            `json:"ok"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  *CLIError       `json:"error,omitempty"`
}

type CLIError struct {
	Code      string `json:"code"`
	Message   string `json:"message"`
	Retryable bool   `json:"retryable"`
}

// InvokeCLI executes a CLI command with JSON output and timeout
func InvokeCLI(ctx context.Context, args []string, timeout time.Duration) (*CLIResult, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Append standard flags
	fullArgs := append(args, "--json", "--quiet")
	cmd := exec.CommandContext(ctx, fullArgs[0], fullArgs[1:]...)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	cmd.Env = append(cmd.Environ(), "NO_COLOR=1")

	err := cmd.Run()
	if ctx.Err() == context.DeadlineExceeded {
		return &CLIResult{
			OK:    false,
			Error: &CLIError{Code: "timeout", Message: "Command timed out", Retryable: true},
		}, nil
	}

	if stdout.Len() > 0 {
		var result CLIResult
		if err := json.Unmarshal(stdout.Bytes(), &result); err != nil {
			return nil, fmt.Errorf("invalid JSON output: %w", err)
		}
		return &result, nil
	}

	if err != nil {
		exitCode := 1
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		}
		return &CLIResult{
			OK:    false,
			Error: &CLIError{Code: fmt.Sprintf("exit_%d", exitCode), Message: stderr.String()},
		}, nil
	}

	return &CLIResult{OK: true}, nil
}
```

### Context Cancellation and Retry

```go
package agent

import (
	"context"
	"math"
	"math/rand"
	"time"
)

// InvokeWithRetry executes CLI with exponential backoff retry
func InvokeWithRetry(ctx context.Context, args []string, opts RetryOptions) (*CLIResult, error) {
	if opts.MaxRetries == 0 {
		opts.MaxRetries = 3
	}
	if opts.BaseDelay == 0 {
		opts.BaseDelay = time.Second
	}

	var lastResult *CLIResult
	for attempt := 0; attempt <= opts.MaxRetries; attempt++ {
		result, err := InvokeCLI(ctx, args, opts.Timeout)
		if err != nil {
			return nil, err
		}

		if result.OK {
			return result, nil
		}

		lastResult = result
		if result.Error == nil || !result.Error.Retryable {
			return result, nil
		}

		if attempt == opts.MaxRetries {
			break
		}

		// Exponential backoff with jitter
		delay := opts.BaseDelay * time.Duration(math.Pow(2, float64(attempt)))
		jitter := time.Duration(rand.Float64() * float64(time.Second))
		
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(delay + jitter):
		}
	}

	return lastResult, nil
}

type RetryOptions struct {
	MaxRetries int
	BaseDelay  time.Duration
	Timeout    time.Duration
}
```

### JSONL Streaming with Context

```go
package agent

import (
	"bufio"
	"context"
	"encoding/json"
	"os/exec"
)

// TaskEvent represents a streaming task event
type TaskEvent struct {
	Type   string          `json:"type"`
	TaskID string          `json:"task_id,omitempty"`
	Data   json.RawMessage `json:"data,omitempty"`
}

// StreamTaskEvents streams JSONL events from task follow
func StreamTaskEvents(ctx context.Context, taskID string) (<-chan TaskEvent, <-chan error) {
	events := make(chan TaskEvent)
	errs := make(chan error, 1)

	go func() {
		defer close(events)
		defer close(errs)

		cmd := exec.CommandContext(ctx, "mycli", "task", "follow", taskID, "--json")
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			errs <- err
			return
		}

		if err := cmd.Start(); err != nil {
			errs <- err
			return
		}

		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			var event TaskEvent
			if err := json.Unmarshal(scanner.Bytes(), &event); err != nil {
				continue // Skip malformed lines
			}
			select {
			case events <- event:
			case <-ctx.Done():
				cmd.Process.Kill()
				return
			}
		}

		if err := scanner.Err(); err != nil {
			errs <- err
		}
		cmd.Wait()
	}()

	return events, errs
}

// Usage example
func RunTaskWithStreaming(ctx context.Context, promptFile string) error {
	// Start task
	result, err := InvokeCLI(ctx, []string{"mycli", "task", "start", promptFile}, 30*time.Second)
	if err != nil || !result.OK {
		return fmt.Errorf("failed to start task: %v", err)
	}

	var startResp struct {
		TaskID string `json:"task_id"`
	}
	json.Unmarshal(result.Result, &startResp)

	// Stream events
	events, errs := StreamTaskEvents(ctx, startResp.TaskID)
	for {
		select {
		case event, ok := <-events:
			if !ok {
				return nil
			}
			switch event.Type {
			case "approval":
				// Auto-approve (use --yes in production)
				InvokeCLI(ctx, []string{"mycli", "request", "answer", "req_id", "--yes"}, 10*time.Second)
			case "complete":
				return nil
			case "error":
				return fmt.Errorf("task error: %s", event.Data)
			}
		case err := <-errs:
			if err != nil {
				return err
			}
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}
```

---

## 12. Error Recovery Patterns

### Auth Token Refresh

```typescript
interface TokenManager {
  getToken(): Promise<string>;
  refreshToken(): Promise<string>;
  clearToken(): void;
}

class AuthRecoveryCLI {
  constructor(
    private cli: CLIAgent,
    private tokens: TokenManager
  ) {}

  async invokeWithAuthRecovery(cmd: string[]): Promise<CLIResult> {
    let result = await this.cli.invoke(cmd);

    // Exit code 4 = auth error
    if (!result.ok && result.error?.code === 'exit_4') {
      console.log('Auth expired, refreshing token...');
      
      try {
        await this.tokens.refreshToken();
        // Retry with fresh token
        result = await this.cli.invoke(cmd);
      } catch (refreshError) {
        // Refresh failed, force re-login
        this.tokens.clearToken();
        await this.cli.invoke(['auth', 'login', '--yes']);
        result = await this.cli.invoke(cmd);
      }
    }

    return result;
  }
}
```

### Conflict Resolution

```typescript
type ConflictStrategy = 'force' | 'merge' | 'abort' | 'prompt';

async function invokeWithConflictResolution(
  cmd: string[],
  strategy: ConflictStrategy = 'merge'
): Promise<CLIResult> {
  const result = await invokeCLI(cmd);

  // Exit code 5 = conflict
  if (!result.ok && result.error?.code === 'exit_5') {
    const conflictData = result.error as { base_version?: string; current_version?: string };

    switch (strategy) {
      case 'force':
        // Retry with --force flag
        return invokeCLI([...cmd, '--force']);

      case 'merge':
        // Attempt three-way merge
        const mergeCmd = [
          'mycli', 'resource', 'merge',
          '--base', conflictData.base_version,
          '--current', conflictData.current_version,
          '--json', '--yes'
        ];
        const mergeResult = await invokeCLI(mergeCmd);
        if (mergeResult.ok) {
          return invokeCLI(cmd); // Retry original
        }
        return mergeResult;

      case 'abort':
        return result; // Return conflict as-is

      case 'prompt':
        // In agent context, escalate to human
        return {
          ok: false,
          error: {
            code: 'human_required',
            message: `Conflict requires human resolution: ${result.error.message}`,
            retryable: false,
          },
        };
    }
  }

  return result;
}
```

### Circuit Breaker Pattern

```typescript
enum CircuitState {
  CLOSED = 'closed',    // Normal operation
  OPEN = 'open',        // Failing fast
  HALF_OPEN = 'half_open', // Testing recovery
}

class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold: number;
  private readonly resetTimeout: number;

  constructor(options: { threshold?: number; resetTimeoutMs?: number } = {}) {
    this.threshold = options.threshold ?? 5;
    this.resetTimeout = options.resetTimeoutMs ?? 60000;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailure > this.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error('Circuit breaker is OPEN - failing fast');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = CircuitState.CLOSED;
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = CircuitState.OPEN;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

// Usage with CLI
const breaker = new CircuitBreaker({ threshold: 3, resetTimeoutMs: 30000 });

async function resilientInvoke(cmd: string[]): Promise<CLIResult> {
  return breaker.execute(async () => {
    const result = await invokeCLI(cmd);
    if (!result.ok && !result.error?.retryable) {
      throw new Error(result.error?.message);
    }
    return result;
  });
}
```

### Graceful Degradation

```typescript
interface FallbackOptions {
  primary: () => Promise<CLIResult>;
  fallback: () => Promise<CLIResult>;
  shouldFallback: (result: CLIResult) => boolean;
}

async function withFallback(options: FallbackOptions): Promise<CLIResult> {
  const primaryResult = await options.primary();
  
  if (options.shouldFallback(primaryResult)) {
    console.warn('Primary failed, attempting fallback...');
    return options.fallback();
  }
  
  return primaryResult;
}

// Example: Fall back to cached data on API failure
const result = await withFallback({
  primary: () => invokeCLI(['mycli', 'resource', 'get', 'id', '--json']),
  fallback: () => invokeCLI(['mycli', 'cache', 'get', 'id', '--json']),
  shouldFallback: (r) => !r.ok && r.error?.code === 'exit_7', // Transient error
});
```

---

## 13. Agent Framework Integration

### LangChain Tool Definition

```typescript
import { DynamicStructuredTool } from '@langchain/core/tools';
import { z } from 'zod';

const cliTool = new DynamicStructuredTool({
  name: 'invoke_cli',
  description: 'Execute CLI commands and return structured JSON results. Always use --json and --quiet flags.',
  schema: z.object({
    command: z.string().describe('CLI command (e.g., "mycli task start")'),
    args: z.array(z.string()).optional().describe('Positional arguments'),
    flags: z.record(z.string()).optional().describe('Named flags as key-value pairs'),
    timeout: z.number().optional().default(30).describe('Timeout in seconds'),
    dryRun: z.boolean().optional().describe('If true, adds --dry-run flag'),
  }),
  func: async ({ command, args = [], flags = {}, timeout, dryRun }) => {
    const cmd = command.split(' ');
    
    // Add positional args
    cmd.push(...args);
    
    // Add named flags
    for (const [key, value] of Object.entries(flags)) {
      cmd.push(`--${key}`, value);
    }
    
    // Standard flags
    cmd.push('--json', '--quiet');
    if (dryRun) cmd.push('--dry-run');
    
    const result = await invokeCLI(cmd, { timeout: timeout * 1000 });
    return JSON.stringify(result, null, 2);
  },
});

// LangChain agent usage
import { ChatOpenAI } from '@langchain/openai';
import { AgentExecutor, createOpenAIToolsAgent } from 'langchain/agents';

const llm = new ChatOpenAI({ model: 'gpt-4o' });
const agent = await createOpenAIToolsAgent({ llm, tools: [cliTool], prompt });
const executor = new AgentExecutor({ agent, tools: [cliTool] });

const result = await executor.invoke({
  input: 'Start a coding task using the prompt in task.md and wait for completion',
});
```

### Claude Computer Use / Tool Use

```typescript
// Claude tool definition for Anthropic API
const claudeTools = [
  {
    name: 'execute_cli',
    description: `Execute CLI commands for task automation. Returns JSON output.
    
Available commands:
- task start <file.md>: Start async task, returns task_id
- task follow <id>: Stream task events  
- task wait <id>: Block until completion
- task read <id>: Read task state and artifacts
- request answer <req_id> --yes: Approve pending request
- session list: List active sessions

Flags (always include):
--json: Structured JSON output
--quiet: Suppress non-essential output
--yes: Auto-approve confirmations
--timeout <secs>: Set timeout
--dry-run: Preview without executing`,
    input_schema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'Full CLI command string',
        },
        working_directory: {
          type: 'string',
          description: 'Working directory for command execution',
        },
      },
      required: ['command'],
    },
  },
];

// Handle Claude tool calls
async function handleClaudeToolCall(
  toolName: string,
  toolInput: Record<string, unknown>
): Promise<string> {
  if (toolName === 'execute_cli') {
    const cmd = (toolInput.command as string).split(' ');
    const cwd = toolInput.working_directory as string | undefined;
    
    // Ensure JSON output
    if (!cmd.includes('--json')) cmd.push('--json');
    if (!cmd.includes('--quiet')) cmd.push('--quiet');
    
    const result = await invokeCLI(cmd, { cwd });
    return JSON.stringify(result);
  }
  throw new Error(`Unknown tool: ${toolName}`);
}
```

### OpenAI Function Calling

```typescript
// OpenAI function definition
const openAIFunctions = [
  {
    type: 'function' as const,
    function: {
      name: 'cli_invoke',
      description: 'Execute a CLI command and return structured JSON output',
      parameters: {
        type: 'object',
        properties: {
          subcommand: {
            type: 'string',
            enum: ['task start', 'task follow', 'task wait', 'task read', 
                   'request answer', 'session list', 'session new', 'model list'],
            description: 'CLI subcommand to execute',
          },
          arguments: {
            type: 'array',
            items: { type: 'string' },
            description: 'Positional arguments for the command',
          },
          options: {
            type: 'object',
            properties: {
              yes: { type: 'boolean', description: 'Auto-approve (--yes)' },
              timeout: { type: 'number', description: 'Timeout in seconds (--timeout)' },
              session: { type: 'string', description: 'Session ID (--session)' },
              dry_run: { type: 'boolean', description: 'Dry run mode (--dry-run)' },
            },
          },
        },
        required: ['subcommand'],
      },
    },
  },
];

// Process OpenAI function call
async function processOpenAIFunctionCall(
  name: string,
  args: string
): Promise<string> {
  const parsed = JSON.parse(args);
  
  if (name === 'cli_invoke') {
    const cmd = ['mycli', ...parsed.subcommand.split(' ')];
    
    // Add positional args
    if (parsed.arguments) {
      cmd.push(...parsed.arguments);
    }
    
    // Add option flags
    const opts = parsed.options || {};
    if (opts.yes) cmd.push('--yes');
    if (opts.timeout) cmd.push('--timeout', String(opts.timeout));
    if (opts.session) cmd.push('--session', opts.session);
    if (opts.dry_run) cmd.push('--dry-run');
    
    // Standard flags
    cmd.push('--json', '--quiet');
    
    const result = await invokeWithRetry(cmd);
    return JSON.stringify(result);
  }
  
  throw new Error(`Unknown function: ${name}`);
}

// OpenAI chat completion with function calling
import OpenAI from 'openai';

const openai = new OpenAI();

async function runAgentLoop(userMessage: string): Promise<string> {
  const messages: OpenAI.ChatCompletionMessageParam[] = [
    { role: 'user', content: userMessage },
  ];

  while (true) {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages,
      tools: openAIFunctions,
    });

    const choice = response.choices[0];
    
    if (choice.finish_reason === 'stop') {
      return choice.message.content || '';
    }

    if (choice.finish_reason === 'tool_calls') {
      messages.push(choice.message);
      
      for (const toolCall of choice.message.tool_calls || []) {
        const result = await processOpenAIFunctionCall(
          toolCall.function.name,
          toolCall.function.arguments
        );
        messages.push({
          role: 'tool',
          tool_call_id: toolCall.id,
          content: result,
        });
      }
    }
  }
}
```

### AutoGen Integration

```python
from autogen import AssistantAgent, UserProxyAgent, register_function
import subprocess
import json

def invoke_cli(command: str, timeout: int = 30, dry_run: bool = False) -> dict:
    """
    Execute CLI command with JSON output.
    
    Args:
        command: Full CLI command string
        timeout: Command timeout in seconds
        dry_run: If True, adds --dry-run flag
    
    Returns:
        Structured JSON result with ok, result, error fields
    """
    cmd = command.split() + ['--json', '--quiet']
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {'ok': result.returncode == 0}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': {'code': 'timeout', 'retryable': True}}
    except json.JSONDecodeError:
        return {'ok': False, 'error': {'code': 'invalid_json', 'message': result.stdout}}

# Register with AutoGen
assistant = AssistantAgent("cli_assistant", llm_config=llm_config)
user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)

register_function(
    invoke_cli,
    caller=assistant,
    executor=user_proxy,
    description="Execute CLI commands with structured JSON output"
)
```

---

## 14. Observability

### Structured Logging

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
});

interface InvocationLog {
  cmd: string[];
  duration_ms: number;
  exit_code?: number;
  ok: boolean;
  error_code?: string;
}

async function invokeCLIWithLogging(cmd: string[]): Promise<CLIResult> {
  const start = Date.now();
  const childLogger = logger.child({ cmd: cmd.join(' ') });

  childLogger.debug('CLI invocation starting');

  try {
    const result = await invokeCLI(cmd);
    const duration = Date.now() - start;

    const logData: InvocationLog = {
      cmd,
      duration_ms: duration,
      ok: result.ok,
      error_code: result.error?.code,
    };

    if (result.ok) {
      childLogger.info(logData, 'CLI invocation succeeded');
    } else {
      childLogger.warn(logData, 'CLI invocation failed');
    }

    return result;
  } catch (error) {
    childLogger.error({ err: error, duration_ms: Date.now() - start }, 'CLI invocation error');
    throw error;
  }
}
```

### Metrics Collection

```typescript
import { Counter, Histogram, Registry } from 'prom-client';

const registry = new Registry();

const cliInvocations = new Counter({
  name: 'cli_invocations_total',
  help: 'Total CLI invocations',
  labelNames: ['command', 'status', 'exit_code'],
  registers: [registry],
});

const cliDuration = new Histogram({
  name: 'cli_duration_seconds',
  help: 'CLI invocation duration',
  labelNames: ['command'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
  registers: [registry],
});

const cliRetries = new Counter({
  name: 'cli_retries_total',
  help: 'CLI retry attempts',
  labelNames: ['command', 'reason'],
  registers: [registry],
});

async function invokeCLIWithMetrics(cmd: string[]): Promise<CLIResult> {
  const command = cmd.slice(0, 3).join('_'); // e.g., mycli_task_start
  const timer = cliDuration.startTimer({ command });

  try {
    const result = await invokeCLI(cmd);
    
    cliInvocations.inc({
      command,
      status: result.ok ? 'success' : 'failure',
      exit_code: result.error?.code || '0',
    });

    return result;
  } finally {
    timer();
  }
}

// Expose metrics endpoint
import express from 'express';
const app = express();
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});
```

### Distributed Tracing (OpenTelemetry)

```typescript
import { trace, SpanStatusCode, context } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

// Initialize tracer
const provider = new NodeTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(new OTLPTraceExporter()));
provider.register();

const tracer = trace.getTracer('cli-agent');

async function invokeCLIWithTracing(cmd: string[]): Promise<CLIResult> {
  return tracer.startActiveSpan('cli.invoke', async (span) => {
    span.setAttributes({
      'cli.command': cmd[0],
      'cli.subcommand': cmd.slice(1, 3).join(' '),
      'cli.args_count': cmd.length,
    });

    try {
      const result = await invokeCLI(cmd);

      span.setAttributes({
        'cli.ok': result.ok,
        'cli.error_code': result.error?.code || '',
      });

      if (!result.ok) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: result.error?.message,
        });
      }

      return result;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  });
}

// Propagate trace context to CLI (if supported)
async function invokeCLIWithContextPropagation(cmd: string[]): Promise<CLIResult> {
  return tracer.startActiveSpan('cli.invoke', async (span) => {
    const traceId = span.spanContext().traceId;
    const spanId = span.spanContext().spanId;

    // Add trace context as env vars or headers
    const result = await invokeCLI(cmd, {
      env: {
        TRACE_ID: traceId,
        SPAN_ID: spanId,
      },
    });

    return result;
  });
}
```

### Health Checks

```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, {
    status: 'pass' | 'fail';
    latency_ms?: number;
    message?: string;
  }>;
  timestamp: string;
}

async function checkCLIHealth(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = {};

  // Check CLI is accessible
  const start = Date.now();
  try {
    const result = await invokeCLI(['mycli', 'version', '--json'], { timeout: 5000 });
    checks.cli_accessible = {
      status: result.ok ? 'pass' : 'fail',
      latency_ms: Date.now() - start,
    };
  } catch {
    checks.cli_accessible = { status: 'fail', message: 'CLI not accessible' };
  }

  // Check daemon is running
  try {
    const result = await invokeCLI(['mycli', 'daemon', 'status', '--json'], { timeout: 5000 });
    checks.daemon_running = {
      status: result.ok ? 'pass' : 'fail',
      latency_ms: Date.now() - start,
    };
  } catch {
    checks.daemon_running = { status: 'fail', message: 'Daemon not responding' };
  }

  // Check auth is valid
  try {
    const result = await invokeCLI(['mycli', 'account', 'whoami', '--json'], { timeout: 5000 });
    checks.auth_valid = { status: result.ok ? 'pass' : 'fail' };
  } catch {
    checks.auth_valid = { status: 'fail', message: 'Auth check failed' };
  }

  // Determine overall status
  const failedChecks = Object.values(checks).filter((c) => c.status === 'fail').length;
  let status: HealthStatus['status'] = 'healthy';
  if (failedChecks > 0) status = 'degraded';
  if (failedChecks === Object.keys(checks).length) status = 'unhealthy';

  return {
    status,
    checks,
    timestamp: new Date().toISOString(),
  };
}
```

### Alerting Integration

```typescript
interface AlertConfig {
  webhook_url: string;
  threshold_errors_per_minute: number;
  threshold_latency_p99_ms: number;
}

class AlertManager {
  private errors: number[] = [];
  private latencies: number[] = [];
  private readonly windowMs = 60000;

  constructor(private config: AlertConfig) {}

  recordInvocation(ok: boolean, latencyMs: number): void {
    const now = Date.now();
    
    // Clean old entries
    this.errors = this.errors.filter((t) => now - t < this.windowMs);
    this.latencies = this.latencies.filter((t) => now - t < this.windowMs);

    if (!ok) this.errors.push(now);
    this.latencies.push(latencyMs);

    this.checkThresholds();
  }

  private checkThresholds(): void {
    // Check error rate
    if (this.errors.length > this.config.threshold_errors_per_minute) {
      this.sendAlert('error_rate', {
        errors_per_minute: this.errors.length,
        threshold: this.config.threshold_errors_per_minute,
      });
    }

    // Check p99 latency
    if (this.latencies.length >= 10) {
      const sorted = [...this.latencies].sort((a, b) => a - b);
      const p99 = sorted[Math.floor(sorted.length * 0.99)];
      if (p99 > this.config.threshold_latency_p99_ms) {
        this.sendAlert('high_latency', {
          p99_latency_ms: p99,
          threshold: this.config.threshold_latency_p99_ms,
        });
      }
    }
  }

  private async sendAlert(type: string, data: Record<string, unknown>): Promise<void> {
    await fetch(this.config.webhook_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alert_type: type,
        timestamp: new Date().toISOString(),
        data,
      }),
    });
  }
}
```

---

## 15. Standard CLI Flags Reference

| Flag | Short | Description | When to Use |
|------|-------|-------------|-------------|
| `--json` | | Structured JSON output | **Always** in agent context |
| `--quiet` | `-q` | Suppress non-essential output | Cleaner parsing, reduce noise |
| `--yes` | `-y` | Auto-approve confirmations | Non-interactive automation |
| `--timeout <secs>` | `-t` | Set operation timeout | Long-running tasks, prevent hangs |
| `--dry-run` | | Preview without executing | Validation before commit |
| `--force` | `-f` | Override safety checks | Conflict resolution |
| `--verbose` | `-v` | Extra debug output | Troubleshooting (not for agents) |

### Flag Usage Patterns

```bash
# Standard agent invocation
mycli task start prompt.md --json --quiet --yes --timeout 300

# Dry run validation
mycli resource create config.yaml --json --dry-run

# Force overwrite on conflict
mycli resource update id --json --yes --force

# Verbose for debugging (human use)
mycli task start prompt.md --json --verbose 2>&1 | tee debug.log
```

---

## 16. Steering Contract: Put Next-Step Guidance in CLI stdout

Everything learned from MCP tool steering also applies to CLI tools. If the CLI is being called by an agent, stdout is not just a payload channel. It is the continuation contract.

Return guidance in a stable top-level field so the agent can decide what to do next without guessing:

```json
{
  "ok": true,
  "result": {
    "query": "technical seo agent workflows",
    "results": ["..."]
  },
  "guidance": {
    "summary": "Current results cover general overviews but miss concrete CLI examples.",
    "next_actions": [
      {
        "command": "seo-research fetch-pages --source-set current --json",
        "reason": "Open the top authoritative sources from this wave."
      }
    ],
    "recommended_queries": [
      {
        "query": "agentic cli seo workflow examples",
        "reason": "Fill the CLI implementation gap",
        "confidence": 0.81
      }
    ],
    "stop_conditions": [
      "Stop after 12 total searches.",
      "Stop if two consecutive waves add no novel high-quality domains."
    ],
    "actions_taken": [
      {
        "type": "internal_planner_turn",
        "purpose": "derive next-query candidates from current SERP"
      }
    ]
  },
  "error": null,
  "schema_version": "v1"
}
```

**Why this matters:**
- The agent sees the answer and the continuation frontier in one parseable envelope.
- You eliminate a class of low-signal turns where the model asks itself what to do next.
- The CLI becomes agentic without becoming opaque.

**Design rules:**
- Put steering in `guidance`, not mixed into `result`.
- Use ranked `recommended_queries` or `next_actions`, not one vague paragraph.
- Distinguish between `actions_taken` and `next_actions`.
- Keep the same field names across commands so the agent learns the contract once.

This pattern is especially strong for SEO and research CLIs, where the real job is not "return results" but "advance the search frontier."

---

## 17. Planner-in-the-CLI Is Valid if It Is Bounded and Disclosed

Do not assume agentic continuation is only for MCP. A CLI can also spend a small internal planning budget and return better follow-up guidance.

Example:

```bash
seo-research serp "technical seo agent workflows" --json --plan-next 3
```

The command can:
1. fetch the current SERP
2. run a bounded internal model or heuristic planner
3. return the current results plus the best next three queries

This is the CLI version of a server-side continuation pattern. It is valid when:
- the workflow is read-only
- the continuation budget is bounded
- the command reports what it already did
- the output stays machine-readable

Do not hide writes, destructive actions, or expensive unbounded loops behind `--plan-next`. Use planner turns to collapse obvious research loops, not to make the CLI inscrutable.

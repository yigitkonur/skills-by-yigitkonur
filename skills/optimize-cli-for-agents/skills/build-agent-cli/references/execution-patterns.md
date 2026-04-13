# Execution Patterns for Agent-Friendly CLIs

This reference covers patterns that make CLI tools predictable, retry-safe, and automation-friendly.

---

## 1. Idempotency Patterns

Idempotent operations produce the same result regardless of how many times they're executed. This is critical for retry logic and agent workflows.

### Verb Semantics

| Verb | Absent Target | Present Target | Retry Safe? |
|------|--------------|----------------|-------------|
| `create` | Create | Fail (conflict) | With idempotency key |
| `apply` | Create | Update/patch | After conflict resolution |
| `ensure` | Create | No-op or update if needed | Yes |
| `delete` | Success (or 404) | Delete | Yes (absent = done) |
| `sync` | Create all | Update to match | Yes |

### Idempotency Key Pattern

```bash
# Same key = same result (server caches outcome)
mycli create resource --idempotency-key "create-foo-v1" --name foo
```

**Go Implementation:**

```go
type CreateRequest struct {
    Name           string `json:"name"`
    IdempotencyKey string `json:"idempotency_key,omitempty"`
}

func (s *Server) handleCreate(w http.ResponseWriter, r *http.Request) {
    var req CreateRequest
    json.NewDecoder(r.Body).Decode(&req)
    
    // Check idempotency cache
    if req.IdempotencyKey != "" {
        if cached, ok := s.idempotencyCache.Get(req.IdempotencyKey); ok {
            json.NewEncoder(w).Encode(cached)
            return
        }
    }
    
    // Perform creation
    result, err := s.createResource(req)
    if err != nil {
        // Don't cache errors (except for specific cases)
        writeError(w, err)
        return
    }
    
    // Cache successful result
    if req.IdempotencyKey != "" {
        s.idempotencyCache.Set(req.IdempotencyKey, result, 24*time.Hour)
    }
    
    json.NewEncoder(w).Encode(result)
}
```

**Python Implementation:**

```python
import hashlib
from functools import lru_cache
from typing import Optional
import redis

class IdempotencyStore:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
    
    def get_or_execute(self, key: str, operation: callable) -> dict:
        # Check cache
        cached = self.redis.get(f"idempotency:{key}")
        if cached:
            return json.loads(cached)
        
        # Execute operation
        result = operation()
        
        # Cache result
        self.redis.setex(
            f"idempotency:{key}",
            self.ttl,
            json.dumps(result)
        )
        return result

# CLI usage
@click.command()
@click.option('--idempotency-key', help='Key for idempotent retry')
@click.option('--name', required=True)
def create(idempotency_key: Optional[str], name: str):
    def do_create():
        return api.create_resource(name=name)
    
    if idempotency_key:
        result = idempotency_store.get_or_execute(idempotency_key, do_create)
    else:
        result = do_create()
    
    output_json(result)
```

**Node.js Implementation:**

```typescript
import { createHash } from 'crypto';

interface IdempotencyResult<T> {
  cached: boolean;
  result: T;
}

class IdempotencyManager {
  private cache: Map<string, { result: unknown; expiry: number }> = new Map();
  private ttlMs = 24 * 60 * 60 * 1000; // 24 hours

  async executeIdempotent<T>(
    key: string,
    operation: () => Promise<T>
  ): Promise<IdempotencyResult<T>> {
    // Check cache
    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return { cached: true, result: cached.result as T };
    }

    // Execute operation
    const result = await operation();

    // Cache result
    this.cache.set(key, {
      result,
      expiry: Date.now() + this.ttlMs,
    });

    return { cached: false, result };
  }
}

// CLI command
program
  .command('create')
  .option('--idempotency-key <key>', 'Idempotency key for safe retry')
  .option('--name <name>', 'Resource name')
  .action(async (options) => {
    const idempotency = new IdempotencyManager();
    
    const { result } = options.idempotencyKey
      ? await idempotency.executeIdempotent(
          options.idempotencyKey,
          () => api.createResource(options.name)
        )
      : { result: await api.createResource(options.name) };
    
    console.log(JSON.stringify(result));
  });
```

### Declarative vs Imperative

| Style | Example | When to Use |
|-------|---------|-------------|
| **Declarative** | `apply -f config.yaml` | Complex resources, GitOps |
| **Imperative** | `create`, `delete`, `scale` | Simple one-off actions |

**Declarative Apply Pattern:**

```bash
# Specify desired state - tool figures out how to get there
mycli apply -f deployment.yaml

# Output shows what changed
{
  "ok": true,
  "changes": [
    {"action": "update", "resource": "deployment/web", "field": "replicas", "old": 2, "new": 3}
  ]
}
```

---

## 2. Retry Logic

### Retry Classification

| Error Class | Retry? | Strategy | Example |
|-------------|--------|----------|---------|
| `transient` | Yes | Exponential backoff | Temporary server issue |
| `rate_limit` | Yes | Honor Retry-After | 429 Too Many Requests |
| `timeout` | Yes | With jitter | Request timeout |
| `network` | Yes | With jitter | Connection refused |
| `conflict` | Maybe | Re-read, re-apply | Optimistic lock failure |
| `validation` | No | Fail fast | Invalid input |
| `auth` | No | Fail fast | Unauthorized |
| `not_found` | No | Fail fast | Resource doesn't exist |

### Go Retry Implementation

```go
package retry

import (
    "context"
    "errors"
    "math"
    "math/rand"
    "net/http"
    "strconv"
    "time"
)

type Config struct {
    MaxAttempts     int
    InitialBackoff  time.Duration
    MaxBackoff      time.Duration
    BackoffFactor   float64
    Jitter          float64 // 0.0 to 1.0
}

var DefaultConfig = Config{
    MaxAttempts:    5,
    InitialBackoff: 100 * time.Millisecond,
    MaxBackoff:     30 * time.Second,
    BackoffFactor:  2.0,
    Jitter:         0.2,
}

type RetryableError struct {
    Err        error
    RetryAfter time.Duration
}

func (e *RetryableError) Error() string { return e.Err.Error() }
func (e *RetryableError) Unwrap() error { return e.Err }

func IsRetryable(err error) bool {
    var retryErr *RetryableError
    return errors.As(err, &retryErr)
}

func Do(ctx context.Context, cfg Config, operation func() error) error {
    var lastErr error
    
    for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
        err := operation()
        if err == nil {
            return nil
        }
        
        lastErr = err
        
        // Check if retryable
        var retryErr *RetryableError
        if !errors.As(err, &retryErr) {
            return err // Non-retryable, fail immediately
        }
        
        // Check context
        if ctx.Err() != nil {
            return ctx.Err()
        }
        
        // Calculate backoff
        var backoff time.Duration
        if retryErr.RetryAfter > 0 {
            backoff = retryErr.RetryAfter
        } else {
            backoff = cfg.InitialBackoff * time.Duration(math.Pow(cfg.BackoffFactor, float64(attempt)))
            if backoff > cfg.MaxBackoff {
                backoff = cfg.MaxBackoff
            }
            // Add jitter
            jitter := time.Duration(float64(backoff) * cfg.Jitter * (rand.Float64()*2 - 1))
            backoff += jitter
        }
        
        select {
        case <-time.After(backoff):
            continue
        case <-ctx.Done():
            return ctx.Err()
        }
    }
    
    return fmt.Errorf("max retries exceeded: %w", lastErr)
}

// HTTP client with retry
func DoHTTP(ctx context.Context, client *http.Client, req *http.Request) (*http.Response, error) {
    var resp *http.Response
    
    err := Do(ctx, DefaultConfig, func() error {
        var err error
        resp, err = client.Do(req.Clone(ctx))
        if err != nil {
            return &RetryableError{Err: err}
        }
        
        switch resp.StatusCode {
        case http.StatusTooManyRequests:
            retryAfter := parseRetryAfter(resp.Header.Get("Retry-After"))
            return &RetryableError{
                Err:        fmt.Errorf("rate limited"),
                RetryAfter: retryAfter,
            }
        case http.StatusServiceUnavailable, http.StatusBadGateway, http.StatusGatewayTimeout:
            return &RetryableError{Err: fmt.Errorf("server error: %d", resp.StatusCode)}
        case http.StatusConflict:
            // Conflict might be retryable after re-read
            return &RetryableError{Err: fmt.Errorf("conflict")}
        default:
            if resp.StatusCode >= 500 {
                return &RetryableError{Err: fmt.Errorf("server error: %d", resp.StatusCode)}
            }
            return nil // Success or client error (not retryable)
        }
    })
    
    return resp, err
}

func parseRetryAfter(value string) time.Duration {
    if value == "" {
        return 0
    }
    // Try seconds
    if seconds, err := strconv.Atoi(value); err == nil {
        return time.Duration(seconds) * time.Second
    }
    // Try HTTP date (simplified)
    if t, err := time.Parse(time.RFC1123, value); err == nil {
        return time.Until(t)
    }
    return 0
}
```

### Python Retry Implementation

```python
import time
import random
from functools import wraps
from typing import Callable, Type, Tuple
from dataclasses import dataclass
import httpx

@dataclass
class RetryConfig:
    max_attempts: int = 5
    initial_backoff: float = 0.1
    max_backoff: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.2
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.NetworkError,
    )
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)

class RetryExhausted(Exception):
    def __init__(self, last_error: Exception, attempts: int):
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_error}")

def with_retry(config: RetryConfig = None):
    config = config or RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_error = e
                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in config.retryable_status_codes:
                        raise
                    last_error = e
                    
                    # Honor Retry-After header
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            backoff = float(retry_after)
                            time.sleep(backoff)
                            continue
                        except ValueError:
                            pass
                
                # Calculate backoff
                backoff = min(
                    config.initial_backoff * (config.backoff_factor ** attempt),
                    config.max_backoff
                )
                # Add jitter
                jitter = backoff * config.jitter * (random.random() * 2 - 1)
                backoff += jitter
                
                time.sleep(backoff)
            
            raise RetryExhausted(last_error, config.max_attempts)
        
        return wrapper
    return decorator

# Usage
@with_retry(RetryConfig(max_attempts=3))
def create_resource(name: str) -> dict:
    response = httpx.post(f"{API_URL}/resources", json={"name": name})
    response.raise_for_status()
    return response.json()
```

### Node.js Retry Implementation

```typescript
interface RetryConfig {
  maxAttempts: number;
  initialBackoffMs: number;
  maxBackoffMs: number;
  backoffFactor: number;
  jitter: number;
  isRetryable?: (error: Error) => boolean;
}

const defaultConfig: RetryConfig = {
  maxAttempts: 5,
  initialBackoffMs: 100,
  maxBackoffMs: 30000,
  backoffFactor: 2,
  jitter: 0.2,
  isRetryable: (error) => {
    // Default: retry network errors and 5xx
    if (error.name === 'FetchError') return true;
    if ('status' in error) {
      const status = (error as any).status;
      return status === 429 || (status >= 500 && status < 600);
    }
    return false;
  },
};

async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const cfg = { ...defaultConfig, ...config };
  let lastError: Error;

  for (let attempt = 0; attempt < cfg.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      if (!cfg.isRetryable!(lastError)) {
        throw error;
      }

      // Check for Retry-After header
      let backoffMs: number;
      const retryAfter = (error as any).response?.headers?.get?.('retry-after');
      if (retryAfter) {
        backoffMs = parseInt(retryAfter, 10) * 1000;
      } else {
        backoffMs = Math.min(
          cfg.initialBackoffMs * Math.pow(cfg.backoffFactor, attempt),
          cfg.maxBackoffMs
        );
        // Add jitter
        const jitter = backoffMs * cfg.jitter * (Math.random() * 2 - 1);
        backoffMs += jitter;
      }

      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }

  throw new Error(`Retry exhausted after ${cfg.maxAttempts} attempts: ${lastError!.message}`);
}

// Usage
const result = await withRetry(
  () => fetch(`${API_URL}/resources`, { method: 'POST', body: JSON.stringify({ name }) }),
  { maxAttempts: 3 }
);
```

### Circuit Breaker Pattern

Stop retrying after repeated failures:

```go
type CircuitBreaker struct {
    maxFailures   int
    resetTimeout  time.Duration
    failures      int
    lastFailure   time.Time
    state         string // "closed", "open", "half-open"
    mu            sync.Mutex
}

func (cb *CircuitBreaker) Execute(operation func() error) error {
    cb.mu.Lock()
    
    // Check if circuit is open
    if cb.state == "open" {
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = "half-open"
        } else {
            cb.mu.Unlock()
            return errors.New("circuit breaker open")
        }
    }
    cb.mu.Unlock()
    
    err := operation()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = "open"
        }
        return err
    }
    
    // Success - reset
    cb.failures = 0
    cb.state = "closed"
    return nil
}
```

---

## 3. Dry-Run Modes

### Client-side vs Server-side

| Mode | What It Does | Accuracy |
|------|--------------|----------|
| `--dry-run=client` | Local validation only | May miss server-side issues |
| `--dry-run=server` | Full server processing, no persistence | High accuracy |

**Always prefer server-side dry-run when available.**

### Diff Output

```bash
$ mycli apply -f config.yaml --dry-run
```

Human-friendly output:
```
Dry run - no changes will be made

deployment/web
  ~ replicas: 2 → 3
  
deployment/api
  + (will be created)
  
configmap/legacy
  - (will be deleted)
  
Summary: 1 to create, 1 to update, 1 to delete
```

### Structured Dry-Run Response

```json
{
  "ok": true,
  "dry_run": true,
  "changes": [
    {
      "action": "create",
      "resource_type": "deployment",
      "resource_id": "web",
      "diff": null
    },
    {
      "action": "update",
      "resource_type": "deployment", 
      "resource_id": "api",
      "diff": {
        "replicas": {"old": 2, "new": 3},
        "image": {"old": "app:v1.0", "new": "app:v1.1"}
      }
    },
    {
      "action": "delete",
      "resource_type": "configmap",
      "resource_id": "legacy",
      "diff": null
    }
  ],
  "summary": {
    "create": 1,
    "update": 1,
    "delete": 1,
    "unchanged": 5
  },
  "validation_warnings": [
    {
      "resource": "deployment/api",
      "message": "Deprecated API version v1beta1, consider upgrading to v1"
    }
  ]
}
```

### Implementation

**Go:**

```go
type DryRunMode string

const (
    DryRunNone   DryRunMode = ""
    DryRunClient DryRunMode = "client"
    DryRunServer DryRunMode = "server"
)

type ApplyOptions struct {
    DryRun DryRunMode
    Files  []string
}

type Change struct {
    Action       string            `json:"action"` // create, update, delete
    ResourceType string            `json:"resource_type"`
    ResourceID   string            `json:"resource_id"`
    Diff         map[string]Diff   `json:"diff,omitempty"`
}

type Diff struct {
    Old interface{} `json:"old"`
    New interface{} `json:"new"`
}

type ApplyResult struct {
    OK       bool     `json:"ok"`
    DryRun   bool     `json:"dry_run"`
    Changes  []Change `json:"changes"`
    Summary  Summary  `json:"summary"`
}

func (c *Client) Apply(ctx context.Context, opts ApplyOptions) (*ApplyResult, error) {
    req := ApplyRequest{
        Resources: loadResources(opts.Files),
        DryRun:    opts.DryRun == DryRunServer,
    }
    
    // Client-side validation
    if opts.DryRun == DryRunClient {
        return c.validateLocally(req.Resources)
    }
    
    // Send to server
    return c.api.Apply(ctx, req)
}
```

**Python:**

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class DryRunMode(Enum):
    NONE = None
    CLIENT = "client"
    SERVER = "server"

@dataclass
class Change:
    action: str  # create, update, delete
    resource_type: str
    resource_id: str
    diff: Optional[Dict[str, Dict[str, Any]]] = None

@dataclass
class ApplyResult:
    ok: bool
    dry_run: bool
    changes: List[Change]
    summary: Dict[str, int]

def apply_resources(
    files: List[str],
    dry_run: DryRunMode = DryRunMode.NONE
) -> ApplyResult:
    resources = load_resources(files)
    
    if dry_run == DryRunMode.CLIENT:
        return validate_locally(resources)
    
    response = api.apply(
        resources=resources,
        dry_run=(dry_run == DryRunMode.SERVER)
    )
    
    return ApplyResult(
        ok=response["ok"],
        dry_run=response.get("dry_run", False),
        changes=[Change(**c) for c in response["changes"]],
        summary=response["summary"]
    )
```

---

## 4. Non-Interactive Mode

### Essential Flags

| Flag | Behavior |
|------|----------|
| `--non-interactive` / `--no-input` | Fail immediately if prompt needed |
| `--yes` / `-y` | Auto-confirm prompts (still validates) |
| `--force` / `-f` | Bypass safety checks (explicit risk) |

### TTY Detection

**Go:**

```go
import (
    "os"
    "golang.org/x/term"
)

type InteractiveMode int

const (
    ModeAuto InteractiveMode = iota
    ModeInteractive
    ModeNonInteractive
)

func IsInteractive(mode InteractiveMode) bool {
    switch mode {
    case ModeInteractive:
        return true
    case ModeNonInteractive:
        return false
    default:
        // Auto-detect
        return term.IsTerminal(int(os.Stdin.Fd())) && 
               term.IsTerminal(int(os.Stdout.Fd()))
    }
}

func Prompt(message string, mode InteractiveMode) (string, error) {
    if !IsInteractive(mode) {
        return "", fmt.Errorf("prompt required in non-interactive mode: %s", message)
    }
    
    fmt.Print(message)
    reader := bufio.NewReader(os.Stdin)
    return reader.ReadString('\n')
}

func Confirm(message string, mode InteractiveMode, autoYes bool) (bool, error) {
    if autoYes {
        return true, nil
    }
    
    if !IsInteractive(mode) {
        return false, fmt.Errorf("confirmation required in non-interactive mode: %s", message)
    }
    
    fmt.Printf("%s [y/N]: ", message)
    reader := bufio.NewReader(os.Stdin)
    response, _ := reader.ReadString('\n')
    return strings.ToLower(strings.TrimSpace(response)) == "y", nil
}
```

**Python:**

```python
import sys
import os

def is_interactive() -> bool:
    """Check if running in interactive mode."""
    # Check environment variable first
    if os.environ.get("MYCLI_NON_INTERACTIVE"):
        return False
    
    # Check if stdin/stdout are TTYs
    return sys.stdin.isatty() and sys.stdout.isatty()

def prompt(message: str, *, non_interactive: bool = False) -> str:
    """Prompt for input, fail in non-interactive mode."""
    if non_interactive or not is_interactive():
        raise RuntimeError(f"Prompt required in non-interactive mode: {message}")
    
    return input(message)

def confirm(
    message: str,
    *,
    non_interactive: bool = False,
    auto_yes: bool = False,
    default: bool = False
) -> bool:
    """Confirm action with user."""
    if auto_yes:
        return True
    
    if non_interactive or not is_interactive():
        return default
    
    response = input(f"{message} [y/N]: ").strip().lower()
    return response == "y"

# CLI integration
@click.command()
@click.option('--non-interactive', is_flag=True, envvar='MYCLI_NON_INTERACTIVE')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm prompts')
@click.option('--force', '-f', is_flag=True, help='Bypass safety checks')
def delete(non_interactive: bool, yes: bool, force: bool):
    if not force:
        if not confirm("This will delete all data. Continue?", 
                      non_interactive=non_interactive, auto_yes=yes):
            click.echo("Aborted")
            sys.exit(1)
    
    # Proceed with deletion
```

**Node.js:**

```typescript
import * as readline from 'readline';

function isInteractive(): boolean {
  if (process.env.MYCLI_NON_INTERACTIVE) {
    return false;
  }
  return process.stdin.isTTY && process.stdout.isTTY;
}

async function prompt(
  message: string,
  options: { nonInteractive?: boolean } = {}
): Promise<string> {
  if (options.nonInteractive || !isInteractive()) {
    throw new Error(`Prompt required in non-interactive mode: ${message}`);
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(message, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

async function confirm(
  message: string,
  options: { nonInteractive?: boolean; autoYes?: boolean } = {}
): Promise<boolean> {
  if (options.autoYes) {
    return true;
  }

  if (options.nonInteractive || !isInteractive()) {
    return false;
  }

  const answer = await prompt(`${message} [y/N]: `);
  return answer.toLowerCase() === 'y';
}
```

### Environment Variable Support

```bash
# Set globally for CI/CD
export MYCLI_NON_INTERACTIVE=1
export MYCLI_AUTO_YES=1

# Now all commands run non-interactively
mycli deploy
mycli delete resource
```

---

## 5. Batch Operations

### Chunked Processing

```bash
# Process in chunks with controlled concurrency
mycli bulk-create \
  --input items.json \
  --chunk-size 100 \
  --concurrency 5 \
  --continue-on-error
```

### Partial Failure Handling

**Response Structure:**

```json
{
  "ok": false,
  "status": "partial_failure",
  "summary": {
    "total": 100,
    "succeeded": 95,
    "failed": 5
  },
  "succeeded": [
    {"id": "item-1", "resource_id": "res_abc123"},
    {"id": "item-2", "resource_id": "res_def456"}
  ],
  "failed": [
    {
      "id": "item-96",
      "error": {
        "class": "validation",
        "code": "INVALID_NAME",
        "message": "Name contains invalid characters"
      }
    },
    {
      "id": "item-97",
      "error": {
        "class": "conflict",
        "code": "ALREADY_EXISTS",
        "message": "Resource already exists"
      }
    }
  ],
  "failed_items_file": "./bulk-create-failed-2024-01-15T10-30-00.json",
  "retry_command": "mycli bulk-create --input ./bulk-create-failed-2024-01-15T10-30-00.json"
}
```

### Implementation

**Go:**

```go
type BulkOptions struct {
    ChunkSize       int
    Concurrency     int
    ContinueOnError bool
    StopOnError     bool
}

type BulkResult struct {
    OK        bool         `json:"ok"`
    Status    string       `json:"status"` // success, partial_failure, failed
    Summary   BulkSummary  `json:"summary"`
    Succeeded []ItemResult `json:"succeeded"`
    Failed    []ItemError  `json:"failed"`
}

func BulkCreate(ctx context.Context, items []Item, opts BulkOptions) (*BulkResult, error) {
    result := &BulkResult{
        Succeeded: make([]ItemResult, 0),
        Failed:    make([]ItemError, 0),
    }
    
    // Process in chunks
    chunks := chunkItems(items, opts.ChunkSize)
    
    for _, chunk := range chunks {
        // Process chunk with concurrency limit
        sem := make(chan struct{}, opts.Concurrency)
        var wg sync.WaitGroup
        var mu sync.Mutex
        
        for _, item := range chunk {
            if ctx.Err() != nil {
                break
            }
            
            sem <- struct{}{}
            wg.Add(1)
            
            go func(item Item) {
                defer wg.Done()
                defer func() { <-sem }()
                
                res, err := createItem(ctx, item)
                
                mu.Lock()
                defer mu.Unlock()
                
                if err != nil {
                    result.Failed = append(result.Failed, ItemError{
                        ID:    item.ID,
                        Error: classifyError(err),
                    })
                    
                    if opts.StopOnError {
                        // Signal cancellation
                    }
                } else {
                    result.Succeeded = append(result.Succeeded, res)
                }
            }(item)
        }
        
        wg.Wait()
        
        if opts.StopOnError && len(result.Failed) > 0 {
            break
        }
    }
    
    // Set final status
    result.Summary = BulkSummary{
        Total:     len(items),
        Succeeded: len(result.Succeeded),
        Failed:    len(result.Failed),
    }
    
    if len(result.Failed) == 0 {
        result.OK = true
        result.Status = "success"
    } else if len(result.Succeeded) > 0 {
        result.OK = false
        result.Status = "partial_failure"
    } else {
        result.OK = false
        result.Status = "failed"
    }
    
    return result, nil
}
```

**Python:**

```python
import asyncio
from dataclasses import dataclass, field
from typing import List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class BulkResult:
    ok: bool
    status: str  # success, partial_failure, failed
    summary: dict
    succeeded: List[dict] = field(default_factory=list)
    failed: List[dict] = field(default_factory=list)

async def bulk_create(
    items: List[dict],
    chunk_size: int = 100,
    concurrency: int = 5,
    continue_on_error: bool = True
) -> BulkResult:
    succeeded = []
    failed = []
    
    # Process in chunks
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        
        # Process chunk with semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_item(item):
            async with semaphore:
                try:
                    result = await create_item(item)
                    return ("success", item["id"], result)
                except Exception as e:
                    return ("error", item["id"], classify_error(e))
        
        results = await asyncio.gather(
            *[process_item(item) for item in chunk],
            return_exceptions=True
        )
        
        for result in results:
            if result[0] == "success":
                succeeded.append({"id": result[1], **result[2]})
            else:
                failed.append({"id": result[1], "error": result[2]})
                
                if not continue_on_error:
                    break
        
        if not continue_on_error and failed:
            break
    
    # Determine status
    if not failed:
        status = "success"
        ok = True
    elif succeeded:
        status = "partial_failure"
        ok = False
    else:
        status = "failed"
        ok = False
    
    return BulkResult(
        ok=ok,
        status=status,
        summary={
            "total": len(items),
            "succeeded": len(succeeded),
            "failed": len(failed)
        },
        succeeded=succeeded,
        failed=failed
    )
```

---

## 6. Transaction/Rollback

### Multi-Step Operations

```bash
# Automatic rollback on failure
mycli deploy --rollback-on-failure

# Manual checkpoint-based rollback
mycli rollback --to checkpoint_abc123
```

### Implementation

**Go:**

```go
type Step struct {
    Name    string
    Execute func(ctx context.Context) error
    Undo    func(ctx context.Context) error
}

type Transaction struct {
    steps     []Step
    completed []int
}

func (t *Transaction) AddStep(step Step) {
    t.steps = append(t.steps, step)
}

func (t *Transaction) Execute(ctx context.Context, rollbackOnFailure bool) error {
    for i, step := range t.steps {
        if err := step.Execute(ctx); err != nil {
            if rollbackOnFailure {
                t.Rollback(ctx)
            }
            return fmt.Errorf("step %s failed: %w", step.Name, err)
        }
        t.completed = append(t.completed, i)
    }
    return nil
}

func (t *Transaction) Rollback(ctx context.Context) error {
    // Undo in reverse order
    for i := len(t.completed) - 1; i >= 0; i-- {
        stepIdx := t.completed[i]
        step := t.steps[stepIdx]
        
        if step.Undo != nil {
            if err := step.Undo(ctx); err != nil {
                // Log but continue rollback
                log.Printf("Rollback step %s failed: %v", step.Name, err)
            }
        }
    }
    return nil
}

// Usage
func Deploy(ctx context.Context) error {
    tx := &Transaction{}
    
    tx.AddStep(Step{
        Name: "create-database",
        Execute: func(ctx context.Context) error {
            return createDatabase(ctx)
        },
        Undo: func(ctx context.Context) error {
            return deleteDatabase(ctx)
        },
    })
    
    tx.AddStep(Step{
        Name: "run-migrations",
        Execute: func(ctx context.Context) error {
            return runMigrations(ctx)
        },
        Undo: func(ctx context.Context) error {
            return rollbackMigrations(ctx)
        },
    })
    
    tx.AddStep(Step{
        Name: "deploy-application",
        Execute: func(ctx context.Context) error {
            return deployApp(ctx)
        },
        Undo: func(ctx context.Context) error {
            return rollbackApp(ctx)
        },
    })
    
    return tx.Execute(ctx, true) // rollback on failure
}
```

---

## 7. Long-Running Task Handling

### Submit and Poll Pattern

```bash
# Submit (returns immediately)
$ mycli deploy --background
{
  "ok": true,
  "operation_id": "op_abc123",
  "status": "accepted",
  "poll_url": "/operations/op_abc123",
  "poll_interval_ms": 5000
}

# Poll for status
$ mycli task status op_abc123
{
  "operation_id": "op_abc123",
  "status": "running",
  "progress": {
    "phase": "deploying",
    "percent": 65,
    "message": "Deploying to region us-east-1"
  },
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:35:00Z"
}

# Wait (blocking with timeout)
$ mycli task wait op_abc123 --timeout 5m
{
  "operation_id": "op_abc123",
  "status": "succeeded",
  "result": {
    "deployment_id": "dep_xyz789",
    "url": "https://app.example.com"
  },
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:34:00Z"
}

# Cancel
$ mycli task cancel op_abc123
{
  "operation_id": "op_abc123",
  "status": "cancelling",
  "message": "Cancellation requested"
}
```

### Streaming Progress

```bash
$ mycli deploy --stream
{"type": "started", "operation_id": "op_abc123", "timestamp": "2024-01-15T10:30:00Z"}
{"type": "progress", "phase": "building", "percent": 10, "message": "Installing dependencies"}
{"type": "progress", "phase": "building", "percent": 25, "message": "Compiling application"}
{"type": "progress", "phase": "building", "percent": 50, "message": "Running tests"}
{"type": "progress", "phase": "deploying", "percent": 75, "message": "Uploading artifacts"}
{"type": "progress", "phase": "deploying", "percent": 90, "message": "Starting containers"}
{"type": "completed", "status": "succeeded", "result": {"url": "https://app.example.com"}}
```

### Implementation

**Go:**

```go
type Operation struct {
    ID        string         `json:"operation_id"`
    Status    string         `json:"status"` // accepted, running, succeeded, failed, cancelled
    Progress  *Progress      `json:"progress,omitempty"`
    Result    interface{}    `json:"result,omitempty"`
    Error     *ErrorInfo     `json:"error,omitempty"`
    StartedAt time.Time      `json:"started_at"`
    UpdatedAt time.Time      `json:"updated_at"`
}

type Progress struct {
    Phase   string `json:"phase"`
    Percent int    `json:"percent"`
    Message string `json:"message"`
}

// CLI commands
func cmdTaskStatus(operationID string) error {
    op, err := api.GetOperation(operationID)
    if err != nil {
        return err
    }
    return outputJSON(op)
}

func cmdTaskWait(operationID string, timeout time.Duration) error {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    ticker := time.NewTicker(2 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return fmt.Errorf("timeout waiting for operation")
        case <-ticker.C:
            op, err := api.GetOperation(operationID)
            if err != nil {
                return err
            }
            
            switch op.Status {
            case "succeeded":
                return outputJSON(op)
            case "failed":
                return outputJSON(op)
            case "cancelled":
                return outputJSON(op)
            }
            // Continue polling
        }
    }
}

func cmdDeployStream() error {
    ctx := context.Background()
    
    // Start operation
    op, err := api.StartDeploy(ctx)
    if err != nil {
        return err
    }
    
    // Stream progress
    stream, err := api.StreamOperation(ctx, op.ID)
    if err != nil {
        return err
    }
    
    for event := range stream {
        outputJSON(event)
        if event.Type == "completed" || event.Type == "failed" {
            break
        }
    }
    
    return nil
}
```

---

## 8. Timeout and Cancellation

### Timeout Configuration

```bash
# Overall timeout + graceful shutdown period
mycli long-operation \
  --timeout 5m \
  --graceful-shutdown-timeout 30s
```

### Signal Handling

| Signal | Behavior |
|--------|----------|
| `SIGINT` (Ctrl+C) | Graceful shutdown, attempt cleanup |
| `SIGTERM` | Graceful shutdown, shorter deadline |
| `SIGKILL` | Immediate termination (not catchable) |

### Implementation

**Go:**

```go
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    
    // Handle signals
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    
    go func() {
        sig := <-sigCh
        log.Printf("Received signal: %v", sig)
        
        // Start graceful shutdown
        cancel()
        
        // Force exit after grace period
        var gracePeriod time.Duration
        if sig == syscall.SIGTERM {
            gracePeriod = 10 * time.Second
        } else {
            gracePeriod = 30 * time.Second
        }
        
        time.Sleep(gracePeriod)
        log.Println("Grace period expired, forcing exit")
        os.Exit(1)
    }()
    
    // Run main operation
    if err := run(ctx); err != nil {
        if ctx.Err() == context.Canceled {
            outputJSON(map[string]interface{}{
                "ok":     true,
                "status": "cancelled",
                "cleanup_status": "completed",
            })
            os.Exit(0)
        }
        log.Fatal(err)
    }
}

func run(ctx context.Context) error {
    // Long-running operation that respects context cancellation
    for i := 0; i < 100; i++ {
        select {
        case <-ctx.Done():
            // Cleanup
            cleanup()
            return ctx.Err()
        default:
            // Continue work
            doWork(i)
        }
    }
    return nil
}
```

**Python:**

```python
import signal
import sys
from contextlib import contextmanager

class GracefulShutdown:
    def __init__(self, grace_period: float = 30.0):
        self.grace_period = grace_period
        self.shutting_down = False
        
    def __enter__(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        return self
    
    def __exit__(self, *args):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
    
    def _handle_signal(self, signum, frame):
        if self.shutting_down:
            # Second signal - force exit
            sys.exit(1)
        
        self.shutting_down = True
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        
        # Schedule force exit
        signal.alarm(int(self.grace_period))
    
    def check(self):
        """Check if shutdown requested. Call periodically in long operations."""
        if self.shutting_down:
            raise KeyboardInterrupt("Shutdown requested")

# Usage
with GracefulShutdown() as shutdown:
    for i in range(100):
        shutdown.check()  # Raises if shutdown requested
        do_work(i)
```

### Cancellation Response

```json
{
  "ok": true,
  "status": "cancelled",
  "completed_before_cancel": 45,
  "total_planned": 100,
  "cleanup_status": "completed",
  "cleanup_details": {
    "rolled_back": ["step-3", "step-2", "step-1"],
    "preserved": ["checkpoint-1"]
  }
}
```

---

## Summary: Agent-Friendly Execution Patterns

| Pattern | Key Benefit | Implementation Priority |
|---------|-------------|------------------------|
| **Idempotency** | Safe retries | High |
| **Retry with backoff** | Handles transient failures | High |
| **Dry-run** | Preview before commit | High |
| **Non-interactive** | CI/CD compatibility | High |
| **Batch with partial failure** | Efficient bulk operations | Medium |
| **Long-running tasks** | Async operation support | Medium |
| **Transaction/rollback** | Atomic multi-step ops | Medium |
| **Timeout/cancellation** | Graceful failure handling | Medium |

All patterns should:
1. Return structured JSON output
2. Use clear exit codes
3. Provide sufficient context for automated recovery
4. Never hang waiting for human input

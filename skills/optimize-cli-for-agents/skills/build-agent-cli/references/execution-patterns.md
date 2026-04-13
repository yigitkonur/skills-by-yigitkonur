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

### CLI Timeout Flags

```bash
# Standard timeout patterns
mycli long-operation \
  --timeout 5m \                         # Overall operation timeout
  --connect-timeout 10s \                # Connection establishment timeout
  --read-timeout 30s \                   # Per-request read timeout
  --graceful-shutdown-timeout 30s        # Time allowed for cleanup

# Timeout with behavior control
mycli deploy \
  --timeout 10m \
  --timeout-exit-code 124 \              # Custom exit code on timeout (like GNU timeout)
  --on-timeout cleanup                   # Action: cleanup | abort | preserve
```

### Timeout Flag Standards

| Flag | Description | Default |
|------|-------------|---------|
| `--timeout <duration>` | Overall operation timeout | None (wait forever) |
| `--connect-timeout <duration>` | Connection establishment | 10s |
| `--read-timeout <duration>` | Read/response timeout | 30s |
| `--write-timeout <duration>` | Write/send timeout | 30s |
| `--idle-timeout <duration>` | Idle connection timeout | 60s |
| `--graceful-shutdown-timeout <duration>` | Cleanup time on cancel | 30s |
| `--on-timeout <action>` | Timeout behavior | abort |

### Timeout Output

```json
{
  "ok": false,
  "error": {
    "class": "timeout",
    "code": "OPERATION_TIMEOUT",
    "message": "Operation timed out after 5m",
    "timeout_type": "overall",
    "elapsed": "5m0.023s",
    "timeout_configured": "5m"
  },
  "partial_result": {
    "completed_steps": 45,
    "total_steps": 100,
    "last_checkpoint": "step-45"
  },
  "recovery": {
    "resumable": true,
    "resume_command": "mycli long-operation --resume-from step-45"
  }
}
```

### Timeout Configuration

### Signal Handling

| Signal | Behavior | Exit Code |
|--------|----------|-----------|
| `SIGINT` (Ctrl+C) | Graceful shutdown, attempt cleanup | 130 |
| `SIGTERM` | Graceful shutdown, shorter deadline | 143 |
| `SIGKILL` | Immediate termination (not catchable) | 137 |
| `SIGHUP` | Reload config, continue running | N/A |
| `SIGUSR1` | Dump status/progress | N/A |

### Context Cancellation Patterns

**Hierarchical Timeout Structure:**

```
Operation (5m overall)
├── Phase 1: Prepare (30s)
│   ├── Sub-operation A (10s)
│   └── Sub-operation B (10s)
├── Phase 2: Execute (4m)
│   └── Per-item timeout (5s each)
└── Phase 3: Cleanup (30s)
```

### Implementation

**Go - Comprehensive Timeout + Signal Handling:**

```go
func main() {
    // Parse timeout flags
    timeout := parseFlags().timeout // e.g., 5 * time.Minute
    gracePeriod := parseFlags().gracefulShutdownTimeout // e.g., 30 * time.Second
    
    // Create timeout context
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
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

## 9. Pagination Patterns

### Cursor-Based Pagination

Cursor-based pagination is preferred for large datasets as it's stable under concurrent modifications.

```bash
# Basic cursor pagination
mycli list items --per-page 50

# Continue with cursor from previous response
mycli list items --per-page 50 --cursor "eyJpZCI6MTAwfQ=="

# Fetch all pages automatically
mycli list items --all --per-page 100

# Specific page (offset-based fallback)
mycli list items --page 3 --per-page 50
```

### Pagination Flag Standards

| Flag | Description | Default |
|------|-------------|---------|
| `--per-page <n>` | Items per page | 20-100 |
| `--page <n>` | Page number (1-indexed, offset-based) | 1 |
| `--cursor <token>` | Cursor for next page | None |
| `--all` | Fetch all pages automatically | false |
| `--max-pages <n>` | Maximum pages when using `--all` | 100 |
| `--direction <dir>` | Pagination direction: `forward` \| `backward` | forward |
| `--sort-by <field>` | Sort field | created_at |
| `--sort-order <order>` | Sort order: `asc` \| `desc` | desc |

### Paginated Response Structure

```json
{
  "ok": true,
  "data": [
    {"id": "item-51", "name": "Item 51"},
    {"id": "item-52", "name": "Item 52"}
  ],
  "pagination": {
    "total_count": 1500,
    "page_size": 50,
    "has_next": true,
    "has_previous": true,
    "next_cursor": "eyJpZCI6MTAwLCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDozMDowMFoifQ==",
    "previous_cursor": "eyJpZCI6NTAsImNyZWF0ZWRfYXQiOiIyMDI0LTAxLTE1VDA5OjMwOjAwWiJ9",
    "current_page": 2,
    "total_pages": 30
  },
  "next_command": "mycli list items --per-page 50 --cursor 'eyJpZCI6MTAwLCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDozMDowMFoifQ=='"
}
```

### Implementation

**Go - Cursor Pagination:**

```go
type PaginationOptions struct {
    PerPage   int    `json:"per_page"`
    Cursor    string `json:"cursor,omitempty"`
    Page      int    `json:"page,omitempty"`
    All       bool   `json:"all,omitempty"`
    MaxPages  int    `json:"max_pages,omitempty"`
    SortBy    string `json:"sort_by,omitempty"`
    SortOrder string `json:"sort_order,omitempty"`
}

type PageInfo struct {
    TotalCount     int    `json:"total_count"`
    PageSize       int    `json:"page_size"`
    HasNext        bool   `json:"has_next"`
    HasPrevious    bool   `json:"has_previous"`
    NextCursor     string `json:"next_cursor,omitempty"`
    PreviousCursor string `json:"previous_cursor,omitempty"`
    CurrentPage    int    `json:"current_page,omitempty"`
    TotalPages     int    `json:"total_pages,omitempty"`
}

type PaginatedResponse[T any] struct {
    OK         bool     `json:"ok"`
    Data       []T      `json:"data"`
    Pagination PageInfo `json:"pagination"`
}

func (s *Server) ListItems(ctx context.Context, opts PaginationOptions) (*PaginatedResponse[Item], error) {
    // Decode cursor if provided
    var startAfter *Item
    if opts.Cursor != "" {
        decoded, err := decodeCursor(opts.Cursor)
        if err != nil {
            return nil, fmt.Errorf("invalid cursor: %w", err)
        }
        startAfter = decoded
    }
    
    // Fetch one extra to determine has_next
    limit := opts.PerPage + 1
    items, err := s.db.QueryItems(ctx, startAfter, limit, opts.SortBy, opts.SortOrder)
    if err != nil {
        return nil, err
    }
    
    hasNext := len(items) > opts.PerPage
    if hasNext {
        items = items[:opts.PerPage]
    }
    
    var nextCursor string
    if hasNext && len(items) > 0 {
        nextCursor = encodeCursor(items[len(items)-1])
    }
    
    return &PaginatedResponse[Item]{
        OK:   true,
        Data: items,
        Pagination: PageInfo{
            PageSize:   opts.PerPage,
            HasNext:    hasNext,
            NextCursor: nextCursor,
        },
    }, nil
}

// Cursor encoding/decoding
func encodeCursor(item *Item) string {
    data, _ := json.Marshal(map[string]interface{}{
        "id":         item.ID,
        "created_at": item.CreatedAt,
    })
    return base64.URLEncoding.EncodeToString(data)
}

func decodeCursor(cursor string) (*Item, error) {
    data, err := base64.URLEncoding.DecodeString(cursor)
    if err != nil {
        return nil, err
    }
    var item Item
    if err := json.Unmarshal(data, &item); err != nil {
        return nil, err
    }
    return &item, nil
}
```

**Python - Fetch All Pages:**

```python
import click
from typing import Iterator, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Page(Generic[T]):
    data: list[T]
    next_cursor: str | None
    total_count: int | None

def fetch_all_pages(
    fetch_fn: callable,
    per_page: int = 100,
    max_pages: int = 100
) -> Iterator[T]:
    """Generator that yields items from all pages."""
    cursor = None
    pages_fetched = 0
    
    while pages_fetched < max_pages:
        page = fetch_fn(per_page=per_page, cursor=cursor)
        yield from page.data
        
        pages_fetched += 1
        
        if not page.next_cursor:
            break
        cursor = page.next_cursor

@click.command()
@click.option('--per-page', default=50, help='Items per page')
@click.option('--cursor', help='Pagination cursor')
@click.option('--page', type=int, help='Page number (offset-based)')
@click.option('--all', 'fetch_all', is_flag=True, help='Fetch all pages')
@click.option('--max-pages', default=100, help='Max pages when using --all')
@click.option('--sort-by', default='created_at', help='Sort field')
@click.option('--sort-order', type=click.Choice(['asc', 'desc']), default='desc')
def list_items(per_page, cursor, page, fetch_all, max_pages, sort_by, sort_order):
    if fetch_all:
        items = list(fetch_all_pages(
            lambda **kw: api.list_items(**kw, sort_by=sort_by, sort_order=sort_order),
            per_page=per_page,
            max_pages=max_pages
        ))
        output_json({
            "ok": True,
            "data": items,
            "pagination": {"total_fetched": len(items)}
        })
    else:
        result = api.list_items(
            per_page=per_page,
            cursor=cursor,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        output_json(result)
```

**Node.js - Async Iterator:**

```typescript
interface PaginationOptions {
  perPage?: number;
  cursor?: string;
  page?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface PageInfo {
  totalCount?: number;
  pageSize: number;
  hasNext: boolean;
  nextCursor?: string;
}

interface Page<T> {
  data: T[];
  pagination: PageInfo;
}

async function* fetchAllPages<T>(
  fetchFn: (opts: PaginationOptions) => Promise<Page<T>>,
  options: { perPage?: number; maxPages?: number } = {}
): AsyncGenerator<T> {
  const perPage = options.perPage ?? 100;
  const maxPages = options.maxPages ?? 100;
  let cursor: string | undefined;
  let pagesFetched = 0;

  while (pagesFetched < maxPages) {
    const page = await fetchFn({ perPage, cursor });
    
    for (const item of page.data) {
      yield item;
    }
    
    pagesFetched++;
    
    if (!page.pagination.hasNext) break;
    cursor = page.pagination.nextCursor;
  }
}

// CLI command
program
  .command('list')
  .option('--per-page <n>', 'Items per page', '50')
  .option('--cursor <token>', 'Pagination cursor')
  .option('--page <n>', 'Page number')
  .option('--all', 'Fetch all pages')
  .option('--max-pages <n>', 'Max pages for --all', '100')
  .option('--sort-by <field>', 'Sort field', 'created_at')
  .option('--sort-order <order>', 'Sort order', 'desc')
  .action(async (options) => {
    if (options.all) {
      const items: Item[] = [];
      for await (const item of fetchAllPages(
        (opts) => api.listItems(opts),
        { perPage: parseInt(options.perPage), maxPages: parseInt(options.maxPages) }
      )) {
        items.push(item);
      }
      console.log(JSON.stringify({ ok: true, data: items }));
    } else {
      const result = await api.listItems({
        perPage: parseInt(options.perPage),
        cursor: options.cursor,
        page: options.page ? parseInt(options.page) : undefined,
        sortBy: options.sortBy,
        sortOrder: options.sortOrder,
      });
      console.log(JSON.stringify(result));
    }
  });
```

---

## 10. Batch Operation Limits

### Batch Size and Concurrency Controls

```bash
# Control batch execution
mycli bulk-create \
  --input items.json \
  --batch-size 100 \                   # Items per batch
  --max-concurrent 5 \                 # Parallel batch workers
  --delay-between-batches 1s \         # Rate limiting between batches
  --max-items 10000 \                  # Total item limit
  --continue-on-error \                # Don't stop on failures
  --fail-threshold 0.1                 # Stop if >10% failures
```

### Batch Flag Standards

| Flag | Description | Default |
|------|-------------|---------|
| `--batch-size <n>` | Items per batch | 100 |
| `--max-concurrent <n>` | Parallel workers | 5 |
| `--delay-between-batches <duration>` | Pause between batches | 0 |
| `--max-items <n>` | Maximum items to process | unlimited |
| `--continue-on-error` | Continue on item failures | false |
| `--stop-on-error` | Stop on first failure | false (default: continue) |
| `--fail-threshold <ratio>` | Stop if failure ratio exceeds | 1.0 |
| `--dry-run` | Preview without executing | false |
| `--retry-failed <n>` | Retry failed items n times | 0 |

### Partial Failure Response

```json
{
  "ok": false,
  "status": "partial_failure",
  "exit_code": 3,
  "summary": {
    "total_input": 1000,
    "processed": 1000,
    "succeeded": 950,
    "failed": 50,
    "skipped": 0,
    "failure_rate": 0.05
  },
  "timing": {
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:35:30Z",
    "elapsed": "5m30s",
    "items_per_second": 3.03
  },
  "batches": {
    "total": 10,
    "completed": 10,
    "batch_size": 100,
    "max_concurrent": 5
  },
  "succeeded": [
    {"id": "item-1", "result": {"resource_id": "res_abc123"}}
  ],
  "failed": [
    {
      "id": "item-51",
      "batch_index": 0,
      "item_index": 50,
      "attempts": 3,
      "error": {
        "class": "validation",
        "code": "INVALID_INPUT",
        "message": "Field 'email' is invalid"
      }
    }
  ],
  "recovery": {
    "failed_items_file": "./failed-items-2024-01-15T10-35-30.json",
    "retry_command": "mycli bulk-create --input ./failed-items-2024-01-15T10-35-30.json"
  }
}
```

### Implementation

**Go - Bounded Concurrency with Semaphore:**

```go
type BatchOptions struct {
    BatchSize            int           `json:"batch_size"`
    MaxConcurrent        int           `json:"max_concurrent"`
    DelayBetweenBatches  time.Duration `json:"delay_between_batches"`
    MaxItems             int           `json:"max_items"`
    ContinueOnError      bool          `json:"continue_on_error"`
    FailThreshold        float64       `json:"fail_threshold"`
    RetryFailed          int           `json:"retry_failed"`
}

type BatchResult struct {
    OK        bool                `json:"ok"`
    Status    string              `json:"status"`
    Summary   BatchSummary        `json:"summary"`
    Timing    BatchTiming         `json:"timing"`
    Succeeded []ItemResult        `json:"succeeded,omitempty"`
    Failed    []ItemFailure       `json:"failed,omitempty"`
    Recovery  *RecoveryInfo       `json:"recovery,omitempty"`
}

func ProcessBatch(ctx context.Context, items []Item, opts BatchOptions) (*BatchResult, error) {
    if opts.MaxItems > 0 && len(items) > opts.MaxItems {
        items = items[:opts.MaxItems]
    }
    
    result := &BatchResult{
        Summary: BatchSummary{TotalInput: len(items)},
    }
    startTime := time.Now()
    
    // Create semaphore for concurrency control
    sem := make(chan struct{}, opts.MaxConcurrent)
    var mu sync.Mutex
    var wg sync.WaitGroup
    
    // Split into batches
    batches := chunkItems(items, opts.BatchSize)
    
    for batchIdx, batch := range batches {
        select {
        case <-ctx.Done():
            result.Status = "cancelled"
            return result, ctx.Err()
        default:
        }
        
        // Delay between batches
        if batchIdx > 0 && opts.DelayBetweenBatches > 0 {
            time.Sleep(opts.DelayBetweenBatches)
        }
        
        for itemIdx, item := range batch {
            wg.Add(1)
            sem <- struct{}{} // Acquire
            
            go func(item Item, bIdx, iIdx int) {
                defer wg.Done()
                defer func() { <-sem }() // Release
                
                // Process with retry
                var lastErr error
                for attempt := 0; attempt <= opts.RetryFailed; attempt++ {
                    if err := processItem(ctx, item); err != nil {
                        lastErr = err
                        if !isRetryable(err) {
                            break
                        }
                        time.Sleep(backoff(attempt))
                        continue
                    }
                    
                    mu.Lock()
                    result.Succeeded = append(result.Succeeded, ItemResult{ID: item.ID})
                    result.Summary.Succeeded++
                    mu.Unlock()
                    return
                }
                
                mu.Lock()
                result.Failed = append(result.Failed, ItemFailure{
                    ID:         item.ID,
                    BatchIndex: bIdx,
                    ItemIndex:  iIdx,
                    Error:      toErrorInfo(lastErr),
                })
                result.Summary.Failed++
                
                // Check fail threshold
                failRate := float64(result.Summary.Failed) / float64(result.Summary.Processed())
                mu.Unlock()
                
                if !opts.ContinueOnError || failRate > opts.FailThreshold {
                    // Signal to stop (in real impl, use context cancellation)
                }
            }(item, batchIdx, itemIdx)
        }
    }
    
    wg.Wait()
    
    result.Timing.Elapsed = time.Since(startTime)
    result.OK = result.Summary.Failed == 0
    result.Status = determineStatus(result.Summary)
    
    // Generate recovery info if failures
    if len(result.Failed) > 0 {
        result.Recovery = generateRecoveryInfo(result.Failed)
    }
    
    return result, nil
}
```

**Python - Async Batch Processing:**

```python
import asyncio
from dataclasses import dataclass
from typing import Callable, TypeVar
import aiofiles

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchOptions:
    batch_size: int = 100
    max_concurrent: int = 5
    delay_between_batches: float = 0.0
    max_items: int | None = None
    continue_on_error: bool = True
    fail_threshold: float = 1.0
    retry_failed: int = 0

async def process_batch(
    items: list[T],
    processor: Callable[[T], R],
    options: BatchOptions
) -> dict:
    if options.max_items:
        items = items[:options.max_items]
    
    semaphore = asyncio.Semaphore(options.max_concurrent)
    succeeded = []
    failed = []
    
    async def process_with_semaphore(item: T, batch_idx: int, item_idx: int):
        async with semaphore:
            for attempt in range(options.retry_failed + 1):
                try:
                    result = await processor(item)
                    succeeded.append({"id": item.id, "result": result})
                    return
                except Exception as e:
                    if attempt == options.retry_failed or not is_retryable(e):
                        failed.append({
                            "id": item.id,
                            "batch_index": batch_idx,
                            "item_index": item_idx,
                            "error": error_to_dict(e)
                        })
                        return
                    await asyncio.sleep(backoff(attempt))
    
    # Process in batches
    batches = [items[i:i+options.batch_size] 
               for i in range(0, len(items), options.batch_size)]
    
    for batch_idx, batch in enumerate(batches):
        if batch_idx > 0 and options.delay_between_batches > 0:
            await asyncio.sleep(options.delay_between_batches)
        
        # Check fail threshold
        if len(succeeded) + len(failed) > 0:
            fail_rate = len(failed) / (len(succeeded) + len(failed))
            if fail_rate > options.fail_threshold:
                break
        
        tasks = [
            process_with_semaphore(item, batch_idx, item_idx)
            for item_idx, item in enumerate(batch)
        ]
        await asyncio.gather(*tasks)
    
    return {
        "ok": len(failed) == 0,
        "status": "success" if len(failed) == 0 else "partial_failure",
        "summary": {
            "total_input": len(items),
            "succeeded": len(succeeded),
            "failed": len(failed)
        },
        "succeeded": succeeded,
        "failed": failed
    }

# CLI
@click.command()
@click.option('--input', 'input_file', required=True)
@click.option('--batch-size', default=100)
@click.option('--max-concurrent', default=5)
@click.option('--delay-between-batches', default='0s')
@click.option('--max-items', type=int)
@click.option('--continue-on-error', is_flag=True)
@click.option('--fail-threshold', default=1.0)
@click.option('--retry-failed', default=0)
def bulk_create(input_file, **kwargs):
    items = load_items(input_file)
    options = BatchOptions(**kwargs)
    
    result = asyncio.run(process_batch(items, create_item, options))
    output_json(result)
```

---

## 11. Rate Limiting (Client-Side)

### Rate Limit Flags

```bash
# Client-side rate limiting
mycli sync \
  --rate-limit 100/minute \            # Request rate limit
  --retry-on-rate-limit \              # Auto-retry on 429
  --max-retries 5 \                    # Maximum retry attempts
  --backoff-initial 1s \               # Initial backoff delay
  --backoff-max 60s \                  # Maximum backoff delay
  --backoff-multiplier 2.0 \           # Exponential multiplier
  --respect-retry-after                # Honor Retry-After header
```

### Rate Limit Flag Standards

| Flag | Description | Default |
|------|-------------|---------|
| `--rate-limit <rate>` | Request rate (e.g., `100/minute`) | unlimited |
| `--retry-on-rate-limit` | Auto-retry on 429 | true |
| `--max-retries <n>` | Maximum retry attempts | 5 |
| `--backoff-initial <duration>` | Initial backoff delay | 1s |
| `--backoff-max <duration>` | Maximum backoff delay | 60s |
| `--backoff-multiplier <n>` | Exponential multiplier | 2.0 |
| `--backoff-jitter <ratio>` | Random jitter (0-1) | 0.1 |
| `--respect-retry-after` | Honor Retry-After header | true |
| `--circuit-breaker-threshold <n>` | Failures before circuit opens | 5 |
| `--circuit-breaker-timeout <duration>` | Time before retry after open | 30s |

### Rate Limit Response

```json
{
  "ok": false,
  "error": {
    "class": "rate_limit",
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 45,
    "retry_after_unit": "seconds",
    "limit": {
      "requests_per_minute": 100,
      "remaining": 0,
      "reset_at": "2024-01-15T10:31:00Z"
    }
  },
  "retry": {
    "should_retry": true,
    "retry_after": "45s",
    "retry_command": "mycli sync --continue"
  }
}
```

### Implementation

**Go - Comprehensive Rate Limiter with Circuit Breaker:**

```go
type RateLimitOptions struct {
    RateLimit             string        `json:"rate_limit"` // e.g., "100/minute"
    RetryOnRateLimit      bool          `json:"retry_on_rate_limit"`
    MaxRetries            int           `json:"max_retries"`
    BackoffInitial        time.Duration `json:"backoff_initial"`
    BackoffMax            time.Duration `json:"backoff_max"`
    BackoffMultiplier     float64       `json:"backoff_multiplier"`
    BackoffJitter         float64       `json:"backoff_jitter"`
    RespectRetryAfter     bool          `json:"respect_retry_after"`
    CircuitBreakerThreshold int         `json:"circuit_breaker_threshold"`
    CircuitBreakerTimeout time.Duration `json:"circuit_breaker_timeout"`
}

type RateLimiter struct {
    limiter       *rate.Limiter
    opts          RateLimitOptions
    failures      int
    circuitOpen   bool
    circuitOpenAt time.Time
    mu            sync.Mutex
}

func NewRateLimiter(opts RateLimitOptions) (*RateLimiter, error) {
    limit, err := parseRateLimit(opts.RateLimit) // e.g., "100/minute" -> rate.Limit
    if err != nil {
        return nil, err
    }
    
    return &RateLimiter{
        limiter: rate.NewLimiter(limit, int(limit)), // burst = limit
        opts:    opts,
    }, nil
}

func (r *RateLimiter) Do(ctx context.Context, fn func() (*http.Response, error)) (*http.Response, error) {
    // Check circuit breaker
    r.mu.Lock()
    if r.circuitOpen {
        if time.Since(r.circuitOpenAt) > r.opts.CircuitBreakerTimeout {
            r.circuitOpen = false
            r.failures = 0
        } else {
            r.mu.Unlock()
            return nil, &CircuitOpenError{
                OpenAt:   r.circuitOpenAt,
                WaitFor:  r.opts.CircuitBreakerTimeout - time.Since(r.circuitOpenAt),
            }
        }
    }
    r.mu.Unlock()
    
    // Wait for rate limit
    if err := r.limiter.Wait(ctx); err != nil {
        return nil, err
    }
    
    var lastErr error
    backoff := r.opts.BackoffInitial
    
    for attempt := 0; attempt <= r.opts.MaxRetries; attempt++ {
        resp, err := fn()
        if err != nil {
            lastErr = err
            r.recordFailure()
            continue
        }
        
        // Handle rate limit response
        if resp.StatusCode == http.StatusTooManyRequests {
            r.recordFailure()
            
            if !r.opts.RetryOnRateLimit {
                return resp, nil
            }
            
            // Determine wait time
            waitTime := backoff
            if r.opts.RespectRetryAfter {
                if retryAfter := resp.Header.Get("Retry-After"); retryAfter != "" {
                    if seconds, err := strconv.Atoi(retryAfter); err == nil {
                        waitTime = time.Duration(seconds) * time.Second
                    } else if t, err := http.ParseTime(retryAfter); err == nil {
                        waitTime = time.Until(t)
                    }
                }
            }
            
            // Add jitter
            if r.opts.BackoffJitter > 0 {
                jitter := time.Duration(float64(waitTime) * r.opts.BackoffJitter * (rand.Float64()*2 - 1))
                waitTime += jitter
            }
            
            select {
            case <-ctx.Done():
                return nil, ctx.Err()
            case <-time.After(waitTime):
            }
            
            // Exponential backoff for next attempt
            backoff = time.Duration(float64(backoff) * r.opts.BackoffMultiplier)
            if backoff > r.opts.BackoffMax {
                backoff = r.opts.BackoffMax
            }
            
            lastErr = &RateLimitError{RetryAfter: waitTime}
            continue
        }
        
        // Success - reset failures
        r.recordSuccess()
        return resp, nil
    }
    
    return nil, fmt.Errorf("max retries exceeded: %w", lastErr)
}

func (r *RateLimiter) recordFailure() {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    r.failures++
    if r.failures >= r.opts.CircuitBreakerThreshold {
        r.circuitOpen = true
        r.circuitOpenAt = time.Now()
    }
}

func (r *RateLimiter) recordSuccess() {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.failures = 0
    r.circuitOpen = false
}
```

**Python - Async Rate Limiter:**

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Callable, TypeVar
import random

T = TypeVar('T')

@dataclass
class RateLimitOptions:
    rate_limit: str = "100/minute"  # e.g., "100/minute", "10/second"
    retry_on_rate_limit: bool = True
    max_retries: int = 5
    backoff_initial: float = 1.0
    backoff_max: float = 60.0
    backoff_multiplier: float = 2.0
    backoff_jitter: float = 0.1
    respect_retry_after: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 30.0

class RateLimiter:
    def __init__(self, options: RateLimitOptions):
        self.options = options
        self.tokens, self.interval = self._parse_rate_limit(options.rate_limit)
        self.available_tokens = self.tokens
        self.last_refill = time.monotonic()
        self.failures = 0
        self.circuit_open = False
        self.circuit_open_at = 0.0
        self._lock = asyncio.Lock()
    
    def _parse_rate_limit(self, rate: str) -> tuple[int, float]:
        count, period = rate.split('/')
        periods = {'second': 1, 'minute': 60, 'hour': 3600}
        return int(count), periods.get(period, 60)
    
    async def _acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.available_tokens = min(
                self.tokens,
                self.available_tokens + (elapsed / self.interval) * self.tokens
            )
            self.last_refill = now
            
            if self.available_tokens < 1:
                wait_time = (1 - self.available_tokens) * (self.interval / self.tokens)
                await asyncio.sleep(wait_time)
                self.available_tokens = 1
            
            self.available_tokens -= 1
    
    async def execute(self, fn: Callable[[], T]) -> T:
        # Check circuit breaker
        if self.circuit_open:
            if time.monotonic() - self.circuit_open_at > self.options.circuit_breaker_timeout:
                self.circuit_open = False
                self.failures = 0
            else:
                raise CircuitOpenError(
                    f"Circuit open, retry after {self.options.circuit_breaker_timeout - (time.monotonic() - self.circuit_open_at):.1f}s"
                )
        
        await self._acquire()
        
        backoff = self.options.backoff_initial
        last_error = None
        
        for attempt in range(self.options.max_retries + 1):
            try:
                result = await fn()
                self.failures = 0
                return result
            except RateLimitError as e:
                self.failures += 1
                if self.failures >= self.options.circuit_breaker_threshold:
                    self.circuit_open = True
                    self.circuit_open_at = time.monotonic()
                    raise CircuitOpenError("Too many failures, circuit opened")
                
                if not self.options.retry_on_rate_limit:
                    raise
                
                # Determine wait time
                wait_time = e.retry_after if self.options.respect_retry_after and e.retry_after else backoff
                
                # Add jitter
                if self.options.backoff_jitter > 0:
                    jitter = wait_time * self.options.backoff_jitter * (random.random() * 2 - 1)
                    wait_time += jitter
                
                await asyncio.sleep(wait_time)
                
                backoff = min(backoff * self.options.backoff_multiplier, self.options.backoff_max)
                last_error = e
            except Exception as e:
                self.failures += 1
                last_error = e
                if self.failures >= self.options.circuit_breaker_threshold:
                    self.circuit_open = True
                    self.circuit_open_at = time.monotonic()
                raise
        
        raise MaxRetriesExceeded(f"Max retries exceeded: {last_error}")

# CLI usage
@click.command()
@click.option('--rate-limit', default='100/minute')
@click.option('--retry-on-rate-limit', is_flag=True, default=True)
@click.option('--max-retries', default=5)
@click.option('--backoff-initial', default='1s')
@click.option('--backoff-max', default='60s')
@click.option('--backoff-multiplier', default=2.0)
@click.option('--respect-retry-after', is_flag=True, default=True)
@click.option('--circuit-breaker-threshold', default=5)
@click.option('--circuit-breaker-timeout', default='30s')
def sync(rate_limit, **kwargs):
    options = RateLimitOptions(rate_limit=rate_limit, **kwargs)
    limiter = RateLimiter(options)
    
    async def run():
        return await limiter.execute(api.sync)
    
    result = asyncio.run(run())
    output_json(result)
```

**Node.js - Token Bucket with Retry:**

```typescript
interface RateLimitOptions {
  rateLimit: string;
  retryOnRateLimit: boolean;
  maxRetries: number;
  backoffInitial: number;
  backoffMax: number;
  backoffMultiplier: number;
  backoffJitter: number;
  respectRetryAfter: boolean;
  circuitBreakerThreshold: number;
  circuitBreakerTimeout: number;
}

class RateLimiter {
  private tokens: number;
  private maxTokens: number;
  private refillInterval: number;
  private lastRefill: number;
  private failures = 0;
  private circuitOpen = false;
  private circuitOpenAt = 0;

  constructor(private options: RateLimitOptions) {
    const [count, period] = this.parseRateLimit(options.rateLimit);
    this.maxTokens = count;
    this.tokens = count;
    this.refillInterval = period;
    this.lastRefill = Date.now();
  }

  private parseRateLimit(rate: string): [number, number] {
    const [count, period] = rate.split('/');
    const periods: Record<string, number> = {
      second: 1000,
      minute: 60000,
      hour: 3600000,
    };
    return [parseInt(count), periods[period] ?? 60000];
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    const refillAmount = (elapsed / this.refillInterval) * this.maxTokens;
    this.tokens = Math.min(this.maxTokens, this.tokens + refillAmount);
    this.lastRefill = now;
  }

  private async acquire(): Promise<void> {
    this.refill();
    if (this.tokens < 1) {
      const waitTime = ((1 - this.tokens) / this.maxTokens) * this.refillInterval;
      await sleep(waitTime);
      this.tokens = 1;
    }
    this.tokens -= 1;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Check circuit breaker
    if (this.circuitOpen) {
      if (Date.now() - this.circuitOpenAt > this.options.circuitBreakerTimeout) {
        this.circuitOpen = false;
        this.failures = 0;
      } else {
        throw new CircuitOpenError(
          `Circuit open, retry after ${this.options.circuitBreakerTimeout - (Date.now() - this.circuitOpenAt)}ms`
        );
      }
    }

    await this.acquire();

    let backoff = this.options.backoffInitial;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.options.maxRetries; attempt++) {
      try {
        const result = await fn();
        this.failures = 0;
        return result;
      } catch (error) {
        this.failures++;

        if (this.failures >= this.options.circuitBreakerThreshold) {
          this.circuitOpen = true;
          this.circuitOpenAt = Date.now();
          throw new CircuitOpenError('Too many failures');
        }

        if (error instanceof RateLimitError) {
          if (!this.options.retryOnRateLimit) throw error;

          let waitTime = backoff;
          if (this.options.respectRetryAfter && error.retryAfter) {
            waitTime = error.retryAfter * 1000;
          }

          // Add jitter
          if (this.options.backoffJitter > 0) {
            const jitter = waitTime * this.options.backoffJitter * (Math.random() * 2 - 1);
            waitTime += jitter;
          }

          await sleep(waitTime);
          backoff = Math.min(backoff * this.options.backoffMultiplier, this.options.backoffMax);
          lastError = error;
          continue;
        }

        throw error;
      }
    }

    throw new MaxRetriesExceeded(`Max retries exceeded: ${lastError?.message}`);
  }
}

// CLI
program
  .command('sync')
  .option('--rate-limit <rate>', 'Rate limit', '100/minute')
  .option('--retry-on-rate-limit', 'Auto retry on 429', true)
  .option('--max-retries <n>', 'Max retries', '5')
  .option('--backoff-initial <ms>', 'Initial backoff', '1000')
  .option('--backoff-max <ms>', 'Max backoff', '60000')
  .option('--backoff-multiplier <n>', 'Backoff multiplier', '2')
  .option('--respect-retry-after', 'Honor Retry-After', true)
  .option('--circuit-breaker-threshold <n>', 'Circuit breaker threshold', '5')
  .option('--circuit-breaker-timeout <ms>', 'Circuit reset timeout', '30000')
  .action(async (options) => {
    const limiter = new RateLimiter({
      rateLimit: options.rateLimit,
      retryOnRateLimit: options.retryOnRateLimit,
      maxRetries: parseInt(options.maxRetries),
      backoffInitial: parseInt(options.backoffInitial),
      backoffMax: parseInt(options.backoffMax),
      backoffMultiplier: parseFloat(options.backoffMultiplier),
      backoffJitter: 0.1,
      respectRetryAfter: options.respectRetryAfter,
      circuitBreakerThreshold: parseInt(options.circuitBreakerThreshold),
      circuitBreakerTimeout: parseInt(options.circuitBreakerTimeout),
    });

    const result = await limiter.execute(() => api.sync());
    console.log(JSON.stringify(result));
  });
```

---

## Summary: Agent-Friendly Execution Patterns

| Pattern | Key Benefit | Implementation Priority |
|---------|-------------|------------------------|
| **Idempotency** | Safe retries | High |
| **Retry with backoff** | Handles transient failures | High |
| **Dry-run** | Preview before commit | High |
| **Non-interactive** | CI/CD compatibility | High |
| **Timeout handling** | Graceful deadline enforcement | High |
| **Pagination** | Efficient large dataset traversal | High |
| **Batch with partial failure** | Efficient bulk operations | Medium |
| **Batch limits** | Resource-safe bulk processing | Medium |
| **Rate limiting (client)** | Prevents throttling, respects quotas | Medium |
| **Long-running tasks** | Async operation support | Medium |
| **Transaction/rollback** | Atomic multi-step ops | Medium |
| **Timeout/cancellation** | Graceful failure handling | Medium |

### Standard Flag Reference

| Category | Flags |
|----------|-------|
| **Timeout** | `--timeout`, `--connect-timeout`, `--read-timeout`, `--graceful-shutdown-timeout`, `--on-timeout` |
| **Pagination** | `--per-page`, `--page`, `--cursor`, `--all`, `--max-pages`, `--sort-by`, `--sort-order` |
| **Batch** | `--batch-size`, `--max-concurrent`, `--delay-between-batches`, `--continue-on-error`, `--fail-threshold` |
| **Rate Limit** | `--rate-limit`, `--max-retries`, `--backoff-initial`, `--backoff-max`, `--respect-retry-after`, `--circuit-breaker-threshold` |
| **General** | `--dry-run`, `--yes`, `--force`, `--idempotency-key`, `--output`, `--quiet` |

All patterns should:
1. Return structured JSON output
2. Use clear exit codes
3. Provide sufficient context for automated recovery
4. Never hang waiting for human input
5. Use consistent `--kebab-case` flag naming

# Instrumentation — Print, Log, Stack Trace Per Language

Phase 2 and Phase 3 need evidence. When the existing logging doesn't surface what you need, you add temporary instrumentation. This file covers the three modes and the per-language idioms.

## The three instrumentation modes

| Mode | When | Lifetime |
|---|---|---|
| **Stdout print** | Quick-check during active debugging. "Does this branch run?" | Temporary — removed in Phase 4 |
| **Structured log** | Evidence you want retained. "This path is rare; log it with context." | Often persists after the fix |
| **Stack-trace capture** | "Who called this function?" — tracing the call chain backward | Temporary unless the anomaly is rare-and-recurring |

Pick by longevity: if the anomaly should leave a production breadcrumb, use a structured log. If it's scaffolding for this debug session only, use a print. If you need the caller's identity, capture the stack.

## Universal patterns

### Stdout print

For any language, the minimum useful print includes:

- A tag naming the file / module / context
- The variable(s) being inspected with their types
- The current state of any guard that gated this code path

Anti-pattern: `println(x)`. Too low context to survive five minutes of debugging.

### Structured log

Fields to always include:

- The identifier that lets you correlate this log with others (request ID, task ID, user ID, operation key)
- The value being reported, with unambiguous units
- The reason this log was added ("rare branch", "retry attempt", "cache miss with age")

### Stack-trace capture

When the question is "who called this?", capture the current call stack and write it to log. Do not use this as a substitute for the stack trace of an actual exception; use it where no exception is thrown but the caller's identity matters.

## Per-language patterns

### TypeScript / Node

```ts
// Print
console.debug('[auth.middleware]', { userId, sessionValid, reason });

// Structured log (pino / winston / bunyan all similar)
logger.warn({ userId, reason: 'session-lookup-miss', cacheAge }, 'session lookup failed');

// Stack trace (no exception thrown)
console.debug('[auth.middleware] caller stack:', new Error().stack);
```

### Python

```python
# Print
print(f"[auth.middleware] user_id={user_id} session_valid={valid} reason={reason}")

# Structured log
logger.warning("session lookup failed",
               extra={"user_id": user_id, "reason": "cache-miss", "cache_age_s": age})

# Stack trace
import traceback
logger.debug("caller stack:\n%s", "".join(traceback.format_stack()))
```

### Rust

```rust
// Print (dev only — use eprintln! for stderr)
eprintln!("[auth.middleware] user_id={:?} session_valid={} reason={:?}", user_id, valid, reason);

// Structured log (tracing is standard)
tracing::warn!(
    user_id = %user_id,
    reason = "session-lookup-miss",
    cache_age_s = cache_age,
    "session lookup failed"
);

// Stack trace
use std::backtrace::Backtrace;
tracing::debug!(backtrace = %Backtrace::capture(), "caller location");
```

### Go

```go
// Print
log.Printf("[auth.middleware] userID=%v sessionValid=%v reason=%s", userID, valid, reason)

// Structured log (zap / zerolog / slog)
logger.Warn("session lookup failed",
    zap.Int64("user_id", userID),
    zap.String("reason", "cache-miss"),
    zap.Duration("cache_age", cacheAge))

// Stack trace
import "runtime/debug"
log.Printf("caller stack:\n%s", debug.Stack())
```

### Swift

```swift
// Print
print("[auth.middleware] userId=\(userId) sessionValid=\(valid) reason=\(reason)")

// Structured log (os_log)
os_log(.info, log: .auth, "session lookup failed: user=%{public}d reason=%{public}@ age=%{public}f",
       userId, reason, cacheAge)

// Stack trace
print("caller stack: \(Thread.callStackSymbols.joined(separator: "\n"))")
```

### Ruby

```ruby
# Print
puts "[auth.middleware] user_id=#{user_id} session_valid=#{valid} reason=#{reason}"

# Structured log (Rails.logger or semantic_logger)
Rails.logger.warn(
  'session lookup failed',
  user_id: user_id, reason: 'cache-miss', cache_age_s: age
)

# Stack trace
Rails.logger.debug("caller stack:\n#{caller.join("\n")}")
```

### Java / Kotlin

```java
// Print
System.out.printf("[auth.middleware] userId=%d sessionValid=%b reason=%s%n", userId, valid, reason);

// Structured log (SLF4J + Logback/Log4j2 with MDC or key-value arguments)
logger.warn("session lookup failed user_id={} reason={} cache_age_s={}",
            userId, "cache-miss", cacheAge);

// Stack trace
logger.debug("caller stack: {}", Thread.currentThread().getStackTrace());
```

## Instrumentation that survives the fix

Phase 4 removes temporary diagnosis code. Decide per-line: stays or comes out.

| Code | Decision |
|---|---|
| Temporary `println!` / `console.log` / `dbg!` added during Phase 3 | **Remove** |
| Structured log on a rare branch that would have helped Phase 2 | **Keep** — it makes the next debug session cheaper |
| Stack-trace capture added to prove a caller identity | **Remove** (unless the anomaly is expected to recur rarely in prod, in which case convert to structured log with context) |
| Debug assertion that failed during Phase 3 and surfaced the mechanism | **Keep as a production assertion** (if the cost is acceptable) or **keep as a test assertion** (always) |
| Comment-out debug code ("// TODO: remove this") | **Remove** |

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `console.log(x)` with no context | Include the file/module tag + the values around x |
| Logging at INFO level for noise that should be DEBUG | Use DEBUG for rare-branch diagnostics; INFO is user-facing |
| Logging secrets or PII during debugging | Redact (`"***"` for secrets, `hash(user_id)` for PII) even in temporary instrumentation |
| Removing the log after the fix "because it's noisy" | If it helped once, it will help again. Either keep at DEBUG or convert to a metric. |
| Adding 20 `println` calls in one round | Add 2-3 with specific hypotheses; more means you are fishing, not testing. |
| Logging "here" / "reached here 1" | Logs must carry context (file, line, values). "Here" is a placeholder, not a log. |

## When logging is not enough

If the symptom is performance (not correctness), stdout/log is the wrong tool. Use a profiler, tracing system (OpenTelemetry, Jaeger), or a runtime debugger. `references/bisection-strategies.md` covers the search-space techniques; this file covers evidence capture.

## When the existing logging is enough

Before adding any instrumentation, read the existing logs with the symptom's timestamp and identifiers. In mature codebases, 70%+ of bugs have enough evidence in existing logs if you query them correctly. Run the query first, add instrumentation only when the existing logs genuinely don't surface the needed evidence.

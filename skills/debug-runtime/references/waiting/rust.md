# Rust / tokio — Condition-Based Waiting

Drop-in utilities for tokio-based async tests. Covers the common case (polling a condition) plus cancellation-token integration for cooperative cancellation.

## Utilities

```rust
// src/test_utils/poll.rs
use std::future::Future;
use std::time::{Duration, Instant};
use tokio::time::sleep;

#[derive(Debug, thiserror::Error)]
pub enum WaitError {
    #[error("wait_for timed out after {timeout:?}: {description}")]
    Timeout {
        timeout: Duration,
        description: String,
    },
}

pub struct WaitOpts {
    pub timeout: Duration,
    pub interval: Duration,
    pub description: String,
}

impl Default for WaitOpts {
    fn default() -> Self {
        Self {
            timeout: Duration::from_secs(5),
            interval: Duration::from_millis(10),
            description: "condition".into(),
        }
    }
}

pub async fn wait_for<F, Fut, T>(condition: F, opts: WaitOpts) -> Result<T, WaitError>
where
    F: Fn() -> Fut,
    Fut: Future<Output = Option<T>>,
{
    let deadline = Instant::now() + opts.timeout;
    loop {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err(WaitError::Timeout {
                timeout: opts.timeout,
                description: opts.description,
            });
        }
        // Enforce the deadline even while awaiting `condition()`. A stuck condition
        // future would otherwise block indefinitely.
        match tokio::time::timeout(remaining, condition()).await {
            Ok(Some(result)) => return Ok(result),
            Ok(None) => sleep(opts.interval.min(remaining)).await,
            Err(_) => {
                return Err(WaitError::Timeout {
                    timeout: opts.timeout,
                    description: opts.description,
                })
            }
        }
    }
}

pub async fn wait_for_count<F, Fut>(
    get_count: F,
    expected: usize,
    opts: WaitOpts,
) -> Result<(), WaitError>
where
    F: Fn() -> Fut,
    Fut: Future<Output = usize>,
{
    wait_for(
        || async { if get_count().await >= expected { Some(()) } else { None } },
        opts,
    )
    .await
}
```

## Usage

```rust
use std::sync::Arc;
use tokio::sync::Mutex;

#[tokio::test]
async fn cleanup_completes() {
    let store = Arc::new(Mutex::new(vec![1, 2, 3]));
    let store_clone = store.clone();
    tokio::spawn(async move {
        store_clone.lock().await.clear();
    });

    wait_for(
        || {
            let store = store.clone();
            async move { if store.lock().await.is_empty() { Some(()) } else { None } }
        },
        WaitOpts {
            timeout: Duration::from_secs(5),
            description: "store to empty".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
}
```

## Cancellation-token variant

For cooperative cancellation (preferred over hard timeouts in production code):

```rust
use tokio_util::sync::CancellationToken;

pub async fn wait_for_cancellable<F, Fut, T>(
    condition: F,
    cancel: CancellationToken,
    interval: Duration,
) -> Result<T, WaitError>
where
    F: Fn() -> Fut,
    Fut: Future<Output = Option<T>>,
{
    loop {
        // `biased;` ensures the cancel branch is checked before every poll
        // (and wraps `condition()` so cancellation interrupts an in-flight
        // condition future, not just the sleep).
        tokio::select! {
            biased;
            _ = cancel.cancelled() => return Err(WaitError::Timeout {
                timeout: Duration::ZERO,
                description: "cancelled".into(),
            }),
            res = condition() => {
                if let Some(result) = res {
                    return Ok(result);
                }
            }
        }
        // Sleep is also cancellable by the token.
        tokio::select! {
            biased;
            _ = cancel.cancelled() => return Err(WaitError::Timeout {
                timeout: Duration::ZERO,
                description: "cancelled".into(),
            }),
            _ = sleep(interval) => {}
        }
    }
}
```

## Test-framework integration

**`#[tokio::test]`**: works directly; the test runtime is already async.
**`tokio-test` crate**: provides `block_on` for sync tests; utilities above use async so prefer `#[tokio::test]`.
**Fake time**: `tokio::time::pause()` + `tokio::time::advance()` work with `sleep`. Either use real time in `wait_for` tests, or advance the pause in parallel with the wait.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `std::thread::sleep` in async code | Use `tokio::time::sleep` — otherwise you block the whole runtime thread |
| Hardcoded `Duration::from_millis(500)` in tests | Replace with `wait_for` + named condition |
| Polling with a synchronous `Mutex` inside `tokio::spawn` | Use `tokio::sync::Mutex` and `async` locking |
| `panic!()` on timeout instead of `Result` | Return `WaitError::Timeout` so callers can add context |

# Java / JUnit 5 / awaitility — Condition-Based Waiting

Awaitility is the idiomatic Java polling library; the examples below show both awaitility and a stdlib fallback.

## Idiomatic: awaitility

Awaitility is a small, zero-deps library that wraps exactly this pattern. For JUnit 5 projects, add:

```xml
<dependency>
  <groupId>org.awaitility</groupId>
  <artifactId>awaitility</artifactId>
  <version>4.2.0</version>
  <scope>test</scope>
</dependency>
```

Usage:

```java
import static org.awaitility.Awaitility.await;
import static org.awaitility.Durations.ONE_HUNDRED_MILLISECONDS;
import static org.awaitility.Durations.FIVE_SECONDS;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;

@Test
void cleanupCompletes() {
    Store store = new Store(List.of(1, 2, 3));
    new Thread(store::clear).start();

    await()
        .atMost(FIVE_SECONDS)
        .pollInterval(Duration.ofMillis(10))
        .alias("store to empty")
        .until(() -> store.size(), equalTo(0));
}

@Test
void bothWorkersCommit() {
    CommitLog log = new CommitLog();
    new Thread(() -> worker1(log)).start();
    new Thread(() -> worker2(log)).start();

    await()
        .atMost(Duration.ofSeconds(10))
        .alias("2 worker commits")
        .until(() -> log.entries().size(), greaterThanOrEqualTo(2));
}
```

`alias(description)` is what surfaces in the timeout message — always set it.

## Stdlib fallback (no awaitility)

```java
// src/test/java/testutil/PollUtils.java
package testutil;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.Callable;
import java.util.function.Supplier;

public class PollUtils {
    public static class WaitTimeoutException extends RuntimeException {
        public WaitTimeoutException(String msg) { super(msg); }
    }

    public static <T> T waitFor(Callable<T> condition, Duration timeout, Duration interval, String description) {
        if (description == null || description.isBlank()) description = "condition";
        Instant deadline = Instant.now().plus(timeout);
        Throwable last = null;
        while (Instant.now().isBefore(deadline)) {
            try {
                T result = condition.call();
                if (result != null && !(result instanceof Boolean b && !b)) return result;
            } catch (Throwable err) {
                last = err;
            }
            try { Thread.sleep(interval.toMillis()); }
            catch (InterruptedException ie) { Thread.currentThread().interrupt(); throw new RuntimeException(ie); }
        }
        String msg = "waitFor timed out after " + timeout + ": " + description;
        if (last != null) msg += " (last error: " + last + ")";
        throw new WaitTimeoutException(msg);
    }

    public static void waitForCount(Supplier<Integer> getCount, int expected, Duration timeout, Duration interval, String description) {
        if (description == null) description = "count >= " + expected;
        waitFor(() -> getCount.get() >= expected ? Boolean.TRUE : Boolean.FALSE, timeout, interval, description);
    }
}
```

## Test-framework integration

**JUnit 5**: native.
**Parameterized tests / `@RepeatedTest`**: polling utilities work per invocation; each has its own deadline.
**Mockito**: when the condition reads a mock's state, use `verify()` with `timeout(...)` as an alternative for signal-shaped waits; `waitFor` for state-shaped waits.
**Kotlin**: call awaitility from Kotlin directly; the same API works via Java interop.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `Thread.sleep(500)` in a JUnit test | awaitility's `await().until(...)` |
| `while(!condition) { Thread.sleep(10); }` with no timeout | Always set `atMost(...)` |
| Missing `alias(description)` in awaitility | Failure messages become useless; always set alias |
| Using `System.currentTimeMillis()` for the deadline | Use `Instant.now()` (monotonic-adjacent) or `java.time.Duration` comparisons |

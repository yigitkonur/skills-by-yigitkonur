# Swift / XCTest — Condition-Based Waiting

Drop-in utilities for XCTest (async/await). Uses Swift 5.5+ concurrency.

## Utilities

```swift
// PollUtils.swift
import Foundation
import XCTest

struct WaitOptions {
    var timeout: TimeInterval = 5.0
    var interval: TimeInterval = 0.01
    var description: String = "condition"
}

enum WaitError: Error, CustomStringConvertible {
    case timeout(TimeInterval, String)

    var description: String {
        switch self {
        case let .timeout(t, desc):
            return "waitFor timed out after \(t)s: \(desc)"
        }
    }
}

func waitFor<T>(
    _ condition: () async throws -> T?,
    options: WaitOptions = .init()
) async throws -> T {
    let deadline = Date().addingTimeInterval(options.timeout)
    var lastError: Error?
    while Date() < deadline {
        do {
            if let result = try await condition() {
                return result
            }
        } catch {
            lastError = error
        }
        try await Task.sleep(nanoseconds: UInt64(options.interval * 1_000_000_000))
    }
    throw WaitError.timeout(options.timeout, options.description + (lastError.map { " (last error: \($0))" } ?? ""))
}

func waitForCount(
    _ getCount: () async -> Int,
    expected: Int,
    options: WaitOptions = .init()
) async throws {
    var opts = options
    if opts.description == "condition" {
        opts.description = "count >= \(expected)"
    }
    _ = try await waitFor(
        { await getCount() >= expected ? () : nil },
        options: opts
    )
}
```

## Usage

```swift
import XCTest

final class StoreTests: XCTestCase {
    func testCleanupCompletes() async throws {
        let store = Store()
        Task { await store.clear() }

        try await waitFor(
            { await store.size == 0 ? () : nil },
            options: .init(timeout: 5, description: "store to empty")
        )
        let size = await store.size
        XCTAssertEqual(size, 0)
    }

    func testBothWorkersCommit() async throws {
        let log = CommitLog()
        async let _ = worker1(log)
        async let _ = worker2(log)

        try await waitForCount({ await log.count }, expected: 2,
                               options: .init(timeout: 10))
    }
}
```

## Test-framework integration

**XCTest + async**: use `async throws` test methods — XCTest awaits them natively.
**`XCTestExpectation`**: works in parallel with `waitFor`; prefer `waitFor` when the condition is query-shaped (you're checking state), `XCTestExpectation` when it's signal-shaped (you're waiting for a callback).
**Swift concurrency**: `Task.sleep` in the poll loop yields cooperatively.
**Actor isolation**: if the condition reads actor-isolated state, `await` is required — the utilities already use it.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `sleep(UInt32(0.5))` inside a test | `waitFor` + named condition |
| `XCTestExpectation` with a bare 5-second timeout | If you're polling state, `waitFor` is more direct |
| Non-async polling blocking the test thread | Use `await` throughout; `Task.sleep` instead of `Thread.sleep` |
| Ignoring errors inside the condition closure | Record as `lastError` so the timeout message carries it |

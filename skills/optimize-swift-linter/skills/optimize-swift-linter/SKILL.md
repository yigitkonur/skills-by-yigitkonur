---
name: optimize-swift-linter
description: "Use skill if you are writing, reviewing, or setting up Swift code quality tooling for macOS/iOS apps — covers SwiftLint, SwiftFormat, Airbnb rules, architecture, testing, and platform-specific patterns."
---

# Optimize Swift Linter

Production-grade Swift code quality patterns drawn from analysis of 75+ top-rated open-source Swift projects, including CotEditor, realm/SwiftLint, nikitabobko/AeroSpace, sindresorhus/Gifski, exelban/stats, and pointfreeco/swift-composable-architecture.

## How to Use

1. **Determine the platform** — macOS, iOS, or both?
2. **Read the relevant references** based on the task
3. **Apply patterns** when writing or reviewing code

## Reference Routing

Read only what the task requires — do not load everything at once.

| File | When to Read |
|------|-------------|
| `references/shared-swift.md` | **Always read first.** Core Swift patterns: naming, concurrency, error handling, generics, memory management, Codable, @Observable. |
| `references/airbnb-style-rules.md` | **Read when writing any Swift code.** Complete Airbnb style rules with WRONG/RIGHT examples, file organization, SwiftUI patterns, testing rules, and copy-paste SwiftLint/SwiftFormat configs. |
| `references/macos-patterns.md` | When building a **macOS** app. AppKit, SwiftUI for Mac, menu bar apps, IOKit/SMC system APIs, Sparkle auto-updates, sandboxing, distribution. |
| `references/ios-patterns.md` | When building an **iOS** app. SwiftUI navigation, SwiftData, StoreKit 2, WidgetKit, push notifications, background tasks, accessibility. |
| `references/architecture.md` | When designing app structure. TCA, MVVM with @Observable, swift-dependencies DI, module structure, multi-platform architecture. |
| `references/tooling-setup.md` | When setting up a project. SwiftLint config, SwiftFormat config, periphery dead-code detection, GitHub Actions CI, Xcode project structure. |
| `references/testing.md` | When writing tests. XCTest, Swift Testing (@Test), snapshot testing, mockolo/@Spyable mocking, TCA TestStore, UI testing. |

## Quick Decisions

### Project Setup (read `tooling-setup.md`)
- Use SwiftLint + SwiftFormat from day one
- Prefer Swift Package Manager over CocoaPods/Carthage
- Set up CI with `periphery` for dead code detection
- Use `.editorconfig` for consistent whitespace

### Architecture (read `architecture.md`)
- **Small apps**: MVVM with `@Observable`
- **Medium apps**: MVVM + Coordinator + dependency injection via `swift-dependencies`
- **Large apps**: TCA (The Composable Architecture) for full testability
- **Multi-platform**: Shared/ + Mac/ + iOS/ module structure (NetNewsWire pattern)

### Platform-Specific
- **macOS** (read `macos-patterns.md`): AppKit for system-level, SwiftUI for UI. Sparkle for updates. Handle sandboxing.
- **iOS** (read `ios-patterns.md`): SwiftUI-first with UIKit for advanced needs. Handle lifecycle, background tasks, push notifications.

### Testing (read `testing.md`)
- XCTest for unit tests (built-in, no dependencies)
- `swift-snapshot-testing` for UI regression
- `swift-custom-dump` for better assertion messages
- `mockolo` or `@Spyable` macro for mock generation

## Universal Principles

Apply to every Swift file, regardless of platform:

1. **Prefer value types** (structs, enums) over classes unless you need identity or inheritance
2. **Use Swift concurrency** (async/await, actors) instead of GCD or Combine for new code
3. **Make illegal states unrepresentable** — use enums with associated values
4. **Protocol-oriented design** — define behavior via protocols, not inheritance
5. **Minimize optionals** — use non-optional types when the value is always present
6. **Access control matters** — default to `private`, expose only what's needed
7. **Name things clearly** — follow Apple's API Design Guidelines (clarity > brevity)
8. **Keep files focused** — one type per file, max ~300 lines
9. **Default classes to `final`** — composition over inheritance
10. **No `print()` in production** — use `os_log` or `swift-log`

## Anti-Patterns

- **Massive view controllers/views** — break into smaller components
- **Force unwrapping** (`!`) outside of `IBOutlet` — use `guard let` or `if let`
- **Stringly-typed code** — use enums, not raw strings for keys/identifiers
- **Ignoring errors** — handle every `throws` explicitly, don't use `try?` lazily
- **God objects** — no single type should handle networking, persistence, AND UI
- **Premature abstraction** — don't create protocols for things with one conformer
- **Combine for new code** — prefer Swift concurrency; Combine is being superseded
- **`@unchecked Sendable`** — use `Sendable`, `@MainActor`, or `@preconcurrency import` instead

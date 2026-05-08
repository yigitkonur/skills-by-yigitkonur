# Snapshot Testing — SPM Wiring

The discipline references (`expectation-loop.md`, `capture-modes.md`, `drift-analysis.md`, `troubleshooting.md`) describe **how to think** about visual validation. This file describes **how to wire it up** with `swift-snapshot-testing` so the discipline is enforceable in CI.

If the user wants screenshot validation but doesn't have a harness yet, this is the path.

## Library choice

Default: `pointfreeco/swift-snapshot-testing` (the de-facto standard).

Why not roll your own:
- The library handles snapshot file IO, diffing, record/verify modes, and pretty failure output.
- Failures emit an Xcode-clickable image diff, which is the fastest debugging surface for visual regressions.
- It works with `XCTest` (which the macOS toolchain already ships) — no extra runner.

## SPM dependency

In `Package.swift`:

```swift
let package = Package(
    name: "AppName",
    platforms: [.macOS(.v26)],
    targets: [
        .executableTarget(name: "AppName", dependencies: []),
        .testTarget(
            name: "AppNameSnapshotTests",
            dependencies: [
                "AppName",
                .product(name: "SnapshotTesting", package: "swift-snapshot-testing"),
            ]
        ),
    ],
    dependencies: [
        .package(
            url: "https://github.com/pointfreeco/swift-snapshot-testing.git",
            from: "1.17.0"
        ),
    ]
)
```

For Xcode projects without a `Package.swift`: File → Add Package Dependencies → paste URL → add to the snapshot test target only.

## Test target setup

Create `Tests/AppNameSnapshotTests/AppNameSnapshotTests.swift`:

```swift
import SnapshotTesting
import SwiftUI
import XCTest
@testable import AppName

final class AppNameSnapshotTests: XCTestCase {
    override func setUp() {
        super.setUp()
        // Set true ONLY when intentionally re-recording. Never commit with this on.
        // isRecording = true
    }

    func test_contentView_default() {
        let view = ContentView().frame(width: 900, height: 600)
        assertSnapshot(of: view, as: .image(layout: .fixed(width: 900, height: 600)))
    }

    func test_contentView_dark() {
        let view = ContentView()
            .frame(width: 900, height: 600)
            .preferredColorScheme(.dark)
        assertSnapshot(
            of: view,
            as: .image(layout: .fixed(width: 900, height: 600)),
            named: "dark"
        )
    }
}
```

## Recording vs verifying

The library has two modes:

| Mode | What happens | When to use |
|---|---|---|
| **Verify** (default) | Compare against stored PNG; fail on diff | Every CI run, every local commit |
| **Record** | Overwrite stored PNG with current render | Once when adding a new test, or after an intentional design change |

To re-record a single test, flip `isRecording = true` in that test's `setUp`. **Never commit with `isRecording = true`** — the pre-commit hook should catch this. Add a SwiftLint custom rule if you don't trust your team:

```yaml
# in .swiftlint.yml
custom_rules:
  no_committed_isRecording:
    name: "Snapshot recording mode left enabled"
    regex: '^[^/]*isRecording\s*=\s*true'
    message: "Disable isRecording before committing — never ship a record-mode test."
    severity: error
```

## Light + dark + size matrix

Pinned dimensions matter — the same view at 900×600 and 1200×800 will produce different snapshots, both legitimate. Standardize on a small set:

| Variant | Size | Use |
|---|---|---|
| `default` | 900×600 | Primary canvas |
| `compact` | 720×480 | Smaller windows |
| `wide` | 1280×800 | Hero / large displays |

Run each in `.light` and `.dark`. Six snapshots per top-level view is a sustainable baseline; tighten only if drift becomes noisy.

## CI considerations

- **Pin the runner OS.** `macos-15` and `macos-14` produce different system fonts and tinting. Pick one in your CI matrix and never silently bump.
- **Pin Xcode.** `sudo xcode-select -s /Applications/Xcode_26.app` at the start of the workflow.
- **Pin simulator runtimes** if testing iOS or visionOS variants.
- **Cache `~/Library/Developer/Xcode/DerivedData`** between runs — skipped warm-builds save 60-90 seconds per job.

The bundled `<skill-dir>/assets/github-workflows/swift-quality.yml` has a full matrix that does this.

## Failure output

When a snapshot test fails, the library writes three files into `Tests/.../__Snapshots__/<TestClass>/`:

- `failure_<name>.png` — current render
- `<name>.png` — recorded baseline
- `failure_<name>.diff.png` — pixel diff highlighting changes

In CI, **upload these as artifacts** so reviewers can see the diff without rebuilding. The bundled workflow does this automatically.

## How this couples to the expectation loop

`swift-snapshot-testing` answers "did the rendered pixels change?". It does not answer "are the changes correct?" — that's still the loop in `expectation-loop.md`:

1. Write the expectation contract before re-recording.
2. Re-record.
3. Compare visibly (`failure_*.diff.png`).
4. Classify as `Matches` / `Drift` / `Better than expected`.
5. Decide layer (app fix / automation fix / expectation fix) and rerun.

The library is the capture mechanism; the discipline is the meaning. Don't conflate them — a green snapshot test on a buggy expectation is worse than a red one on a correct expectation.

## Common pitfalls

→ `references/visual-validation/troubleshooting.md` covers blank snapshots, focus-dependent failures, permissions issues. The `swift-snapshot-testing`-specific gotchas:

- **`assertSnapshot` runs synchronously** but SwiftUI rendering is async. If a view depends on `@StateObject` data load, render once into an off-screen window and wait via `RunLoop.current.run(until: Date().addingTimeInterval(0.1))` before asserting.
- **`@Environment` defaults differ** between tests and runtime. Inject explicit values: `.environment(\.colorScheme, .dark)`, `.environment(\.locale, Locale(identifier: "en_US"))`.
- **Dynamic Type drifts snapshots**. Pin `.dynamicTypeSize(.large)` (or whatever you record at) on every test view.
- **Backing scale factor matters.** macOS retina renders 2x; non-retina renders 1x. Force `2x` via `.image(layout: .fixed(...), traits: .init(displayScale: 2))` so CI on a non-retina runner doesn't drift.

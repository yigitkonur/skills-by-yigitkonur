# Swift and Xcode CI

Use this file for Swift/Xcode build and iOS test acceleration. Generic CI rules still apply; this file covers the Apple-specific measurement and caching traps.

## Measure first

```bash
xcodebuild -showBuildTimingSummary \
  -scheme App \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  build
```

Compare wall-clock clean, warm/cached clean, and incremental builds. Aggregate task time can exceed wall time because tasks run in parallel; only critical-path work reduces waiting.

Add type-check diagnostics for slow Swift expressions:

```text
-Xfrontend -warn-long-function-bodies=100
-Xfrontend -warn-long-expression-type-checking=100
```

Fix hotspots by splitting expressions and adding type annotations; do not guess from file size.

## Build settings and graph

- Declare run-script input/output files or `.xcfilelist`; scripts without them run every build and serialize work.
- Simplify target dependencies and split monolithic modules when planning/invalidation dominates.
- Use active architecture only for local/debug where appropriate.
- Benchmark explicit modules rather than assuming they help, especially multi-project workspaces and targets with differing compiler options.
- Xcode compilation caching can help clean and branch-switch builds; measure cold and cached-clean separately.

## SwiftPM and DerivedData caching

Cache SwiftPM state by:

- `Package.resolved`,
- Swift/Xcode version,
- OS/architecture,
- cache namespace,
- relevant project configuration.

Save caches even after test failure when the cache is still valid. Raw DerivedData restore can fail to produce incremental hits because Xcode tracks high-resolution timestamps; use tooling that restores file mtimes or accept clean-build semantics.

## Binary dependencies

Move slow, stable source dependencies into versioned XCFrameworks built with library evolution/module stability. Verify checksums and platform slices. Do not use library evolution as a shortcut for packages always built from source together.

## iOS test acceleration

Build once, test many:

```bash
xcodebuild build-for-testing \
  -scheme App \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -derivedDataPath ./DerivedData

xcodebuild test-without-building \
  -xctestrun ./DerivedData/Build/Products/App_iphonesimulator.xctestrun \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -parallel-testing-enabled YES \
  -maximum-parallel-testing-workers 2 \
  -retry-tests-on-failure -test-iterations 3 \
  -enableCodeCoverage NO \
  -resultBundlePath Results.xcresult
```

- Share `.xctestrun` and build products as artifacts across shards.
- Xcode schedules primarily at class granularity; huge classes create stragglers.
- UI tests use cloned simulators and significant RAM; benchmark two or three workers before increasing.
- Test-plan repetition behavior varies by execution path/Xcode; pass explicit retry flags when using `.xctestrun`.
- Emit and merge `.xcresult`; export only failure attachments for diagnostics.

## Runner reliability

- Pin `runs-on: macos-<version>` and select Xcode explicitly; avoid `macos-latest` for reproducible builds/signing.
- Keep lint/typecheck/cross-platform tests on Linux when possible; macOS capacity is scarce.
- Use the fastest local disk for DerivedData and avoid network-mounted build directories.

## Sources

- Explicit modules: https://developer.apple.com/documentation/xcode/building-your-project-with-explicit-module-dependencies (accessed 2026-07-28)
- Incremental builds: https://developer.apple.com/documentation/xcode/improving-the-speed-of-incremental-builds (accessed 2026-07-28)
- Xcode 26 release notes: https://developer.apple.com/documentation/xcode-release-notes/xcode-26-release-notes (accessed 2026-07-28)
- Swift compiler performance: https://github.com/swiftlang/swift/blob/main/docs/CompilerPerformance.md (accessed 2026-07-28)
- Library evolution: https://swift.org/blog/library-evolution/ (accessed 2026-07-28)
- xcresulttool: https://keith.github.io/xcode-man-pages/xcresulttool.1.html (accessed 2026-07-28)

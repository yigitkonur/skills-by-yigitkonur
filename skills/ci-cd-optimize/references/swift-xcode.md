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

## Deterministic dependency resolution

SwiftPM's default fetch is a full git clone per dependency, history included,
repeated on every fresh runner — and before it can clone anything it explores
the version space to pick versions. Both costs are avoidable, and the
exploration is usually the larger one.

Commit `Package.resolved` and resolve from it in CI:

```bash
swift package resolve --force-resolved-versions
```

The flag is documented as "Only use versions from the `Package.resolved` file
and fail resolution if it is out-of-date" — the same loud-on-drift contract
`npm ci` gives, which is what makes it safe to depend on. The aliases
`--disable-automatic-resolution` and `--only-use-versions-from-resolved-file`
are the same option. For Xcode projects, the equivalent is
`xcodebuild -disableAutomaticPackageResolution` (single dash), documented as
preventing packages from resolving to versions other than those recorded in
`Package.resolved`.

Committing the file pins versions for a leaf project — an app or any package
not consumed as a dependency. It does **not** pin anything for consumers of a
library, so a library's committed lockfile is not a reproducibility guarantee
for downstream builds.

**Registry-sourced pins look different.** Where a provider resolves public
packages through a Swift package registry (SE-0292) instead of git, a pin
records a registry identity and integrity `checksum` rather than a repository
URL and `revision`, so the first registry-backed resolve rewrites
`Package.resolved`. Expect that diff, decide deliberately whether the
repository keeps git-form pins, and include *whether registry resolution is
active* in your SwiftPM cache key — the same project can otherwise produce two
legitimately different resolved files.

Measured on Avrea (vapor, 28-package graph, fresh runner): plain git with no
lockfile 23s, registry with no lockfile 11s, registry plus committed lockfile
and `--force-resolved-versions` 4s. The transport change is real, but most of
the remaining win is skipping version exploration — which costs nothing to
adopt and works on any provider. See `references/avrea/caching.md` for the
provider-specific behavior.

## SwiftPM and DerivedData caching

Cache SwiftPM state by:

- `Package.resolved`,
- Swift/Xcode version,
- OS/architecture,
- cache namespace,
- whether registry resolution is active,
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
- `swift package resolve` options: https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/packageresolve/ (accessed 2026-07-29)
- Resolving package versions: https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/resolvingpackageversions/ (accessed 2026-07-29)
- SE-0292 Package Registry Service: https://github.com/apple/swift-evolution/blob/main/proposals/0292-package-registry-service.md (accessed 2026-07-29)
- Adding package dependencies (Xcode): https://developer.apple.com/documentation/xcode/adding-package-dependencies-to-your-app (accessed 2026-07-29)
- Swift compiler performance: https://github.com/swiftlang/swift/blob/main/docs/CompilerPerformance.md (accessed 2026-07-28)
- Library evolution: https://swift.org/blog/library-evolution/ (accessed 2026-07-28)
- xcresulttool: https://keith.github.io/xcode-man-pages/xcresulttool.1.html (accessed 2026-07-28)

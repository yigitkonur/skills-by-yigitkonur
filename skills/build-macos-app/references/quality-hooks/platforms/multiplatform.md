# Multi-platform Apple projects

When a single repo targets two or more Apple platforms (a watchOS app paired with an iOS companion, a Catalyst+iOS+macOS app, an SPM library targeting all five platforms), the hook itself stays identical — only the **typecheck stage** needs platform awareness.

## Strategy options

| Strategy | Pros | Cons | When to use |
|---|---|---|---|
| **Typecheck the primary platform only** in pre-commit; check all platforms in CI | Fast hook (one platform); CI catches the rest | Cross-platform-specific issues caught later (in CI, not at commit) | **Default for most multi-platform projects** |
| **Typecheck all platforms in pre-commit** | Maximum signal at commit time | Slow (5-25s per platform); brittle (any missing simulator runtime fails the commit) | Rare; only for small libraries with stable SDK availability |
| **Typecheck on each affected platform based on which files staged** | Smart; minimum work | Complex to implement; fragile heuristics | Skip — not worth the complexity |

## Recommended setup: primary-platform pre-commit, full matrix in CI

In `scripts/swift-typecheck.sh`, set the primary platform:

```bash
# Pick the platform you develop on most. macOS is fastest and most reliable.
SWIFT_HOOK_PLATFORM="${SWIFT_HOOK_PLATFORM:-macOS}"
```

Developers can override per-shell when working on platform-specific code:

```bash
export SWIFT_HOOK_PLATFORM=iOS    # for iOS-only feature work
```

In CI (e.g., `.github/workflows/ci.yml`), run the full matrix:

```yaml
jobs:
  typecheck:
    runs-on: macos-15
    strategy:
      matrix:
        platform: [macOS, iOS, tvOS, watchOS, visionOS]
    steps:
      - uses: actions/checkout@v4
      - name: Install simulator runtime if needed
        if: matrix.platform == 'visionOS'
        run: sudo xcodebuild -downloadPlatform visionOS
      - name: Typecheck
        run: SWIFT_HOOK_PLATFORM=${{ matrix.platform }} bash scripts/swift-typecheck.sh
```

CI auto-skips the pre-commit hook (`$CI` check) so the matrix runs cleanly without re-invoking pre-commit per platform.

## Project type detection

The typecheck script auto-detects:

```sh
if [ -f Package.swift ] && ! ls *.xcworkspace >/dev/null 2>&1 && ! ls *.xcodeproj >/dev/null 2>&1; then
    PROJECT_TYPE="spm"
elif ls *.xcworkspace >/dev/null 2>&1; then
    PROJECT_TYPE="workspace"
elif ls *.xcodeproj >/dev/null 2>&1; then
    PROJECT_TYPE="xcodeproj"
fi
```

Then chooses the right command:
- `spm` + macOS → `swift build --build-tests=false` (fastest)
- `spm` + non-macOS → `xcodebuild` with the platform's destination
- `workspace` → `xcodebuild -workspace`
- `xcodeproj` → `xcodebuild -project`

`swift build --triple` is **NOT supported** for cross-compiling to Apple platforms (apple/swift-package-manager#6571) — even pure-SPM repos must use `xcodebuild` for non-host targets.

## Per-target SwiftLint configs

If your repo has dramatically different style needs per platform (rare), use **nested `.swiftlint.yml`** files:

```
repo/
├── .swiftlint.yml                  # base config
├── iOS/
│   └── .swiftlint.yml              # iOS-only overrides
├── macOS/
│   └── .swiftlint.yml              # macOS-only overrides
└── visionOS/
    └── .swiftlint.yml              # visionOS-only overrides
```

SwiftLint walks up from each linted file to find the closest config (per SwiftLint README §Nested Configurations). **Only ONE nested config is merged per file** — there's no chain-of-config behavior. Use sparingly; most multi-platform projects benefit from a single root config.

## Schemes that build for multiple platforms

If a single Xcode scheme builds multiple platform targets (e.g., a "Universal" scheme with both iOS and macOS targets), the typecheck stage only needs ONE invocation per platform — but you must pick the right scheme per platform.

Discover schemes with:

```bash
xcodebuild -list -json | jq -r '.project.schemes[]'         # for .xcodeproj
xcodebuild -list -workspace YourWorkspace.xcworkspace -json | jq -r '.workspace.schemes[]'
```

Show what platforms a scheme supports:

```bash
xcodebuild -showdestinations -scheme YourScheme | grep generic
```

## SwiftLint and SwiftFormat: no per-platform changes

Both tools are platform-agnostic. The same `.swiftlint.yml` and `.swiftformat` work for the entire project regardless of how many Apple platforms are targeted. There are no platform-gated rules.

## References

- SwiftLint README §Nested Configurations
- apple/swift-package-manager#6571 — `swift build --triple` unsupported
- `xcodebuild -showdestinations` — discover supported platforms per scheme
- mokacoding xcodebuild cheatsheet — https://mokacoding.com/blog/xcodebuild-destination-options/

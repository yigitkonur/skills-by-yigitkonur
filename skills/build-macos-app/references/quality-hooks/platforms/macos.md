# Platform: macOS

macOS is the **default and simplest** target for the Swift quality hook. No simulator runtime required, no code-signing complications for typecheck, and the fastest typecheck times of any Apple platform. Macros and SPM plugins compile against the host SDK without any cross-compilation step.

## Hook configuration

Same as the cross-platform default — no platform-specific changes needed. SwiftLint and SwiftFormat are platform-agnostic; the hook script in `.githooks/pre-commit` runs identically.

## Typecheck stage configuration

In `scripts/swift-typecheck.sh`, set:

```bash
SWIFT_HOOK_PLATFORM=macOS    # this is the default
```

The script translates this to:

```bash
DESTINATION="generic/platform=macOS"
```

For a **Mac Catalyst** target (iPad app running on macOS), use the same destination plus a `variant`:

```bash
SWIFT_HOOK_DESTINATION='generic/platform=macOS,variant=Mac Catalyst'
```

## Typical typecheck command (after auto-detection)

```bash
xcodebuild build \
  -scheme YourScheme \
  -destination "generic/platform=macOS" \
  -configuration Debug \
  -derivedDataPath /tmp/swift-hook-build \
  -clonedSourcePackagesDirPath .spm-cache \
  -parallelizeTargets \
  -skipMacroValidation \
  -skipPackagePluginValidation \
  ONLY_ACTIVE_ARCH=YES \
  CODE_SIGNING_ALLOWED=NO \
  -quiet
```

## Speed expectations

- Incremental typecheck on a small (<10k LOC) macOS app: **3-8 seconds** with warm derived-data
- Cold typecheck (after `make clean`): 30-90 seconds depending on dependency graph
- For Pure SPM (`Package.swift`-only) macOS-targeting libraries, `swift build --build-tests=false` is **30-60% faster** than `xcodebuild` because it skips the Xcode project resolve step

## Known issues

None macOS-specific as of Xcode 16.3 / Xcode 26 betas (April 2026). The general SwiftLint pitfalls apply (Apple Silicon `/opt/homebrew/bin` PATH, Xcode 15+ user-script sandboxing for **build-phase** SwiftLint — pre-commit hooks are unaffected). See `references/troubleshooting.md`.

## CI considerations

GitHub Actions `macos-15` runners (default since Aug 2025; `macos-latest` migrated July 2025 per github.blog 2025-07-11) include a fresh macOS SDK. No simulator runtime install needed. `macos-13` is being retired by 2025-12-04 — pin to `macos-15` or `macos-latest`.

## Pure SPM macOS package

For a `Package.swift`-only library:

```bash
# Hook stage 4 path:
swift build --build-tests=false      # fastest typecheck for host platform

# Or via xcodebuild for parity with the multi-platform setup:
xcodebuild -scheme MyLib \
  -destination "generic/platform=macOS" \
  -clonedSourcePackagesDirPath .spm-cache \
  build
```

`swift build --triple` is **NOT supported** for cross-platform builds (apple/swift-package-manager#6571) — for non-host platforms, `xcodebuild` is mandatory.

## References

- `xcodebuild(1)` man page — generic destination semantics
- Xcode 16 release notes — https://developer.apple.com/documentation/xcode-release-notes/xcode-16-release-notes
- `actions/runner-images` macos-15 README — https://github.com/actions/runner-images/blob/main/images/macos/macos-15-Readme.md
- GitHub blog macos-latest migration — https://github.blog/changelog/2025-07-11-upcoming-changes-to-macos-hosted-runners-macos-latest-migration-and-xcode-support-policy-updates/

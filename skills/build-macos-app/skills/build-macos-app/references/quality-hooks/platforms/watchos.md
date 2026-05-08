# Platform: watchOS

watchOS has one significant quirk: `xcodebuild test` requires a **paired iOS destination**, but `xcodebuild build` (what the typecheck stage runs) does NOT — pure typecheck works fine standalone.

## Hook configuration

Same `.githooks/pre-commit` and configs as macOS/iOS. SwiftLint/SwiftFormat unchanged.

## Typecheck stage configuration

```bash
SWIFT_HOOK_PLATFORM=watchOS
# auto-translates to:
# DESTINATION="generic/platform=watchOS Simulator"
```

## Typical typecheck command

```bash
xcodebuild build \
  -scheme YourWatchApp \
  -destination "generic/platform=watchOS Simulator" \
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

## Pairing requirement (test only, NOT build)

Per the `xcodebuild(1)` man page: "a watchOS app is always built and deployed nested inside of an iOS app." For `xcodebuild test`, the destination MUST specify the **paired iOS destination** (`platform=iOS Simulator,name=iPhone 15,OS=17.0` plus `companionAppDestination`). For `xcodebuild build` (typecheck), the generic watchOS destination works standalone — no pairing needed.

This is **important**: don't add iOS pairing flags to the typecheck stage. They only matter for `test`, which the pre-commit hook does NOT run.

## Speed expectations

- Incremental typecheck: **5-15 seconds**
- watchOS is generally smaller in scope than iOS apps — typecheck times tend to be at the lower end of the range

## Known issues

- **SPM packages with XCTest fail to build for watchOS** historically (forums.swift.org/t/40474). If your `Package.swift` imports XCTest and you typecheck for watchOS via `swift build`, you'll hit this. Workaround: only run `swift build` for the host platform; use `xcodebuild` for watchOS so XCTest is conditionally available.
- **watchOS Simulator runtime availability on CI:** Less reliable than iOS. Same pattern as tvOS — `xcrun simctl list runtimes | grep -i watch` to verify; `xcodebuild -downloadPlatform watchOS` to install.

## CI considerations

GitHub Actions `macos-15` typically includes watchOS Simulator runtime. The three-runtime support policy applies — verify before relying on it.

## Pure SPM watchOS package

```bash
xcodebuild -scheme MyWatchLib \
  -destination "generic/platform=watchOS Simulator" \
  -clonedSourcePackagesDirPath .spm-cache \
  build
```

## References

- `xcodebuild(1)` man page (watchOS pairing semantics — for `test` only)
- forums.swift.org/t/40474 — SPM XCTest unavailable on watchOS
- `actions/runner-images#12541`

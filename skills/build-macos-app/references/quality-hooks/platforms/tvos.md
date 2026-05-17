# Platform: tvOS

tvOS uses the same hook architecture as iOS — SwiftLint/SwiftFormat are platform-agnostic, only the typecheck destination changes.

## Hook configuration

Same `.githooks/pre-commit` and configs as macOS/iOS.

## Typecheck stage configuration

```bash
SWIFT_HOOK_PLATFORM=tvOS
# auto-translates to:
# DESTINATION="generic/platform=tvOS Simulator"
```

## Typical typecheck command

```bash
xcodebuild build \
  -scheme YourTVApp \
  -destination "generic/platform=tvOS Simulator" \
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

- Incremental typecheck on a typical tvOS app: **5-15 seconds** with warm derived-data
- Similar profile to iOS — tvOS shares most of the iOS toolchain

## Known issues

- **tvOS Simulator runtime availability on CI:** Less reliable than iOS Simulator on GitHub Actions. Verify with `xcrun simctl list runtimes | grep -i tvos`. If missing, install with `xcodebuild -downloadPlatform tvOS` (Xcode 15+).
- All iOS pitfalls apply (code-signing, sandboxing, macro validation).

## CI considerations

GitHub Actions `macos-15` typically includes the tvOS Simulator runtime, but the **three-runtime support policy** (#12541, Aug 2025) means older Xcode versions on the runner may have it removed. Pin Xcode and verify: `xcrun simctl list runtimes | grep -i tvos`.

## Pure SPM tvOS package

```bash
xcodebuild -scheme MyLib \
  -destination "generic/platform=tvOS Simulator" \
  -clonedSourcePackagesDirPath .spm-cache \
  build
```

## References

- `xcodebuild(1)` man page
- `actions/runner-images#12541` — three-runtime support policy

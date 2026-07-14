# Phase 1 — Explore the Repo

Before recommending or installing anything, profile *this* project. Sentry's correct shape
depends entirely on facts you can only get from the repo. Run the sweep, record eight
signals, then decide.

## Detection sweep

Run from the repo root. Every line is read-only.

```bash
# 1. Existing Sentry dependency (skip install if already present — go configure)
grep -rEi "sentry|SentrySPM|SentrySwiftUI" \
  --include="Package.swift" --include="Package.resolved" --include="Podfile" \
  --include="Cartfile" --include="project.pbxproj" . 2>/dev/null | head

# 2. Dependency manager
ls Package.swift 2>/dev/null && echo "SPM manifest"
ls Podfile 2>/dev/null && echo "CocoaPods"
find . -name project.pbxproj -maxdepth 3 2>/dev/null | head   # SPM-in-xcodeproj if refs exist
grep -l "XCRemoteSwiftPackageReference" $(find . -name project.pbxproj) 2>/dev/null

# 3. App lifecycle — SwiftUI App vs AppKit AppDelegate
grep -rE "@main|struct .*: *App\b" --include="*.swift" . 2>/dev/null | head
grep -rE "NSApplicationDelegateAdaptor|@main .*AppDelegate|NSApplicationMain" --include="*.swift" . 2>/dev/null | head

# 4. Sandbox + hardened runtime + platform
grep -A1 "com.apple.security.app-sandbox" $(find . -name "*.entitlements") 2>/dev/null
grep -rE "ENABLE_HARDENED_RUNTIME|MACOSX_DEPLOYMENT_TARGET|SUPPORTED_PLATFORMS" \
  $(find . -name project.pbxproj) 2>/dev/null | sort -u | head

# 5. Distribution — App Store vs notarized DMG (Sparkle) vs ad-hoc
grep -rEi "sparkle|appcast|SUFeedURL" . --include="*.xml" --include="*.plist" --include="*.swift" 2>/dev/null | head
find . -iname "appcast*.xml" 2>/dev/null

# 6. CI present?
ls -d .github/workflows .gitlab-ci.yml .circleci fastlane 2>/dev/null

# 7. Existing logging (bridge candidates)
grep -rE "import OSLog|os\.Logger|Logger\(subsystem|CocoaLumberjack|DDLog" --include="*.swift" . 2>/dev/null | head

# 8. Companion backend (distributed tracing candidate)
ls ../backend ../server ../api ../*/go.mod ../*/requirements.txt ../*/package.json 2>/dev/null
```

## The eight signals and what each changes

| Signal | Values | Consequence |
|---|---|---|
| **Dependency manager** | SPM-in-`.xcodeproj` / `Package.swift` / CocoaPods | *SPM-in-xcodeproj:* add via Xcode "Add Package Dependencies". *Manifest:* `.package(...)`. *CocoaPods:* deprecated — migrate or use SPM. |
| **App lifecycle** | SwiftUI `App` / AppKit `AppDelegate` | Where `SentrySDK.start` goes. SwiftUI `App.init()` (earliest) vs `applicationDidFinishLaunching`. SwiftUI + `NSApplicationDelegateAdaptor` → NSException opt-in is the code path, not the principal-class swap. |
| **Sandboxed?** | yes / no | Non-sandboxed → crash cache in `~/Library/Caches/`; paths embed the username (scrub them). No entitlement needed for crash capture either way. |
| **Hardened Runtime** | on / off | On is normal; crash handlers still work. Only matters for the verification smoke test (test on a real signed build). |
| **Distribution** | App Store / notarized DMG (Sparkle) / ad-hoc | Drives dSYM upload flow and release naming. Sparkle: default `releaseName` already matches the appcast version — leave it auto. |
| **CI present?** | yes / no | *No CI* → dSYM upload is a **local** Makefile/build-phase step, not a pipeline. This is the common macOS-indie case. |
| **Existing logging** | `os.Logger` / CocoaLumberjack / none | Decide whether to bridge into breadcrumbs/logs. Note: there is **no official OSLog→Sentry bridge** — dual-log at call sites (see advanced-instrumentation). |
| **Data sensitivity** | handles user text/files/PII? / not really | The single biggest driver of scrub aggressiveness and whether reporting is opt-in. When in doubt, treat as sensitive. |

## Output of Phase 1

A short written fact sheet, e.g.:

> SPM-in-xcodeproj · SwiftUI App + NSApplicationDelegateAdaptor · non-sandboxed · Hardened
> Runtime on · notarized DMG via Sparkle · no CI · uses `os.Logger` heavily · handles
> user documents (sensitive).

That sheet decides everything downstream. Do not install before you have it.

## Gotchas

- **A `project.pbxproj` with `XCRemoteSwiftPackageReference` = SPM managed inside the
  Xcode project**, not a `Package.swift`. Add packages via the Xcode UI, and the resolved
  pins live in `*.xcworkspace/xcshareddata/swiftpm/Package.resolved`.
- **"No CI" is not a blocker** — it just means the dSYM upload and release commands live in
  the local build runbook (Makefile target or Xcode Run Script). Plan for that, don't skip it.
- If Sentry is **already present**, don't reinstall — jump to Phase 2 and audit which
  signals/options/scrubbing are configured versus missing.

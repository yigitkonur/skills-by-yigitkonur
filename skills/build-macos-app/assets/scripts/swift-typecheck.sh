#!/usr/bin/env bash
# Swift typecheck stage for the pre-commit hook.
#
# Auto-detects project type (SPM / xcodeproj / xcworkspace) and runs the
# correct typecheck command for the active platform. Per-platform xcodebuild
# destinations live in this script — edit PLATFORM_DESTINATION below to
# match your project.
#
# Invoked by .githooks/pre-commit ONLY when SWIFT_HOOK_TYPECHECK=1 is set.
# Opt-in because the project graph can drift transiently.
#
# Args: list of staged .swift files (informational; the build covers the
# whole graph regardless).

set -euo pipefail

if REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" && [ -n "$REPO_ROOT" ]; then
    :
else
    REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi
cd "$REPO_ROOT"

# ─── Configuration ────────────────────────────────────────────────────────
# Override per-platform via env vars; defaults are macOS-first.
SCHEME="${SWIFT_HOOK_SCHEME:-}"                                # auto-detected if empty
PROJECT="${SWIFT_HOOK_PROJECT:-}"                              # auto-detected if empty
PLATFORM="${SWIFT_HOOK_PLATFORM:-macOS}"                       # macOS | iOS | tvOS | watchOS | visionOS
DERIVED_DATA="${SWIFT_HOOK_DERIVED_DATA:-/tmp/swift-hook-build}"
SPM_CACHE="${SWIFT_HOOK_SPM_CACHE:-$REPO_ROOT/.spm-cache}"

# Map platform to xcodebuild destination. Simulator destinations avoid
# code-signing entirely; device destinations are faster but need cert config.
case "$PLATFORM" in
    macOS)     DESTINATION="generic/platform=macOS" ;;
    iOS)       DESTINATION="generic/platform=iOS Simulator" ;;
    tvOS)      DESTINATION="generic/platform=tvOS Simulator" ;;
    watchOS)   DESTINATION="generic/platform=watchOS Simulator" ;;
    visionOS)  DESTINATION="generic/platform=visionOS Simulator" ;;
    *)         echo "  ✗ Unknown SWIFT_HOOK_PLATFORM: $PLATFORM"; exit 1 ;;
esac

# ─── Stage 1: Detect project type ─────────────────────────────────────────
HAS_PACKAGE_SWIFT=false
HAS_XCWORKSPACE=false
HAS_XCODEPROJ=false
[ -f Package.swift ]                  && HAS_PACKAGE_SWIFT=true
ls *.xcworkspace >/dev/null 2>&1      && HAS_XCWORKSPACE=true
ls *.xcodeproj   >/dev/null 2>&1      && HAS_XCODEPROJ=true

# ─── Stage 2: Package-graph sanity check (xcodeproj only) ────────────────
if [ "$HAS_XCODEPROJ" = "true" ] && [ -f project.yml ]; then
    MISSING_PKGS=()
    while IFS= read -r pkg_path; do
        if [ -n "$pkg_path" ] && [ ! -d "$pkg_path" ]; then
            MISSING_PKGS+=("$pkg_path")
        fi
    done < <(grep -E "^\s*path:\s*Packages/" project.yml | sed 's/.*path:[[:space:]]*//' | tr -d '"' | sort -u)

    if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
        echo "  ⚠ Typecheck skipped: missing local package(s):"
        printf "      %s\n" "${MISSING_PKGS[@]}"
        echo "      Restore via SPM resolve, then retry."
        exit 0  # Graceful skip — graph drift is not a hook failure
    fi
fi

# ─── Stage 3: Run typecheck per project type ─────────────────────────────
LOG_FILE="$(mktemp /tmp/swift-typecheck.XXXXXX.log)"
trap 'rm -f "$LOG_FILE"' EXIT

if [ "$HAS_PACKAGE_SWIFT" = "true" ] && [ "$HAS_XCWORKSPACE" = "false" ] && [ "$HAS_XCODEPROJ" = "false" ]; then
    # Pure SPM — fastest path; host-platform only
    if [ "$PLATFORM" != "macOS" ]; then
        echo "  ⚠ SPM typecheck on $PLATFORM requires xcodebuild (swift build --triple is unsupported for Apple non-host)."
        echo "    Add a dummy .xcodeproj or use the package's Xcode-generated scheme."
        exit 0
    fi
    if ! swift build --build-tests=false > "$LOG_FILE" 2>&1; then
        echo ""
        echo "  ✗ swift build failed:"
        grep -E "error:|warning:" "$LOG_FILE" | head -30 | sed 's/^/    /'
        echo "    Full log: $LOG_FILE (preserved on failure)"
        trap - EXIT
        exit 1
    fi
elif [ "$HAS_XCWORKSPACE" = "true" ] || [ "$HAS_XCODEPROJ" = "true" ]; then
    # Xcode project / workspace
    if [ -z "$SCHEME" ]; then
        # Auto-detect first scheme if not set
        if [ "$HAS_XCWORKSPACE" = "true" ]; then
            WS=$(ls *.xcworkspace | head -1)
            SCHEME=$(xcodebuild -list -workspace "$WS" -json 2>/dev/null | grep -m1 '"name"' | sed -E 's/.*"name" : "([^"]+)".*/\1/' || true)
        else
            PRJ=$(ls *.xcodeproj | head -1)
            SCHEME=$(xcodebuild -list -project "$PRJ" -json 2>/dev/null | grep -m1 '"name"' | sed -E 's/.*"name" : "([^"]+)".*/\1/' || true)
        fi
        [ -z "$SCHEME" ] && { echo "  ✗ Could not auto-detect scheme; set SWIFT_HOOK_SCHEME=YourScheme"; exit 1; }
    fi

    XCODEBUILD_ARGS=(
        build
        -scheme "$SCHEME"
        -destination "$DESTINATION"
        -configuration Debug
        -derivedDataPath "$DERIVED_DATA"
        -clonedSourcePackagesDirPath "$SPM_CACHE"
        -parallelizeTargets
        -skipMacroValidation
        -skipPackagePluginValidation
        ONLY_ACTIVE_ARCH=YES
        CODE_SIGNING_ALLOWED=NO
        CODE_SIGNING_REQUIRED=NO
        -quiet
    )

    if [ "$HAS_XCWORKSPACE" = "true" ]; then
        WS=$(ls *.xcworkspace | head -1)
        XCODEBUILD_ARGS=(-workspace "$WS" "${XCODEBUILD_ARGS[@]}")
    elif [ -n "$PROJECT" ]; then
        XCODEBUILD_ARGS=(-project "$PROJECT" "${XCODEBUILD_ARGS[@]}")
    fi

    if ! xcodebuild "${XCODEBUILD_ARGS[@]}" > "$LOG_FILE" 2>&1; then
        echo ""
        echo "  ✗ xcodebuild typecheck failed (platform=$PLATFORM, scheme=$SCHEME):"
        grep -E ":\s*(error|warning):" "$LOG_FILE" | head -30 | sed 's/^/    /'
        echo "    Full log: $LOG_FILE (preserved on failure)"
        trap - EXIT
        exit 1
    fi
else
    echo "  ⚠ No Package.swift / *.xcodeproj / *.xcworkspace found — skipping typecheck"
    exit 0
fi

echo "  ✓ Swift typecheck passed ($PLATFORM)"
exit 0

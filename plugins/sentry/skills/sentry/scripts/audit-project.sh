#!/usr/bin/env bash
set -euo pipefail

# Automated Sentry Feature Audit Scanner
# Evaluates project adoption across the 4 Sentry Feature Pillars.

TARGET_DIR="${1:-.}"

echo "========================================================="
echo "   Sentry Deep Feature Audit: ${TARGET_DIR}"
echo "========================================================="

check_feature() {
  local name="$1"
  local pattern="$2"
  local pillar="$3"
  
  if grep -rqE "${pattern}" "${TARGET_DIR}/src" "${TARGET_DIR}/app" "${TARGET_DIR}/pages" "${TARGET_DIR}/package.json" 2>/dev/null; then
    printf "  [✅ PRESENT] %-30s (%s)\n" "${name}" "${pillar}"
    return 0
  else
    printf "  [⚠️ MISSING] %-30s (%s)\n" "${name}" "${pillar}"
    return 1
  fi
}

echo ""
echo "--- Pillar 1: Core Error Tracking & Resolution ---"
check_feature "Exception Capture" "(captureException|registerProcessErrorHandlers|uncaughtException)" "Error Tracking" || true
check_feature "Sourcemaps Pipeline" "(sourceMap|sourcemap|sourcemaps upload)" "Error Tracking" || true
check_feature "Custom Fingerprinting" "(setFingerprint|fingerprint)" "Error Tracking" || true
check_feature "Inbound Filtering" "(beforeSend.*return null|inbound-filters)" "Error Tracking" || true

echo ""
echo "--- Pillar 2: Contextual Breadcrumbs & Environment ---"
check_feature "System Breadcrumbs" "(addBreadcrumb.*category:\s*['\"](http|db|cache))" "Breadcrumbs" || true
check_feature "UI Breadcrumbs" "(breadcrumbsIntegration|recordUiAction)" "Breadcrumbs" || true
check_feature "Custom Tags" "(setTag|tags:\s*\{)" "Breadcrumbs" || true
check_feature "User Feedback" "(captureFeedback|showReportDialog)" "Breadcrumbs" || true
check_feature "Device Context" "(setContext.*(device|runtime|os))" "Breadcrumbs" || true

echo ""
echo "--- Pillar 3: Log Management & Analytics ---"
check_feature "Structured Logs" "(Sentry\.logger|pino-transport|winston-transport)" "Logging" || true
check_feature "Pin-to-Top Logs" "(pinned:\s*['\"]true['\"]|severity:\s*['\"]critical['\"])" "Logging" || true

echo ""
echo "--- Pillar 4: Performance, Tracing & Replay ---"
check_feature "Distributed Tracing" "(startSpan|startTransaction|sentry-trace)" "Performance" || true
check_feature "AsyncLocalStorage" "(AsyncLocalStorage|withContext)" "Performance" || true
check_feature "Session Replay" "(replayIntegration|replaysSessionSampleRate)" "Performance" || true
check_feature "Cron Monitors" "(withMonitor|check-ins)" "Performance" || true

echo ""
echo "--- Network & Security Resilience ---"
check_feature "Envelope Tunneling" "(tunnel:\s*|/envelope/)" "Network" || true
check_feature "Credential Redaction" "(redact|Filtered|beforeBreadcrumb)" "Security" || true
check_feature "Offline Isolation Gate" "(!dsn|offline.*gate|isSentryInitialized)" "Testing" || true

echo ""
echo "========================================================="
echo "Audit complete. Review 'references/modes/mode-2-audit.md' for gap remediation."
echo "========================================================="

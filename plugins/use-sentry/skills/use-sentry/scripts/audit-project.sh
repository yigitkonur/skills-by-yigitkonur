#!/usr/bin/env bash
set -euo pipefail

# Automated Sentry Feature Audit Scanner
# Evaluates project adoption across the 4 Sentry Feature Pillars.
# Supports multi-lingual codebases: Node/JavaScript/TypeScript, Python, Go.

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: $0 [TARGET_DIR]"
    echo ""
    echo "Automated Sentry Feature Audit Scanner."
    echo "Evaluates project adoption across the 4 Sentry Feature Pillars."
    echo "Supports JavaScript/TypeScript, Python, and Go codebases."
    echo ""
    echo "Arguments:"
    echo "  TARGET_DIR   Directory of the project to audit (default: .)"
    echo "  -h, --help   Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 ."
    echo "  $0 /path/to/my-python-service"
    exit 0
  fi
done

TARGET_DIR="${1:-.}"

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "❌ Error: Directory '${TARGET_DIR}' does not exist."
  exit 1
fi

echo "========================================================="
echo "   Sentry Deep Feature Audit: ${TARGET_DIR}"
echo "========================================================="

# Detect project ecosystems
DETECTED_ECOSYSTEMS=()
if [[ -f "${TARGET_DIR}/package.json" || -f "${TARGET_DIR}/tsconfig.json" || -f "${TARGET_DIR}/jsconfig.json" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name dist -o -name build \) -prune -o \( -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" -o -name "*.mjs" -o -name "*.cjs" \) -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Node/JavaScript/TypeScript")
fi
if [[ -f "${TARGET_DIR}/pyproject.toml" || -f "${TARGET_DIR}/requirements.txt" || -f "${TARGET_DIR}/Pipfile" || -f "${TARGET_DIR}/setup.py" || -f "${TARGET_DIR}/setup.cfg" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name __pycache__ \) -prune -o -name "*.py" -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Python")
fi
if [[ -f "${TARGET_DIR}/go.mod" || -f "${TARGET_DIR}/go.sum" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name node_modules -o -name .git -o -name vendor \) -prune -o -name "*.go" -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Go")
fi

if [[ ${#DETECTED_ECOSYSTEMS[@]} -gt 0 ]]; then
  echo "Detected Ecosystem: $(IFS=', '; echo "${DETECTED_ECOSYSTEMS[*]}")"
else
  echo "Detected Ecosystem: Generic / Polyglot"
fi

check_feature() {
  local name="$1"
  local pattern="$2"
  local pillar="$3"

  # Recursively search the target directory, excluding noise directories and build artifacts
  if grep -rIqE \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=dist \
    --exclude-dir=build \
    --exclude-dir=.next \
    --exclude-dir=__pycache__ \
    --exclude-dir=.turbo \
    --exclude-dir=.svelte-kit \
    --exclude-dir=vendor \
    --exclude-dir=.agents \
    --exclude="*.log" \
    --exclude="*.lock" \
    --exclude="*-lock.json" \
    --exclude="package-lock.json" \
    "${pattern}" "${TARGET_DIR}" 2>/dev/null; then
    printf "  [✅ PRESENT] %-30s (%s)\n" "${name}" "${pillar}"
    return 0
  else
    printf "  [⚠️ MISSING] %-30s (%s)\n" "${name}" "${pillar}"
    return 1
  fi
}

echo ""
echo "--- Pillar 1: Core Error Tracking & Resolution ---"
check_feature "Exception Capture" "(captureException|capture_exception|CaptureException|registerProcessErrorHandlers|uncaughtException|sentry\.CaptureMessage|capture_message)" "Error Tracking" || true
check_feature "Sourcemaps Pipeline" "(sourceMap|sourcemap|sourcemaps upload|sentry-cli sourcemaps|upload-sourcemaps|upload-dif)" "Error Tracking" || true
check_feature "Custom Fingerprinting" "(setFingerprint|set_fingerprint|SetFingerprint|fingerprint|Fingerprint)" "Error Tracking" || true
check_feature "Inbound Filtering" "(beforeSend|before_send|BeforeSend|inbound-filters|ignoreErrors|ignore_errors|IgnoreErrors|before_send_transaction|beforeSendTransaction)" "Error Tracking" || true

echo ""
echo "--- Pillar 2: Contextual Breadcrumbs & Environment ---"
check_feature "System Breadcrumbs" "(addBreadcrumb|add_breadcrumb|AddBreadcrumb)" "Breadcrumbs" || true
check_feature "UI Breadcrumbs" "(breadcrumbsIntegration|recordUiAction|breadcrumbs|Breadcrumbs)" "Breadcrumbs" || true
check_feature "Custom Tags" "(setTag|set_tag|SetTag|tags:\s*\{|tags=\s*\{|set_tags|setTags|SetTags)" "Breadcrumbs" || true
check_feature "User Feedback" "(captureFeedback|capture_feedback|CaptureFeedback|showReportDialog)" "Breadcrumbs" || true
check_feature "Device Context" "(setContext|set_context|SetContext)" "Breadcrumbs" || true

echo ""
echo "--- Pillar 3: Log Management & Analytics ---"
check_feature "Structured Logs" "(Sentry\.logger|sentry_sdk\.integrations\.logging|LoggingIntegration|winston-transport|pino-sentry|sentry\.NewHub)" "Logging" || true
check_feature "Pin-to-Top Logs" "(severity:\s*['\"]critical['\"]|fatal_assertion|critical_failure|severity.*critical)" "Logging" || true

echo ""
echo "--- Pillar 4: Performance, Tracing & Replay ---"
check_feature "Distributed Tracing" "(startSpan|startTransaction|start_span|start_transaction|StartSpan|sentry-trace|traces_sample_rate|tracesSampleRate|TracesSampleRate)" "Performance" || true
check_feature "AsyncLocalStorage" "(AsyncLocalStorage|withContext|withScope|with_scope|WithScope|isolation_scope|new_scope|ConfigureScope|configure_scope)" "Performance" || true
check_feature "Session Replay" "(replayIntegration|replaysSessionSampleRate|replaysOnErrorSampleRate|replays_session_sample_rate)" "Performance" || true
check_feature "Cron Monitors" "(withMonitor|with_monitor|monitor\(|check-ins|capture_checkin|captureCheckIn|CaptureCheckIn|crons?\.monitor)" "Performance" || true

echo ""
echo "--- Network & Security Resilience ---"
check_feature "Envelope Tunneling" "(tunnel:\s*|tunnelRoute|/envelope/|tunnel=)" "Network" || true
check_feature "Credential Redaction" "(redact|Filtered|beforeBreadcrumb|before_breadcrumb|BeforeBreadcrumb)" "Security" || true
check_feature "Offline Isolation Gate" "(!dsn|offline.*gate|getClient|dsn=None|dsn=\"\"|DSN == \"\"|dsn:\s*['\"]['\"]|enabled:\s*false|enabled=\s*False)" "Testing" || true

echo ""
echo "========================================================="
echo "Audit complete. Review 'references/modes/mode-2-audit.md' for gap remediation."
echo "========================================================="

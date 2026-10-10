#!/usr/bin/env bash
set -euo pipefail

# Automated Sentry Feature Audit Scanner
# Evaluates project adoption across Enterprise Sentry Observability Pillars.
# Supports multi-lingual codebases: JavaScript/TypeScript, Python, Go, Swift/Apple.

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: $0 [TARGET_DIR]"
    echo ""
    echo "Automated Sentry Feature Audit Scanner."
    echo "Evaluates project adoption across Enterprise Sentry Observability Pillars."
    echo "Supports JavaScript/TypeScript, Python, Go, and Swift/Apple codebases."
    echo ""
    echo "Arguments:"
    echo "  TARGET_DIR   Directory of the project to audit (default: .)"
    echo "  -h, --help   Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 ."
    echo "  $0 /path/to/my-service"
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
if [[ -f "${TARGET_DIR}/wrangler.jsonc" || -f "${TARGET_DIR}/wrangler.json" || -f "${TARGET_DIR}/wrangler.toml" ]] || grep -rq "@sentry/cloudflare" "${TARGET_DIR}/package.json" 2>/dev/null; then
  DETECTED_ECOSYSTEMS+=("Cloudflare Workers/Pages")
fi
if [[ -f "${TARGET_DIR}/app.json" || -f "${TARGET_DIR}/app.config.ts" || -f "${TARGET_DIR}/app.config.js" ]] || grep -rqE "(\"expo\"|@sentry/react-native)" "${TARGET_DIR}/package.json" 2>/dev/null; then
  DETECTED_ECOSYSTEMS+=("Expo/React Native")
fi
if [[ -f "${TARGET_DIR}/pyproject.toml" || -f "${TARGET_DIR}/requirements.txt" || -f "${TARGET_DIR}/Pipfile" || -f "${TARGET_DIR}/setup.py" || -f "${TARGET_DIR}/setup.cfg" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name node_modules -o -name .git -o -name .venv -o -name venv -o -name __pycache__ \) -prune -o -name "*.py" -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Python")
fi
if [[ -f "${TARGET_DIR}/go.mod" || -f "${TARGET_DIR}/go.sum" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name node_modules -o -name .git -o -name vendor \) -prune -o -name "*.go" -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Go")
fi
if [[ -f "${TARGET_DIR}/Package.swift" ]] || find "${TARGET_DIR}" -maxdepth 3 \( -name .build -o -name .git -o -name DerivedData \) -prune -o \( -name "*.swift" -o -name "*.xcodeproj" -o -name "*.xcworkspace" \) -print 2>/dev/null | grep -q .; then
  DETECTED_ECOSYSTEMS+=("Swift/Apple")
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
    --exclude-dir=.build \
    --exclude-dir=DerivedData \
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
    printf "  [✅ PRESENT] %-32s (%s)\n" "${name}" "${pillar}"
    return 0
  else
    printf "  [⚠️ MISSING] %-32s (%s)\n" "${name}" "${pillar}"
    return 1
  fi
}

echo ""
echo "--- Core Error Tracking & Grouping ---"
check_feature "Exception Capture" "(captureException|capture_exception|CaptureException|uncaughtException|sentry\.CaptureMessage|capture_message|SentrySDK\.capture|withSentry|sentryCloudflareVitePlugin)" "Error Tracking" || true
check_feature "Sourcemaps / Debug IDs" "(sourceMap|sourcemap|sourcemaps inject|sourcemaps upload|sentry-cli debug-files|sentryVitePlugin|sentryWebpackPlugin|upload_source_maps)" "Error Tracking" || true
check_feature "Custom Fingerprinting" "(setFingerprint|set_fingerprint|SetFingerprint|fingerprint|Fingerprint)" "Error Tracking" || true
check_feature "Inbound Filtering" "(beforeSend|before_send|BeforeSend|inbound-filters|ignoreErrors|ignore_errors|IgnoreErrors|before_send_transaction|beforeSendTransaction)" "Error Tracking" || true

echo ""
echo "--- Contextual Breadcrumbs & Environment ---"
check_feature "System Breadcrumbs" "(addBreadcrumb|add_breadcrumb|AddBreadcrumb|SentrySDK\.addBreadcrumb)" "Breadcrumbs" || true
check_feature "UI Breadcrumbs" "(breadcrumbsIntegration|recordUiAction|breadcrumbs|Breadcrumbs|enableUserInteractionTracing)" "Breadcrumbs" || true
check_feature "Custom Tags" "(setTag|set_tag|SetTag|tags:\s*\{|tags=\s*\{|set_tags|setTags|SetTags)" "Breadcrumbs" || true
check_feature "User Feedback" "(feedbackIntegration|captureFeedback|capture_feedback|CaptureFeedback|showReportDialog)" "Breadcrumbs" || true
check_feature "Device Context" "(setContext|set_context|SetContext)" "Breadcrumbs" || true

echo ""
echo "--- Logging & Structured Analytics ---"
check_feature "Structured Logs" "(Sentry\.logger|pinoIntegration|sentry_sdk\.integrations\.logging|LoggingIntegration|winston-transport|pino-sentry|sentry\.NewHub)" "Logging" || true
check_feature "Pin-to-Top Logs" "(severity:\s*['\"]critical['\"]|fatal_assertion|critical_failure|severity.*critical)" "Logging" || true

echo ""
echo "--- Distributed Tracing & Profiling ---"
check_feature "Distributed Tracing" "(startSpan|startTransaction|start_span|start_transaction|StartSpan|sentry-trace|traces_sample_rate|tracesSampleRate|TracesSampleRate|rpcTracePropagationBindings)" "Performance" || true
check_feature "Continuous Profiling" "(profilesSampleRate|profiles_sample_rate|profileSessionSampleRate|profiling-node|ContinuousProfiling)" "Performance" || true
check_feature "Cron Monitors" "(withMonitor|with_monitor|monitor\(|check-ins|capture_checkin|captureCheckIn|CaptureCheckIn|crons?\.monitor)" "Performance" || true
check_feature "Application Metrics" "(metrics\.count|metrics\.gauge|metrics\.distribution|metrics\.set|sentry_sdk\.metrics|setMeasurement)" "Performance" || true

echo ""
echo "--- Privacy, Replay & Local Dev ---"
check_feature "Session Replay" "(replayIntegration|mobileReplayIntegration|replaysSessionSampleRate|replaysOnErrorSampleRate|sessionReplay)" "Replay" || true
check_feature "Credential Redaction" "(redact|Filtered|beforeBreadcrumb|before_breadcrumb|BeforeBreadcrumb|maskAllText)" "Security" || true
check_feature "Spotlight Local Dev" "(spotlight:\s*|spotlight=True|spotlight\.init)" "Dev Tools" || true

echo ""
echo "--- AI, LLM & MCP Observability ---"
check_feature "AI / LLM Monitoring" "(openAiIntegration|anthropicIntegration|OpenAIIntegration|AnthropicIntegration|LangchainIntegration|gen_ai|instrumentAgentWithSentry)" "AI/LLM" || true
check_feature "MCP Server Telemetry" "(McpServer|StdioServerTransport|sentry_sdk\.integrations\.mcp|mcp\.tool|mcpServerIntegration|registerTool)" "MCP" || true

echo ""
echo "--- Apple / Native Diagnostics ---"
check_feature "App Hang Tracking" "(enableAppHangTracking|appHangTimeoutInterval)" "Apple Native" || true
check_feature "MetricKit Integration" "(enableMetricKit|MXDiagnosticPayload)" "Apple Native" || true
check_feature "Watchdog OOM Tracking" "(enableWatchdogTerminationTracking)" "Apple Native" || true
check_feature "SwiftUI View Tracing" "(sentryTrace|SentryTracedView|reportFullyDisplayed)" "Apple Native" || true

echo ""
echo "--- Mobile & Edge Frameworks ---"
check_feature "Expo Config Plugin" "(@sentry/react-native/expo|withSentry)" "Expo Mobile" || true
check_feature "Expo Metro Serializer" "(getSentryExpoConfig)" "Expo Mobile" || true
check_feature "Expo Router Tracing" "(expoRouterIntegration|reactNavigationIntegration)" "Expo Mobile" || true
check_feature "Mobile Session Replay" "(mobileReplayIntegration|maskAllImages|maskAllVectors)" "Expo Mobile" || true
check_feature "Cloudflare Worker Instrumentation" "(sentryCloudflareVitePlugin|instrumentDurableObjectWithSentry|instrumentWorkflowWithSentry)" "Cloudflare" || true

echo ""
echo "--- Network & Resilience ---"
check_feature "Envelope Tunneling" "(tunnel:\s*|tunnelRoute|/envelope/|tunnel=)" "Network" || true
check_feature "Offline Isolation Gate" "(!dsn|offline.*gate|getClient|dsn=None|dsn=\"\"|DSN == \"\"|dsn:\s*['\"]['\"]|enabled:\s*false|enabled=\s*False)" "Testing" || true

echo ""
echo "========================================================="
echo "Audit complete. Review 'references/modes/mode-2-audit.md' for gap remediation."
echo "========================================================="

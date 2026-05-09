#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage:
  audit-cli.sh [--json-flag FLAG|none] [--timeout SECONDS] -- <command> [args...]

Runs a conservative agent-readiness preflight for a safe CLI probe command.
It checks help availability, non-interactive completion, stdout JSON parseability,
stderr separation, ANSI noise, and semantic-looking exit behavior.

Examples:
  audit-cli.sh -- mycli list
  audit-cli.sh --json-flag --output=json -- mycli list projects
  audit-cli.sh --json-flag none -- /bin/echo '{"ok":true,"schema_version":"1"}'
USAGE
}

json_flag="--json"
timeout_seconds=10

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json-flag)
      [[ $# -ge 2 ]] || { echo "missing value for --json-flag" >&2; exit 2; }
      json_flag="$2"
      shift 2
      ;;
    --timeout)
      [[ $# -ge 2 ]] || { echo "missing value for --timeout" >&2; exit 2; }
      timeout_seconds="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

cmd=("$@")
probe=("$@")
if [[ "$json_flag" != "none" ]]; then
  probe+=("$json_flag")
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

run_with_timeout() {
  local stdout_file="$1"
  local stderr_file="$2"
  shift 2

  if command -v timeout >/dev/null 2>&1; then
    NO_COLOR=1 TERM=dumb timeout "$timeout_seconds" "$@" >"$stdout_file" 2>"$stderr_file"
    return $?
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    NO_COLOR=1 TERM=dumb gtimeout "$timeout_seconds" "$@" >"$stdout_file" 2>"$stderr_file"
    return $?
  fi

  NO_COLOR=1 TERM=dumb "$@" >"$stdout_file" 2>"$stderr_file"
}

json_valid() {
  local file="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -e . "$file" >/dev/null 2>&1
    return $?
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -m json.tool "$file" >/dev/null 2>&1
    return $?
  fi
  return 2
}

has_ansi() {
  LC_ALL=C grep -q "$(printf '\033')" "$1" 2>/dev/null
}

help_out="$tmpdir/help.out"
help_err="$tmpdir/help.err"
probe_out="$tmpdir/probe.out"
probe_err="$tmpdir/probe.err"

"${cmd[0]}" --help >"$help_out" 2>"$help_err"
help_code=$?

run_with_timeout "$probe_out" "$probe_err" "${probe[@]}"
probe_code=$?

json_status="fail"
if [[ -s "$probe_out" ]]; then
  if json_valid "$probe_out"; then
    json_status="pass"
  else
    json_status="fail"
  fi
else
  json_status="empty"
fi

ansi_status="pass"
if has_ansi "$probe_out"; then
  ansi_status="fail"
fi

stderr_json_status="pass"
if [[ -s "$probe_err" ]] && json_valid "$probe_err"; then
  stderr_json_status="warn"
fi

exit_status="pass"
if [[ "$probe_code" -eq 124 || "$probe_code" -eq 137 ]]; then
  exit_status="timeout"
elif [[ "$probe_code" -lt 0 || "$probe_code" -gt 7 ]]; then
  exit_status="warn"
fi

cat <<REPORT
# CLI Agent-Readiness Preflight

Target: ${cmd[*]}
Probe: ${probe[*]}

| Check | Result | Evidence |
|---|---|---|
| help available | $([[ "$help_code" -eq 0 ]] && echo pass || echo warn) | exit=$help_code |
| probe completes | $([[ "$probe_code" -ne 124 && "$probe_code" -ne 137 ]] && echo pass || echo fail) | exit=$probe_code |
| stdout JSON | $json_status | bytes=$(wc -c <"$probe_out" | tr -d ' ') |
| stderr separation | $stderr_json_status | stderr_bytes=$(wc -c <"$probe_err" | tr -d ' ') |
| ANSI-free stdout | $ansi_status | NO_COLOR=1 TERM=dumb |
| exit code class | $exit_status | expected taxonomy is 0-7 |

Limitations: this preflight exercises one safe command only. It does not prove destructive commands, auth flows, retries, or all subcommands are agent-ready.
REPORT

if [[ "$json_status" == "pass" && "$ansi_status" == "pass" && "$exit_status" != "timeout" ]]; then
  exit 0
fi
exit 1

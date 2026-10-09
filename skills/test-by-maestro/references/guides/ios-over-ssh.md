# Remote iOS Simulator Testing over SSH

Executing iOS Simulator tests from a Linux or headless authoring host requires orchestrating commands over SSH to a macOS runner machine with Xcode. Linux cannot drive iOS Simulators directly.

## Remote Execution Topology

```text
┌────────────────────────┐         SSH         ┌────────────────────────┐
│ Linux Authoring Host   │ ──────────────────▶ │ macOS Execution Host   │
│ (Test Runner / CI)     │                     │ (Xcode + Simulator)    │
│                        │                     │                        │
│ 1. Workspace tarball   │ ── tar transport ─▶ │ 1. Unique run root     │
│ 2. Preflight & syntax  │ ── remote probe ──▶ │ 2. Host driver lease   │
│ 3. Execution trigger   │ ── bash script ───▶ │ 3. Maestro CLI test    │
│ 4. Artifact collection │ ◀─ tar retrieve ─── │ 4. Output results tree │
└────────────────────────┘                     └────────────────────────┘
```

In this architecture, SSH transports workspace files, triggers execution, and retrieves test telemetry.

## Core Operational Invariants

### 1. Non-Interactive SSH Environment
Non-interactive SSH commands (`ssh host '...'`) do not load user shell profiles (`.zprofile` or `.zshrc`). If Java 17+ is installed in `/opt/homebrew/opt/java`, Maestro will fail with "Unable to locate a Java Runtime" unless `JAVA_HOME` is exported. Every remote invocation must explicitly export required toolchain paths:

```bash
export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/java}"
export PATH="$JAVA_HOME/bin:$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"
```

### 2. Dynamic Simulator Resolution
Never hardcode static UDID strings or use fragile grep matches. Query Simulator status directly via `xcrun simctl` JSON output and verify that exactly one booted, available simulator matches criteria:

```python
import json, subprocess
raw = subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json'], text=True)
devices = [d for g in json.loads(raw)['devices'].values() for d in g
           if d.get('isAvailable') and d.get('state') == 'Booted']
assert len(devices) == 1, 'Require exactly one booted available simulator'
target_udid = devices[0]['udid']
```

### 3. Coordinated Host-Wide Driver Lease
Maestro runs an XCUITest runner (`dev.mobile.maestro-driver-iosUITests.xctrunner`) with a Swift `FlyingFox` HTTP server (fallback port 22087, or ephemeral dynamic port passed via `SIMCTL_CHILD_PORT`). Multiple concurrent OS processes on the same host targeting the same simulator will collide and preempt each other's test sessions. Implement an atomic filesystem mutex using `mkdir` with parent directory creation, stale lock recovery, and clean signal exit codes:

```bash
lock="$HOME/.cache/test-by-maestro/driver.lock"
mkdir -p "$(dirname "$lock")"
acquired=0
for _ in 1 2; do
  if mkdir "$lock" 2>/dev/null; then
    acquired=1
    break
  fi
  owner_pid=""
  owner_udid=""
  if [ -f "$lock/owner" ]; then
    read -r owner_pid owner_udid < "$lock/owner" || true
  fi
  if [ -z "${owner_pid:-}" ] || ! kill -0 "$owner_pid" 2>/dev/null; then
    printf 'Removing stale driver lease from dead PID %s (device %s)\n' "${owner_pid:-none}" "${owner_udid:-unknown}" >&2
    rm -f "$lock/owner"
    rmdir "$lock" 2>/dev/null || true
    continue
  fi
  printf 'Driver lease busy: held by active PID %s on %s\n' "$owner_pid" "${owner_udid:-unknown}" >&2
  exit 75
done
if [ "$acquired" -ne 1 ]; then
  printf 'Driver lease busy\n' >&2
  exit 75
fi
printf '%s %s\n' "$$" "${udid:-${target_udid:-unknown}}" > "$lock/owner"
trap 'rc=$?; rm -f "$lock/owner"; rmdir "$lock" || true; exit "$rc"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
```

### 4. Full Workspace Transfer
Maestro tests often rely on modular subflows, JavaScript helpers, and configuration files. Transfer the entire workspace directory rather than a single YAML file, ensuring all relative paths remain valid.

### 5. Deterministic Artifact Retrieval
Even when a test fails, execution artifacts (console logs, JUnit XML, screenshots) must be retrieved to the authoring host before reporting failure.

## Complete Remote Execution Recipe

The following recipe implements workspace validation, dynamic discovery, exclusive locking, execution, and artifact retrieval:

```bash
# Caller sets: HOST, WORKSPACE (absolute), FLOW (relative), ARTIFACTS (local destination)
# Optional: TARGET_UDID, DEVICE_NAME, MODE (syntax or test), OWNERSHIP_CONFIRMED
set -euo pipefail
MODE=${MODE:-syntax}
TARGET_UDID=${TARGET_UDID:-}
DEVICE_NAME=${DEVICE_NAME:-}
OWNERSHIP_CONFIRMED=${OWNERSHIP_CONFIRMED:-unconfirmed}
shq() { python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$1"; }
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST")

# 1. Local workspace preflight validation
python3 - "$HOST" "$WORKSPACE" "$FLOW" "$MODE" <<'PY'
import pathlib, re, sys
host, workspace, flow, mode = sys.argv[1:]
assert re.fullmatch(r'[A-Za-z0-9_.@-]+', host) and not host.startswith('-')
root = pathlib.Path(workspace).resolve(strict=True)
p = pathlib.PurePosixPath(flow)
assert pathlib.Path(workspace).is_absolute() and root.is_dir()
assert not p.is_absolute() and '..' not in p.parts and mode in ('syntax', 'test')
assert (root / flow).resolve(strict=True).is_relative_to(root)
for f in root.rglob('*'):
    if f.is_symlink():
        raise AssertionError('Workspace must not contain symlinks: ' + str(f))
PY

# 2. Remote toolchain preflight
"${SSH[@]}" 'export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/java}"; export PATH="$JAVA_HOME/bin:$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"; export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"; command -v maestro; java -version; maestro --version; maestro test --help'

# 3. Dynamic device resolution (test mode only)
if [ "$MODE" = test ]; then
  TARGET_UDID=$(python3 - "$HOST" "$TARGET_UDID" "$DEVICE_NAME" <<'PY'
import json, subprocess, sys
host, wanted, name = sys.argv[1:]
cmd = 'export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"; xcrun simctl list devices --json'
raw = subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host, cmd], text=True)
devices = [d for group in json.loads(raw)['devices'].values() for d in group
           if d.get('isAvailable') and d.get('state') == 'Booted']
matches = [d for d in devices if (not wanted or d['udid'] == wanted) and (not name or d['name'] == name)]
if len(matches) != 1:
    print('Require exactly one booted target: ' + json.dumps(devices), file=sys.stderr)
    sys.exit(1)
print(matches[0]['udid'])
PY
  )
fi

# 4. Staged workspace transfer
RDIR=$("${SSH[@]}" 'umask 077; mkdir -p "$HOME/.cache/test-by-maestro/runs"; mktemp -d "$HOME/.cache/test-by-maestro/runs/run-XXXXXXXX"')
test -n "$RDIR"
"${SSH[@]}" "mkdir -p $(shq "$RDIR/workspace") $(shq "$RDIR/results")"
tar -C "$WORKSPACE" -cf - . | "${SSH[@]}" "tar -xf - -C $(shq "$RDIR/workspace")"

# 5. Remote test execution body
REMOTE_BODY=$(cat <<'SH'
set -euo pipefail
run=$1; flow=$2; udid=$3; mode=$4; ownership=$5
export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/java}"
export PATH="$JAVA_HOME/bin:$HOME/.maestro/bin:/opt/homebrew/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-$(xcode-select -p)}"

if [ "$mode" = test ]; then
  test "$ownership" = confirmed || { printf 'Operator ownership unconfirmed\n' >&2; exit 75; }
  lock="$HOME/.cache/test-by-maestro/driver.lock"
  mkdir -p "$(dirname "$lock")"
  acquired=0
  for _ in 1 2; do
    if mkdir "$lock" 2>/dev/null; then
      acquired=1
      break
    fi
    owner_pid=""
    owner_udid=""
    if [ -f "$lock/owner" ]; then
      read -r owner_pid owner_udid < "$lock/owner" || true
    fi
    if [ -z "${owner_pid:-}" ] || ! kill -0 "$owner_pid" 2>/dev/null; then
      printf 'Removing stale driver lease from dead PID %s (device %s)\n' "${owner_pid:-none}" "${owner_udid:-unknown}" >&2
      rm -f "$lock/owner"
      rmdir "$lock" 2>/dev/null || true
      continue
    fi
    printf 'Driver lease busy: held by active PID %s on %s\n' "$owner_pid" "${owner_udid:-unknown}" >&2
    exit 75
  done
  if [ "$acquired" -ne 1 ]; then
    printf 'Driver lease busy\n' >&2
    exit 75
  fi
  printf '%s %s\n' "$$" "$udid" > "$lock/owner"
  trap 'rc=$?; rm -f "$lock/owner"; rmdir "$lock" || true; exit "$rc"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  python3 - "$udid" <<'PY'
import json, pathlib, subprocess, sys
udid = sys.argv[1]
raw = subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '--json'], text=True)
targets = [d for group in json.loads(raw)['devices'].values() for d in group
           if d.get('udid') == udid and d.get('isAvailable') and d.get('state') == 'Booted']
assert len(targets) == 1, 'Target simulator is no longer uniquely booted'

rows = subprocess.check_output(['ps', '-axo', 'pid=,comm=,args='], text=True).splitlines()
conflicts = []
for row in rows:
    fields = row.strip().split(None, 2)
    if len(fields) != 3: continue
    pid, comm, args = fields
    binary = pathlib.Path(comm).name.lower()
    if 'maestro' in args.lower() and ('java' in binary or 'maestro' in binary or 'xctest' in binary):
        conflicts.append(pid + ' ' + comm)
assert not conflicts, 'Active conflicting driver process: ' + ', '.join(conflicts)
PY
fi

cd "$run/workspace"
set +e
if [ "$mode" = syntax ]; then
  maestro check-syntax "$flow" > "$run/results/console.log" 2>&1
else
  maestro --udid "$udid" test "$flow" --test-output-dir "$run/results" \
    --format JUNIT --output "$run/results/junit.xml" > "$run/results/console.log" 2>&1
fi
rc=$?
set -e
printf '%s\n' "$rc" > "$run/results/exit-status.txt"
exit "$rc"
SH
)

run_status=0
"${SSH[@]}" "bash -c $(shq "$REMOTE_BODY") -- $(shq "$RDIR") $(shq "$FLOW") $(shq "$TARGET_UDID") $(shq "$MODE") $(shq "$OWNERSHIP_CONFIRMED")" || run_status=$?

# 6. Artifact retrieval and exit status handling
mkdir -p "$ARTIFACTS"
copy_status=0
"${SSH[@]}" "tar -C $(shq "$RDIR/results") -cf - ." | tar -xf - -C "$ARTIFACTS" || copy_status=$?
printf 'execution=%s retrieval=%s artifacts=%s\n' "$run_status" "$copy_status" "$ARTIFACTS"
test "$copy_status" -eq 0 || exit "$copy_status"
exit "$run_status"
```

## Related References

- [CLI and Artifacts](../commands/cli-and-artifacts.md) — Artifact inspection and reporting options.
- [Android and Local iOS](android-and-local-ios.md) — Local simulator and Android testing alternatives.
- [Suites and CI](../patterns/suites-and-ci.md) — CI execution and tag-based suites.

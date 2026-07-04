#!/usr/bin/env bash
# backends/tart.sh — macOS (and Linux-on-Apple-Silicon) backend via cirruslabs Tart.
# Runs against a REMOTE Tart host so your own Mac stays free: either a spare Apple Silicon
# Mac you SSH into, or an Orchard cluster / managed provider (Cirrus Runners) endpoint.
# Model: `tart clone GOLDEN job` = instant CoW copy (= macOS "checkpoint"), boot, SSH the
# worktree in, run, return exit code, delete the clone.
#
# CLI surface (cirruslabs/tart, well-documented OSS):
#   tart clone SRC DST ; tart run VM --no-graphics ; tart ip VM ; tart stop VM ; tart delete VM
# Apple license caps macOS VMs at 2 per host; Linux VMs unlimited. Pick a host accordingly.
# NOTE: not exercised here (no Tart host in this session) — provision a host, then pilot.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; source "$HERE/lib.sh"

: "${OFFLOAD_TART_HOST:=}"            # e.g. user@build-mac  (empty = local tart)
: "${OFFLOAD_TART_SSH_USER:=admin}"   # SSH user INSIDE the Tart VM (Tart macOS default: admin)
: "${OFFLOAD_WORKDIR:=work}"

# Run a tart CLI command on the host (local or remote).
tcli() { if [ -n "$OFFLOAD_TART_HOST" ]; then ssh "$OFFLOAD_TART_HOST" tart "$@"; else tart "$@"; fi; }

tart_backend() {
  local type="$1" hash="$2" root="$3"; shift 3
  local q; printf -v q '%q ' "$@"   # shell-quote argv for safe re-parse on the remote
  local golden; golden="$(golden_name "$type" "$hash")"
  local vm="offload-job-$$"

  if [ -z "$OFFLOAD_TART_HOST" ]; then
    have tart || die "tart not found and OFFLOAD_TART_HOST unset — install Tart or point at a host"
  fi

  # 1. Ensure a golden image exists (build once if missing).
  if ! tcli list 2>/dev/null | grep -q "$golden"; then
    log "golden image $golden missing — see references/setup.md to build it once"
    die "build golden '$golden' first (packer/tart + deps), then re-run"
  fi

  # 2. Clone the golden (instant CoW = the macOS 'checkpoint') and boot it.
  log "cloning $golden -> $vm"
  tcli clone "$golden" "$vm"
  # shellcheck disable=SC2064
  trap "tcli stop '$vm' >/dev/null 2>&1 || true; tcli delete '$vm' >/dev/null 2>&1 || true" EXIT
  tcli run "$vm" --no-graphics >/dev/null 2>&1 &

  # 3. Wait for the VM's SSH to come up, resolve its IP.
  local ip="" i
  for i in $(seq 1 60); do ip="$(tcli ip "$vm" 2>/dev/null || true)"; [ -n "$ip" ] && break; sleep 2; done
  [ -n "$ip" ] || die "VM $vm never got an IP"
  local vmssh=("ssh" "-o" "StrictHostKeyChecking=no")
  # If the host is remote, hop through it to reach the VM's private IP.
  [ -n "$OFFLOAD_TART_HOST" ] && vmssh+=("-J" "$OFFLOAD_TART_HOST")
  local target="${OFFLOAD_TART_SSH_USER}@${ip}"

  # 4. Sync the worktree into the VM (deps already baked into the golden).
  log "syncing worktree to $target"
  worktree_tar "$root" | "${vmssh[@]}" "$target" \
    "rm -rf $OFFLOAD_WORKDIR && mkdir -p $OFFLOAD_WORKDIR && tar -xzf - -C $OFFLOAD_WORKDIR"

  # 5. Run the command; capture and return its exit code.
  log "running: $*"
  "${vmssh[@]}" "$target" "cd $OFFLOAD_WORKDIR && $q"
}

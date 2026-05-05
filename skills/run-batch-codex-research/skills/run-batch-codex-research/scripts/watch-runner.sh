#!/usr/bin/env bash
# watch-runner.sh — Monitor command for run-batch.sh.
#
# Tails the runner log and emits one event per state transition, augmented
# with the byte size of the corresponding answer file. Designed to be called
# by Claude Code's Monitor tool.
#
# Coverage rule: every terminal state (DONE/FAIL/SKIP) plus START and the
# "all jobs finished" sentinel triggers an event, so silence cannot mask a
# crash or hang. Lines below MIN bytes are flagged with [SMALL].
#
# Usage:
#   watch-runner.sh [LOG] [ANSWERS_DIR] [MIN_BYTES]
#
# Defaults:
#   LOG          logs/_runner.log
#   ANSWERS_DIR  answers
#   MIN_BYTES    10000

set -u
cd "$(dirname "$0")/.."

LOG="${1:-logs/_runner.log}"
ANSWERS="${2:-answers}"
MIN="${3:-10000}"

# Defense-in-depth: ANSWERS is spliced into a shell command inside the awk
# `sizeof` helper, so reject anything outside a strict path charset before
# tailing. A wrapper that passes `answers; rm -rf /` would otherwise execute.
case "$ANSWERS" in
  *[!A-Za-z0-9._/-]*|"")
    echo "watch-runner: ANSWERS must match [A-Za-z0-9._/-]+, got: $ANSWERS" >&2
    exit 2
    ;;
esac

# Wait briefly for the log to appear (the runner may not have written its
# first line yet when the Monitor is armed).
for _ in 1 2 3 4 5; do
  [ -f "$LOG" ] && break
  sleep 0.5
done

# tail -F follows truncation/recreation; awk's fflush() on every output is
# critical so events surface immediately rather than being buffered. The
# size-injection per event uses `wc -c` via a piped command. Defense-in-depth:
# the `sizeof` function rejects any name outside the render-prompts.sh slug
# charset [A-Za-z0-9._-] before splicing it into the shell, so a hand-edited
# log with metacharacters cannot inject commands.
exec tail -F "$LOG" 2>/dev/null | awk -v ANS="$ANSWERS" -v MIN="$MIN" '
function sizeof(name,   cmd, n, status) {
  if (name !~ /^[A-Za-z0-9._-]+$/) return -1
  # Test existence first so missing files are distinguishable from empty
  # ones (and so stderr from the shell `<` redirect cannot leak into our
  # event stream).
  cmd = "[ -f " ANS "/" name ".md ] && wc -c < " ANS "/" name ".md || echo MISSING"
  if ((cmd | getline n) <= 0) { close(cmd); return -1 }
  close(cmd)
  if (n == "MISSING") return -1
  return n+0
}
# Three-way result: -1 = missing, 0..MIN-1 = small, >=MIN = ok.
function fmt(n) {
  if (n < 0)     return " (MISSING) [SMALL]"
  if (n < MIN)   return " (" n " bytes) [SMALL]"
  return         " (" n " bytes)"
}
function fmt_skip(n) {
  if (n < 0)     return " (existing MISSING) [SMALL]"
  if (n < MIN)   return " (existing " n " bytes) [SMALL]"
  return         " (existing " n " bytes)"
}
/^START / { print; fflush(); next }
/^DONE /  { n=sizeof($2); print $0 fmt(n); fflush(); next }
/^FAIL /  { print; fflush(); next }
/^SKIP /  { n=sizeof($2); print $0 fmt_skip(n); fflush(); next }
/^---/    { print; fflush(); next }
'

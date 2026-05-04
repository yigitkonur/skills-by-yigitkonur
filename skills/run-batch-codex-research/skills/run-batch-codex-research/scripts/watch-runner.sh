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
function sizeof(name,   cmd, n) {
  if (name !~ /^[A-Za-z0-9._-]+$/) return 0
  cmd = "wc -c < " ANS "/" name ".md 2>/dev/null"
  cmd | getline n
  close(cmd)
  return n+0
}
function flag(n) { return (n>0 && n<MIN) ? " [SMALL]" : "" }
/^START / { print; fflush(); next }
/^DONE /  { n=sizeof($2); print $0 " (" n " bytes)" flag(n); fflush(); next }
/^FAIL /  { print; fflush(); next }
/^SKIP /  { n=sizeof($2); print $0 " (existing " n " bytes)" flag(n); fflush(); next }
/^---/    { print; fflush(); next }
'

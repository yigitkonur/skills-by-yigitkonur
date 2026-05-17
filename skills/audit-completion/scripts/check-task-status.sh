#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage: bash scripts/check-task-status.sh <audit-or-completion-report.md>

Checks markdown audit and completion-report tables for known statuses,
missing Action Required cells, and non-terminal completion endings.
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 2
fi

input=$1
if [ ! -r "$input" ]; then
  printf 'ERROR: file not found: %s\n' "$input" >&2
  exit 2
fi

awk '
function trim(s) {
  gsub(/\r/, "", s)
  gsub(/^[ \t]+/, "", s)
  gsub(/[ \t]+$/, "", s)
  return s
}

function clean_cell(s) {
  s = trim(s)
  gsub(/`/, "", s)
  return trim(s)
}

function add_status(s) {
  known[s] = 1
  order[++order_count] = s
}

function add_terminal(s) {
  terminal[s] = 1
}

function normalize_status(s) {
  s = clean_cell(s)
  gsub(/[ \t]+/, " ", s)

  if (s ~ /^Blocked[ \t]*[-—][ \t]*unresolvable/) {
    return "Blocked — unresolvable"
  }

  if (s ~ /^Superseded([ \t]*(\(|-|—|:).*)?$/) {
    return "Superseded"
  }

  return s
}

function is_separator(line, tmp) {
  tmp = line
  gsub(/\|/, "", tmp)
  gsub(/[-:[:space:]]/, "", tmp)
  return tmp == ""
}

function remember_status(raw, row, column, task, count_mode, status) {
  status = normalize_status(raw)
  if (status == "") {
    return ""
  }

  if (count_mode == "count") {
    counts[status]++
  }
  if (!(status in known)) {
    unknown[++unknown_count] = row ": " column "=`" clean_cell(raw) "` task=`" task "`"
  }
  return status
}

function missing_action(action) {
  action = clean_cell(action)
  return action == "" || action == "-" || action == "—" || action == "N/A" || action == "n/a"
}

function read_header(cols, n, i, h) {
  delete header
  for (i = 1; i <= n; i++) {
    h = clean_cell(cols[i])
    gsub(/^\*\*|\*\*$/, "", h)
    header[h] = i
  }

  if (("#" in header) && ("Task" in header) && ("Status" in header) && ("Action Required" in header)) {
    delete field
    mode = "audit"
    field["row"] = header["#"]
    field["task"] = header["Task"]
    field["status"] = header["Status"]
    field["action"] = header["Action Required"]
    next_is_data = 1
    return 1
  }

  if (("#" in header) && ("Task" in header) && ("Started" in header) && ("Ended" in header)) {
    delete field
    mode = "completion"
    field["row"] = header["#"]
    field["task"] = header["Task"]
    field["started"] = header["Started"]
    field["ended"] = header["Ended"]
    next_is_data = 1
    return 1
  }

  return 0
}

BEGIN {
  add_status("Implemented")
  add_status("Partially Implemented")
  add_status("Implemented but Untested")
  add_status("Implemented but Broken")
  add_status("Implemented but Outdated")
  add_status("Assumed Complete")
  add_status("Incorrectly Implemented")
  add_status("Stalled")
  add_status("Timed Out")
  add_status("Crashed")
  add_status("Skipped")
  add_status("Forgotten")
  add_status("Blocked")
  add_status("Deferred to Human")
  add_status("Deprioritized")
  add_status("Superseded")
  add_status("Cancelled")
  add_status("Ambiguous")
  add_status("Duplicate")
  add_status("Planned / Queued")
  add_status("Not Planned")
  add_status("Out of Scope")
  add_status("Blocked — unresolvable")

  add_terminal("Implemented")
  add_terminal("Deferred to Human")
  add_terminal("Deprioritized")
  add_terminal("Cancelled")
  add_terminal("Out of Scope")
  add_terminal("Superseded")
  add_terminal("Blocked — unresolvable")
}

!/^[ \t]*\|/ {
  mode = ""
  next
}

/^[ \t]*\|/ {
  if (is_separator($0)) {
    next
  }

  n = split($0, cols, "|")
  if (read_header(cols, n)) {
    next
  }

  if (mode == "audit") {
    row = clean_cell(cols[field["row"]])
    task = clean_cell(cols[field["task"]])
    if (row == "" || task == "" || row == "#") {
      next
    }

    status = remember_status(cols[field["status"]], row, "Status", task, "count")
    audit_rows++

    if (status != "" && status != "Implemented" && missing_action(cols[field["action"]])) {
      missing_actions[++missing_action_count] = row ": `" task "` has status `" status "`"
    }
    next
  }

  if (mode == "completion") {
    row = clean_cell(cols[field["row"]])
    task = clean_cell(cols[field["task"]])
    if (row == "" || task == "" || row == "#") {
      next
    }

    remember_status(cols[field["started"]], row, "Started", task, "check")
    ended = remember_status(cols[field["ended"]], row, "Ended", task, "count")
    completion_rows++

    if (ended != "" && (ended in known) && !(ended in terminal)) {
      non_terminal[++non_terminal_count] = row ": `" task "` ended as `" ended "`"
    }
    next
  }
}

END {
  print "Status counts:"
  printed = 0
  for (i = 1; i <= order_count; i++) {
    status = order[i]
    if (counts[status] > 0) {
      printf "  %s: %d\n", status, counts[status]
      printed = 1
    }
  }
  for (status in counts) {
    if (!(status in known)) {
      printf "  %s: %d\n", status, counts[status]
      printed = 1
    }
  }
  if (!printed) {
    print "  none"
  }

  print ""
  if (unknown_count == 0) {
    print "Unknown statuses: none"
  } else {
    print "Unknown statuses:"
    for (i = 1; i <= unknown_count; i++) {
      print "  " unknown[i]
    }
  }

  print ""
  if (missing_action_count == 0) {
    print "Audit rows missing Action Required: none"
  } else {
    print "Audit rows missing Action Required:"
    for (i = 1; i <= missing_action_count; i++) {
      print "  " missing_actions[i]
    }
  }

  print ""
  if (non_terminal_count == 0) {
    print "Non-terminal completion endings: none"
  } else {
    print "Non-terminal completion endings:"
    for (i = 1; i <= non_terminal_count; i++) {
      print "  " non_terminal[i]
    }
  }

  if (audit_rows == 0 && completion_rows == 0) {
    print ""
    print "ERROR: no audit or completion-report table found" > "/dev/stderr"
    exit 2
  }

  if (unknown_count > 0 || missing_action_count > 0 || non_terminal_count > 0) {
    exit 1
  }
}
' "$input"

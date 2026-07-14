#!/usr/bin/env bash
set -o pipefail

usage() {
  cat <<'USAGE'
Usage:
  parse-derailment-trace.sh TRACE_PATH [--context N]

Reads a JSONL or plain-text derailment trace and emits a compact markdown
report with marker counts, marker context, and tool/failure snippets.

Options:
  --context N   Surrounding lines to show around each marker, default: 1
  -h, --help    Show this help
USAGE
}

die() {
  local code="$1"
  shift
  printf 'ERROR: %s\n' "$*" >&2
  exit "$code"
}

trace_path=""
context="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --context)
      [[ $# -ge 2 ]] || die 2 "--context requires a value"
      context="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      die 2 "unknown argument: $1"
      ;;
    *)
      [[ -z "$trace_path" ]] || die 2 "only one TRACE_PATH is allowed"
      trace_path="$1"
      shift
      ;;
  esac
done

[[ -n "$trace_path" ]] || die 2 "missing TRACE_PATH"
[[ -f "$trace_path" ]] || die 2 "trace file not found: $trace_path"
[[ -r "$trace_path" ]] || die 2 "trace file is not readable: $trace_path"
[[ "$context" =~ ^[0-9]+$ ]] || die 2 "--context must be a non-negative integer"

python3 - "$trace_path" "$context" <<'PY'
import json
import re
import sys
from pathlib import Path

trace_path = Path(sys.argv[1])
context = int(sys.argv[2])
markers = ["[STUCK]", "[GUESSED]", "[BROKE]", "[NICE]"]
failure_re = re.compile(
    r"(command failed|failed|error|exit code|nonzero|not found|no such file|traceback|exception)",
    re.IGNORECASE,
)


def shorten(value, limit=700):
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value if len(value) <= limit else value[: limit - 3] + "..."


def content_items(value):
    items = []
    if isinstance(value, str):
        items.append(("text", value))
    elif isinstance(value, list):
        for item in value:
            items.extend(content_items(item))
    elif isinstance(value, dict):
        typ = value.get("type")
        if typ in {"text", "output_text"} and isinstance(value.get("text"), str):
            items.append(("text", value["text"]))
        elif typ in {"tool_use", "function_call"}:
            name = value.get("name") or value.get("function", {}).get("name") or "tool"
            payload = value.get("input", value.get("arguments", {}))
            items.append(("tool", f"TOOL: {name} {shorten(json.dumps(payload, ensure_ascii=False))}"))
        elif typ in {"tool_result", "function_call_output"}:
            payload = value.get("content", value.get("output", ""))
            items.append(("tool_result", f"TOOL_RESULT: {shorten(payload)}"))
        elif isinstance(value.get("message"), dict):
            items.extend(content_items(value["message"].get("content", [])))
        elif "content" in value:
            items.extend(content_items(value["content"]))
        elif any(k in value for k in ("error", "stderr", "exit_code", "status")):
            items.append(("failure", shorten(value)))
    return items


entries = []
snippets = []
json_lines = 0

with trace_path.open(errors="replace") as handle:
    for raw_no, raw in enumerate(handle, 1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            entries.append((raw_no, f"line {raw_no}", line))
            if failure_re.search(line):
                snippets.append((f"line {raw_no}", line))
            continue

        json_lines += 1
        extracted = content_items(obj)
        if not extracted:
            extracted = [("json", shorten(obj))]
        for kind, text in extracted:
            for offset, piece in enumerate(str(text).splitlines() or [str(text)]):
                entries.append((len(entries) + 1, f"jsonl {raw_no}", piece))
            if kind in {"tool", "tool_result", "failure"} or failure_re.search(text):
                snippets.append((f"jsonl {raw_no}", text))

counts = {marker: 0 for marker in markers}
marker_indexes = []
for idx, (_entry_no, _source, text) in enumerate(entries):
    matched = False
    for marker in markers:
        found = text.count(marker)
        if found:
            counts[marker] += found
            matched = True
    if matched:
        marker_indexes.append(idx)

print("# Derailment Trace Report")
print()
print(f"Source: `{trace_path}`")
print(f"Format: `{'jsonl' if json_lines else 'plain-text'}`")
print()
print("## Marker Counts")
print()
print("| Marker | Count |")
print("|---|---:|")
for marker in markers:
    print(f"| `{marker}` | {counts[marker]} |")
print()

print("## Marker Matches")
print()
if marker_indexes:
    shown = 0
    for idx in marker_indexes[:40]:
        start = max(0, idx - context)
        end = min(len(entries), idx + context + 1)
        entry_no, source, _text = entries[idx]
        print(f"- `{source}`, extracted line {entry_no}")
        print("```text")
        for i in range(start, end):
            no, src, text = entries[i]
            print(f"{src} | {no}: {text}")
        print("```")
        shown += 1
    if len(marker_indexes) > shown:
        print(f"... {len(marker_indexes) - shown} more marker match(es) omitted.")
else:
    print("No markers found. Scan manually for silent symptoms: rereads, failed commands, skipped steps.")
print()

print("## Tool Use And Command Failures")
print()
if snippets:
    for source, text in snippets[:25]:
        print(f"- `{source}`")
        print("```text")
        print(shorten(text, 1000))
        print("```")
    if len(snippets) > 25:
        print(f"... {len(snippets) - 25} more snippet(s) omitted.")
else:
    print("None detected.")
PY

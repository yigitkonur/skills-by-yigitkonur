#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 path/to/script.py|script.sh" >&2
  exit 2
fi

python3 - "$1" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
errors: list[str] = []
allowed_modes = {"fullOutput", "compact", "silent", "inline"}
allowed_argument_types = {"text", "password", "dropdown"}

if not path.exists():
    print(f"FAIL {path}: file does not exist")
    raise SystemExit(1)

if path.suffix not in {".py", ".sh"}:
    errors.append("extension must be .py or .sh")

try:
    lines = path.read_text(encoding="utf-8").splitlines()
except UnicodeDecodeError:
    errors.append("file is not valid UTF-8 text")
    lines = []

if not lines or not lines[0].startswith("#!"):
    errors.append("first line must be a shebang")

top_lines = lines[:80]
metadata: dict[str, list[str]] = {}
pattern = re.compile(r"^\s*#\s*@raycast\.([A-Za-z0-9]+)\s*(.*)$")
for line in top_lines:
    match = pattern.match(line)
    if match:
        key, value = match.groups()
        metadata.setdefault(key, []).append(value.strip())

for required in ("schemaVersion", "title", "mode"):
    if required not in metadata:
        errors.append(f"missing @raycast.{required} near the top of the file")

schema_versions = metadata.get("schemaVersion", [])
if schema_versions and schema_versions[0] != "1":
    errors.append(f"unsupported schemaVersion {schema_versions[0]!r}; expected 1")

mode_values = metadata.get("mode", [])
if mode_values:
    mode = mode_values[0]
    if mode not in allowed_modes:
        errors.append(f"unsupported mode {mode!r}; expected one of {', '.join(sorted(allowed_modes))}")
    if mode == "inline" and "refreshTime" not in metadata:
        errors.append("inline mode requires @raycast.refreshTime")

argument_numbers: list[int] = []
for key, values in metadata.items():
    match = re.fullmatch(r"argument(\d+)", key)
    if not match:
        continue
    number = int(match.group(1))
    argument_numbers.append(number)
    if number > 3:
        errors.append(f"@raycast.argument{number} is not supported; maximum is argument3")
    for raw_value in values:
        try:
            data = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            errors.append(f"@raycast.{key} is not valid JSON: {exc.msg}")
            continue
        if not isinstance(data, dict):
            errors.append(f"@raycast.{key} must be a JSON object")
            continue
        argument_type = data.get("type")
        if argument_type not in allowed_argument_types:
            errors.append(
                f"@raycast.{key} has unsupported type {argument_type!r}; "
                "Script Commands support text, password, and dropdown"
            )
        if "placeholder" not in data:
            errors.append(f"@raycast.{key} is missing required placeholder")
        if argument_type == "dropdown":
            choices = data.get("data")
            if not isinstance(choices, list) or not choices:
                errors.append(f"@raycast.{key} dropdown requires non-empty data array")
            else:
                for index, choice in enumerate(choices, start=1):
                    if not isinstance(choice, dict):
                        errors.append(f"@raycast.{key} dropdown item {index} must be an object")
                        continue
                    if "title" not in choice or "value" not in choice:
                        errors.append(
                            f"@raycast.{key} dropdown item {index} requires title and value"
                        )

if len(set(argument_numbers)) > 3:
    errors.append("Script Commands support no more than three arguments")

if errors:
    print(f"FAIL {path}")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

mode = metadata.get("mode", ["unknown"])[0]
argument_count = len(set(argument_numbers))
print(f"PASS {path}")
print(f"- mode: {mode}")
print(f"- arguments: {argument_count}")
PY

# parse-derailment-trace.sh

Parse a saved derailment trace into a compact markdown report.

## Usage

```bash
bash scripts/parse-derailment-trace.sh /path/to/trace.jsonl
```

Optional context around each marker:

```bash
bash scripts/parse-derailment-trace.sh /path/to/trace.txt --context 2
```

The trace may be JSONL or plain text. JSONL is parsed structurally for assistant
text, tool-use entries, tool results, and failure-shaped fields before marker
counts are computed.

## Output

The report contains:

- counts for `[STUCK]`, `[GUESSED]`, `[BROKE]`, and `[NICE]`
- matching lines with surrounding context
- tool-use and command-failure snippets when present
- a no-marker branch that points back to silent symptoms: rereads, failed commands, skipped steps

## Examples

```bash
bash scripts/parse-derailment-trace.sh /tmp/derailment-round-1.jsonl > /tmp/report.md
bash scripts/parse-derailment-trace.sh /tmp/derailment-round-1.txt --context 3
```

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Trace parsed and report emitted |
| `2` | Missing path, unreadable trace, invalid arguments, or invalid context |

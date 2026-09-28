# audit-worker-pane.sh

Performs automated forensic inspection on a Herdr worker agent terminal pane, extracting unwrapped terminal scrollback, tool command lines, crash signals, thought chains, and physical filesystem artifacts.

---

## Usage

```bash
bash scripts/audit-worker-pane.sh <pane-id> [options]
```

### Arguments
- `<pane-id>`: Herdr pane ID to audit (e.g. `w2N:pP`, `w2N:pQ`).

### Options
- `-n, --lines <N>`: Scrollback lines to fetch from unwrapped buffer (default: `500`).
- `-d, --output-dir <DIR>`: Path to physical directory where worker was expected to generate assets.
- `--thoughts`: Extract model thought and reasoning blocks.
- `--tools`: Extract executed CLI and tool invocations.
- `--receipts`: Extract delimited JSON receipts (`__TAKE_RESULT_JSON_START__`).
- `-h, --help`: Display usage.

### Output
Emits a structured report containing:
1. Agent registration metadata (Name, Kind, Status, Working Dir).
2. Crash and non-zero exit code detections.
3. Executed tool commands.
4. Extracted machine-readable receipts.
5. Physical disk artifact verification table (File size, MIME type, Magic header).

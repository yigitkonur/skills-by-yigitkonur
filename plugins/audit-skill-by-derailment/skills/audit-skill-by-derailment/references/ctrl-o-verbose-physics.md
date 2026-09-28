# AGY Terminal TUI Physics & The Ctrl+O Verbose Audit Protocol

Understanding the terminal user interface (TUI) mechanics of Antigravity CLI (AGY), the significance of the `Ctrl+O` verbose mode toggle, and how to extract comprehensive cognitive traces from terminal scrollbacks.

---

## 1. The Anatomy of AGY TUI Rendering

Antigravity CLI (AGY) runs inside interactive terminal emulators using a rich TUI library (e.g. Ink / Bubble Tea). By default, to maintain visual cleanliness for interactive human users, AGY applies **aggressive visual folding**:

### Collapsed Standard View (Default)
In standard view, the agent's internal activity is compressed into minimalist single-line UI badges:
- **Thoughts:** Rendered as a single folded line (e.g. `▸ Thought (12s)` or `thinking...`).
- **Tool Invocations:** Folded into status pills (e.g. `● Run command: node scripts/scene-take.mjs...`). Full flags, prompt parameters, and paths are hidden.
- **Command Output (stdout/stderr):** Suppressed or truncated to the last 2-3 lines.
- **Model Responses:** Rendered cleanly in Markdown.

### Why Standard View Blinds Forensic Audits
When an auditing agent reads terminal scrollback from a standard-view pane:
1. Tool arguments cannot be verified (did the agent run the right script flags or invent bogus arguments?).
2. Error stack traces are invisible (a script may have crashed silently with code 1, but the TUI only displays `Command finished`).
3. Thought processes are unavailable (did the agent get confused by skill text, or did it make a lucky guess?).

---

## 2. The `Ctrl+O` Verbose Mode Invariant

Pressing `Ctrl+O` toggles AGY into **Verbose / Unfolded Mode**:

```
[Standard View] ────────( Ctrl+O )────────► [Verbose View]
- Folded thought pills                      - Full thought block expanded
- Truncated tool calls                       - Complete CLI invocation & arguments
- Suppressed stdout/stderr                   - Raw, uncensored stdout and stderr
```

### What Verbose Mode Exposes in Terminal Scrollback

1. **Expanded Thought Chains:**
   ```
   Thinking Process:
   1. The user requested Act 1 for the luxury perfume reel.
   2. Checking SKILL.md Invariant 10: "Every scene take must be executed via scripts/scene-take.mjs".
   3. Running pre-flight probe: node scripts/scene-take.mjs --help to verify options.
   4. Observation: The script requires --prompt and --ratio 9:16.
   ```
2. **Exact Tool Calls with Full CLI Arguments:**
   ```
   Tool: run_command
   CommandLine: node scripts/scene-take.mjs --prompt "Macro close-up of amber crystal perfume bottle..." --ratio 9:16 --output-dir ~/Downloads/flow-videos/scenes/
   ```
3. **Uncensored Standard Output & Error Streams:**
   ```
   [FLOW_RENDER] Submitting prompt to Veo 3.1...
   [FLOW_DIFFUSION] Card 0 progress: 14% -> 48% -> 100%
   [DOWNLOAD] Strategy B triggered. Hovering .video-canvas...
   [DISK_VERIFY] File saved: scene_01.mp4 (14.2 MB, valid ftyp header).
   Process exited with code 0.
   ```

---

## 3. Automating `Ctrl+O` via Herdr

When orchestrating or auditing worker agents, always ensure verbose mode is active so that scrollback capture contains complete evidence.

### Interactive Injection
```bash
# Send Ctrl+O keystroke to the target pane
herdr pane send-keys <pane-id> ctrl+o

# Or via agent send-keys
herdr agent send-keys <pane-id> ctrl+o
```

### Verifying Verbose Mode in Scrollback
Inspect the pane's recent output to confirm whether thought blocks or full command lines are rendering:
```bash
herdr pane read <pane-id> --source recent-unwrapped --lines 50 | grep -E "(Thinking Process:|CommandLine:|Tool:)"
```
If the output contains only folded single-line badges (e.g. `▸ Thought`), dispatch `herdr pane send-keys <pane-id> ctrl+o` and re-read.

---

## 4. Scrollback Extraction with Soft-Wrap Joining

Terminal emulators insert hard newline characters (`\n`) when text exceeds the column width of the viewport. This breaks long shell commands and JSON output across arbitrary columns.

### Always Use `--source recent-unwrapped`
Herdr provides an intelligent unwrapping engine:
```bash
# Correct: Re-joins soft wrapped lines into single logical lines
herdr pane read <pane-id> --source recent-unwrapped --lines 500

# Avoid for parsing: Splits long commands across columns based on window size
herdr pane read <pane-id> --source visible
```

### Pattern Matching on Unwrapped Streams
Once unwrapped, standard Unix utilities reliably extract:
```bash
# Extract all executed tool commands
herdr pane read <pane-id> --source recent-unwrapped --lines 500 | grep -E "(CommandLine:|● Bash|● Run command)"

# Extract all error messages and non-zero exits
herdr pane read <pane-id> --source recent-unwrapped --lines 500 | grep -E "(exited with code [1-9]|TypeError|Error:|Exception)"

# Extract all structured JSON receipts
herdr pane read <pane-id> --source recent-unwrapped --lines 500 | sed -n '/__TAKE_RESULT_JSON_START__/,/__TAKE_RESULT_JSON_END__/p' | grep -v "__TAKE_RESULT_JSON"
```

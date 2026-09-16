# macOS AppleScript, Accessibility & SSH Bridge Architecture

This reference explains how to reliably dispatch research prompts, monitor generation progress, and extract completed research from the official macOS ChatGPT desktop application from Linux or macOS.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph HostEnvironment [Calling Agent (Linux / Remote Host)]
        CLI[chatgpt-research-runner.mjs]
        B64[Base64 Encoding]
    end

    subgraph Transport [Secure Shell Bridge]
        SSH[ssh macbook]
    end

    subgraph TargetMac [User macOS Workstation]
        PB[pbcopy / pbpaste]
        OSA[osascript / System Events]
        AX[chatgpt_status Native C Bridge]
        APP[ChatGPT.app Chromium Desktop Window]
    end

    CLI --> B64
    B64 -->|SSH Pipe| SSH
    SSH --> PB
    PB --> OSA
    OSA -->|Cmd+N, Cmd+V, Enter| APP
    SSH --> AX
    AX -->|AXEnhancedUserInterface| APP
    AX -->|Real-Time Status & Text Extraction| CLI
```

---

## 2. Safe Transport via Base64 & `pbcopy`

Passing multiline prompts containing Turkish characters, quotes (`"`, `'`), parentheses, and markdown punctuation directly through bash strings over SSH frequently causes syntax errors, quote breaking, or truncated inputs.

To achieve 100% data integrity without character dropping:

1. **Encode prompt to Base64 on caller host:**
   ```javascript
   const b64 = Buffer.from(prompt, 'utf8').toString('base64');
   ```
2. **Decode and pipe directly into macOS `pbcopy`:**
   ```bash
   echo "<base64_string>" | base64 -d | pbcopy
   ```
3. **Trigger AppleScript to paste the clipboard:**
   Using clipboard paste (`Cmd+V`) is instantaneous, preserves formatting, and avoids the slow, error-prone character-by-character `keystroke` rendering.

---

## 3. AppleScript Execution Timing

The ChatGPT desktop app requires specific micro-delays between keystrokes to ensure event handling succeeds:

```applescript
tell application "ChatGPT" to activate
delay 0.4
tell application "System Events" to tell process "ChatGPT"
  -- 1. Open fresh chat window/tab
  keystroke "n" using command down
  delay 0.5
  -- 2. Paste prompt from system pasteboard
  keystroke "v" using command down
  delay 0.3
  -- 3. Submit prompt (Return key)
  key code 36
end tell
```

- `Cmd+N`: Clears previous context and ensures the input composer has focus.
- `0.5s delay`: Allows the new conversation view to mount.
- `Cmd+V`: Injects the rich prompt.
- `0.3s delay`: Ensures pasteboard buffer flush before triggering Return.
- `key code 36`: Return / Enter.

Total execution time per prompt is ~1.2 seconds, allowing rapid back-to-back dispatching ("tak-tak-tak").

---

## 4. Native Accessibility Bridge (`chatgpt_status`)

While AppleScript via `System Events` is suitable for firing keystrokes (`Cmd+N`, `Cmd+V`), traversing Chromium's accessibility DOM (3,000+ elements) using AppleScript IPC takes 60–120 seconds due to Mach IPC message overhead.

To achieve real-time (0.3s) detection and extraction, `chatgpt_status.c` compiles directly with macOS `ApplicationServices.framework`:

```bash
clang -O2 -framework ApplicationServices -framework CoreFoundation chatgpt_status.c -o chatgpt_status
```

### Key Engineering Details
1. **Chromium Accessibility Flag:** ChatGPT desktop uses Chromium under the hood. Setting `AXEnhancedUserInterface = true` on the application element unlocks the full DOM tree.
2. **State Detection Signatures:**
   - **Generating:** Presence of an `AXButton` whose description is `"Stop generating"`, `"Stop streaming"`, or `"Stop"`.
   - **Idle / Ready:** Absence of stop buttons AND presence of an `AXButton` whose description is `"Send"` or `"Dictate"`.
3. **Smart Text Extraction (`--extract`):**
   - Recursively walks `AXStaticText` nodes.
   - Automatically detects conversation boundaries by locating the latest `"ChatGPT said:"` marker.
   - Filters out sidebar chat titles, system disclaimer notices, and UI drag events, outputting the clean research response with full citations and markdown tables.

### CLI Usage
```bash
# Instant JSON status (0.3s)
~/.local/bin/chatgpt_status

# Polling wait until generation completes (exits 0 on completion, 1 on timeout)
~/.local/bin/chatgpt_status --wait 180

# Clean output extraction of the latest response
~/.local/bin/chatgpt_status --extract
```

---

## 5. SSH Host Configuration (`~/.ssh/config`)

To allow seamless remote execution without hardcoded IP addresses or repeated password prompts:

```sshconfig
Host macbook
    HostName <Mac_Local_or_Tailscale_IP>
    User <mac_username>
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ConnectTimeout 5
```

### Health Check Recipe

```bash
# Verify connection & osascript presence
ssh -o ConnectTimeout=2 -o BatchMode=yes macbook "which osascript && pgrep -l -i chatgpt"
```

---

## 6. TCC Accessibility Permissions

macOS requires that the process driving `System Events` has Accessibility permissions (*System Settings → Privacy & Security → Accessibility*).

- If connected via SSH: `sshd-keygen-wrapper` or the user's terminal emulator (iTerm, Terminal, Ghostty) must be granted Accessibility access.
- Test command:
  ```bash
  ssh macbook "osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'"
  ```
- If it returns the frontmost app name (e.g. `ChatGPT` or `Finder`), Accessibility is fully authorized.

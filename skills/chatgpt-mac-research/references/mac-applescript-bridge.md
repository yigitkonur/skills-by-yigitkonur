# macOS AppleScript & SSH Bridge Architecture

This reference explains how to reliably dispatch research prompts from any Linux server, container, or local macOS terminal directly into the official macOS ChatGPT desktop application.

---

## 1. System Architecture

```mermaid
flowchart LR
    subgraph HostEnvironment [Calling Agent (Linux / Remote Host)]
        CLI[chatgpt-research-runner.mjs]
        B64[Base64 Encoding]
    end

    subgraph Transport [Secure Shell Bridge]
        SSH[ssh macbook]
    end

    subgraph TargetMac [User macOS Workstation]
        PB[pbcopy Clipboard]
        OSA[osascript / System Events]
        APP[ChatGPT.app Native Window]
    end

    CLI --> B64
    B64 -->|SSH Pipe| SSH
    SSH --> PB
    PB --> OSA
    OSA -->|Cmd+N, Cmd+V, Enter| APP
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

The ChatGPT desktop app requires specific micro-delays between keystrokes to ensure SwiftUI / Catalyst event handling succeeds:

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

## 4. SSH Host Configuration (`~/.ssh/config`)

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

Before launching a research batch, verify the bridge:

```bash
# Verify connection & osascript presence
ssh -o ConnectTimeout=2 -o BatchMode=yes macbook "which osascript && pgrep -l -i chatgpt"
```

If ChatGPT is not running, launch it remotely:
```bash
ssh macbook "open -a ChatGPT"
```

---

## 5. TCC Accessibility Permissions

macOS requires that the process driving `System Events` has Accessibility permissions (*System Settings → Privacy & Security → Accessibility*).

- If connected via SSH: `sshd-keygen-wrapper` or the user's terminal emulator (iTerm, Terminal, Ghostty) must be granted Accessibility access.
- Test command:
  ```bash
  ssh macbook "osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'"
  ```
- If it returns the frontmost app name (e.g. `ChatGPT` or `Finder`), Accessibility is fully authorized.

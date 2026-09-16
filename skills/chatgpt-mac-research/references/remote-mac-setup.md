# Remote Mac Setup Guide (Linux to macOS ChatGPT Bridge)

This guide walks through connecting a Linux server, container, or remote workstation to a Mac running the official **ChatGPT desktop app** (`/Applications/ChatGPT.app`).

---

## 1. Prerequisites

- **Mac Workstation:** macOS 13 (Ventura), macOS 14 (Sonoma), or macOS 15 (Sequoia).
- **ChatGPT Desktop App:** Installed at `/Applications/ChatGPT.app` and logged into your OpenAI account.
- **Xcode Command Line Tools:** Installed on Mac (`xcode-select --install`) to provide `clang` for compiling the native status bridge.
- **Network Link:** Either local Wi-Fi/Ethernet LAN or a zero-config mesh VPN like **Tailscale**.

---

## 2. Prepare the Mac Workstation

### A. Enable Remote Login (SSH Server)
1. Open **System Settings** on your Mac.
2. Go to **General → Sharing**.
3. Toggle **Remote Login** to **ON**.
4. Under the info icon (ℹ️) next to Remote Login:
   - Allow access for: **All users** (or specify your macOS user account).
   - Note the provided username and network name (e.g. `mac@192.168.1.50` or `mac@macs-macbook-pro.local`).

### B. Grant Accessibility Permissions
macOS requires Accessibility permissions for applications or background SSH daemons to control the GUI via System Events and query the UI element tree.

1. Open **System Settings → Privacy & Security → Accessibility**.
2. Click the **+** (Add) button.
3. If connecting over SSH, add **sshd-keygen-wrapper**:
   - Press `Cmd + Shift + G` in the file chooser.
   - Enter path: `/usr/libexec/sshd-keygen-wrapper`
   - Select it and toggle the permission to **ON**.
4. Also ensure your primary terminal application (e.g. **Terminal**, **iTerm2**, or **Ghostty**) has Accessibility toggled **ON**.

---

## 3. Configure Network Connectivity (Tailscale Recommended)

If your Linux machine and Mac are not on the same local Wi-Fi, use Tailscale for a secure, peer-to-peer encrypted wireguard connection without opening firewall ports.

1. **Install Tailscale on Mac:**
   - Download from the Mac App Store or run:
     ```bash
     brew install tailscale
     ```
   - Launch and sign in.
2. **Install Tailscale on Linux:**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
3. **Verify Tailscale IP:**
   - On Mac: Run `tailscale ip -4` (e.g. `100.x.y.z`).
   - On Linux: Ping the Mac:
     ```bash
     ping 100.x.y.z
     ```

---

## 4. Setup Passwordless SSH Authentication

Automation scripts require non-interactive, passwordless authentication.

1. **On your Linux machine, generate an SSH key (if you don't already have one):**
   ```bash
   ssh-keygen -t ed25519 -C "chatgpt-bridge" -f ~/.ssh/id_ed25519 -N ""
   ```

2. **Copy the public key to your Mac:**
   ```bash
   ssh-copy-id -i ~/.ssh/id_ed25519.pub <mac_user>@<mac_ip_or_tailscale_name>
   ```

3. **Verify passwordless login:**
   ```bash
   ssh <mac_user>@<mac_ip_or_tailscale_name> "uname -a"
   ```

---

## 5. Configure SSH Alias (`~/.ssh/config`)

Add a clean host alias so the runner tool and CLI agents can connect automatically without specifying IP addresses or usernames:

Edit or create `~/.ssh/config` on your Linux machine:

```sshconfig
Host macbook
    HostName 100.x.y.z               # Replace with your Mac's Tailscale IP or hostname
    User mac                         # Replace with your macOS username
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 5
```

Test your configuration:
```bash
ssh macbook "echo 'Bridge connected successfully!'"
```

---

## 6. Environment Variables (Optional)

If your Mac host is named differently in `~/.ssh/config`, you can set the environment variable:

```bash
export CHATGPT_SSH_HOST=my-work-mac
```

Or pass it per command:
```bash
node scripts/chatgpt-research-runner.mjs --ssh-host=my-work-mac --check-bridge
```

---

## 7. Verify End-to-End Bridge Health

Run the diagnostic tool from your Linux terminal:

```bash
node skills/chatgpt-mac-research/scripts/chatgpt-research-runner.mjs --check-bridge
```

Expected output:
```text
Checking ChatGPT bridge connection...
✅ Bridge operational! Mode: ssh (macbook)
ℹ️  ChatGPT state: idle (generating: false, ready: true)
```

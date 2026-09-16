# chatgpt-mac-research

Autonomous web research bridge driving the native macOS ChatGPT desktop app via AppleScript and SSH.

## Features

- **macOS Desktop Automation:** Controls `/Applications/ChatGPT.app` via AppleScript GUI automation (`System Events`).
- **Remote SSH Bridge:** Transparently commands a Mac workstation from any Linux server or container (`ssh macbook`).
- **Browser Plugin Hook:** Automatic `[@Browser](plugin://browser@openai-bundled)` injection for live web searching.
- **Rapid Burst & Cooldown:** Dispatches batches of 10 prompts back-to-back ("tak-tak-tak") with 5-minute rate-limit cooldowns.
- **State Persistence:** Atomic JSON state ledger prevents duplicate submissions across restarts.

## Quick Usage

```bash
# Check connection
node scripts/chatgpt-research-runner.mjs --check-bridge

# Single prompt
node scripts/chatgpt-research-runner.mjs --prompt "Research XYZ"

# Batch targets
node scripts/chatgpt-research-runner.mjs --targets targets.json --batch-size=10 --wait-minutes=5
```

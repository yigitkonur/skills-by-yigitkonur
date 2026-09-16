# use-chatgpt-by-applescript

Autonomous web research and desktop automation bridge driving the native macOS ChatGPT desktop app via AppleScript, Browser/Computer plugins, and native accessibility extraction.

## Features

- **macOS Desktop Automation:** Controls `/Applications/ChatGPT.app` locally or remotely via AppleScript GUI automation (`System Events`).
- **Universal Portability:** Runs directly with zero network overhead on macOS, and connects transparently from Linux via Tailscale / SSH.
- **Plugin Dispatch Framework:** Supports live web research via `[@Browser](plugin://browser@openai-bundled)` and desktop control via `[@Computer](plugin://computer-use@openai-bundled)`.
- **0.3s Generation Detection & Wait:** Uses a native C accessibility bridge (`ApplicationServices`) to detect generation completion and wait for completion.
- **AST-to-Markdown Extraction:** Reconstructs pristine Markdown with headers, code blocks, lists, and citations straight from the accessibility DOM.
- **Rapid Burst & Cooldown:** Dispatches batches of 10 prompts back-to-back ("tak-tak-tak") with 5-minute rate-limit cooldowns.
- **State Persistence:** Atomic JSON state ledger prevents duplicate submissions across restarts.

## Quick Usage

```bash
# Check connection
node skills/use-chatgpt-by-applescript/scripts/chatgpt-research-runner.mjs --check-bridge

# Single prompt with automatic wait & markdown extraction
node skills/use-chatgpt-by-applescript/scripts/chatgpt-research-runner.mjs --prompt "Research XYZ" --wait --extract

# Computer automation
node skills/use-chatgpt-by-applescript/scripts/chatgpt-research-runner.mjs --prompt "Inspect Downloads folder" --plugin=computer --wait

# Batch targets
node skills/use-chatgpt-by-applescript/scripts/chatgpt-research-runner.mjs --targets targets.json --batch-size=10 --wait-minutes=5
```

# Codex Harness Physics & Steering Protocols

This reference defines the operational physics, native queue commands, steering behavior, and parser recovery protocols for OpenAI Codex agents operating within Herdr.

---

## 1. Steering at Tool Boundaries vs. Follow-Up Enqueue

In the interactive Codex TUI:
- **Enter Steering**: Pressing Enter delivers steering that the model evaluates at its next tool boundary or decision point.
- **Tab Enqueue**: Pressing Tab enqueues input as a deferred follow-up turn to be executed after the current turn sequence completes.
- **Never Apply AGY Escape Mechanics to Codex**: The Escape key does NOT behave like AGY's composer-staging mechanism in Codex. Sending Escape blindly to a busy Codex session can close dialogs, cancel active prompts unexpectedly, or leave unhandled PTY state.

---

## 2. Native Queue Delivery (`codex queue`)

On hosts where the Codex CLI provides native queue support (verified on this host):

```bash
codex queue --thread <THREAD_UUID_OR_NAME> --message "<TEXT>"
```

### Usage Rules:
1. **Thread Identification**: Always target an explicit, verified thread UUID or exact session name. Do not guess identifiers.
2. **Enqueue is NOT Consumption**: A successful exit code ($0$) from `codex queue` proves only that the transport accepted the message into the thread's queue buffer. It does NOT prove the agent has read, parsed, or acted on the text. Always inspect agent output or wait for completion to confirm consumption.
3. **No Double Delivery**: Do not send the same message through both `codex queue` and raw PTY keystroke injection (`herdr agent prompt`). Choose one transport channel.

---

## 3. Slash Parser Failure Recovery

Codex agents may reject or fail to parse slash command prefixes (e.g. `/herdr`, `/teamwork-preview`, `/boost`) if skill configurations or system prompts differ:

### Recovery Rules:
1. **Fallback to Plain Language**: If a slash prefix fails or triggers a command-not-found error, **immediately switch to clear, standalone natural language**:
   - Instead of: `/herdr /teamwork-preview You are the Lead Implementer...`
   - Use: `You are the Lead Implementer for Task #101. Review the following brief and implement...`
2. **No Blind Repetition**: Never repeatedly resend an identical rejected slash command. If the parser rejects the token once, it will reject it again.

---

## 4. Sandboxing & Permission Flags

When starting Codex agents via `herdr agent start`:

```bash
herdr agent start reviewer --kind codex --pane "$PANE_ID" -- [AGENT_ARGS]...
```

### Critical Security Invariants:
1. **Sandbox Policies**:
   - `read-only`: Safe default for auditors and read-only reviewers.
   - `workspace-write`: Default for implementers requiring local file modifications.
   - `danger-full-access`: Extreme risk; grants unconstrained system access.
2. **Approval Bypasses**:
   - Flags such as `--dangerously-bypass-approvals-and-sandbox` or `--dangerously-bypass-hook-trust` strip confirmation dialogs entirely.
   - **Strict Invariant**: These flags are permitted ONLY when explicitly authorized for dedicated, externally sandboxed environments. Never enable them by default on production machines or uncontained hosts.

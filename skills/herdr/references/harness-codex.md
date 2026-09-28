# Codex Harness Physics & Steering Protocols

This reference defines pane-based prompt delivery, steering behavior, and parser recovery for OpenAI Codex agents operating within Herdr.

---

## 1. Visible Pane Steering

In the interactive Codex TUI:
- **Prompt Delivery**: Verify the target pane and agent identity, then deliver a single instruction with `herdr agent prompt <PANE_ID> <TEXT>` without `--wait`. If Codex is busy, inspect its visible buffer and wait for the current tool boundary before deciding whether any follow-up is needed.
- **Receipt**: A successful prompt command proves submission only. Read `herdr agent read <PANE_ID> --source visible` or recent scrollback and confirm Codex consumed the instruction or produced the expected checkpoint before acting on it.
- **Never Apply AGY Escape Mechanics to Codex**: The Escape key does NOT behave like AGY's composer-staging mechanism in Codex. Sending Escape blindly to a busy Codex session can close dialogs, cancel active prompts unexpectedly, or leave unhandled PTY state.

---

## 2. Pending Prompt Discipline

1. **One Target, One Message**: Keep one verified pane ID and one pending instruction per decision. Do not submit the same brief again because Codex has not reached a tool boundary yet.
2. **Inspect Before Recovery**: Use pane scrollback, `herdr agent get`, and `herdr pane process-info --pane <PANE_ID>` to distinguish an active turn from an idle composer or a blocked modal.
3. **Continue in the Same Pane**: Once the earlier instruction is visibly consumed or the agent is input-ready, send the next concise prompt to that pane. Preserve the session and its scrollback.

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

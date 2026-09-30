# Claude interactive harness

Read for Claude workers and the Advanced EM. Start the visible native TUI using
`--model MODEL --effort EFFORT` from agent-profiles.md. Do not use `-p`/print mode
or blanket permission bypasses as an orchestration shortcut.
Inspect the native permission mode too: the live test inherited bypass mode
from existing user settings despite no bypass launch flag. A per-launch
`--permission-mode manual` (verified in 2.1.285 help) exercised concrete approval
dialogs without changing global settings. Honor explicit user permission choices;
do not claim launch argv alone proves the effective mode.

New task briefs use `/herdr (/resolved/absolute/path/herdr/SKILL.md)` and the
plain authority block from prompt-and-messaging.md. `/teamwork-preview` is AGY
only. If skill discovery is unavailable, read the supplied file directly.

## Readiness and delivery

After start, read the visible screen for trust/login/permission dialogs; resolve
only a visible, authorized choice. A timeout does not mean start failed cleanly.
Use `herdr agent prompt TARGET TEXT` without `--wait` for callbacks. A busy
supervisor can consume a callback later; the worker yields after submitting.

For a new task, prefer input-ready submission. Verify consumption in transcript
before accepting output. Do not assume Codex Tab queue or AGY Escape staging
works in Claude. Any ambiguous composer/modal needs inspection before keys.

After canceling a native approval, the tested TUI showed “Interrupted · What
should Claude do instead?” and a ready composer while Herdr still classified it
as blocked. `agent prompt` rejected the correction. Root verified the exact
Claude process and empty composer, then used `pane send-text` for that
clarification, read the staged text, and sent one `pane send-keys ... enter`.
The same session consumed it. This answers the canceled operation; it is not a
new-task retry or permission bypass. Inspect before using this fallback.
For each approval, verify the currently selected option: a later dialog had
“switch to auto mode” selected. Choose and confirm the scoped one-time option
before Enter; do not assume the previous dialog's selection persists.

## Recovery and identity

Record native model/effort identity when observable; argv only proves requested
configuration. If startup rejects the selected profile, report exact rejection;
do not silently replace it with an alias or another account.

Before resuming, capture the exact session ID, verify the old process is dead,
inspect the clean shell and consult installed native resume help. Restore the
original scope, authority and return pane. Reconcile pending messages/effects
before retrying. General recovery and two-equivalent-failure stopping conditions
live in event-monitoring.md.

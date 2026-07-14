# Jean Computer Use Runbook

Use this reference before the first Jean UI action and whenever navigation or accessibility state becomes uncertain.

## Contents

- [Required runtime](#required-runtime)
- [Jean process invariant](#jean-process-invariant)
- [State-action-observation cycle](#state-action-observation-cycle)
- [Navigation discipline](#navigation-discipline)
- [Accessibility first, screenshot second](#accessibility-first-screenshot-second)
- [Prompt entry](#prompt-entry)
- [Notifications and approvals](#notifications-and-approvals)
- [Failure handling](#failure-handling)
- [Confirmation boundary](#confirmation-boundary)
- [Locked or inaccessible UI](#locked-or-inaccessible-ui)
- [Troubleshooting](#troubleshooting)

## Required runtime

Use the bundled `computer-use` skill and its `node_repl` plus `@oai/sky` wrapper. Do not substitute AppleScript, `osascript`, JXA, System Events, CGEvent synthesis, coordinate automation libraries, or a third-party Computer Use MCP unless the user explicitly requests that technology.

Bootstrap once per fresh `node_repl` session using the plugin-owned wrapper described by the bundled Computer Use skill. Do not import `@oai/sky` directly. Keep the JavaScript session persistent so `sky`, the current state, and helper imports remain available.

The relevant operations are:

- `sky.get_app_state({ app, disableDiff? })`
- `sky.list_apps()` only when the app cannot be resolved directly
- `sky.click({ app, element_index })`
- `sky.set_value({ app, element_index, value })`
- `sky.type_text({ app, text })`
- `sky.press_key({ app, key })`
- `sky.scroll({ app, element_index, direction, pages })`
- `sky.perform_secondary_action({ app, element_index, action })` only for actions exposed in accessibility text

Verify the exact live API surface from the bundled skill or runtime when it may have changed. Do not copy tool names from generic Computer Use skills.

## Jean process invariant

The open Jean process is durable orchestration state. It holds active sessions, backend selection, UI navigation, and context the user expects to remain intact.

Forbidden recovery actions:

- quitting Jean;
- force-quitting Jean;
- killing its process;
- relaunching the app over the running instance;
- restarting Jean's internal server by restarting the app;
- closing the main window as a troubleshooting experiment.

If Jean is not running at the start of a new task and the user asked to open it, `get_app_state` may launch it as normal Computer Use behavior. During an existing supervision or heartbeat, first use the live app list only to confirm that Jean is still running because `get_app_state` can launch a missing app. If it disappeared, do not relaunch it as recovery. Preserve repo/provider evidence, continue read-only work that does not need the UI, and surface the missing process only when UI action is the sole remaining blocker.

## State-action-observation cycle

Use Computer Use for visible identity, mode/model, approvals, prompt placement, and post-action proof. Use `scripts/jean_ops.py` for repeated read-only status observation. Do not keep refreshing the whole UI while an unchanged session watcher already owns the wait; return to fresh UI state on a material transition or immediately before a UI action.

For every UI decision:

1. Fetch current state.
2. Read the accessibility tree and current project/session header.
3. Choose an element from that state.
4. Perform one logical action or a tightly coupled pair.
5. Fetch current state again.
6. Verify the intended project/session/header before continuing.

Element indices are ephemeral. A click, scroll, notification, model change, session response, or sidebar refresh can renumber them. Never reuse an index obtained before a material UI change.

Prefer diff state for efficiency. Request a full tree with `disableDiff: true` when the diff lacks enough context or navigation is ambiguous.

## Navigation discipline

Jean's sidebar can reorder or shift rows as projects and sessions update. Labels may be truncated, repeated, or visually adjacent.

Use this order:

1. locate the project/session by accessible label in fresh state;
2. click its fresh `element_index`;
3. fetch state;
4. verify the main header, repository path, session title, or visible message history;
5. only then type or approve anything.

If the header does not match, stop. Fetch a full state and navigate again. Do not compensate with an old coordinate.

## Accessibility first, screenshot second

Prefer accessibility text for labels, enabled state, values, and exact controls. Use the screenshot when:

- the tree omits a visually present control;
- rows have indistinguishable labels;
- a menu or overlay is visually obvious but absent from the tree;
- layout or focus matters;
- an accessibility action failed after a fresh-state retry.

Coordinate clicks are the last fallback. Derive coordinates from the latest screenshot, account for its actual pixel dimensions, click once, and immediately verify the resulting state. Never keep a coordinate map across sidebar changes.

## Prompt entry

Before typing:

1. confirm the correct project and session;
2. confirm the input is editable and the send control's state;
3. use `set_value` on the input element when supported, otherwise focus then `type_text`;
4. fetch state to confirm the text landed in the intended input;
5. submit using the exposed send button or verified key behavior;
6. fetch state to confirm the prompt appears in the intended history and the session shows a new running/cancel state or another fresh progress marker.

Never paste a recovery prompt into a session selected only by sidebar position.

Jean MCP sends are fire-and-forget. A returned “started” value is not proof that a prompt entered a UI-owned session. Prefer the UI for the currently selected/running session; if MCP is used, verify both a fresh session status/message marker and the visible UI before treating the turn as active. Follow `jean-state-and-steering.md` when sources conflict.

## Notifications and approvals

Treat a Jean completion notification as a routing hint, not approval evidence.

For each completion:

1. open that notification/session;
2. identify project, branch/worktree, task scope, and claimed evidence;
3. compare it with the ledger and project instructions;
4. run or request the missing completion gates;
5. approve only the individually verified result;
6. retry or steer the same session when proof or implementation is incomplete.

Do not use “mark all read” or bulk approval as a substitute for review.

## Failure handling

If an action fails by app display name, refresh available apps and retry with Jean's bundle identifier. If multiple running Jean builds share that bundle identifier, choose the already-running intended app by its exact path from the live app list (normally the installed `/Applications/Jean.app`, not a development build), fetch full state, and verify the Jean/project header before acting. Do not launch or close either build to disambiguate it. If accessibility becomes incomplete, use a screenshot and fresh full state. If a control is disabled, determine its unmet UI precondition; do not restart the app.

When a session is producing output, avoid repeated clicks. Read fresh state at the monitoring cadence. When a tool is visibly frozen, use the bounded stall criteria in `derailment-recovery.md`; cancel only that agent turn.

## Confirmation boundary

Follow the bundled Computer Use confirmations policy. The user's authorization to supervise and approve Jean work covers routine internal Jean actions described in that request. It does not automatically authorize unrelated external messages, purchases, credential changes, data deletion, or other gated actions. Prepare those actions, then obtain any confirmation the live policy requires.

“Approve everything” or YOLO mode covers routine agent command approvals only. It never authorizes bulk completion approval, weakens independent verification, or overrides actions that the Computer Use policy requires confirming at action time.

## Locked or inaccessible UI

If macOS is locked, Jean has no accessible window, or accessibility temporarily fails:

1. confirm the condition with fresh app/accessibility state;
2. do not quit, kill, reopen, or click through another app to recover Jean;
3. continue safe read-only Jean MCP, git, CI, deploy, log, and transcript checks;
4. record which UI-only action remains;
5. retry on the next bounded check or heartbeat;
6. ask for unlock only when that UI-only action is the sole blocker and the live policy requires user presence.

## Troubleshooting

| Symptom | Response |
|---|---|
| Invalid element index | Fetch fresh state and re-derive the element |
| Wrong project opened | Stop, fetch full state, navigate by label, verify header |
| Missing control | Inspect screenshot, then fresh full accessibility tree |
| Typed into wrong field | Do not submit; clear safely and re-navigate |
| Jean appears unresponsive | Inspect session/tool state and recover in place; never restart |
| Screenshot and tree disagree | Treat current screenshot plus a fresh full tree as ground truth |
| Jean is absent during a continuing heartbeat | Do not call an action that auto-launches it; continue non-UI proof and report the UI blocker |
| MCP reports a turn but UI has no new prompt | Treat the turn as unstarted and resolve ownership before sending again |
| Bundle identifier resolves to two Jean builds | Use the exact path of the intended already-running app and verify its visible header |

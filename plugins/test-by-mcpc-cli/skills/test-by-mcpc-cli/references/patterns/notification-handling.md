# Notification Handling

Verified against `mcpc` 0.6.0. Sessions have first-class task commands and surface
list-changed / resource-update notification state through JSON.

## Where to inspect notification state

Use the **top-level** `mcpc --json` session list, not per-session JSON — the flat
`notifications` field lives on `.sessions[]` there. `mcpc --json @<session>` does **not**
carry a `_mcpc.notifications` key in 0.6.0 despite what the README's prose implies; only
the global list exposes it (confirmed by reading the shipped `sessions.js`/`connect.js`
source and live-testing both JSON shapes).

```bash
mcpc --json | jq '.sessions[] | select(.name=="@my-session") | .notifications'
```

## What to watch

- `tools.listChangedAt`
- `prompts.listChangedAt`
- `resources.listChangedAt`

The whole `notifications` field is absent (`null`) until the first list-changed event of
any kind fires. After that, all three type keys (`tools`, `prompts`, `resources`) appear —
possibly as empty objects — but `listChangedAt` itself only appears under the type that
actually fired; a missing `listChangedAt` means "not observed yet," not an error.
`tools-list`/`prompts-list`/`resources-list` stay current either way; these timestamps are
just the audit trail. On `2026-07-28` connections there are no unsolicited server
notifications — the bridge instead opens a `subscriptions/listen` stream at connect and
re-opens it automatically if it drops, so the observable behavior (fresh lists, updated
timestamps) is unchanged from the CLI side.

## Resources and subscriptions

```bash
mcpc @everything-http resources-subscribe demo://resource/dynamic/text/1 ./text-sync.json
mcpc @everything-http resources-unsubscribe demo://resource/dynamic/text/1
```

`<file>` is required (since v0.4.0): the bridge downloads the resource immediately, then
rewrites `<file>` on every `notifications/resources/updated` event while connected. To
prove an update notification actually fired (not just that the file happens to match),
correlate the file's mtime with `mcpc @everything-http logs | rg
'resources/updated|resource-sync'`. Sync mechanics and the `resourceSubscriptions` JSON
field live in `references/guides/tool-resource-testing.md`; this file is about observing
the notification itself.

## Tasks are first-class

```bash
mcpc @everything-http tools-call simulate-research-query topic:='"notify"' --task
mcpc @everything-http tools-call simulate-research-query topic:='"detach"' --detach
mcpc @everything-http tasks-list
mcpc @everything-http tasks-get <taskId>
mcpc @everything-http tasks-result <taskId>
mcpc @everything-http tasks-cancel <taskId>
```

`tasks-result <taskId>` recovers a detached task's final result body — including from a
separate process invocation — not just its status.

## Deprecation warnings aren't failures

`logging-set-level` still succeeds (exit `0`) on `2025-11-25` servers despite printing `⚠
logging-set-level is deprecated ... will be removed in a future mcpc release` — that's
advance notice about a **future** spec version dropping the underlying request, not a
report that the current call failed. On an actual `2026-07-28` connection it errors
outright instead of warning.

`shell` — previously the only place server log messages (`notifications/message`) were
visible live — was removed in v0.4.0; those messages now go straight to the bridge log,
read them with `mcpc @<session> logs`.

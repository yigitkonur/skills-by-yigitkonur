# Notification Handling

`mcpc 0.2.x` has first-class task commands and still surfaces list-changed notification state through session metadata.

## Where to inspect notification state

Use top-level session JSON, not `mcpc --json @session`, when you want stored notification timestamps.

```bash
mcpc --json | jq '.sessions[] | select(.name == "@my-session") | .notifications'
```

## What to watch

- `tools.listChangedAt`
- `prompts.listChangedAt`
- `resources.listChangedAt`

These timestamps tell you that discovery caches were invalidated and refreshed.

## Resources and subscriptions

```bash
mcpc @everything-http resources-subscribe demo://resource/dynamic/config
mcpc @everything-http resources-unsubscribe demo://resource/dynamic/config
```

Use bridge logs together with session JSON when you need to prove a subscription update happened.

## Tasks are no longer “unsupported”

Use the public task surface directly:

```bash
mcpc @everything-http tools-call simulate-research-query topic:='"notify"' --task
mcpc @everything-http tools-call simulate-research-query topic:='"detach"' --detach
mcpc @everything-http tasks-list
mcpc @everything-http tasks-get <taskId>
mcpc @everything-http tasks-cancel <taskId>
```

## Shell note

`shell` is session-only in `0.2.4`.
Do not document direct-URL shell commands.

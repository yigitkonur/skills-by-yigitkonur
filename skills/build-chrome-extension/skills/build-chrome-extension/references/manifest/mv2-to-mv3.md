# MV2 to MV3

Treat MV2 to MV3 migration as a runtime model change, not a search-and-replace job.

## Required moves

- replace background pages with a service worker
- move long-lived state out of globals and into `chrome.storage.*`
- replace timer-driven background loops with events or `chrome.alarms`
- review blocking network logic for `declarativeNetRequest`
- update permissions and host permissions explicitly

## Migration checklist

1. Remove `"background.page"` and add `"background.service_worker"`.
2. Audit every global variable in background code.
3. Move DOM-dependent background work to popup, offscreen documents, or content scripts.
4. Re-check messaging because the worker can restart between messages.
5. Re-test install, update, browser restart, and idle wake-up behavior.

## Common traps

- assuming service worker globals survive between events
- leaving listeners inside async setup paths instead of top-level registration
- forgetting that DOM APIs are unavailable in the worker
- carrying over broad MV2 permissions without re-validating need

## Fast decision rule

If the old extension relied on always-on background state, redesign that flow first.
That is the highest-risk MV3 breakage.

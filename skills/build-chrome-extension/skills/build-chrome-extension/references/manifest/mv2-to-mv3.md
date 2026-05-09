# MV2 to MV3

Treat MV2 to MV3 migration as a runtime model change, not a search-and-replace job.

Verified: 2026-05-09 against Chrome's official [Manifest V2 support timeline](https://developer.chrome.com/docs/extensions/develop/migrate/mv2-deprecation-timeline).

## Current timeline

- July 24, 2025: Manifest V2 was disabled everywhere with Chrome 138; users can no longer re-enable MV2 extensions.
- Chrome 139 removes enterprise policy support for MV2. MV2 extensions cease functioning for users upgrading to Chrome 139 and later.

## Required moves

- replace background pages with a service worker
- move long-lived state out of globals and into `chrome.storage.*`
- replace timer-driven background loops with events or `chrome.alarms`
- replace blocking `webRequest` logic with `declarativeNetRequest`; blocking `webRequest` remains available only for policy-installed MV3 extensions
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

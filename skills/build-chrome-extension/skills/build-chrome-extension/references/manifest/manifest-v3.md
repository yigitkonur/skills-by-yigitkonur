# Manifest V3

Use Manifest V3 as the default target for new Chrome extensions.

## Minimum rules

- set `"manifest_version": 3`
- use a service worker instead of a persistent background page
- keep permissions minimal
- prefer optional permissions when a capability is not needed at install time
- declare content scripts, host permissions, action, options, and side panel explicitly

## Minimal starting point

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "description": "A brief description.",
  "permissions": ["storage"],
  "action": {
    "default_popup": "popup/index.html"
  },
  "background": {
    "service_worker": "background.js",
    "type": "module"
  }
}
```

## High-signal checks

- every referenced file path must exist in the built output
- background logic must tolerate service worker restarts
- host permissions must match the real target origins
- if the extension injects code dynamically, request `scripting`
- if the extension uses a side panel, declare `"side_panel"`

## When manifest bugs happen

- popup does not open: check `action.default_popup`
- background logic never runs: check `background.service_worker`
- content script does not inject: check `content_scripts.matches` or runtime `chrome.scripting` usage
- runtime permission errors: check `permissions` and `host_permissions`

Route permission details to `references/manifest/permissions.md`.

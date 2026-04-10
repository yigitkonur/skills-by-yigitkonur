# Permissions

Ask for the smallest permission set that makes the feature work.

## Core rule

- use install-time permissions only when the extension cannot function without them
- use optional permissions for feature paths the user triggers later
- keep host access as narrow as possible

## Common permissions

| Permission | Use when |
|---|---|
| `storage` | persisting settings or state |
| `tabs` | reading tab metadata or acting on tabs |
| `scripting` | injecting scripts or CSS at runtime |
| `activeTab` | temporary access to the current tab after user action |
| `alarms` | scheduled wakeups from the service worker |
| `sidePanel` | side panel UI |
| `declarativeNetRequest` | rule-based request modification or blocking |

## Host permissions

- prefer exact origins over wildcards
- separate `host_permissions` from generic API permissions
- if a feature is user-triggered, consider requesting host access at runtime

## Review checklist

- can `activeTab` replace a broad host wildcard
- can an optional permission replace an install-time permission
- does the extension justify every store-visible permission prompt
- do content scripts and runtime injection target only the domains they need

## Failure pattern

If a feature works in development but fails with permission errors in the packed extension, compare:

- `permissions`
- `optional_permissions`
- `host_permissions`
- any runtime `chrome.permissions.request()` flow

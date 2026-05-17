# Chrome Web Store Review Readiness

Prepare a Chrome MV3 extension for Web Store submission and review.

Verified: 2026-05-09 against official Chrome Web Store docs:

- [Publish in the Chrome Web Store](https://developer.chrome.com/docs/webstore/publish)
- [Fill out the privacy fields](https://developer.chrome.com/docs/webstore/cws-dashboard-privacy)
- [Quality guidelines](https://developer.chrome.com/docs/webstore/program-policies/quality-guidelines/)
- [Troubleshooting Chrome Web Store violations](https://developer.chrome.com/docs/webstore/troubleshooting/)
- [Accepting Payment From Users](https://developer.chrome.com/docs/webstore/program-policies/accepting-payment)
- [Manifest V2 support timeline](https://developer.chrome.com/docs/extensions/develop/migrate/mv2-deprecation-timeline)

## Submission Dashboard

Use the official [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole). The official publish guide still routes uploads there.

Upload flow:

1. Sign in to the publisher account.
2. Add a new item.
3. Upload the production zip.
4. Complete Package, Store Listing, Privacy, Distribution, and Test instructions tabs.
5. Submit for review.

## Package Gate

Run these before creating the zip:

```bash
scripts/check-mv3-manifest.sh <built-output>
scripts/preflight-extension.sh <built-output>
```

Create the zip from inside the built output folder so `manifest.json` is at the zip root:

```bash
(cd dist && zip -r ../extension.zip . -x "*.DS_Store" "__MACOSX/*")
```

Package must exclude:

- source maps unless deliberately shipped
- tests and test fixtures
- `.DS_Store`
- `__MACOSX`
- repo metadata such as `.git`, `.github`, `node_modules`
- source-only files not loaded by Chrome

## Required Listing Assets

| Asset | Requirement |
|---|---|
| Store icon | 128x128 PNG |
| Manifest icon | 128x128 PNG minimum; include smaller sizes when used |
| Screenshot | At least one 1280x800 or 640x400 image |
| Description | Match actual behavior and single purpose |
| Support/contact | Use a monitored channel |
| Privacy policy URL | Required when data collection or sensitive permissions apply; recommended for most extensions |

## Privacy Practices Tab

The Privacy practices tab is a review gate, not an afterthought.

Fill these fields with review-ready detail:

| Field | Review-ready answer |
|---|---|
| Single purpose | One narrow, easy-to-understand purpose aligned with the listing and actual behavior |
| Permission justifications | One specific sentence per permission and host permission |
| Remote code | State whether remote executable code is used; MV3 cannot load remote hosted executable files |
| Data use | Disclose collected user data categories and certify limited-use compliance |
| Privacy policy | Must match the data-use disclosures and remote services actually used |
| Test instructions | Credentials, setup, feature flags, and reviewer path when needed |

## Permission Justification Pattern

Use concrete feature language:

| Permission | Weak | Better |
|---|---|---|
| `tabs` | Needed for functionality | Reads tab URLs to detect duplicate tabs and shows the duplicates in the popup for user selection |
| `activeTab` | Access current page | Activated only after toolbar click to read the current page text for the displayed word count |
| `storage` | Store data | Stores extension settings locally; data is not transmitted externally |
| `alarms` | Background tasks | Schedules the user-configured daily price check |
| `notifications` | Notify users | Shows a notification only when a tracked price crosses the configured threshold |
| `scripting` | Run scripts | Injects a content script into matched product pages after user action |
| Host permission | API access | Sends requests to the declared API origin for the feature named in the listing |

## Single-Purpose And Quality Gate

Chrome's quality guidelines require a narrow, understandable single purpose.

Reject-risk signals:

- unrelated features bundled together
- side panel hijacking browsing/search behavior instead of complementing the current task
- ad-serving as the primary purpose
- listing text that promises behavior the extension does not provide
- minimum-functionality extension that could be a bookmark or trivial redirect
- excessive permissions unrelated to the stated purpose
- broken core workflow after load

Fix by cutting features, splitting unrelated capabilities into separate extensions, or rewriting listing/permissions to match the actual product.

## Remote Code And MV3

MV3 extensions must not load and execute remote hosted code.

Safe pattern:

- bundle executable JavaScript with the extension package
- fetch remote data, JSON, images, or configuration only as data
- validate and sanitize fetched data before displaying it
- disclose remote services and data use in Privacy practices

Reject-risk pattern:

- remote `<script src="https://...">`
- CDN JavaScript in extension pages
- `eval()`, `new Function()`, dynamic remote modules
- undeclared remote-code use in Privacy practices

## MV2 Policy Note

Verified: 2026-05-09 against the official MV2 timeline.

- July 24, 2025: MV2 was disabled everywhere with Chrome 138; users cannot re-enable MV2 extensions.
- Chrome 139 removes enterprise policy support for MV2.
- New or updated Web Store guidance should target MV3 only.

## Review Checklist

Before submission:

- `manifest_version` is `3`.
- built output loads locally in Chrome.
- `scripts/check-mv3-manifest.sh` passes.
- `scripts/preflight-extension.sh` passes or review-only warnings are documented.
- every permission and host permission has a feature-level justification.
- broad host access has a narrower alternative analysis.
- single purpose appears consistently in listing, Privacy practices, and actual behavior.
- data collection, remote services, analytics, and error reporting match the privacy policy.
- remote executable code is absent.
- screenshots show real extension behavior, not marketing-only art.
- test instructions let reviewers exercise gated flows.
- MV2-only APIs and `background.scripts` are absent.

## Update Workflow

For an existing item:

1. Bump `manifest.json` version.
2. Build production output.
3. Run manifest and preflight scripts.
4. Zip from built output root.
5. Upload through Chrome Developer Dashboard.
6. Update Privacy practices if permissions, host access, remote services, or data use changed.
7. Add reviewer notes for changed behavior.

Use deferred publishing when release timing matters. If a bug is found after submission but before review completes, cancel the pending review, upload a corrected package, and resubmit.

## Payments

Use an external payment and license system for current monetization. Follow the Chrome Web Store payment policy for truthful pricing, seller identification, terms, refunds, sensitive data handling, and prohibited transactions. Do not present Chrome Web Store Payments as a viable new integration unless current official docs are re-verified first.

## Final Report Fields

Web Store work should report:

- zip path
- built output folder
- script results
- Chrome version used for manual load, when tested
- permission justification summary
- Privacy practices notes
- single-purpose statement
- remote-code/data-use posture
- MV2/MV3 policy note
- known reviewer risks or manual checks

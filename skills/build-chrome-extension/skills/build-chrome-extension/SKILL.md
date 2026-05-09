---
name: build-chrome-extension
description: Use skill if you are building or debugging a Chrome MV3 extension with service workers, content scripts, popup/sidepanel, messaging, storage, permissions, testing, or Web Store publishing.
---

# Build Chrome Extension

Build, debug, package, and prepare Chrome Manifest V3 extensions for Web Store review.

## Trigger Boundary

Use this skill for Chrome MV3 extension work:

- creating a new Chrome MV3 extension
- adding extension surfaces: content scripts, popup, options, side panel, service worker, offscreen document
- fixing MV3 lifecycle, messaging, storage, manifest, permission, or content-script issues
- migrating a Chrome extension from MV2 to MV3
- choosing a Chrome MV3 extension framework
- validating built output, packaging a Web Store zip, or preparing Web Store review notes

Do not use this skill for:

- Firefox, Safari, or cross-browser extension builds; route to a browser-extension skill with that scope
- Edge enterprise-policy extension deployment or managed policy packaging
- generic website, app, or component work without Chrome extension APIs
- generic browser automation; use `run-playwright` or `run-agent-browser`
- writing Playwright suites beyond extension-specific launch/load patterns; use `run-playwright`
- npm/package-registry publishing; use `publish-npm-package`
- Raycast or other platform extension artifacts; use the platform-specific skill such as `build-raycast-script-command`

## Pinned Defaults

| Key | Default |
|---|---|
| Manifest target | MV3 only; never generate MV2 |
| Greenfield framework | WXT unless the repo already dictates another Chrome MV3 tool |
| State model | Persistent state in `chrome.storage.local`; ephemeral restart-safe state in `chrome.storage.session` |
| Background model | Event-driven service worker with top-level listeners |
| Network modification | `declarativeNetRequest`, not blocking `webRequest` |
| Permissions | Least privilege; prefer runtime optional permissions |
| Loaded folder | Built output only: WXT `.output/chrome-mv3-dev/` or `.output/chrome-mv3/`, Plasmo `build/chrome-mv3-*`, CRXJS/vanilla `dist/` |
| Package preflight | Run the bundled manifest and package scripts before zipping |

## MV3 Footguns

Keep these in working memory before generating files:

- Service workers idle out; global state disappears. Persist state before and after meaningful work.
- Register all service-worker event listeners synchronously at top level.
- `setTimeout` and `setInterval` do not make background work reliable. Use `chrome.alarms`.
- Async `chrome.runtime.onMessage` handlers must return `true` synchronously.
- Content scripts run in isolated worlds by default. Use MAIN world only for page-JS access, then bridge safely.
- Extension-origin fetches need `host_permissions`; content-script fetches remain subject to the page origin.
- MV3 blocks inline scripts, `eval()`, `new Function()`, and remote executable code.
- Hand-written manifests must point at built files, not `src/*.ts` or source-only HTML.

## Decision Rules

Use these rules before writing code:

| Decision | Default | Escalate when |
|---|---|---|
| Background state | Persist through `chrome.storage.session` or `chrome.storage.local` | State needs transactions, large indexes, or binary blobs; consider IndexedDB |
| Periodic work | `chrome.alarms` | Work needs continuous real-time transport; design reconnect and queue behavior |
| Network changes | `declarativeNetRequest` | Read-only observation is enough; use non-blocking `webRequest` only for observation |
| Page data fetch | Service worker fetch with host permissions | Content script can safely use the page origin without extra privileges |
| Page JS access | MAIN world bridge with validation | DOM-only access is enough; stay in ISOLATED world |
| UI persistence | `chrome.storage.session` for transient UI state | Settings or user choices must survive browser restart; use `local` or `sync` |
| Host access | `activeTab` or optional host permissions | The extension cannot function without install-time host access |
| Side panel | Use for persistent companion workflows | A quick action or short form fits in popup |
| Offscreen document | Use only for DOM, canvas, clipboard, audio, or worker needs from the service worker | Popup/options/content script can own the DOM work |

## Chrome-Only Boundary Matrix

| Request shape | Action |
|---|---|
| "Build a Chrome extension" | Use this skill; target MV3 |
| "Build a browser extension for Chrome and Firefox" | Keep Chrome MV3 here; route cross-browser build rules elsewhere |
| "Automate this website in a browser" | Use `run-playwright` or `run-agent-browser` |
| "Write Playwright tests for an extension" | Keep extension launch/load notes here; route test-suite authoring to `run-playwright` |
| "Publish the package to npm" | Use `publish-npm-package` |
| "Submit to Chrome Web Store" | Use this skill; read Web Store reference |
| "Deploy through enterprise policy" | Treat as out of scope unless the repo has a dedicated enterprise policy skill |

## Minimal Build Evidence

Before stopping, collect the smallest proof that matches the task:

| Task | Evidence |
|---|---|
| New scaffold | built output path plus manifest check script result |
| Feature change | relevant unit/integration test plus manual load note when Chrome behavior changed |
| Manifest/permission change | manifest check script result plus permission justification |
| Content-script change | allowed URL and disallowed URL injection result |
| Service-worker change | restart-resilience note or explicit not-exercised caveat |
| Package/Web Store work | package preflight result, zip path, and review notes |

## Workflow

### 1. Scope The Extension

**Think first:** "Which extension contexts exist, which Chrome APIs are required, and which permissions can be delayed until runtime?"

1. Identify required surfaces: popup, options, side panel, content script, service worker, offscreen document.
2. Identify Chrome APIs and required permissions.
3. Choose install-time vs optional permissions.
4. Choose framework using `references/frameworks/comparison.md`.
5. Record the built output folder that Chrome will load.

### 2. Scaffold Or Adapt

**Think first:** "Is this a greenfield Chrome MV3 build, an existing framework build, or a hand-written manifest?"

- Greenfield default: WXT.
- Existing Vite app becoming an extension: CRXJS if it keeps the change small.
- Explicit manual control or custom build: vanilla + Vite.
- Existing repo: follow the repo's framework and output conventions.

Use built output only. Chrome should never load `src/`, framework cache directories, or unbundled TypeScript.

### 3. Implement Extension Contexts

**Think first:** "Which context owns the state, which context owns the DOM, and which messages cross the boundary?"

- Service worker: read `references/patterns/service-worker.md`.
- Content scripts: read `references/patterns/content-scripts.md`.
- Popup/options/side panel: read `references/patterns/ui-surfaces.md`.
- Messaging: read `references/apis/messaging.md`.
- Storage: read `references/apis/storage.md`.
- Permissions and runtime grants: read `references/manifest/permissions.md`.
- Core APIs: read `references/apis/core-apis.md`.

Keep UI logic separate from extension plumbing when practical. Validate messages, storage reads, external API data, and content-script bridge payloads at boundaries.

### 4. Validate Built Output

**Think first:** "Can Chrome load this exact output folder, and do all manifest paths exist there?"

Run the bundled checks from the skill directory:

```bash
scripts/check-mv3-manifest.sh dist
scripts/preflight-extension.sh dist
```

Adjust the path for framework output:

| Framework | Dev output | Production output |
|---|---|---|
| WXT | `.output/chrome-mv3-dev/` | `.output/chrome-mv3/` |
| Plasmo | `build/chrome-mv3-dev/` | `build/chrome-mv3-prod/` |
| CRXJS | `dist/` | `dist/` |
| Vanilla Vite | `dist/` | `dist/` |

Read `scripts/check-mv3-manifest.md` and `scripts/preflight-extension.md` before changing either script.

### 5. Test Extension Behavior

**Think first:** "What failure would only appear after Chrome loads the extension?"

Keep this skill focused on extension-specific checks:

- Unit-test pure logic and message/storage helpers.
- Mock `chrome.*` only at test boundaries.
- Manually load the built output in `chrome://extensions`.
- Inspect the service worker from `chrome://extensions`.
- Test service-worker restart resilience.
- Test content-script injection on allowed and disallowed URLs.
- Verify runtime permission request UX.

Read `references/testing/testing-guide.md` for extension-specific testing. Route broad browser automation or full Playwright authoring to `run-playwright` or `run-agent-browser`.

### 6. Package For Web Store Review

**Think first:** "Would a reviewer understand the single purpose, permission need, data use, and remote-code posture?"

1. Build production output.
2. Run both bundled scripts against the production output.
3. Remove junk before zipping: source maps unless intentionally shipped, tests, `.DS_Store`, `__MACOSX`, local caches.
4. Create the package zip from inside the built output folder.
5. Prepare Privacy practices, permission justifications, remote-code disclosure, data-use certification, and test instructions.
6. Read `references/publishing/web-store.md` before submission.

## Canonical Routing

| Need | Read |
|---|---|
| Manifest shape, required fields, output-path checks | `references/manifest/manifest-v3.md` |
| MV2 to MV3 migration | `references/manifest/mv2-to-mv3.md` |
| Install-time, optional, host, and runtime permissions | `references/manifest/permissions.md` |
| Service-worker lifecycle, persistence, alarms, offscreen documents | `references/patterns/service-worker.md` |
| Content-script injection, worlds, idempotency, cross-origin request routing | `references/patterns/content-scripts.md` |
| Popup, options, side panel, DevTools, new-tab surfaces | `references/patterns/ui-surfaces.md` |
| One-time messages, ports, external/native messaging, page bridges | `references/apis/messaging.md` |
| `chrome.storage` areas, quotas, typed wrappers, migrations | `references/apis/storage.md` |
| Tabs, scripting, alarms, DNR, side panel, offscreen, runtime APIs | `references/apis/core-apis.md` |
| WXT, Plasmo, CRXJS, vanilla Vite selection for Chrome MV3 | `references/frameworks/comparison.md` |
| Extension-specific tests and Chrome load checks | `references/testing/testing-guide.md` |
| Debugging service worker, popup, content script, permissions, storage | `references/testing/debugging.md` |
| Web Store listing, privacy, policy, package, review readiness | `references/publishing/web-store.md` |
| Built manifest sanity check script | `scripts/check-mv3-manifest.md` |
| Package/Web Store preflight script | `scripts/preflight-extension.md` |

## Output Contract

Final reports for Chrome extension work should include:

- loaded build directory
- zip path, when packaged
- Chrome version used for manual load, when manually tested
- permissions and host-permissions justification summary
- Web Store policy notes: single purpose, data use, remote code, MV2/MV3 posture
- scripts and tests run, including any failures
- reviewer notes for remaining manual checks

## Guardrails

- Never generate or preserve Manifest V2 for new work.
- Never load source folders in Chrome unless the framework explicitly outputs loadable code there.
- Never use global variables as durable service-worker state.
- Never rely on timers to keep the service worker alive.
- Never use blocking `webRequest` for normal MV3 network modification.
- Never request `<all_urls>` without a feature-level justification and narrower alternatives.
- Never expose arbitrary background fetch through content-script messages.
- Never ship remote executable code or undeclared remote-code behavior.
- Always validate built output paths against `manifest.json`.
- Always make extension permissions explainable in one sentence each.

## Bottom Line

Build Chrome MV3 around restart-safe state, top-level service-worker listeners, least-privilege permissions, built-output validation, and Web Store review evidence. Route tutorials to references; keep the spine for decisions, defaults, and proof.

# Chrome Web Store Publishing Guide (Manifest V3)

## Developer Account Setup

1. Go to the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
2. Sign in with a Google account (use a team/org account for team-owned extensions)
3. Pay the **one-time $5 registration fee**
4. Accept the developer agreement
5. Verify your email address (required before publishing)

**Important considerations:**
- The account that registers owns the extension listing forever — choose carefully
- You can add other developers as group publishers later
- The registered email receives review notifications, policy violations, and user reviews

---

## Required Store Listing Assets

| Asset | Dimensions | Format | Required | Notes |
|-------|-----------|--------|----------|-------|
| Extension icon (in manifest) | 128x128 px | PNG | Yes | Shown in store and `chrome://extensions` |
| Store icon | 128x128 px | PNG | Yes | Uploaded separately to dashboard |
| Screenshot (at least 1) | 1280x800 or 640x400 | PNG, JPEG | Yes | At most 5; show key features |
| Small promo tile | 440x280 | PNG, JPEG | No | Used in store listings and search |
| Large promo tile (marquee) | 1400x560 | PNG, JPEG | No | For featured placement |
| Promotional video | YouTube URL | — | No | Shown at top of listing |

### Icon Sizes in manifest.json

```json
{
  "icons": {
    "16": "icons/icon-16.png",
    "32": "icons/icon-32.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  }
}
```

| Size | Used For |
|------|----------|
| 16x16 | Favicon, tab context menus |
| 32x32 | Windows taskbar shortcut |
| 48x48 | Extensions management page |
| 128x128 | Chrome Web Store, installation dialog |

---

## Store Listing Best Practices

### Title (max 75 characters)

- Lead with your extension's name, not a keyword dump
- Good: `"TabSaver — Save and Restore Tab Groups"`
- Bad: `"Best Tab Manager Extension Free Tab Saver 2025"`

### Short Description (max 132 characters)

Shown in search results. Make every character count.

```
Save, organize, and restore browser tab groups with one click. Reduce memory usage by suspending inactive tabs.
```

### Detailed Description (max 16,384 characters)

Structure:

```
[One-line value proposition]

Features:
• Feature 1 — brief explanation
• Feature 2 — brief explanation
• Feature 3 — brief explanation

How it works:
1. Step one
2. Step two
3. Step three

Privacy:
This extension does not collect any personal data. All data is stored locally on your device.

Support:
Report issues at https://github.com/yourname/extension/issues
```

### Category Selection

| Category | Best For |
|----------|----------|
| Productivity | Tab managers, note-taking, time tracking |
| Developer Tools | Code utilities, debugging, API tools |
| Search Tools | Search enhancers, URL tools |
| Shopping | Price trackers, coupon finders |
| Social & Communication | Social media enhancers |
| Accessibility | Screen readers, color adjusters, magnifiers |
| Fun | Themes, games, entertainment |

---

## Privacy Policy

### Requirements

A privacy policy is **required** if your extension:
- Collects any user data (even anonymized analytics)
- Uses `host_permissions` for any site
- Uses permissions like `tabs`, `history`, `bookmarks`, `cookies`
- Sends any data to a remote server

In practice, **almost every extension needs one**. Host it on a publicly accessible URL.

### Minimal Privacy Policy Template

```markdown
# Privacy Policy for [Extension Name]

Last updated: [Date]

## Data Collection
[Extension Name] does not collect, transmit, or share any personal data. All user
preferences and settings are stored locally on your device using Chrome's built-in
storage API (chrome.storage.local).

## Permissions Justification
- **activeTab**: Used to interact with the current page only when you click the
  extension icon. No data is read or stored from the page.
- **storage**: Used to save your preferences locally on your device.

## Third-Party Services
This extension does not use any third-party analytics, tracking, or advertising services.

## Changes to This Policy
Any changes will be posted on this page with an updated revision date.

## Contact
For questions about this policy, contact: [your-email@example.com]
```

If your extension **does** collect data (e.g., error reporting, analytics):

```markdown
## Data Collection
[Extension Name] collects the following data:
- **Error reports**: Crash data including stack traces (no personal information)
  sent to [Service Name] for debugging purposes.
- **Usage analytics**: Anonymous feature usage counts (e.g., "button clicked 5 times")
  sent to [Service Name]. No browsing history, page content, or personal identifiers
  are included.

You can opt out of data collection in the extension's settings page.
```

---

## Permission Justification Writing Guide

When submitting, you must justify each permission. Reviewers reject vague justifications.

| Permission | Bad Justification | Good Justification |
|-----------|-------------------|-------------------|
| `tabs` | "Needed for functionality" | "Used to read tab URLs to detect duplicate tabs and offer to close them. Tab titles are displayed in the extension popup for the user to select which duplicates to close." |
| `activeTab` | "To access the page" | "Activated only when the user clicks the extension icon. Reads the current page's text content to calculate word count and reading time, displayed in the popup." |
| `storage` | "To store data" | "Stores user preferences (theme, language, blocked site list) locally. No data is transmitted externally." |
| `alarms` | "For background tasks" | "Schedules a daily check at the user-configured time to compare saved prices against current prices and show a notification if a price drops." |
| `notifications` | "To notify users" | "Displays a desktop notification when a tracked product's price drops below the user-set threshold." |
| `host_permissions: *://api.example.com/*` | "API access" | "Sends requests to our API endpoint to fetch price data for products the user is tracking. No page content or browsing data is sent." |
| `scripting` | "To run scripts" | "Injects a content script into e-commerce product pages (matched by URL pattern) to extract the product name and price for the user's price tracking list." |

---

## Building and Packaging for Submission

### Build Script

```bash
#!/bin/bash
# scripts/build.sh

set -e

# Clean previous build
rm -rf dist extension.zip

# Build the extension (adjust for your bundler)
npm run build

# Verify manifest exists
if [ ! -f dist/manifest.json ]; then
  echo "ERROR: dist/manifest.json not found"
  exit 1
fi

# Remove development-only files
rm -f dist/**/*.map
rm -f dist/**/*.test.*

# Create zip for Chrome Web Store
cd dist
zip -r ../extension.zip . -x "*.DS_Store" -x "__MACOSX/*"
cd ..

echo "Created extension.zip ($(du -h extension.zip | cut -f1))"
```

### Pre-Submission Checklist

```typescript
// scripts/validate-manifest.ts
import { readFileSync } from "fs";

const manifest = JSON.parse(readFileSync("dist/manifest.json", "utf-8"));

const checks = [
  ["manifest_version === 3", manifest.manifest_version === 3],
  ["name is set", typeof manifest.name === "string" && manifest.name.length > 0],
  ["version is semver", /^\d+\.\d+\.\d+$/.test(manifest.version)],
  ["description ≤ 132 chars", manifest.description?.length <= 132],
  ["icons.128 exists", !!manifest.icons?.["128"]],
  ["no localhost in permissions", !JSON.stringify(manifest).includes("localhost")],
  ["no http:// in host_permissions",
    !(manifest.host_permissions ?? []).some((p: string) => p.startsWith("http://") && !p.includes("localhost"))],
] as const;

let allPassed = true;
for (const [label, result] of checks) {
  console.log(result ? `  PASS  ${label}` : `  FAIL  ${label}`);
  if (!result) allPassed = false;
}

if (!allPassed) {
  process.exit(1);
}
console.log("\nAll checks passed.");
```

---

## Version Bumping

Use semver in `manifest.json`:

```json
{
  "version": "1.2.3"
}
```

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Bug fixes, minor tweaks | Patch: `1.2.3` → `1.2.4` | Fix popup not closing |
| New features, backward compatible | Minor: `1.2.3` → `1.3.0` | Add dark mode |
| Breaking changes, major overhaul | Major: `1.2.3` → `2.0.0` | New UI, changed storage schema |

**Automate version bumping:**

```bash
# scripts/bump-version.sh
#!/bin/bash
# Usage: ./scripts/bump-version.sh patch|minor|major

LEVEL=${1:-patch}
CURRENT=$(node -p "require('./dist/manifest.json').version")
NEW=$(npx semver $CURRENT -i $LEVEL)

# Update manifest.json
node -e "
  const fs = require('fs');
  const m = JSON.parse(fs.readFileSync('src/manifest.json', 'utf-8'));
  m.version = '$NEW';
  fs.writeFileSync('src/manifest.json', JSON.stringify(m, null, 2) + '\n');
"

echo "Bumped version: $CURRENT → $NEW"
```

---

## Review Process

### Timeline

| Submission Type | Typical Review Time |
|----------------|-------------------|
| New extension | 1–5 business days |
| Update (no new permissions) | 1–3 business days |
| Update (new sensitive permissions) | 3–7 business days |
| After rejection (resubmission) | 1–5 business days |
| Appeal | 7–14 business days |

### Common Rejection Reasons

| Reason | Description | Fix |
|--------|-------------|-----|
| **Single purpose violation** | Extension does too many unrelated things | Focus on one core feature; split into multiple extensions |
| **Missing privacy policy** | Required when using certain permissions | Add a hosted privacy policy URL |
| **Excessive permissions** | Requesting `<all_urls>` without justification | Use `activeTab` instead; narrow `host_permissions` |
| **Keyword spam in listing** | Title or description stuffed with keywords | Write natural, user-focused copy |
| **Deceptive functionality** | Extension does not do what the listing claims | Align listing text with actual behavior |
| **Broken functionality** | Extension crashes or key features do not work | Test thoroughly before submission |
| **Remote code execution** | Loading and executing remote JS (`eval`, remote `<script>`) | Bundle all code locally; use `fetch` only for data |
| **Missing or inadequate justification** | Permission justification text is too vague | Write specific, detailed justifications (see table above) |
| **User data policy violation** | Collecting data not disclosed in privacy policy | Disclose all data collection; add opt-out |
| **Minimum functionality** | Extension is too simple (e.g., single redirect) | Add meaningful functionality beyond what a bookmark provides |

---

## Update Workflow

### Incremental Rollout

The Chrome Web Store supports partial rollout for updates:

1. Upload new version in the Developer Dashboard
2. Under **Distribution** → select "Publish to a percentage of users"
3. Start with 5–10%, monitor for crashes/complaints
4. Increase to 50%, then 100%

### Automated Publishing with chrome-webstore-upload

```bash
npm install -D chrome-webstore-upload-cli
```

```yaml
# .github/workflows/publish.yml
name: Publish to Chrome Web Store

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - run: cd dist && zip -r ../extension.zip .
      - name: Upload to Chrome Web Store
        run: npx chrome-webstore-upload-cli upload --source extension.zip --auto-publish
        env:
          EXTENSION_ID: ${{ secrets.CWS_EXTENSION_ID }}
          CLIENT_ID: ${{ secrets.CWS_CLIENT_ID }}
          CLIENT_SECRET: ${{ secrets.CWS_CLIENT_SECRET }}
          REFRESH_TOKEN: ${{ secrets.CWS_REFRESH_TOKEN }}
```

### Generating OAuth Credentials for CWS API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project (or use existing)
3. Enable the **Chrome Web Store API**
4. Create **OAuth 2.0 Client ID** (Desktop application)
5. Use the client ID and secret to generate a refresh token:

```bash
# Get authorization code (opens browser)
open "https://accounts.google.com/o/oauth2/auth?response_type=code&scope=https://www.googleapis.com/auth/chromewebstore&client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob"

# Exchange code for refresh token
curl -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=YOUR_CLIENT_ID&client_secret=YOUR_SECRET&code=AUTH_CODE&grant_type=authorization_code&redirect_uri=urn:ietf:wg:oauth:2.0:oob"
```

---

## Analytics and Monitoring

### Chrome Web Store Dashboard Metrics

- **Weekly users** — active installs over 7 days
- **Total installs** — cumulative install count
- **Uninstalls** — track churn rate
- **Ratings and reviews** — respond to user feedback
- **Impressions** — how often your listing appears in search

### In-Extension Analytics (Privacy-Respecting)

```typescript
// src/analytics.ts — anonymous, opt-in feature usage tracking
interface AnalyticsEvent {
  event: string;
  timestamp: number;
}

const ANALYTICS_KEY = "analytics_events";
const MAX_EVENTS = 500;

export async function trackEvent(event: string): Promise<void> {
  const { analytics_enabled } = await chrome.storage.sync.get("analytics_enabled");
  if (!analytics_enabled) return;

  const { [ANALYTICS_KEY]: events = [] } = await chrome.storage.local.get(ANALYTICS_KEY);
  events.push({ event, timestamp: Date.now() });

  // Keep only recent events
  const trimmed = events.slice(-MAX_EVENTS);
  await chrome.storage.local.set({ [ANALYTICS_KEY]: trimmed });
}

// Flush to your analytics endpoint periodically
export async function flushEvents(endpoint: string): Promise<void> {
  const { [ANALYTICS_KEY]: events = [] } = await chrome.storage.local.get(ANALYTICS_KEY);
  if (events.length === 0) return;

  await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events, extensionVersion: chrome.runtime.getManifest().version }),
  });

  await chrome.storage.local.remove(ANALYTICS_KEY);
}
```

---

## Monetization Options

| Model | Implementation | Pros | Cons |
|-------|---------------|------|------|
| Free | No payment | Maximum adoption | No revenue |
| Freemium | Feature-gate premium features | Large free user base, conversion funnel | Must maintain two tiers |
| One-time purchase | Chrome Web Store Payments (deprecated) or external payment | Simple | CWS Payments sunset; external payment adds complexity |
| Subscription | External payment (Stripe, LemonSqueezy) + license key validation | Recurring revenue | Must build license server |

### License Key Validation Pattern

```typescript
// background.ts — validate license on install and periodically
async function validateLicense(key: string): Promise<{ valid: boolean; tier: string }> {
  const response = await fetch("https://api.yourservice.com/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, extensionId: chrome.runtime.id }),
  });
  return response.json();
}

chrome.runtime.onInstalled.addListener(async () => {
  const { licenseKey } = await chrome.storage.sync.get("licenseKey");
  if (licenseKey) {
    const result = await validateLicense(licenseKey);
    await chrome.storage.local.set({ licenseStatus: result });
  }
});

// Re-validate daily
chrome.alarms.create("license-check", { periodInMinutes: 1440 });
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "license-check") {
    const { licenseKey } = await chrome.storage.sync.get("licenseKey");
    if (licenseKey) {
      const result = await validateLicense(licenseKey);
      await chrome.storage.local.set({ licenseStatus: result });
    }
  }
});
```

---

## Distribution Models

### Public (Default)

- Listed in Chrome Web Store search results
- Anyone can install
- Subject to full review process

### Unlisted

- Not shown in search results
- Accessible only via direct URL
- Still hosted on Chrome Web Store
- Still subject to review
- Good for beta testing or internal tools

Set via Developer Dashboard → Distribution → Visibility.

### Enterprise Distribution

For organizations deploying extensions to managed Chrome browsers:

**Option 1: Force-install via policy**

```json
// Chrome Enterprise policy (managed via Google Admin Console or GPO)
{
  "ExtensionInstallForcelist": [
    "abcdefghijklmnopabcdefghijklmnop;https://clients2.google.com/service/update2/crx"
  ]
}
```

**Option 2: Self-hosted (private web store)**

```xml
<!-- update.xml — host on your own server -->
<?xml version="1.0" encoding="UTF-8"?>
<gupdate xmlns="http://www.google.com/update2/response" protocol="2.0">
  <app appid="YOUR_EXTENSION_ID">
    <updatecheck codebase="https://yourserver.com/extension.crx" version="1.0.0" />
  </app>
</gupdate>
```

Set via policy:

```json
{
  "ExtensionInstallSources": ["https://yourserver.com/*"],
  "ExtensionInstallForcelist": [
    "YOUR_EXTENSION_ID;https://yourserver.com/update.xml"
  ]
}
```

**Option 3: Chrome Browser Cloud Management**

1. Upload extension to Google Admin Console
2. Assign to organizational units
3. Extensions are auto-installed for managed users
4. No Chrome Web Store listing required

# Architecture: Expo & React Native Mobile Observability

Comprehensive guide for architecting production-grade Sentry observability in Expo and React Native applications using `@sentry/react-native` (v8+), Hermes bytecode Debug IDs, Expo Router tracing, Mobile Session Replay, and EAS Build integration.

---

## 1. Architectural Overview & The Modern Standard

Modern Expo mobile applications run on a hybrid architecture combining JavaScript/TypeScript on the **Hermes VM** with native **iOS (`sentry-cocoa`)** and **Android (`sentry-java`/`sentry-android`)** runtimes.

```
┌────────────────────────────────────────────────────────┐
│                   React Native App                     │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │     Expo Router       │  │  Sentry Mobile Replay │  │
│  │ (expoRouterIntegration)│  │ (mobileReplayIntegration)│
│  └───────────┬───────────┘  └───────────┬───────────┘  │
│              ▼                          ▼              │
│       @sentry/react-native (JavaScript SDK Layer)      │
│              │ (Hermes JS Engine + Debug IDs)          │
├──────────────┼─────────────────────────────────────────┤
│              ▼ JSI / TurboModules                      │
│   Native iOS (sentry-cocoa)   Native Android (sentry)  │
│   - Mach/Unix Crash Handlers  - NDK / Java Handlers    │
│   - MetricKit Diagnostics     - ANR Tracking           │
│   - Frozen / Slow Frames      - Frame Render Timings   │
└────────────────────────────────────────────────────────┘
```

### Critical Package Disambiguation
> [!WARNING]
> **`sentry-expo` is completely DEPRECATED and RETIRED.**
> Legacy guides referencing `sentry-expo` are obsolete as of Expo SDK 50+. Modern Expo projects **must** use `@sentry/react-native` directly with the `@sentry/react-native/expo` config plugin.

### Expo Go vs. Development Builds
- **Expo Go**: Contains pre-compiled native code with limited support for custom native modules. Native crash reporters, native frame tracking, and certain Mobile Replay features cannot run in Expo Go.
- **Development Builds (`npx expo run:ios`, `npx expo run:android`, or `eas build --profile development`)**: **Mandatory for production observability.** Enables the full native Sentry SDK (`sentry-cocoa`, `sentry-android`, NDK crash handling, and MetricKit).

---

## 2. Installation & Dependencies

Install the core SDK and peer dependencies via the Expo CLI to ensure compatibility with your current Expo SDK:

```bash
# Recommended installation via Expo CLI
npx expo install @sentry/react-native

# Optional: Run the automated Sentry configuration wizard
npx @sentry/wizard@latest -i reactNative
```

---

## 3. Configuration Architecture

### A. Expo Config Plugin (`app.json` or `app.config.ts`)

Add the Sentry config plugin. During `npx expo prebuild` or `eas build`, this plugin configures:
- Android: Sentry Gradle plugin for automatic source map and ProGuard/R8 mapping uploads.
- iOS: Xcode build phases for Hermes bytecode symbolication and dSYM debug symbol uploads.

#### Static `app.json`:
```json
{
  "expo": {
    "name": "MyMobileApp",
    "slug": "my-mobile-app",
    "version": "1.0.0",
    "plugins": [
      [
        "@sentry/react-native/expo",
        {
          "url": "https://sentry.io/",
          "project": "my-mobile-app",
          "organization": "my-org"
        }
      ]
    ]
  }
}
```

> [!NOTE]
> If your organization is on the EU cluster, configure `"url": "https://de.sentry.io/"`.

#### Dynamic `app.config.ts` (using `withSentry`):
```ts
import { ExpoConfig } from "expo/config";
import { withSentry } from "@sentry/react-native/expo";

const config: ExpoConfig = {
  name: "MyMobileApp",
  slug: "my-mobile-app",
  version: "1.0.0",
};

export default withSentry(config, {
  url: "https://sentry.io/",
  project: "my-mobile-app",
  organization: "my-org",
});
```

---

## 4. Metro Bundler Configuration (`metro.config.js`)

Hermes bytecode requires deterministic **Debug IDs** embedded in the bundle and source map for accurate stack trace unminification. Wrap the Metro configuration with `getSentryExpoConfig`:

```javascript
// metro.config.js
const { getSentryExpoConfig } = require("@sentry/react-native/metro");

const config = getSentryExpoConfig(__dirname);

module.exports = config;
```

If chaining with other Metro plugins (e.g. NativeWind or SVG transformer):
```javascript
// metro.config.js
const { getSentryExpoConfig } = require("@sentry/react-native/metro");
const { withNativeWind } = require("nativewind/metro");

const config = getSentryExpoConfig(__dirname);

module.exports = withNativeWind(config, { input: "./global.css" });
```

---

## 5. Application Initialization (`app/_layout.tsx`)

In modern Expo Router applications, initialize Sentry at the module level in `app/_layout.tsx` before any components mount, and wrap the root layout:

```tsx
// app/_layout.tsx
import { Stack } from "expo-router";
import * as Sentry from "@sentry/react-native";
import { isRunningInExpoGo } from "expo";

Sentry.init({
  dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
  // Adds IP address, user context, and OS metadata
  sendDefaultPii: true,
  
  // Distributed Tracing
  tracesSampleRate: 1.0,
  
  // Continuous Profiling (Hermes JS CPU profiling)
  profilesSampleRate: 1.0,
  
  // Session Replay on Mobile
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  
  integrations: [
    // Mobile Session Replay with strict privacy redaction
    Sentry.mobileReplayIntegration({
      maskAllText: true,
      maskAllImages: true,
      maskAllVectors: true,
    }),
    
    // Expo Router first-class navigation and TTID tracing
    Sentry.expoRouterIntegration({
      enableTimeToInitialDisplay: !isRunningInExpoGo(),
    }),
  ],
  
  // Native slow and frozen frame metrics (requires development build)
  enableNativeFramesTracking: !isRunningInExpoGo(),
  
  // Environment tagging
  environment: process.env.EXPO_PUBLIC_APP_ENV || "development",
});

function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="modal" options={{ presentation: "modal" }} />
    </Stack>
  );
}

// Sentry.wrap attaches the global error boundary and touch interaction tracking
export default Sentry.wrap(RootLayout);
```

---

## 6. Navigation Tracing & User Interactions

### A. Expo Router (`Sentry.expoRouterIntegration`)
`expoRouterIntegration` automatically binds to Expo Router's navigation container without requiring manual ref pass-through:
- Captures navigation transitions (`ui.navigation`).
- Measures **Time to Initial Display (TTID)** on route changes.
- Automatically catches render crashes via per-route ErrorBoundary.

### B. React Navigation (Bare or Non-Router Expo)
If your app uses raw React Navigation:
```tsx
import { NavigationContainer } from "@react-navigation/native";
import * as Sentry from "@sentry/react-native";

const navigationIntegration = Sentry.reactNavigationIntegration();

Sentry.init({
  dsn: "...",
  integrations: [navigationIntegration],
});

function App() {
  return (
    <NavigationContainer
      ref={(ref) => navigationIntegration.registerNavigationContainer(ref)}
    >
      {/* Screens */}
    </NavigationContainer>
  );
}
```

### C. Touch & User Interaction Tracking
`Sentry.wrap` instruments touch events automatically. To ensure clear breadcrumbs, provide explicit `testID` or `accessibilityLabel` props to buttons and touchables:
```tsx
<Pressable
  testID="submit-checkout-btn"
  accessibilityLabel="Submit Checkout"
  onPress={handleCheckout}
>
  <Text>Checkout</Text>
</Pressable>
```

---

## 7. Mobile Session Replay & Privacy Shields

Sentry Mobile Session Replay captures low-bandwidth visual representations of user sessions correlated with crashes and performance drops.

### Privacy Shields & Redaction
```tsx
Sentry.mobileReplayIntegration({
  // Globally mask all text, images, and vector graphics
  maskAllText: true,
  maskAllImages: true,
  maskAllVectors: true,
})
```

To selectively unmask non-sensitive elements or mask specific custom views:
```tsx
// Unmask specific public text
<Text sentry-unmask={true}>Welcome to Sentry App</Text>

// Explicitly mask a sensitive card or form
<View sentry-mask={true}>
  <CreditCardForm />
</View>
```

---

## 8. EAS Build & Source Map Automation

When compiling in the cloud with Expo Application Services (EAS Build), source maps and native debug symbols (dSYM / ProGuard) are uploaded automatically by the Sentry build phases.

### A. Setting the Authentication Token
Never commit auth tokens to version control. Add `SENTRY_AUTH_TOKEN` as an **EAS secret**:

```bash
# Add auth token to EAS
eas secret:create --name SENTRY_AUTH_TOKEN --value "<YOUR_SENTRY_AUTH_TOKEN>" --type string
```

For local release builds (`npx expo run:ios --configuration Release`), create a local uncommitted `.env.local`:
```bash
# .env.local (MUST be in .gitignore)
SENTRY_AUTH_TOKEN=sntrys_...
```

### B. Apple Privacy Manifest
For App Store compliance, modern iOS requires privacy manifest declarations. `@sentry/react-native` provides the necessary privacy declarations automatically through its Cocoa dependencies.

---

## 9. Expo Updates (OTA) & Release Matching

When publishing Over-The-Air (OTA) JavaScript updates using `eas update`, the native binary release remains unchanged while the JavaScript bundle changes.

### A. Automatic Runtime Tags
`@sentry/react-native` automatically tags events with Expo Updates metadata:
- `expo.update.id`: Unique UUID of the active OTA update.
- `expo.channel`: The release channel (e.g. `production`, `staging`).
- `expo.runtime_version`: The underlying native runtime compatibility version.

### B. Uploading OTA Source Maps
When running `eas update`, upload the corresponding source maps to Sentry:
```bash
# Automatically handled if EAS Build hooks are configured or run manually:
npx sentry-expo-upload-sourcemaps \
  --org my-org \
  --project my-mobile-app \
  --release <RELEASE_NAME> \
  --dist <DIST_NAME>
```

---

## 10. Common Pitfalls & Checklist

| Pitfall | Root Cause | Fix |
|---|---|---|
| Unsymbolicated Hermes stack frames | Missing `getSentryExpoConfig` in `metro.config.js` | Wrap Metro config with `getSentryExpoConfig(__dirname)` |
| `SENTRY_AUTH_TOKEN` leaked in git | Committed `.env` file | Add `.env.local` to `.gitignore`; configure EAS secret via `eas secret:create` |
| Native crashes not reporting in Expo Go | Expo Go does not execute custom native SDK hooks | Build a development build via `npx expo run:ios` or `eas build --profile development` |
| 404 during source map upload on EAS | Organization is on EU cluster (`de.sentry.io`) | Configure `"url": "https://de.sentry.io/"` in `@sentry/react-native/expo` plugin options |
| `sentry-expo` package not found | Legacy package deprecated since SDK 50 | Uninstall `sentry-expo`; install `@sentry/react-native` |
| Native frames tracking warning in Expo Go | Calling native frame APIs inside Expo Go | Guard with `enableNativeFramesTracking: !isRunningInExpoGo()` |
| Sensitive user text visible in Replay | `maskAllText: false` | Always enforce `maskAllText: true` in `mobileReplayIntegration` |

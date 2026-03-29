# Deployment Checklist

## Use This When
- Preparing to deploy a Convex + SwiftUI app to production.
- Running through pre-submission checks before App Store upload.
- Verifying the auth, backend, and client layers are correctly configured for production.

---

## Backend Deployment

### 1. Deploy to Production

```bash
npx convex deploy
```

This pushes all functions and schema to your production deployment. Convex runs migrations automatically if the schema changed.

### 2. Set Environment Variables

In the Convex Dashboard (dashboard.convex.dev):

Navigate to Settings -> Environment Variables and set:

| Variable | Value | Notes |
|----------|-------|-------|
| `CLERK_JWT_ISSUER_DOMAIN` | `https://your-app.clerk.accounts.dev` | From Clerk Dashboard -> JWT Templates |

### 3. Verify auth.config.ts

Confirm your `convex/auth.config.ts` references the environment variable:

```typescript
export default {
  providers: [
    {
      domain: process.env.CLERK_JWT_ISSUER_DOMAIN!,
      applicationID: "convex",
    },
  ],
};
```

### 4. Verify Functions Deployed

```bash
npx convex functions
```

Check that all expected functions appear: `users:createOrUpdate`, `channels:list`, `channels:create`, `channels:join`, `messages:list`, `messages:send`.

### 5. Remove Test-Only Functions

Ensure `testHelpers:resetAll` and `testHelpers:resetForTesting` are either:
- Deleted from the `convex/` directory, or
- Marked as `internalMutation` with an environment guard

Never deploy data-wiping functions to production.

---

## iOS App Configuration

### 6. Update Deployment URL

Replace the dev URL with the production URL in your client singleton:

```swift
@MainActor
let client = ConvexClientWithAuth(
    deploymentUrl: "https://YOUR_PROD_SLUG.convex.cloud",
    authProvider: ClerkConvexAuthProvider()
)
```

Consider using a build configuration to switch URLs:

```swift
struct Env {
    #if DEBUG
    static let convexDeploymentUrl = "https://dev-slug.convex.cloud"
    static let clerkPublishableKey = "pk_test_xxx"
    #else
    static let convexDeploymentUrl = "https://prod-slug.convex.cloud"
    static let clerkPublishableKey = "pk_live_xxx"
    #endif
}
```

### 7. Configure Clerk for Production

In Clerk Dashboard:
- [ ] Enable production instance
- [ ] Add your app's bundle ID to allowed iOS apps
- [ ] Configure sign-in methods (Apple, Google, email, etc.)
- [ ] Create a "convex" JWT template if not already present

### 8. Remove Debug Logging

Verify `initConvexLogging()` is wrapped in `#if DEBUG`:

```swift
init() {
    #if DEBUG
    initConvexLogging()
    #endif
}
```

Logs expose JWTs and user data. This is a security requirement.

---

## Testing on Real Device

### 9. Test Authentication Flow

- [ ] Fresh install: sign-in screen appears
- [ ] Sign in with Clerk: redirects back, auth state becomes `.authenticated`
- [ ] `users:createOrUpdate` mutation fires on first login (if using a users table)
- [ ] Profile view shows correct user info
- [ ] Sign out works and returns to sign-in screen
- [ ] Relaunch app: auth state transitions to `.authenticated` without showing sign-in screen (session restored via bind())
- [ ] Switch from Wi-Fi to cellular -- brief banner, then reconnects
- [ ] Lock device for 30 seconds, unlock -- reconnects automatically

### 10. Test Realtime Features

- [ ] Open a channel on two devices
- [ ] Send a message from device A -- appears on device B within 1-2 seconds
- [ ] Channel list updates in realtime when a new channel is created
- [ ] Messages scroll to bottom on new message arrival

### 11. Test Connection Banner

- [ ] Enable airplane mode -- "Reconnecting..." banner appears
- [ ] Disable airplane mode -- banner disappears, subscriptions resume
- [ ] Switch from Wi-Fi to cellular -- brief banner, then reconnects
- [ ] Lock device for 30 seconds, unlock -- reconnects automatically

### 12. Test Background/Foreground Reconnect

- [ ] Send app to background for 5+ minutes
- [ ] Bring to foreground -- verify data refreshes
- [ ] No crash on background -> foreground transition
- [ ] Memory does not grow unbounded after repeated cycles

---

## Performance and Size

### 13. Check Binary Size

The ConvexMobile SDK includes a Rust binary (~5-15 MB on-device after App Store thinning). Verify:

```bash
# After archive
du -sh MyApp.app/Frameworks/ConvexMobile.framework
```

- [ ] Total app size is acceptable for App Store
- [ ] Bitcode is disabled (Rust FFI does not support bitcode)

### 14. Profile Network Usage

- [ ] WebSocket connection uses minimal bandwidth when idle
- [ ] Queries are bounded with .take(N) — Convex re-sends full results on invalidation, not diffs
- [ ] No unnecessary subscriptions running on hidden tabs

---

## App Store Submission

### 15. Pre-Submission Checks

- [ ] App runs on minimum supported iOS version (iOS 17+)
- [ ] No private API usage warnings from Xcode
- [ ] Privacy manifest includes required entries for network usage
- [ ] Export compliance: app uses HTTPS (standard exemption applies)

### 16. Info.plist Entries

If using Clerk with OAuth providers:

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>your-clerk-redirect-scheme</string>
        </array>
    </dict>
</array>
```

### 17. Final Verification

```
Backend:
  [x] npx convex deploy -- successful
  [x] Environment variables set in dashboard
  [x] auth.config.ts verified
  [x] Test-only functions removed

iOS:
  [x] Production deployment URL configured
  [x] Debug logging guarded by #if DEBUG
  [x] Clerk production instance configured
  [x] Real device testing passed
  [x] Connection banner works
  [x] Background/foreground reconnect works
  [x] Binary size acceptable
  [x] App Store submission requirements met
```

---

## Rollback Plan

If something goes wrong after deployment:

1. **Backend rollback:** `npx convex deploy --preview rollback-branch` then promote when fixed
2. **Schema issues:** Convex does not support destructive schema changes in production -- add new fields as optional, backfill, then migrate
3. **iOS rollback:** You cannot recall an App Store release, but you can expedite a new review with App Store Connect's expedited review request

## Avoid
- Deploying with `initConvexLogging()` enabled in production builds -- exposes JWTs.
- Leaving test-only data-wiping functions deployed to production.
- Hard-coding the dev deployment URL in the production binary.
- Skipping real-device testing -- simulator does not exercise network transitions or background/foreground correctly.
- Force-pushing schema changes that remove fields in production -- add new fields as optional first.

## Read Next
- [01-from-zero-to-realtime-chat-app.md](01-from-zero-to-realtime-chat-app.md)
- [../operations/01-verified-corrections-and-trust-boundaries.md](../operations/01-verified-corrections-and-trust-boundaries.md)
- [../platforms/01-ios-backgrounding-reconnection-and-staleness.md](../platforms/01-ios-backgrounding-reconnection-and-staleness.md)

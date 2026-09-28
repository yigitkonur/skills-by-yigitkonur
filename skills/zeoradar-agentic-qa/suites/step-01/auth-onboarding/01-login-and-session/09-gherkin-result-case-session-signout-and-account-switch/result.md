# Test Execution Result: TC-AUTH-09-SIGNOUT-SWITCH

- **Executed At**: 2026-09-25T19:39:46Z
- **Outcome**: PASSED
- **Duration**: ~6s
- **Target URL**: `https://zeoradar.endpoints.lol/#/auth`
- **Task Space**: `zeoradar-suite-01-login`

## Executive Summary
Session termination (`handleAuthSignOut`) and account switching (`handleAuthSwitchAccount`) behaviors were verified end-to-end.
1. **User Sign-Out**: Calling `handleAuthSignOut()` invokes `client.signOut()`, purges tokens from client storage (`localStorage`), resets sensitive form fields (`auth.email`, `auth.password`), and safely redirects the user to the root authentication view (`/auth`).
2. **Account Switching**: In the brand setup onboarding step (`step: 'brand_setup'`), triggering `handleAuthSwitchAccount()` resets `window.state.auth` to a fresh null state, cancels any pending OTP resend timer interval, and re-renders step `email` with clean blank inputs, preventing previous credentials from leaking across sessions.

## Artifacts Captured
- `screenshots/01-authenticated-dashboard.png`
- `screenshots/02-signout-auth-screen.png`
- `evidence.json`

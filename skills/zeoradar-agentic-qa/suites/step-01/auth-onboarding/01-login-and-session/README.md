# Test Suite 01: Authentication, Login & Session Management

## 1. Module Overview & Architectural Grounding

The **Authentication & Session Management** subsystem (`assets/auth.js`, `assets/auth.css`, `assets/supabase-client.js`) implements a deterministic, multi-phase client-side authentication state machine that interfaces with the router (`assets/router.js`), the global state (`window.state.auth`), and the unified authentication authority (`window.ZEO_AUTH_CLIENT`).

### State Machine Architecture
```
┌────────────────────────────────────────────────────────────────────────┐
│                      AUTH STATE MACHINE FLOW                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   Initial Navigation (/#/auth)                                         │
│        │                                                               │
│        ▼                                                               │
│   [step: 'email'] ──(OAuth Google/GitHub)──► IdP OAuth Redirect        │
│        │          ──(Toggle SSO Drawer)───► [SAML SSO Input]           │
│        │          ──(Click Create Acc)────► [step: 'signup_details']   │
│        │          ──(Click E2E Bypass)────► [Bypass Direct Login]      │
│        │                                                               │
│   (Valid Email Entered & Submitted)                                    │
│        │                                                               │
│        ▼                                                               │
│   [step: 'signin_password']                                            │
│        ├── (Forgot Password Click)────────► [step: 'password_reset']   │
│        ├── (Email Me Code Click)──────────► [step: 'otp_verify']       │
│        └── (Submit Valid Credentials)─────► [signed_in] ──► Dashboard  │
│                                                                        │
│   [step: 'otp_verify']                                                 │
│        ├── 6-Digit Grid [data-idx="0..5"]                              │
│        ├── 55-Second Resend Countdown                                  │
│        └── (Submit OTP '246810')──────────► [signed_in] ──► Dashboard  │
│                                                                        │
│   [step: 'password_reset'] (.auth-solo-step)                           │
│        ├── 6-Digit Recovery OTP Grid                                   │
│        ├── New Password + Confirm Password (Dual Eye Toggles)          │
│        └── (Submit Match & Update)────────► [signed_in] ──► Dashboard  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Test Cases

This directory contains 12 focused, modular Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-email-precheck-and-validation.md` | TC-AUTH-01 | Email Pre-check, Syntax Regex Validation & Normalization | TC-AUTH-02, TC-AUTH-12 |
| `02-gherkin-case-password-authentication.md` | TC-AUTH-02 | Password Authentication, Visibility Toggles & Credential Rejection | TC-AUTH-01, TC-AUTH-03 |
| `03-gherkin-case-new-user-signup.md` | TC-AUTH-03 | New User Registration, Unicode Support & Consent Gating | TC-AUTH-07 |
| `04-gherkin-case-otp-code-verification.md` | TC-AUTH-04 | 6-Digit OTP Grid, Keyboard Navigation & Dirty Paste Sanitization | TC-AUTH-04, TC-AUTH-14 |
| `05-gherkin-case-otp-resend-timer-lifecycle.md` | TC-AUTH-05 | 55-Second OTP Resend Cooldown, Timer Expiry & Re-dispatch | TC-AUTH-13 |
| `06-gherkin-case-password-recovery-and-reset.md` | TC-AUTH-06 | Full-Bleed Password Reset Flow, OTP Recovery & Eye Toggles | TC-AUTH-06 |
| `07-gherkin-case-enterprise-saml-sso.md` | TC-AUTH-07 | Enterprise SAML SSO Drawer, Domain Validation & IdP Routing | TC-AUTH-05, TC-AUTH-15 |
| `08-gherkin-case-dev-bypass-and-auto-login.md` | TC-AUTH-08 | E2E Dev Bypass Login, Query Parameter & Corrupt Storage Fallback | TC-AUTH-08, TC-AUTH-16 |
| `09-gherkin-case-session-signout-and-account-switch.md` | TC-AUTH-09 | Session Termination, Account Switching & State Cleansing | TC-AUTH-09 |
| `10-gherkin-case-rate-limiting-and-concurrency.md` | TC-AUTH-10 | Rate Limiting (429), Error Banners & In-Flight Double-Click Lock | TC-AUTH-10, TC-AUTH-17 |
| `11-gherkin-case-network-outage-and-service-degradation.md` | TC-AUTH-11 | Network Outage, Service 500/Offline Handling & Non-Destructive Recovery | TC-AUTH-11 |
| `12-gherkin-case-localization-and-social-proof.md` | TC-AUTH-12 | Internationalization (EN/TR), Social Proof Testimonials & Footer | Shell / UI Invariants |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite use standardized, bracketed placeholders. The table below defines each placeholder, how it is set, and representative variants:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[APP_URL]` | Base origin URL of the running web application | Base URL parameter in `openOrReuseTab` | `https://zeoradar.endpoints.lol` |
| `[DOMAIN]` | Monitored target brand domain under test | Target brand website or SSO domain | `daikin.com.tr` |
| `[COUNTRY]` | ISO 3166-1 alpha-2 country code targeting locale evaluation | Selected country dropdown or detected domain ccTLD | `US`, `TR`, `UK`, `DE`, `FR` |
| `[LANGUAGE]` | IETF language tag for UI localization and LLM prompt generation | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[USER_EMAIL]` | Email address used for authentication | `#auth-email-input` or `zeoBypassLogin(email)` | `e2e-agent@zeogen.com`, `alexsmith@content-mobbin.com`, `new-user@zeogen.com` |
| `[PASSWORD]` | Password secret for credential authentication | `#auth-password-input` or `#auth-password-signup` | `ZeoTest2026!`, `zeo-demo-2026`, `Short1!`, `InvalidPwd999` |
| `[OTP_CODE]` | 6-digit numeric verification or recovery code | `#otp-digit-grid .otp-digit-box[data-idx="0..5"]` | `246810` (standard fixture code), `000000` (fallback), `999999` (invalid) |
| `[AUTH_STATE]` | Target session state in `window.state.auth` or `ZEO_AUTH_CLIENT` | `window.getAuthState().step` or client session | `email`, `signin_password`, `signup_details`, `otp_verify`, `password_reset`, `signed_in` |
| `[INDUSTRY_PRESET]`| Preset weighting category for AI evaluation models | `.ob-preset-card[data-preset]` | `ecommerce`, `saas`, `finance`, `custom` |

---

## 4. Ego Browser / MacBook Execution Model

### Physical Topology & Gateway
E2E testing is executed using `ego-browser nodejs` on the physical MacBook gateway connected via SSH.

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     Linux Host (Development)     │           │      MacBook Gateway (Live)     │
│                                 │   SSH     │                                 │
│  - Test Suite & Gherkin Specs   │──────────►│  - Ego Browser Runtime (Node)   │
│  - Storage / Result Directories │           │  - Active Display / GPU Render  │
│  - SCP Evidence Downloader      │◄──────────│  - Local Screenshot Cache       │
└─────────────────────────────────┘    SCP    └─────────────────────────────────┘
```

### Execution Lifecycle Protocol
1. **Heredoc Dispatch**: The test script is executed remotely via:
   ```bash
   ssh macbook "ego-browser nodejs <<'EOF'
     const task = await useOrCreateTaskSpace('e2e-auth-session-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/auth', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-auth-session-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/auth/` or `~/Desktop/shots/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/auth/case-01-*.png ./01-gherkin-result-case-email-precheck-and-validation/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.
   - A complete result directory contains:
     - `result.md` (Execution outcome, timing, environment specs, pass/fail status)
     - `evidence.json` (Structured DOM dumps, console errors, state snapshots)
     - `screenshots/*.png` (Visual evidence downloaded from MacBook)
     - `network/*.json` (Recorded HTTP / RPC telemetry)

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Gap Hardening |
|:---|:---|:---|:---|
| TC-AUTH-01 | Login Happy Path | `02-gherkin-case-password-authentication.md` | `assets/auth.js:1320` `handleSignInSubmit`, `assets/supabase-client.js:379` `signInWithPassword` |
| TC-AUTH-02 | Client Validation | `01-gherkin-case-email-precheck-and-validation.md` | `assets/auth.js:198` `validateEmail`, `assets/auth.js:206` `isAuthStepValid` |
| TC-AUTH-03 | Server Rejection | `02-gherkin-case-password-authentication.md` | `assets/auth.js:147` `authErrorCopy('unauthenticated')`, `.input-error` class |
| TC-AUTH-04 | OTP Verification | `04-gherkin-case-otp-code-verification.md` | `assets/auth.js:1325` `handleOTPInput`, `data/mock-backend-fixtures.js:32` `DEMO_OTP_CODE = '246810'` |
| TC-AUTH-05 | Enterprise SSO | `07-gherkin-case-enterprise-saml-sso.md` | `assets/auth.js:1336` `toggleSSODrawer`, `assets/auth.js:1339` `handleSSOSubmit` |
| TC-AUTH-06 | Password Reset | `06-gherkin-case-password-recovery-and-reset.md` | `assets/auth.js:1324` `handlePasswordResetSubmit`, dual eye toggles `auth.resetPasswordVisible` |
| TC-AUTH-07 | Signup Flow | `03-gherkin-case-new-user-signup.md` | `assets/auth.js:1321` `handleSignUpSubmit`, Turkish char support (Ç, Ğ, İ, Ö, Ş, Ü) |
| TC-AUTH-08 | Dev Bypass Mode | `08-gherkin-case-dev-bypass-and-auto-login.md` | `assets/auth.js:1341` `zeoBypassLogin`, `assets/auth.js:1372` `?auto_login=1` handler |
| TC-AUTH-09 | Session Logout | `09-gherkin-case-session-signout-and-account-switch.md` | `assets/auth.js:1332` `handleAuthSignOut`, `assets/auth.js:1333` `handleAuthSwitchAccount` |
| TC-AUTH-10 | Rate Limiting | `10-gherkin-case-rate-limiting-and-concurrency.md` | `assets/auth.js:150` `rate_limited`, release of `auth.busy = false` |
| TC-AUTH-11 | Network Outage | `11-gherkin-case-network-outage-and-service-degradation.md` | `assets/auth.js:151` `dependency_unavailable`, non-destructive input preservation |
| TC-AUTH-12 | Malformed Email | `01-gherkin-case-email-precheck-and-validation.md` | Trim & lowercase in `handleAuthEmailSubmit`, double dot rejection |
| TC-AUTH-13 | OTP Resend Lockout | `05-gherkin-case-otp-resend-timer-lifecycle.md` | `assets/auth.js:123` `resendTimer = 55`, `clearOTPTimer`, `#btn-otp-resend` gating |
| TC-AUTH-14 | OTP Sanitized Paste | `04-gherkin-case-otp-code-verification.md` | `assets/auth.js:1328` `handleOTPPaste`, regex replace `/[^0-9]/g` |
| TC-AUTH-15 | SSO Drawer Edge Cases| `07-gherkin-case-enterprise-saml-sso.md` | Whitespace trimming on domain, drawer toggle state idempotency |
| TC-AUTH-16 | Corrupt Storage | `08-gherkin-case-dev-bypass-and-auto-login.md` | `assets/supabase-client.js:56` JSON.parse error handling on `zeo-mock-auth:v1` |
| TC-AUTH-17 | Double-Click Flight | `10-gherkin-case-rate-limiting-and-concurrency.md` | `assets/auth.js:133` `auth.busy` locking against duplicate concurrent RPC calls |

# Clerk Account and JWT Template Setup

## Use This When
- Creating a Clerk account for a new Convex-backed iOS or macOS app.
- Configuring the JWT template that Convex will validate.
- Adding Sign in with Apple or other OAuth providers through Clerk.

## Platform Requirement

Clerk iOS SDK v1.0+ requires **iOS 17+ / macOS 14+**. This is stricter than ConvexMobile's iOS 13+ minimum. Set your deployment target to iOS 17+ when using Clerk.

## Step 1: Create a Clerk Account

1. Sign up at [clerk.com](https://clerk.com).
2. Create an application.
3. Copy your **Publishable Key** (`pk_test_...` or `pk_live_...`).

## Step 2: Create a JWT Template for Convex

1. Clerk Dashboard -> **JWT Templates**.
2. Click **New Template** -> choose **Convex**.
3. Clerk auto-configures:
   - **Issuer**: `https://verb-noun-00.clerk.accounts.dev`
   - **Audience**: `convex`
4. **Copy the Issuer URL** -- needed for the Convex backend `auth.config.ts`.

## Step 3: Configure Sign-In Methods

In Clerk Dashboard -> **User & Authentication** -> **Email, Phone, Username**:

- Enable **Sign in with Apple** (recommended for iOS).
- Enable email/password or any OAuth providers as needed.

For Sign in with Apple:
1. Apple Developer account required.
2. Add the Sign in with Apple capability to your Xcode project.
3. Configure the Apple provider in Clerk.

## Step 4: Add SPM Packages to Xcode

| Package | URL |
|---|---|
| Clerk iOS SDK | `https://github.com/clerk/clerk-ios` |
| Clerk + Convex Bridge | `https://github.com/clerk/clerk-convex-swift` |

Add both via **File -> Add Package Dependencies** in Xcode. The bridge product is `ClerkConvex`.

## What You Have After This Step

| Item | Value |
|---|---|
| Publishable Key | `pk_test_xxx` or `pk_live_xxx` |
| JWT Issuer Domain | `https://verb-noun-00.clerk.accounts.dev` |
| JWT Audience | `convex` |
| SPM imports | `import ClerkKit`, `import ClerkConvex`, `import ClerkKitUI` |

## Avoid
- Using `import Clerk`, `import ClerkSDK`, or `import ConvexClerk` -- the correct imports are `import ClerkKit`, `import ClerkConvex`, `import ClerkKitUI`.
- Skipping the JWT template -- without it, `ctx.auth.getUserIdentity()` always returns `null` on the backend.
- Hardcoding the issuer URL in Swift code -- it belongs in the backend `auth.config.ts` via an environment variable.
- Building custom sign-in UI when `AuthView()` from `ClerkKitUI` handles all Clerk-supported methods.

## Read Next
- [04-connecting-clerk-to-convex-auth-config.md](04-connecting-clerk-to-convex-auth-config.md)
- [../authentication/01-clerk-first-setup.md](../authentication/01-clerk-first-setup.md)
- [../backend/04-auth-rules-and-server-ownership.md](../backend/04-auth-rules-and-server-ownership.md)

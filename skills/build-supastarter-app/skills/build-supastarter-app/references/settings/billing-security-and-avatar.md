# Billing, Security, and Avatar Settings

> Covers the settings components that handle avatar uploads, security-adjacent account actions, and billing entry points. Consult this when changing profile media flows or customer-portal access from settings.

> ⚠️ **Avatar uploads go through S3 signed URLs.** See `references/patterns/direct-upload-s3.md` for the full upload pattern.

## Key files

- `apps/web/modules/saas/settings/components/UserAvatarUpload.tsx`
- `apps/web/modules/saas/settings/components/UserLanguageForm.tsx`
- `apps/web/modules/saas/settings/components/CustomerPortalButton.tsx`

## Representative code

`UserAvatarUpload` drives a multi-step flow:

- accept/detect dropped image file
- crop through `CropImageDialog`
- upload through a signed URL mutation
- update the user record with the new avatar path

This same upload component is reused in onboarding.

## Practical notes

- avatar updates usually require session refresh so the new image appears everywhere
- locale updates should stay consistent with the i18n config/cookie model
- billing actions usually redirect into the active provider’s customer portal rather than mutating billing state locally

---

**Related references:**
- `references/storage/signed-urls.md` — File upload/download contract
- `references/onboarding/onboarding-step-one.md` — Shared avatar upload usage
- `references/payments/stripe-provider.md` — Customer portal creation
- `references/patterns/direct-upload-s3.md` — Upload pattern
- `references/auth/session-hook-provider.md` — Session reload after changes

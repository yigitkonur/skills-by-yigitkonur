# Replacing Supabase Auth's built-in mailer with Cloudflare Email Service

Supabase Auth sends its own emails (signup confirmation, magic link,
recovery, email-change) through a built-in mailer that is rate-limited to a
trickle (2/hour on hosted defaults) and template-constrained. Two distinct
strategies exist; pick deliberately.

## Strategy A — custom SMTP (Supabase keeps orchestrating)

Supabase Auth continues to decide *when* to send; Cloudflare carries the
mail. Zero application-code changes.

1. Onboard the sending domain on Cloudflare (SKILL.md §2).
2. Create a Cloudflare API token scoped **Email Sending: Edit** only
   (dashboard-gated — this is the one step wrangler cannot do).
3. Supabase dashboard → Auth → SMTP settings:
   - Host `smtp.mx.cloudflare.net`, port `465` (implicit TLS)
   - Username: literal string `api_token`
   - Password: the Cloudflare token
   - Sender: an address at the onboarded domain
4. Verify with a real password-reset request and watch it arrive.

Hosted Supabase auth settings are dashboard-owned — record the change in the
project's runbook, since it isn't in git.

Best when: the built-in auth-email flows are fine and the pain is only
deliverability/rate limits.

## Strategy B — custom emails via admin tokens (you orchestrate)

Bypass Supabase's mailer entirely: generate the auth token server-side,
embed it in your own email, send through Cloudflare. Full template control,
your own copy, works for CLI/device flows where the email *is* the product
surface.

Verified semantics (mid-2026, supabase-js v2):

- `supabase.auth.admin.generateLink({type: "magiclink", email})` —
  creates-or-finds the user, does **not** send anything, returns
  `data.properties.hashed_token`.
- Client exchanges it with `supabase.auth.verifyOtp({token_hash, type:
  "magiclink"})` — creates a session **and** confirms an unconfirmed email;
  needs no redirect-URL allowlisting (unlike clicking the raw `action_link`).
- **Token-family landmine:** magiclink and recovery tokens share the single
  `recovery_token` column on `auth.users` — issuing one invalidates the
  other. Never put a verify link *and* a set-password link in the same
  email; offer set-password as an in-session step on the landing page after
  `verifyOtp`.
- Link TTL follows the project's Email-OTP expiry (default 3600s).

Flow: registration endpoint → `generateLink` → build your landing-page URL
carrying `token_hash` → render your template → POST to the email-sender
Worker → landing page runs `verifyOtp` and continues.

Guard the landing page against email-client link prefetchers: token exchange
on load is acceptable, but any consequential action (approving a device,
granting access) must sit behind an explicit user click.

Best when: custom flows (device login, welcome-with-verification), branded
templates, or emails that must carry app-specific state.

## Combining

Real deployments often use both: Strategy A for stock recovery emails,
Strategy B for the flows you designed. They don't conflict — A uses
Supabase's templates + SMTP, B never touches Supabase's mailer.

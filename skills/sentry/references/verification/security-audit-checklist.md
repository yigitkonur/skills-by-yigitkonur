# Sentry Security & Redaction Audit Protocol

Verification protocol to guarantee zero credentials, tokens, or PII leak into code, git history, or Sentry event payloads.

## Codebase Credentials Scan

Before committing any Sentry changes, run an automated scan across the repository:

```bash
# Check for hardcoded Sentry auth tokens
git grep -E "sntry[us]_[a-f0-9]{64}"

# Check for hardcoded JWTs
git grep -E "eyJ[a-zA-Z0-9_-]{15,}\.[a-zA-Z0-9_-]{15,}"

# Check for API keys or secrets in committed code
git grep -iE "(api[_-]?key|secret)\s*[:=]\s*['\"][a-zA-Z0-9_-]{16,}['\"]"
```

## Git Ignore Verification

Verify that local credentials files are excluded in `.gitignore`:

```text
# Sentry local credentials
.sentryclirc
.claude/*.local.md
.env
.env.*
!.env.example
```

## Sentry Event Payload Inspection

When inspecting live events in Sentry via CLI or UI:
1. **Request Headers:** Verify `authorization`, `cookie`, and `x-api-key` display `[Filtered]`.
2. **URLs:** Verify parameters matching `jwt`, `token`, or `key` display `[Filtered]`.
3. **Breadcrumbs:** Verify console logs and HTTP request logs contain no plain text passwords or tokens.

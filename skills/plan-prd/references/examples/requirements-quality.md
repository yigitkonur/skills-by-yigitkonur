# Requirements Quality Examples

Side-by-side examples showing vague vs. concrete requirements across common categories. Use these to calibrate your PRD writing.

## Performance requirements

```diff
# Vague
- The application should load quickly.
- API responses should be fast.
- The system should handle many users.

# Concrete
+ Initial page load completes in under 2 seconds on 3G connection (Lighthouse metric).
+ API endpoints return responses within 200ms at 95th percentile under 100 concurrent users.
+ System supports 10,000 concurrent active sessions with less than 5% degradation in response time.
```

## Security requirements

```diff
# Vague
- The system should be secure.
- User data should be protected.
- Authentication should be robust.

# Concrete
+ All data in transit encrypted via TLS 1.3; all data at rest encrypted via AES-256.
+ PII fields (email, name, phone) encrypted at the application layer before database storage.
+ Authentication uses OAuth 2.0 with PKCE; session tokens expire after 24 hours of inactivity.
+ Failed login attempts are rate-limited to 5 per minute per IP; account locks after 10 consecutive failures.
```

## Accessibility requirements

```diff
# Vague
- The app should be accessible.
- It should work for people with disabilities.

# Concrete
+ Meets WCAG 2.1 AA compliance; verified by axe-core automated audit with zero violations.
+ All interactive elements have minimum 44x44px touch targets.
+ All images have descriptive alt text; decorative images use alt="".
+ Color contrast ratio is at least 4.5:1 for normal text, 3:1 for large text.
+ All functionality is operable via keyboard alone; focus order matches visual order.
```

## Search / AI requirements

```diff
# Vague
- Search should return relevant results.
- The AI should give good answers.
- The system should learn from feedback.

# Concrete
+ Search achieves >= 85% Precision@10 on the 50-question benchmark dataset.
+ AI-generated answers cite at least one source document; citation accuracy >= 95%.
+ Hallucination rate (answers not supported by source material) below 2% on evaluation set.
+ User feedback (thumbs up/down) collected on each answer; weekly report generated.
+ Answer latency under 2 seconds at 95th percentile.
```

## UI / UX requirements

```diff
# Vague
- The UI should look modern.
- Forms should be easy to fill out.
- Navigation should be intuitive.

# Concrete
+ UI follows the project's design system (component library v3.2).
+ Form validates inline on blur; displays error message within 200ms of invalid input.
+ Form auto-saves draft every 30 seconds; draft persists across browser sessions.
+ Primary navigation has max 7 top-level items; current page is visually indicated.
+ Breadcrumb trail shown on all pages deeper than 2 levels.
```

## Error handling requirements

```diff
# Vague
- Errors should be handled gracefully.
- The user should know when something goes wrong.
- The system should recover from failures.

# Concrete
+ All API errors return structured JSON: { code: string, message: string, retryable: boolean }.
+ User-facing error messages explain what went wrong and suggest a next action.
+ Transient failures (network timeout, rate limit) retry up to 3 times with exponential backoff.
+ All unhandled exceptions are captured by the error tracking service with full stack trace.
+ Circuit breaker opens after 5 consecutive failures to an external service; closes after 30 seconds.
```

## Data requirements

```diff
# Vague
- The system should store user data.
- Data should be consistent.
- We need good data quality.

# Concrete
+ User profile stores: name (string, max 100 chars), email (string, unique, RFC 5322 format), role (enum: admin | editor | viewer), created_at (ISO 8601 timestamp).
+ All database writes use transactions; no partial writes on multi-table operations.
+ Email uniqueness enforced at database level (unique constraint) AND application level (pre-check).
+ Soft delete for all user-generated content; hard delete after 90-day retention period.
```

## Integration requirements

```diff
# Vague
- Should integrate with the payment system.
- Should work with our CRM.
- Should support SSO.

# Concrete
+ Integrates with Stripe API v2024-12-18 for payment processing; uses PaymentIntent flow.
+ Syncs customer records to Salesforce via REST API on create, update, and delete events; sync latency under 5 minutes.
+ Supports SAML 2.0 SSO with IdP-initiated and SP-initiated flows; tested against Okta and Azure AD.
```

## The calibration test

For every requirement you write, ask:
1. **Can I write a test for this?** If not, it is too vague.
2. **Would two different engineers interpret this the same way?** If not, add specificity.
3. **Can an AI agent verify this without asking for clarification?** If not, add thresholds.

If you answer "no" to any question, rewrite the requirement until all three are "yes."

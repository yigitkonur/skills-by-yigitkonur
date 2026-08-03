# Frontend Plan and Coverage Design

Read this when creating/revising frontend plans, freezing required coverage, or deciding whether a browser action is authorized.

## Plan model in CLI 0.4.0

A full plan is declarative JSON:

```json
{
  "projectId": "proj_8f0f6",
  "type": "frontend",
  "name": "Guest checkout shows an order confirmation",
  "description": "Critical sandbox checkout contract",
  "priority": "p0",
  "planSteps": [
    {"type": "action", "description": "Open the cart on the authorized public target"},
    {"type": "action", "description": "Continue with authorized sandbox checkout data"},
    {"type": "assertion", "description": "The confirmation is visible with a non-empty order reference"}
  ]
}
```

Constraints retained by this skill and auditor:

| Field | Rule |
|---|---|
| `projectId` | Required non-empty TestSprite project ID |
| `type` | Exactly `frontend` |
| `name` | Required, concrete, maximum 200 characters |
| `description` | Optional non-empty purpose/prerequisite, maximum 2,000 characters |
| `priority` | Optional `p0`, `p1`, `p2`, or `p3` string |
| `planSteps` | 1–200 ordered steps; skill requires at least one observable assertion |
| Step `type` | String `action` or `assertion` |
| Step `description` | Non-empty natural-language intent/visible contract |
| Whole file | At most 256 KiB |

When `--plan-from` is used, the file owns project/type/name/description/priority. Omit redundant metadata flags.

## Freeze the contract before execution

Before any create/run:

1. Freeze the exact plan file identities/hashes, names, priorities, expected test IDs, and material assertions.
2. Record the authoritative product source for each assertion.
3. Record accepted external gates without redefining pass.
4. Treat any post-failure removal, weakening, priority drop, or reclassification as a separately reviewed contract change, not a fix.
5. If the contract legitimately changes, re-freeze it and disclose that the earlier run did not satisfy the old contract.

## Scaffold, audit, and lint

Use the version-matched local scaffold:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite test scaffold --type frontend --out "<PLAN_FILE>"
```

Resolve the loaded skill's directory to its actual absolute path. Never pass `{baseDir}` literally.

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json "<PLAN_FILE>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --output json test lint --plan-from "<PLAN_FILE>"
```

For steps-only replacement, audit then use `test lint --steps`.

The auditor is conservative and does not replace vendor lint. It checks likely secrets/payment numbers, selector mechanics, private/placeholder/credential URLs, numeric private-host shorthands, bypass language, step-scoped outward actions, literal email addresses, vacuous assertions, and basic shape/length policy without printing suspected values.

Authorize only exact zero-based outward steps after recording account, target, effect, concurrency, cleanup, rollback, and retention:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json --authorized-outward-step 1 --authorized-outward-step 4 "<PLAN_FILE>"
```

Each detected authorized outward step still produces a warning. Every unlisted outward step remains an error. A literal email address is an error unless its exact step is authorized; authorization changes it to a warning but does not prove the address is safe. Do not add an index merely to silence the auditor.

`--self-test` is maintainer/CI-only and must not be used as plan validation:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --self-test
```

## Intent belongs in plans; mechanics belong in generated code

Good:

```text
Open the sign-in page.
Sign in as the authorized viewer test account.
The dashboard is visible and admin navigation is absent.
Submit the form without a required email address.
A field-specific validation message is visible and submission is prevented.
```

Bad:

```text
Click #submit-btn.
Use XPath //div[3]/button[2].
Call page.locator('[data-testid="save"]').click().
Enter a password or OTP literal.
Place an order using a real production card.
```

Plans express user intent and visible contracts. Generated Python Playwright owns selectors/action mechanics. Never put tokens, passwords, cookies, OTPs, real card data, personal data, literal production recipients, or credential-bearing URLs in plans.

## Coverage from material user risk

| Dimension | Strong visible contract |
|---|---|
| Navigation/redirect | Correct destination, page identity, no redirect loop |
| Authentication | Expected screen/session boundary without leaked content |
| Forms/validation | Field-specific error, preserved state, prevented invalid submission |
| CRUD/state | Authorized item appears/changes/disappears and cleanup is visible |
| Roles/permissions | Forbidden controls absent/disabled and direct route handled |
| Responsive | Critical controls remain reachable without overlap |
| Accessibility-visible | Named control/region and visible/focus state |
| Error/recovery | Typed error, preserved input, successful bounded retry |
| Upload/download | Safe synthetic filename/status and protected result |
| Third-party | Authorized sandbox/sink outcome and cleanup |

TestSprite execution permission is separate from coverage value.

## Strong assertions

Prefer:

```text
The confirmation heading is visible and includes a non-empty order reference.
The saved display name remains visible after reloading.
The viewer role cannot see the Delete workspace control.
The invalid email field shows a specific validation message and the form is not submitted.
The retry clears the error and shows the new item exactly once.
```

Reject vacuous forms, including:

```text
The page loads.
It works.
Success.
No errors.
The button exists.
The test passes.
```

Status language such as “password is required/masked,” “OTP is invalid,” “API key is hidden,” and “cookie is HttpOnly” is semantic assertion text, not a credential literal. Keep it value-free.

## Authentication and target-origin binding

Plans may name an authorized role but never a credential value. Keep TestSprite API credentials and application login credentials separate.

Record:

- authorized public origin and environment;
- test account identity class, role, tenant, and safe initial state;
- secret delivery mechanism bound to that exact origin;
- whether redirects remain on approved origins;
- session expiry/MFA/provider gates;
- concurrency and account-lock risks;
- reset and cleanup.

Never use credential-bearing target URLs. Never reuse application credentials on a different origin because a project URL or endpoint changed. Reject redirects to an unapproved credential receiver.

## Authorization gate for actions

Before any remote write, billable run, project/test mutation, browser mutation, deployment, or application side effect, require exact IDs/target/account/effect/concurrency/cleanup/rollback/retention authorization.

| Action | Default |
|---|---|
| Read-only navigation/assertion on approved target | Allowed only within authorized target/account scope |
| Negative validation/auth boundary | Bounded, non-abusive, no real outward delivery |
| Create/update isolated fixture | Explicit tenant/effect/concurrency/cleanup authorization |
| Delete/archive data | Explicit scope plus rollback/cleanup proof |
| Send email/message/webhook/notification | Authorized sink/fake recipient and cleanup |
| Invite/publish/post | Authorized sandbox identity/audience and removal |
| Upload/download | Synthetic input, restricted artifact, storage cleanup |
| OAuth/third-party | Authorized sandbox account and exact return origin |
| Payment/order/purchase/booking/reservation | Provider sandbox/test mode only; no real instruments |
| CAPTCHA/MFA/human approval | Do not bypass; preserve as external gate |

Navigation to a checkout page, an email field, a message page, or a post page is not by itself an outward action. A negative-validation journey is not outward when it proves submission was prevented. Actual verb-object actions such as sending an email, publishing a post, placing an order, booking a reservation, or deleting an account require exact step authorization.

## Cleanup and evidence handling

Put cleanup in the journey when faithful, or run a separately authorized cleanup immediately afterward. Verify restored visible state.

Capture terminal JSON, steps, artifacts, reports, code, screenshots, DOM, URLs/data, and form evidence only under `umask 077` in an unpredictable temporary directory. Do not print raw sensitive evidence to transcripts. Share allowlisted metadata and sanitized excerpts. Retention/upload requires explicit authorization; otherwise clean up after the agreed evidence window.

## Update an existing plan

1. Confirm current intent from repository truth, frozen contract, exact steps, run/code versions, and generated code.
2. Author a `{ "planSteps": [...] }` replacement without weakening material assertions.
3. Audit and vendor-lint it.
4. Use optimistic `test plan put --expected-step-count` under explicit write authorization.
5. Trigger a fresh run; never use rerun as proof after plan replacement.
6. If auto-heal is later used diagnostically, compare source/`codeVersion` before and after and explicitly persist the reviewed correction if needed.

## Review checklist

- Exact project ID/type and frozen test/plan identity.
- Name/description within 200/2,000-character limits.
- Every step has string type and non-empty description.
- At least one material visible assertion; no “The test passes.”
- No selectors, secrets, personal recipients, credential URLs, real payment data, or private/placeholder targets.
- Application credentials bound to authorized origin.
- Every outward step individually authorized and still reviewed as a warning.
- Mutation concurrency, cleanup, rollback, and retention recorded.
- Required tests are not removed/reclassified after failure.
- Bundled auditor and authoritative vendor lint both pass.

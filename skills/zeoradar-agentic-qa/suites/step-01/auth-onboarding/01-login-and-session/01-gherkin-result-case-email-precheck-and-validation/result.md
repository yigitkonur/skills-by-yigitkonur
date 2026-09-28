# Test Execution Result: TC-AUTH-01-EMAIL-PRECHECK

- **Executed At**: 2026-09-25T19:29:10Z
- **Outcome**: PASSED
- **Duration**: ~9s
- **Target URL**: `https://zeoradar.endpoints.lol/#/auth`
- **Task Space**: `zeoradar-suite-01-login`

## Executive Summary
Email pre-check, syntax regex validation, whitespace trimming, lowercase normalization, and dynamic button gating verified on live application. Invalid email inputs strictly prevent form submission by keeping the continue button disabled. Entering valid emails with mixed casing and leading/trailing whitespace enables the continue button and normalizes cleanly to lowercase trimmed strings upon submission to the password step.

## Gherkin Scenario Verification
- **Background**: Navigated to `https://zeoradar.endpoints.lol/#/auth`, cleared storage, initial step verified as `email`.
- **Positive Scenario**: Valid emails (`alex.smith@company.com`, `  Alex.Smith@Company.COM  `, `user+tag@domain.co.uk`, `  TEST.USER@ZEO-RADAR.IO  `) enabled `.auth-form button.auth-btn-primary`. Submitting `  Alex.Smith@Company.COM  ` transitioned to step `signin_password` with readonly email displaying `alex.smith@company.com`.
- **Negative Scenario**: Malformed emails (`invalid-email`, `user@`, `user@domain`, `@nodomain.com`, `user space@domain.com`, `""`) kept submit button disabled with `cursor: not-allowed`.

## Observations & Telemetry
- Client-side validation is instant without superfluous network RPCs.
- Readonly box on password view cleanly displays the normalized email.
- Password input is rendered with `type="password"`.

## Artifacts Captured
- `screenshots/01-email-empty-state.png`
- `screenshots/02-email-valid-enabled.png`
- `screenshots/03-email-transition-password.png`
- `evidence.json`

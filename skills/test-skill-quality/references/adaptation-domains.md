# Adaptation Domains

How to apply Derailment Testing beyond Claude skills — to any procedural instructions.

## Core transfer principle

Derailment Testing works wherever:
1. One entity writes instructions
2. Another entity follows them
3. The executor cannot ask clarifying questions during execution

Adapt three variables: instruction format, executor profile, and task domain.

## Domain-specific guidance

### DevOps runbooks

**Executor profile:** On-call engineer at 3am with no system history context.
**Key risk:** Missing prerequisites (VPN, credentials, tool versions) and ambiguous escalation thresholds.

**Adaptations:**
- Test with a simulated incident, not a real one
- The "naive executor" is an engineer who joined last week
- Pay attention to environment prerequisites (which cluster? which region?)
- Time-pressure context: steps requiring 5+ minutes of interpretation are P0

### Onboarding documentation

**Executor profile:** New hire on day 1 with access only to what the doc provides.
**Key risk:** Assumed knowledge about internal tools and tribal knowledge.

**Adaptations:**
- Test on a fresh machine or VM, not your configured workstation
- Every `brew install`, `pip install` must be explicit
- Watch for accumulated drift (step correct when written, system changed since)

### API documentation

**Executor profile:** Developer integrating the API for the first time.
**Key risk:** Format inconsistencies between examples and schemas, undocumented error codes.

**Adaptations:**
- Actually make the API calls, don't just read
- Use `curl` exactly as shown — wrong examples are P0
- Test auth flow from scratch (new API key, not existing one)
- Watch for example rot (schema updated, examples not)

### Internal SOPs

**Executor profile:** Employee in a different department or contractor with no institutional context.
**Key risk:** References to tools by nickname, "just ask [person]" steps.

**Adaptations:**
- "Just ask Sarah" is P0 — what if Sarah is on vacation?
- Every human dependency needs a role (not a name) and a fallback
- Watch for checkbox theater (steps for audit purposes with no operational content)

### Tutorial / course content

**Executor profile:** Student with stated prerequisites and nothing more.
**Key risk:** Unstated dependencies between exercises, platform-specific steps.

**Adaptations:**
- Start from stated prerequisites, not your actual knowledge
- Every "you should see" checkpoint needs a "if you don't see this" recovery
- Test whether the stated prerequisite knowledge is actually sufficient

## Adapting severity thresholds

| Domain | P0 threshold | P1 threshold |
|---|---|---|
| Incident runbooks | Any ambiguity (time-critical) | Requires re-reading |
| AI skills | Hard stop or contradiction | Confusion > 30 seconds |
| Onboarding docs | Cannot proceed on day 1 | Needs to ask a colleague |
| API docs | Example doesn't work | Example works but misleads |
| SOPs | Would fail an audit | Process delay |

## Domain-specific root causes

| Domain | Additional root cause | Code | Description |
|---|---|---|---|
| Runbooks | Credential gap | D1 | Required credentials not listed |
| Onboarding | Platform drift | D2 | Step correct at write time, changed since |
| API docs | Example rot | D3 | Schema updated, example not |
| SOPs | Human dependency | D4 | Requires specific person, not role |
| Tutorials | Invisible prerequisite | D5 | Exercise depends on prior unstated exercise |

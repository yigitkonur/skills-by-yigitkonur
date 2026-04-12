# Drift Analysis

Use this guide when the screenshot does not fully match the expectation contract.

## Common drift types

### Wrong selection

Signals:

- correct window, wrong row, tab, or detail item
- valid content, but not the intended state

Fix direction:

- make selection deterministic
- record actual selected item names when they come from sorted or dynamic data
- do not hardcode unstable names unless the test truly depends on them

### Race or stale state

Signals:

- blank content
- previous screen still visible
- sheet partially animated or missing

Fix direction:

- wait for the app's own ready condition
- increase settle time only if no explicit signal exists
- capture after the state mutation completes

### Real UI regression

Signals:

- missing controls
- clipped content
- wrong copy or layout
- incorrect highlight or selected state

Fix direction:

- change the app, not the automation
- rerun the same capture after the UI fix

### Over-specific expectation

Signals:

- screenshot is structurally correct, but an expected item name, count, or value varies legitimately

Fix direction:

- relax the contract to the invariant structure
- still name the actual observed data so the review remains concrete

### Better-than-expected result

Signals:

- screenshot includes extra valid evidence, such as clearer labels or more visible controls than you required

Fix direction:

- note the stronger evidence
- update the expectation template if future runs should require it

## Reporting rule

Never report only "looks good" or "doesn't match." Always say:

- what exactly matched
- what exactly drifted
- which layer owns the fix
- why that fix is the narrowest correct response

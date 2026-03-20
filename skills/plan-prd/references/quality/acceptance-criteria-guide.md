# Acceptance Criteria Guide

How to write acceptance criteria that AI agents can execute against and verify automatically.

## The three rules

Every acceptance criterion must be:
1. **Atomic** — tests exactly one thing
2. **Measurable** — has a numeric threshold or binary condition
3. **Binary** — pass or fail, no interpretation needed

## Format options

### Checkbox format (recommended for most cases)
```markdown
- [ ] API returns 200 OK with JSON body matching the UserResponse schema
- [ ] Validation rejects emails without @ symbol and returns 422 with error message
- [ ] Response time stays below 200ms at 95th percentile with 100 concurrent users
- [ ] All previous tests continue to pass (no regressions)
```

### Given/When/Then format (for complex user flows)
```markdown
- [ ] Given a logged-in user with "editor" role,
      When they submit the form with valid data,
      Then the system creates a new record and redirects to the detail page
- [ ] Given a logged-in user with "viewer" role,
      When they attempt to submit the form,
      Then the system returns 403 Forbidden and displays "Insufficient permissions"
```

### Must / Should / Must Not format (for AI features with non-deterministic behavior)
```markdown
- [ ] MUST: Handle the query about pricing with accurate, sourced information
- [ ] SHOULD: Offer a follow-up question if the user's intent is ambiguous
- [ ] MUST NOT: Fabricate pricing data that does not exist in the knowledge base
- [ ] MUST NOT: Take irreversible actions without explicit user confirmation
```

## Writing rules

### Verb-first
Start every criterion with an action verb:

| Good verbs | Bad starts |
|---|---|
| Validate, Display, Return, Create, Reject, Redirect, Log, Send, Calculate | The system should..., It is expected..., Make sure..., Ensure... |

### One assertion per criterion

```diff
# BAD — two assertions in one criterion
- [ ] The API returns 200 OK and the response time is under 200ms

# GOOD — separated
+ [ ] API returns 200 OK with valid JSON body
+ [ ] Response time stays below 200ms at 95th percentile
```

### Cover both paths

For every happy-path criterion, consider:
- What happens with invalid input?
- What happens with missing data (null, empty, undefined)?
- What happens with boundary values (0, max, negative)?
- What happens when the user lacks permission?
- What happens when an external service is unavailable?

### Avoid vague language

| Vague | Concrete |
|---|---|
| "should be fast" | "responds within 200ms at 95th percentile under 100 concurrent users" |
| "handles errors gracefully" | "returns structured JSON with error code, human-readable message, and suggested action" |
| "is accessible" | "scores 100% on axe-core accessibility audit; all form fields have labels" |
| "is secure" | "all inputs sanitized against XSS; SQL parameters use prepared statements" |
| "works on mobile" | "renders correctly at 320px-768px viewport width; touch targets are >= 44px" |

## Quantity guidance

| Feature size | Target criteria count |
|---|---|
| Simple (1 user story) | 3-5 criteria |
| Medium (3-5 user stories) | 15-25 criteria |
| Large (10+ user stories) | 40-80 criteria |

If you have more than 100 acceptance criteria, the feature is likely too large for a single PRD. Consider splitting into multiple PRDs or phases.

## Testing alignment

Acceptance criteria should be directly translatable into test cases:

```markdown
# Acceptance criterion
- [ ] Search returns results within 200ms for datasets up to 10K records

# Corresponding test
test('search returns within 200ms for 10K records', async () => {
  // seed 10K records
  const start = performance.now();
  const results = await search('test query');
  const duration = performance.now() - start;
  expect(duration).toBeLessThan(200);
  expect(results).toBeDefined();
});
```

If you cannot imagine how to test a criterion, it is too vague. Rewrite it.

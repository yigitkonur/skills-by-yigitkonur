# Publication Review

Use this reference to decide whether revised content is ready, what blocks publication, and which reviewer owns any residual risk.

## Ready is a multi-part claim

Publication readiness requires all applicable dimensions:

| Dimension | Ready when |
| --- | --- |
| Evidence | Claims are supported, attributed, and appropriately qualified. |
| Meaning | The rewrite preserves values, force, scope, and source intent. |
| Reader fit | The content serves the declared reader and purpose. |
| Voice | Tone matches the accountable speaker, channel, and stakes. |
| Locale | Language and cultural choices meet the claimed confidence level. |
| Inclusion | People and communities are described accurately and respectfully. |
| Format | Syntax parses and the target renderer behaves correctly. |
| Operations | Links, CTA, metadata, dates, ownership, and review state are current. |

A clean spellcheck or preservation script covers only a small part of this table.

## Severity model

### Blocker

Publication would be materially misleading, broken, unsafe, or unauthorized.

Examples:

- unsupported fact, quotation, metric, or source;
- changed legal or causal force;
- broken frontmatter, JSX, HTML, code, link, or CTA;
- unresolved placeholder or assistant chatter;
- wrong locale or meaning-changing translation;
- identity language requiring subject-matter confirmation;
- a required approval that has not happened.

### Warning

The content can publish only if the owner accepts a bounded quality or maintenance risk.

Examples:

- a sentence is dense but accurate;
- a non-critical link lacks descriptive label text;
- local terminology is understandable but not yet checked against a glossary;
- an example is dated but still true;
- stylistic consistency differs from a weak or outdated sample.

### Note

An optional improvement with no meaningful publication risk. Keep notes sparse; do not turn publication review into personal preference commentary.

## Review order

1. Confirm the current editorial contract and protected-content ledger.
2. Check objective production artifacts.
3. Reconcile claims, values, force, attribution, and scope.
4. Review audience, voice, and document structure.
5. Review locale and inclusive language at the proper expertise level.
6. Parse, build, render, and check links with native project tools.
7. Confirm metadata, dates, CTA, ownership, and approval state.
8. Return a bounded verdict.

Review high-risk dimensions before polishing small stylistic points.

## Evidence ownership

Every unresolved item needs an owner and an action:

| Gap | Owner | Required action |
| --- | --- | --- |
| Product capability or metric | Product/data owner | Confirm against current source of truth. |
| Legal or policy wording | Authorized legal/policy owner | Approve exact language. |
| Specialized terminology | Subject-matter expert | Confirm meaning and accepted term. |
| Locale naturalness | Fluent target-locale editor | Review syntax, register, and cultural fit. |
| Identity description | Subject/community guidance or approved standard | Confirm preferred and relevant wording. |
| Markup or renderer behavior | Maintainer/build pipeline | Run parser, build, and preview. |

“Needs review” is incomplete. Name what must be reviewed, by whom, and why.

## Mode-specific output

Use this shape when issues remain:

```markdown
## Blockers
- The 18% claim has no supplied source. Owner: analytics. Action: provide the report or remove the claim.

## Warnings
- Turkish terminology is consistent, but this is high-stakes policy copy. Owner: fluent legal editor.

## Unresolved evidence
- The source and draft disagree on the effective date: 1 May vs 15 May.

## Ready copy
[Only sections that are actually ready]
```

When no material issue remains, return clean ready copy by default. Do not force a report the user did not request.

## Format proof

For structured content, claim only the verification rung reached:

1. Source inspected
2. Deterministic audit passed
3. Parser or formatter passed
4. Project build passed
5. Rendered output observed
6. Accountable reviewer approved

“Audit passed” must not imply “rendered correctly” or “approved.”

## Locale proof

Use confidence labels internally or in unresolved notes:

- **High:** editor is fluent in the target locale and the domain/register is familiar.
- **Moderate:** strong language competence, but specialized terminology or cultural nuance needs review.
- **Low:** meaning-preserving conservative edit only; fluent review required before publication.

Do not claim native fluency on behalf of a model or tool. High-stakes medical, legal, financial, safety, or public-policy content requires appropriately qualified human review even when the prose reads naturally.

## Acceptance test

Ask the following at the end:

- Can a reader distinguish fact, inference, recommendation, and limitation?
- Does every strong claim have adequate evidence and attribution?
- Did any edit broaden scope, causality, certainty, or benefit?
- Does the opening reach the reader's actual task quickly?
- Does each section add a distinct contribution?
- Is the voice warm through helpfulness rather than invented intimacy?
- Does the locale follow local syntax, terminology, and relationship cues?
- Do the file and links parse, render, and navigate correctly?
- Is every unresolved risk assigned to an owner?

## Common failures

| Failure | Correction |
| --- | --- |
| Publishing because the prose “sounds natural” | Verify evidence, meaning, locale, format, and approvals separately. |
| Returning dozens of taste notes | Report only reader-impacting or contract-relevant findings. |
| Saying “native review recommended” with no stakes | State the confidence, risk, owner, and decision. |
| Calling a regex scan validation | Run native parser/build/render checks. |
| Hiding not-ready sections inside polished copy | Separate blockers and withhold unsupported claims. |

## Completion check

- The verdict covers every applicable readiness dimension.
- Blockers, warnings, and notes use consistent severity.
- Unresolved evidence has a named owner and action.
- Verification claims match the highest rung actually observed.
- Ready copy excludes unsupported or structurally broken material.

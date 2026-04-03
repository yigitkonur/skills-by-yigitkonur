# Synthesis Patterns

How the orchestrator reads all agent outputs and creates the master summary and cross-domain connections. This is the phase where the orchestrator's unique value emerges — no individual researcher can see the full picture.

## Why the Orchestrator Synthesizes Personally

Each researcher agent works in isolation. They know their domain deeply but cannot see:
- Contradictions between domains (iOS docs say X, community says Y)
- Cross-cutting patterns (the same limitation affects 3 different features)
- Priority implications (finding A in domain 1 changes the urgency of finding B in domain 3)
- Integration points (how findings from different agents connect to existing project decisions)

The orchestrator reads ALL outputs and creates connections agents working in isolation cannot make. This is not delegable — no subagent gets the cross-domain view.

## The Synthesis Process

### Step 1: Read Everything

Read every documentation file written from agent outputs. Note:
- Recurring themes across agents
- Contradictions between agents
- Surprises (findings that change your understanding of the topic)
- Gaps (topics no agent covered despite planning for them)
- Connection points to existing project context

### Step 2: Resolve Contradictions

When two agents report conflicting information:

| Conflict type | Resolution |
|---|---|
| Different version/date | Use the more recent finding; note the change |
| Official docs vs community | Both are valid — docs = intended, community = actual |
| Platform A vs Platform B | Explicitly document the difference (this IS the finding) |
| Agent A uncertain, Agent B confident | Trust the confident finding if it has source backing |

### Step 3: Extract Cross-Domain Insights

Look for patterns that span multiple documentation files:

- **Feature availability patterns:** "These 5 features are iOS-only; these 3 work on both platforms"
- **Privacy implications:** "These 4 configuration options each have privacy risks for FnTalk"
- **Priority ordering:** "Based on community feedback + feature availability, implement in this order"
- **Risk clusters:** "These 3 findings together create a compound risk that no single finding shows"

### Step 4: Write the Master Summary

Structure:

```markdown
# [Topic] Research — Master Summary

**Research date:** {date}
**Scope:** {what was researched}
**Sources:** {aggregate: N docs pages, N Reddit threads, N GitHub issues}

## Document Index

| # | Doc | Key Content |
|---|-----|-------------|
| 01 | [link](path) | One-line description |
| 02 | [link](path) | One-line description |

## Critical Findings

{The 5-10 most important things. Prioritized. Each with
a cross-reference to the doc that contains the full details.}

## Cross-Domain Insights

{Patterns and connections that only become visible when
reading all research together.}

## Action Items

{Prioritized: what to do first, what to do later, what to skip.
Each action references the finding that motivates it.}

## What This Research Covers vs. Doesn't

{Explicit scope boundaries. What remains to be researched.
What was attempted but couldn't be verified.}
```

### Step 5: Write the Integration Map (if applicable)

When researching for an existing project that has prior research or decisions:

```markdown
# Integration Map

How this research connects to existing project documentation.

## Existing Doc → New Research Cross-References

| Existing Doc | Key Finding | New Research Extends/Confirms |
|---|---|---|
| {path} | {what it said} | {what new research adds} |

## New Findings Not in Existing Research

{Genuinely new information that changes or adds to the
project's knowledge base.}

## Decision Reinforcements

{Which existing decisions are validated by the new research.
Which need revisiting.}
```

## Source Attribution Standards

Throughout all documentation:

| Source Type | Attribution Format |
|---|---|
| Official docs | `docs.sentry.io/platforms/apple/guides/ios/configuration/options/` |
| GitHub issue | `getsentry/sentry-cocoa#4618` |
| Reddit | `u/username, r/subreddit, date` with direct quote |
| Blog post | Author, title, date, URL |
| SDK source code | `Sources/Swift/Options.swift` in `sentry-cocoa@9.8.0` |
| CHANGELOG | `sentry-cocoa CHANGELOG v9.7.0` |

"Reddit consensus" is not a citation. "Community reports" is not a citation. Name the source.

## Common Synthesis Mistakes

| Mistake | Fix |
|---|---|
| Summarizing each agent's output sequentially | Cross-cut by theme, not by agent |
| Ignoring contradictions between agents | Explicitly resolve or document them |
| Master summary is just a table of contents | Add critical findings, insights, and action items |
| No connection to existing project context | Write the integration map |
| Gaps hidden by omission | Explicitly state what couldn't be verified |
| Action items without priority | Order by urgency × impact × reversibility |

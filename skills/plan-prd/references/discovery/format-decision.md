# Format Decision Guide

Not every feature needs a full PRD. Choose the right format based on the situation.

## Decision matrix

| Signal | Full PRD | Lightweight PRD | Eval-first PRD | User Stories Only |
|---|---|---|---|---|
| Multiple stakeholders need alignment | Yes | | | |
| Significant architectural decisions | Yes | | | |
| Cross-team dependencies | Yes | | | |
| New product or major feature | Yes | | | |
| Small enhancement, clear scope | | Yes | | |
| Bug fix with behavior change | | Yes | | |
| AI/ML feature with non-deterministic behavior | | | Yes | |
| Feature best understood through prototype | | | Yes | |
| Problem is well-understood by team | | | | Yes |
| Iteration on existing, well-documented feature | | | | Yes |

## Format descriptions

### Full PRD (10 sections)
Use the full 10-section markdown block in `references/templates/prd-template.md`. Use when multiple stakeholders need to align on what to build, why, and what success looks like. Expected effort: 2-4 hours of discovery + drafting.

### Lightweight PRD (5 sections)
An abbreviated version for smaller features:
1. Problem Statement (2-3 sentences)
2. User Stories + Acceptance Criteria
3. Technical Constraints
4. Out of Scope
5. Success Metric (ONE metric)

Skip personas, architectural options, and detailed risk analysis. Expected effort: 30-60 minutes. Use the concrete markdown block in `references/templates/prd-template.md` rather than inventing your own abbreviated structure.

### Eval-first PRD (for AI/ML features)
When behavior is hard to specify in prose, lead with evaluation criteria:
1. Problem Statement
2. Evaluation Criteria (test cases, expected outputs, accuracy thresholds)
3. Sample Input/Output Pairs (the "golden dataset")
4. Boundaries (what the AI must/should/must-not do)
5. Human Escalation Rules

This follows the "evals as living PRDs" principle — executable evaluations are the truest form of requirements for AI features. Consider "demos before memos": a working prototype may communicate requirements better than documentation. Use the concrete markdown block in `references/templates/prd-template.md` instead of retrofitting the full 10-section structure.

### User Stories Only
When the problem is already well-understood, skip the formal document:
1. Use the user-stories-only markdown block in `references/templates/prd-template.md`
2. Keep the output to a short context line, numbered user stories with acceptance criteria, and one "Out of Scope" section
3. Submit as a GitHub issue or file output using the normal destination rules

## Decision signals from the user

| User says | Likely format |
|---|---|
| "I have a big idea I need to spec out" | Full PRD |
| "We need to add a small feature to..." | Lightweight PRD |
| "I want the AI to be able to..." | Eval-first PRD |
| "Can you just write stories for this?" | User Stories Only |
| "I need alignment across teams on..." | Full PRD |
| "This is a quick enhancement" | Lightweight PRD |

## When to upgrade

Start lightweight and upgrade if:
- Discovery reveals hidden complexity
- Multiple stakeholders have conflicting views
- The feature touches 3+ systems
- Security or compliance concerns surface
- The team disagrees on scope

It is easier to add sections to a lightweight PRD than to strip a full PRD down.

If unanswered `TBD`s remain in any non-full format, append an `Open Questions` section instead of guessing.

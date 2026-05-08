# Degrees of Freedom

Use this file when deciding how specific a step or reference should be. A skill is not one style top-to-bottom — different parts need different levels of prescriptiveness. Get the level wrong and the skill either fights the agent's judgment or leaves the agent guessing.

## The three levels

| Level | What you give the agent | When to use |
|---|---|---|
| **High freedom** | Goals and principles. Let the agent choose how. | The agent has enough training-data coverage that its defaults are already good. |
| **Medium freedom** | A shape, a checklist, or a structured flow. Agent fills in detail. | The agent knows the pieces but skips steps or orders them wrong. |
| **Low freedom** | Exact commands, specific file paths, literal code to copy. | Deterministic steps where any variation breaks the result. |

One skill typically uses all three — high freedom for the "pick the right approach" parts, medium for workflow structure, low for installation commands and validation snippets.

## High freedom — goals and principles

Use this level when:

- The agent has strong defaults (common languages, mainstream frameworks, standard file formats)
- The task has many valid approaches and forcing one would be worse than letting the agent choose
- The step rewards judgment more than checklist compliance

```
High freedom:   "Inventory the workspace enough to understand what already
                 exists before drafting new content."

Too low:        "Run `tree -L 3 --gitignore` and read every .md file."
                (Over-prescribes. Wastes time on large repos.)
```

Risk: high-freedom instructions fail when the agent does not actually have good defaults. If testing shows the agent picks wrong, drop a level.

## Medium freedom — structured flow

Use this level when:

- The agent knows the pieces but order or completeness matters
- There are multiple valid approaches but the skill picks one to ensure consistency
- You want the agent to apply judgment *within* a defined structure

```
Medium freedom:
"Before synthesizing, build a markdown comparison table with at least these
 columns: Source, Focus, Strengths, Gaps, Relevant paths, Inherit / avoid.
 Every row ends with a decision, not just an observation."
```

The shape is fixed (columns, "decision per row"). The content is the agent's judgment. This is the right level for most workflow steps.

Risk: medium-freedom instructions fail when the structure is arbitrary. If the columns or ordering do not actually matter, the prescriptiveness is dead weight — drop to high freedom.

## Low freedom — exact literals

Use this level when:

- Any variation breaks the result (install commands, validation scripts, file paths)
- The step is deterministic and the agent's creativity adds no value
- Correctness depends on an exact string match

```
Low freedom:
"Run this exact command to verify no orphan reference files:

  for f in $(find references -name '*.md' -type f); do
    grep -q \"$(basename $f)\" SKILL.md || echo \"ORPHAN: $f\"
  done"
```

Risk: low-freedom instructions become stale when the underlying command or API changes. Prefer scripts in `scripts/` for anything that needs to stay current — the script can be updated once and every skill referencing it gets the fix.

## Picking the right level — a diagnostic

Ask: what happens when the agent deviates from my instruction?

| Deviation result | Right level |
|---|---|
| Agent picks an equally good alternative — result is fine | High freedom. Stop over-specifying. |
| Agent skips a step or does them out of order — result degrades | Medium freedom. Give it a shape. |
| Agent produces subtly wrong output because a literal value matters | Low freedom. Give it the exact string. |

If you cannot predict the deviation result, test. Run the skill on an agent without the instruction in question and see what it does.

## Mixing levels in one skill

A well-designed skill moves between levels on purpose:

```
Frontmatter description       → Medium (trigger phrases, not just prose)
Trigger boundary              → Medium (specific use-when lists)
Workflow steps (main path)    → Medium (ordered steps, each can be judged)
Step 1: classify the job      → High (agent picks based on described signals)
Step 4: run remote research   → Low (exact commands, specific flags)
Step 5: compare               → Medium (required columns, free content)
Guardrails                    → Low to medium (exact "do not" statements)
Reference routing             → Medium (when-to-read tables)
```

Anti-pattern: uniform low freedom throughout. The skill feels like a manual. The agent loses the room to apply judgment where judgment actually helps.

Anti-pattern: uniform high freedom throughout. The agent has no idea what success looks like. Compliance is zero in testing.

## Interaction with persuasion principles

High freedom pairs with unity. The agent is a collaborator, choosing how to accomplish the goal.

Low freedom pairs with authority. The instruction is non-negotiable. Imperative voice, no hedging. "Run this exact command" — not "you might consider running."

Medium freedom pairs with both, depending on the step. Workflow shape is authoritative ("these are the steps, in this order"); step content invites the agent's judgment.

## When to drop a level

Testing shows the agent consistently produces wrong output at your chosen level? Drop one level down:

- High → medium: add a checklist or structure
- Medium → low: add exact commands and specific values
- Low → code: move the logic to `scripts/` so it is executable, not just prose

When testing shows the agent reliably does the right thing, try moving *up* a level in the next revision. Over-specification is cost without benefit.

## Anti-patterns

**Prescribing where the agent has good defaults.** Listing "read the file using the Read tool" is noise — the agent already knows how to read files.

**Under-specifying at deterministic steps.** "Validate the skill" without a command leaves the agent guessing. If there is one right way, state it.

**Mixing levels randomly within a single step.** A step that starts with "use your judgment to decide X" then says "run exactly this command with these flags" for X confuses the reader. Pick the level per step.

**Leaving literal commands stale.** Low-freedom instructions age. Move commands to `scripts/` so they can be updated once and inherited by every skill that routes to them.

## Bottom line

Freedom is a design choice, not a default. Pick the level per step based on what breaks when the agent deviates. Test. Drop a level when testing shows the agent cannot handle the freedom. Raise a level when the prescriptiveness adds no value.

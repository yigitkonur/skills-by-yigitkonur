# Content / Markdown Review

Author-side checklist for PRs that are primarily about prose — blog posts, documentation, README edits, SKILL.md bodies, changelogs, migration guides. Use when classifying the diff's domain as **content-markdown** in SKILL.md Step 4.

## What content reviewers care about

| Concern | Why it matters | Evidence they want |
|---|---|---|
| **Audience fit** | The right reader, the right level of detail | Audience stated; jargon matched to them |
| **Claim accuracy** | One wrong claim sinks the piece | Claims linked to evidence or marked as opinion |
| **Code snippet correctness** | Broken examples train bad habits | Each snippet runs; outputs shown |
| **Link rot** | Dead links undermine trust | All links resolve; archive for volatile sources |
| **Voice consistency** | Mixed voice feels unedited | One voice, matched to the publication |
| **Structural clarity** | Readers need headings to navigate | Logical H2/H3 tree; no burying |
| **Brevity without loss** | Every redundant paragraph costs reader time | Prose tightened; no throat-clearing |
| **Image + asset hygiene** | Orphaned assets bloat the repo | Every asset used; appropriate format |

## Weaknesses the author should pre-empt

- **Factual claims.** Every assertion you can't defend on the spot is a risk. Link to the primary source, or mark it as your opinion.
- **Code examples.** Did you actually run every snippet you included? If it's pseudo-code, is that labeled?
- **Command accuracy.** `npm install` vs. `pnpm install` vs. `yarn add` — match the actual tool the reader is using, or name both.
- **Version-specific content.** Does the post pin versions? Is there a "last tested on" date? Content about `react@18` becomes wrong under `react@19`.
- **Links.** Internal links (relative paths) break on move/rename. External links rot. Consider archive.org for critical citations.
- **Images.** Are they optimized? Is alt text present for accessibility? Does the image add information or decorate?
- **Consistency with other docs.** If this contradicts `README.md` or a sibling doc, which is right? Update both or flag the conflict.
- **SEO metadata** (if blog post): title, description, og:image, canonical URL.
- **Table of contents** (if >300 lines): readers under context pressure skim the TOC first.
- **Headings hierarchy.** Jumping from H2 to H4 breaks document outline tools and screen readers.

## Questions to ask the reviewer explicitly

- "The post assumes the reader already knows Conventional Commits. Should I add a short primer at the top, or link out?"
- "I made a claim in the 'Why X is bad' section — source is a 2023 blog post. Do you have a more authoritative source, or is this one fine?"
- "The tone leans opinionated ('this pattern is wrong'). Is that the voice the publication wants, or should it be 'this pattern has these trade-offs'?"
- "Migration guide covers 1.x → 2.x. Should it also cover 0.x → 2.x (two-hop), or point to the 0.x → 1.x guide and chain?"
- "README got a new 'Quickstart' section. I didn't remove the old 'Installation' section because it's more complete. Merge or keep split?"

## What to verify before opening the PR

- [ ] All code snippets run as written (copy-paste from the doc, actually execute)
- [ ] All internal links resolve (`find . -name '*.md' | xargs markdown-link-check` or equivalent)
- [ ] All external links open (manual spot check on the critical few)
- [ ] Headings form a valid outline (H1 → H2 → H3, no H2 → H4 jumps)
- [ ] Images have alt text
- [ ] Grammar/spelling pass (`prettier`, `vale`, or equivalent linter if the project uses one)
- [ ] If blog: SEO metadata present; preview rendered
- [ ] If changelog: entries grouped (Added / Changed / Fixed / Removed); dates consistent
- [ ] `wc -w` or similar: is the piece as short as it can be?

## Signals the review is off-track

- "The reader will figure it out." → They won't. Write for the worst-case reader of the piece.
- "This is just copy editing, don't need a review." → Copy changes ship to every user. They deserve the same rigor.
- "I'll update the related docs later." → "Later" is tomorrow, which is never. Update now or flag as follow-up.
- "The code snippet is close — I paraphrased from the real one." → Paste the real one. Paraphrased code is broken code.
- "The post is long because the topic is complex." → Complex topics deserve clear writing. Length ≠ depth.

## When to split the PR

- New blog post + unrelated doc fixes → split; one PR per piece
- Doc overhaul + code change → split; docs land after code if the API shape matters
- Changelog entry + feature code → one PR is fine (they belong together)

## Style notes specific to this repo

If the PR touches SKILL.md files (for Claude skills), additional rules apply:

- Frontmatter `description` starts with "Use skill if you are" (repo convention)
- Frontmatter `description` is 30 words or fewer
- SKILL.md body under 500 lines; split detail into `references/` files
- No junk files, no stale sibling-skill names
- Route to `build-skills` for the authoring workflow if creating a new skill

If the PR touches blog posts or long-form content, consider whether a sibling research/citation doc is expected.

## Content follow-up skills

| Content type | Skill |
|---|---|
| Product Requirements Documents | `github/awesome-copilot/prd` (external) |
| Skill creation | `build-skills` |
| CLAUDE.md / AGENTS.md maintenance | `init-agent-config`, `claude-md-management:revise-claude-md` |

Name the specific doc type in the PR body so the reviewer loads the right lens.

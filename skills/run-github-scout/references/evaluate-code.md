# Code-Level Analysis

Use code-level checks only for the top few repos or when the user
asks for deeper comparison. Hard ceiling: 5 repos for deep evaluation
(see `evaluate.md` and `discipline.md` §10).

## Recommended sequence

1. Read the README intro (with the badge-zone skip below).
2. Check the root file tree for tests, workflows, docs, and release
   basics.
3. Search for the user's must-have feature in docs or obvious source
   locations.
4. Read 1-2 key files only if feature evidence is still unclear.

## README intro: skip the badge zone

Modern READMEs front-load badges, sponsor banners, and trending
markers before the first useful content. `head -100` on a modern
README often returns mostly logos and shields. The first useful prose
can start at line 50, 80, or later.

The better pattern jumps to the first `## ` heading, which usually
puts the agent past the badge wall:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | \
  awk '/^## /{found=1} found{print}' | head -80
```

If the first `## ` heading is sponsor-related (rare but possible),
scan to the second:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | \
  awk '/^## /{c++; if (c>=2){found=1}} found{print}' | head -80
```

If the README has no `## ` headings (a short-README repo), fall back
to:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | head -50
```

Ask of the README intro:

- does the repo describe the same problem the user asked about?
- does it explain installation or quick start clearly?
- does it show feature evidence, screenshots, or examples?

## Root file tree

```bash
gh api repos/OWNER/REPO/contents/ --jq '.[].name'
```

Look for:

- test directories
- workflow files
- docs
- changelog or releases
- clear package or build metadata

## Targeted source read

Use only after README and file-tree evidence:

- read one entry point, API surface, or config file
- verify a must-have feature, not every implementation detail
- stop after 1-2 files unless the user explicitly wants code review
  depth

## Output pattern

For each repo, summarize:

- feature evidence found
- docs or onboarding quality
- test or CI visibility
- obvious maintenance risks
- caveats or unknowns

Keep the per-repo summary tight — the deepen step's output flows into
the final shortlist, not into a separate document.

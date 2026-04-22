# Code-Level Analysis

Use code-level checks only for the top few repos or when the user asks for deeper comparison.

## Recommended sequence

1. Read the README intro and install section.
2. Check the root file tree for tests, workflows, docs, and release basics.
3. Search for the user's must-have feature in docs or obvious source locations.
4. Read 1-2 key files only if feature evidence is still unclear.

## Useful checks

### README intro

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | head -80
```

Ask:
- does the repo describe the same problem the user asked about?
- does it explain installation or quick start clearly?
- does it show feature evidence, screenshots, or examples?

### Root file tree

```bash
gh api repos/OWNER/REPO/contents/ --jq '.[].name'
```

Look for:
- test directories
- workflow files
- docs
- changelog or releases
- clear package or build metadata

### Targeted source read

Use only after README and file-tree evidence:
- read one entry point, API surface, or config file
- verify a must-have feature, not every implementation detail
- stop after 1-2 files unless the user explicitly wants code review depth

## Output pattern

For each repo, summarize:
- feature evidence found
- docs or onboarding quality
- test or CI visibility
- obvious maintenance risks
- caveats or unknowns

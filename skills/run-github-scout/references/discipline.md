# Discipline — How to Think While Searching

This file is the keystone. Read it on first use of the skill, and any
time results feel off-shape. Other references describe **what** to do;
this file describes **how to think** while doing it.

The single most important rule:

> **GitHub search returns LEADS, not ANSWERS. Half the job is
> filtering noise. The other half is asking the right questions
> before searching.**

Most derailments in this skill come from skipping the upstream
thinking and treating raw `gh search repos` output as a shortlist.
That treats the tool as if it were truth. It is not. It is a wide net
that catches many wrong fish.

## 1. The mental model

Every research session looks the same shape:

```
clarify intent → verify named anchors → first-pass search
   → classify → refine once → deepen top 5 → present
```

Of these stages, **the search itself is the cheapest**. The expensive
work is upstream (clarify, verify) and downstream (classify, deepen).
Burning a lot of `gh` calls is rarely the bottleneck; **wasting
attention on the wrong candidates is**. The discipline below biases
attention toward the candidates worth attention.

## 2. Verify-first when the user names a thing

When the user names a known repo, project, tool, or library, the
**first** call is to verify what that thing actually is. Not to
search for alternatives. Not to deepen. Verify.

The pattern:

```bash
gh search repos 'NAME' --limit 5 --sort=stars \
  --json fullName,description,stargazersCount,updatedAt \
  --jq '.[] | [.fullName, (.stargazersCount|tostring), (.updatedAt[:10]), (.description // "" | .[:80])] | @tsv'
```

If multiple repos share the name, follow with one targeted check on
the most plausible match:

```bash
gh api repos/OWNER/REPO --jq '{full_name, description, stars: .stargazers_count, pushed: .pushed_at[:10], topics, license: .license.spdx_id, language}'
```

Confirm the named thing's category, age, owner, license. Only then
proceed to alternative discovery. If the named thing turns out to be
unrelated to what the user is asking about, surface that mismatch
back to the user. Do not silently re-interpret.

**The clink derailment.** A real session: the user named "clink"
alongside `agent-bridge`. The skill assumed clink was a multi-CLI
manager and searched the broader category. Several queries later, a
verify-first call revealed `chrisant996/clink` (5.2k⭐) — a cmd.exe
shell editor, totally unrelated to AI agents. One verify call upfront
would have caught this in 2 seconds. Instead, ~3-4 search calls and
some interpretive drift were spent on the wrong assumption. The
lesson: **never search for alternatives to a name you have not yet
verified.**

## 3. Star threshold matrix by domain

`stars:>N` is a powerful filter when set right and a destructive
filter when set wrong. The right threshold depends on **how mature
the ecosystem is**, not on personal preference.

| Ecosystem maturity | Examples | Threshold | Why |
|---|---|---|---|
| Very young (12-24 months) | AI coding agents, MCP bridges, agent orchestrators, vibe-coding tools | none, or `stars:>1` | Quality repos exist below 100⭐; threshold filters them out. The niche is too young for stars to mean adoption. |
| Young (2-4 years) | Recent JS frameworks, modern CSS toolkits, MLOps tools | `stars:>10` to `stars:>50` | Some signal needed; not enough star history to filter aggressively. |
| Mature (5+ years) | Web frameworks, database tooling, Docker tooling | `stars:>500` | Star noise is high; threshold cuts dead and toy repos. |
| Very mature (10+ years) | Linters, build tools, classic CLIs | `stars:>1000` | Without a strong floor, the long tail of abandoned projects dominates. |

**Decision rule.** Start with **no star threshold** for young
ecosystems. Add a threshold only after the first pass returns
materially too much noise. A threshold added pre-emptively in a young
niche silently filters out the strongest candidates.

When unsure, run the first pass without a threshold and observe the
result distribution. If the top results are obviously toy or dead,
you know you need a threshold; if the top results are credible at
50-200⭐, no threshold is correct.

## 4. The OR trap (three classes)

`OR` in `gh search` is parsed by token, not by phrase. There are
three classes of OR usage and they behave differently:

```
Class A — OR between SINGLE TOKENS: WORKS
  ✓ outline OR affine
  ✓ agent OR copilot OR assistant
  ✓ tmux OR zellij OR screen

Class B — OR between QUOTED PHRASES: WORKS
  ✓ "claude code" OR "openai codex"
  ✓ "code review bot" OR "review agent"
  ✓ "model context protocol" OR "agent protocol"

Class C — OR between BARE MULTI-WORD TERMS: AMBIGUOUS, AVOID
  ✗ claude code OR codex agents
  ✗ notion alternative OR self-hosted wiki
  ✗ aider cline OR continue dev

  Why it breaks: GitHub's parser splits on whitespace and applies OR
  per-token, so the agent intends (A B) OR (C D) but gets
  (A AND B) OR (C AND D). The query returns broad, weakly-relevant
  results that include any pair of the four terms.
```

Mitigation when a Class C query is what you want: split into two
separate searches and merge per `gh-output.md` recipe 4 (sort -u on
the union). Or quote the multi-word phrases (Class B). **Do not run
Class C queries** — they look reasonable, return garbage, and waste
attention on filtering bad results.

## 5. The `topic:` trap

`topic:X` filters to repos that have hand-tagged that topic. Topics
are user-supplied metadata. They are spam-prone, especially for
trending categories where many repos add popular topics for
discoverability.

A real session example: `topic:claude-code topic:multi-agent` returned
175k-star projects that had nothing to do with managing multiple
CLIs (one was a personal "agent harness optimization system"). The
star count correlated with topic-spam reach, not relevance.

**Rule.** Use `topic:` ONLY on shortlisted repos to broaden adjacent
discovery (e.g., "what are the related topics to my best candidate?
let me look at one more topic"). NEVER use `topic:` in a first-pass
discovery search. The signal-to-noise is too low.

The same rule applies (more weakly) to `in:readme` and `in:topic`:
treat them as last-resort qualifiers when other angles failed, not as
first-line tools.

## 6. The `in:readme` trap

`in:readme` matches anywhere in the README body. Modern READMEs
contain dozens of buzzwords for SEO. Searches that hit `in:readme`
return huge result sets with high false-positive rates.

Use `in:name` or `in:description` for naming-mismatch problems.
Reach for `in:readme` only as a last resort when both `in:name` and
`in:description` returned nothing useful AND you have a strong prior
that the term must appear somewhere in the README of relevant repos.

## 7. Empty-result recovery

When a `gh search repos` call returns 0 rows, **do not fire another
search immediately**. Diagnose first. The likely causes have known
fixes:

| Symptom | Likely cause | Recovery |
|---|---|---|
| 0 results, 4+ technical tokens AND-ed | Over-constrained | Drop the most specific token; re-run |
| 0 results, has `topic:X` plus free text | `topic:` filtered too aggressively | Drop the topic qualifier |
| 0 results, has `stars:>N` plus niche domain | Threshold above the niche's ceiling | Drop the threshold (see §3) |
| 0 results, OR query with bare multi-word | OR parsing ambiguity (Class C, see §4) | Quote phrases or split into two searches |
| 0 results across 3 reasonable retries | The combination of constraints genuinely has no matches | Surface the gap; consider `web-augment.md` |

A real session example: `mcp bridge claude codex agent fork:false
archived:false stars:>2` returned 0 because five technical noun-phrase
tokens were AND-ed plus a star threshold in a young niche. The fix:
drop tokens to 2-3 (`mcp bridge agent`), drop the threshold. Worked
on the next call.

**Rule.** Empty results are diagnostic information, not failures.
Read them.

## 8. The classify-before-deepen gate

After the first pass, before reading ANY README or running ANY API
call beyond the bare search, the agent must classify the candidates
into a typed table:

```markdown
| Repo | Class | Reason | Signals |
|---|---|---|---|
| owner/repo1 | relevant | Direct match for X | 4.2k⭐, pushed 2026-04, MIT |
| owner/repo2 | maybe | Adjacent — wrapper, not engine | 800⭐, active, no clear license |
| owner/repo3 | off-topic | Tutorial repo, not implementation | — |
```

The table is the **gate**. Without it, the agent has no basis for
choosing top-3-5 to deepen. Picking 5 candidates from a 50-row
search dump without classifying is guessing.

The classify table also surfaces:
- **Naming clusters** the agent harvests for refinement (terms that
  appear across the relevant set).
- **Off-topic patterns** that explain what to drop from future
  searches.
- **Maybe-tier signals** that may promote to relevant after a brief
  README scan.

Do this BEFORE the first README read. Always. The skill's
`dedup-and-rank.md` describes this; this file enforces it.

## 9. README intro reading: skip the badge zone

`head -100` on a modern README does not give you the README intro.
Modern READMEs front-load badges, sponsor banners, and trending
markers. The first useful prose can start at line 50, 80, or later.

A real session example: `chenhg5/cc-connect`'s README had ~80 lines
of sponsor banners before the first useful content. `head -100`
returned almost entirely sponsor logos.

The better pattern:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | \
  awk '/^## /{found=1} found{print}' | head -80
```

This skips everything before the first `## ` heading, which usually
puts the agent past the badge wall. If the first heading is sponsor-
related (rare but possible), scan to the second:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | \
  awk '/^## /{c++; if (c>=2){found=1}} found{print}' | head -80
```

If the README has no `## ` headings at all (a short-README repo),
fall back to `head -50`.

## 10. Top-N is a hard ceiling, not a target

"Limit deeper evaluation to the top 3-5 repos" is a **hard ceiling
of 5**, not a soft target around 5.

Going to 6+ candidates for deep evaluation requires an explicit
inline justification at the moment the deepening starts:

> "Promoting `owner/repo6` to deep evaluation because it surfaced a
> decision-flipping signal during the classify pass — it was the only
> candidate with X feature."

Without that justification, stop at 5. Going to 7-10 candidates
silently is a discipline failure that erodes the rest of the
session: the synthesis at the end will be diluted across too many
repos, none deeply understood.

## 11. The pre-search checklist

Before firing the first `gh` call, confirm internally:

- [ ] Did the user name a known thing? If yes, **verify-first** call
      goes before any alternative search.
- [ ] What is the ecosystem maturity? Pick a star threshold per §3
      (or none).
- [ ] What is the core problem in ≤10 words? (forces specificity)
- [ ] What 3-6 first-pass angles cover orthogonal facets, not
      paraphrases?
- [ ] Are any angles using `topic:` for discovery? (drop them per §5)
- [ ] Are any angles using bare multi-word OR? (fix or split per §4)
- [ ] Do any angles AND together 4+ technical tokens? (likely
      empty-result risk per §7)

The checklist is mental, not procedural. The agent does not write it
out in the conversation. It just confirms each item before launching
the first call.

## 12. The synthesis discipline

When presenting the final shortlist:

- **Cite the path** when relevant ("found via `topic:X` after Reddit
  hint" — useful when the discovery process itself is informative).
- **Be honest about what was NOT verified** (the agent read 5
  READMEs, not 50; signal that the deeper claims are scoped).
- **Surface naming gaps** the user may want to clarify (e.g., "the
  thing you called clink turned out to be X — were you thinking of
  Y?").
- **Stop when the shortlist answers the need.** The skill's stop
  rules apply: when new searches mostly repeat known repos, when
  remaining gaps are uncertainty rather than discovery, the field
  is exhausted.

## Anti-pattern summary

The five most common derailments observed in real sessions:

1. **Skipping verify-first** when the user names a thing.
2. **First-pass `topic:` discovery** that returns spam.
3. **Class C OR queries** that return ambiguous garbage.
4. **Skipping the classify table** between first-pass and deepen.
5. **Deepening 7-10 READMEs** instead of stopping at 5.

If a session feels off-shape, check this list first. The fix is
almost always upstream — a missed verify, a noisy qualifier, an
unclassified candidate set.

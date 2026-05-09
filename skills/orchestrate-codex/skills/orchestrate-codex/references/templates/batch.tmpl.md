# Batch mode prompt template

The batch runner renders one prompt file per input row by substituting the placeholder `XXXXXXXXXXXXX` in this template with the row's content. The output of each codex invocation lands at `answers/<slug>.md`.

The template should produce a deterministic, focused, non-trivial document per input. "Non-trivial" is enforced by `audit-sizes.sh` after the run.

---

## Template

```
# Intent

<one sentence: what document should this produce — research brief, summary, code-extraction, comparison>

# Input

XXXXXXXXXXXXX

# Discovery — read first

Use up to 80 web search angles if the input warrants it; you may finish under that. Prefer primary sources (official docs, changelogs, source code, RFCs) over aggregators. Use forums and community threads only for edge cases not in the primary sources. (For pure code-generation batch prompts where the Input is self-contained, replace this section with the paths/concepts the agent should read.)

For each cited claim, note the source with title + URL + access date.

# Constraints

- <output format: e.g. markdown with `## Summary`, `## Sources`, `## Open questions` sections>
- <length ceiling: e.g. 2000 words; you may come in under>
- <forbidden: speculation without sources, lifted text without quotation marks, deprecated API references>

# Success criteria

- Output is structured per the format above
- All factual claims are sourced
- File size is non-trivial (≥ MIN bytes; default MIN=10000)

# Out-of-scope

- Do NOT fabricate sources or invent URLs.
- Do NOT include unrelated tangents from web searches.
- Do NOT mix outputs across inputs (one input → one output file).
- Do NOT add prose preamble or trailing commentary outside the documented format.

# Failure protocol

If the input is malformed (parked domain, deleted resource, empty page): produce a 5-line "could not research" output explaining what was tried and what was found. Do not fabricate content. The audit step will flag the small output for human review.
```

Note: the Failure protocol shape above is batch-mode specific (the 5-line "could not research" output is what `audit-sizes.sh` flags for human review). This per-mode template is authoritative for that section; see `references/universal/prompt-discipline.md` §"Failure protocol — mode-specific shapes".

## Why each section

- **Intent** — keeps every output type-coherent across N inputs.
- **Input** — the placeholder. Render-prompts.sh fills this with the row content. Do not prefix with "search for" or "find" — that biases codex toward web search even when the input is enough on its own.
- **Discovery (conditional)** — only include for research/web-grounded prompts. Skip for prompts where the input is self-contained (e.g. code transformations).
- **Constraints** — the output format is the highest-leverage knob. Codex follows formatting hints reliably.
- **Success criteria** — pair the format check with a size check (`audit-sizes.sh`). Size alone is a screening signal, not a quality verdict.
- **Failure protocol** — blocks fabrication. The "5-line could-not-research" output is intentional: it shows in `audit-sizes.sh` as below-floor and the user inspects.

## Slug derivation

The render script takes the input file and produces `prompts/<slug>.md`. Slug rules:
- Tab-delimited input (`name<TAB>content`): `name` becomes the slug. Use this for URL lists where you control the slug derivation upstream.
- Plain-line input: each line is the slug AND the content. Use this for short ID lists.

If two inputs render to the same slug, the render script writes a stderr warning and **skips the second**. Disambiguate the input (add a discriminator) before re-rendering.

## Sizing

Templates run 30–80 lines. Per-input prompt files end up roughly the same size. If your template is over 150 lines, the prompt is doing too much; split into two batches with two templates.

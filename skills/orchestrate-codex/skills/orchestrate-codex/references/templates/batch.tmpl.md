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
- File size is non-trivial (≥ MIN bytes; calibrate `MIN_BYTES` to your prompt type — see `references/universal/output-size-signals.md` "Per-prompt-type calibration table". The 10000-byte default is tuned for research / summarization; for a short prose deliverable like a 200-word TL;DR, set MIN ≈ 1000–2000)

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

If two inputs render to the same slug, `render-prompts.sh` exits 1 with `error: collision on <slug>.md` and writes nothing further. Disambiguate the input (add a discriminator) before re-rendering.

## Shared file + per-input variable

A common batch shape is "one shared rubric / spec / context file + N varying inputs". `render-prompts.sh` only knows about one placeholder (`XXXXXXXXXXXXX`), so the shared file has to enter the prompt one of two ways:

1. **Inline the shared file's content into the template** above the placeholder. Recommended — the rendered `prompts/<slug>.md` is fully self-contained, the prompt is deterministic regardless of cwd or filesystem state at codex spawn time, and audit / replay is trivial. Build the template from the shared file before rendering:

   ```bash
   { cat rubric.md; printf '\n\n# Input\n\nXXXXXXXXXXXXX\n'; } > template.md
   bash render-prompts.sh inputs.txt template.md prompts/
   ```

2. **`Read /abs/path/to/rubric.md` inside the prompt.** Works because batch passes `--dangerously-bypass-approvals-and-sandbox`, so codex can read arbitrary paths without an approval prompt. The runner's cwd at spawn is the workspace root (`--cwd` to the dispatcher), so use absolute paths or paths relative to that root. Less deterministic — the rubric file at the time codex reads it, not at the time you rendered.

   ```
   # Context

   Read /Users/me/project/rubric.md before applying the rubric below to the Input.

   # Input

   XXXXXXXXXXXXX
   ```

Prefer pattern 1 unless the shared file is large enough that inlining bloats every per-input prompt past your token budget.

## Sizing

Templates run 30–80 lines. Per-input prompt files end up roughly the same size. If your template is over 150 lines, the prompt is doing too much; split into two batches with two templates.

## 1:N output (one input → N variants)

Batch renders one prompt and one answer per input. If one logical row needs N output variants (e.g. translate the same string into 4 languages, generate 3 length variants per article), do **not** encode the output dimension into the slug or template — invoke batch N times, once per output bucket, each with its own `--answers-dir` and `--force-new-run --run-id <bucket-tag>`. See `references/modes/batch.md` §"1:N output (multi-invoke pattern)" for the canonical shell-loop.

# Output size signals — when small ≠ bad

The audit script flags small outputs because *most* small outputs in a uniform batch indicate something went wrong. But this is a probabilistic signal, not a verdict. This file walks through how to read sizes and decide.

## What size correlates with

For research/summarisation prompts run with the same template, output size correlates with:

1. **How much source material existed** — a deeply documented product produces a longer answer than one with a sparse public footprint.
2. **Reasoning effort actually spent** — codex sometimes returns early when the prompt seems complete, even if the user wanted more depth.
3. **Tool budget consumed** — if the prompt instructs codex to run web searches and codex hit a rate limit early, the answer is shorter.
4. **Random variance** — codex output is non-deterministic; the same prompt at `medium` reasoning can produce a 10 KB or 18 KB answer.

The third and fourth points mean size alone cannot identify "this answer is bad." A 5 KB answer for a thin product can be perfect; a 30 KB answer for a deep product can be padded with hallucinated detail.

## When small IS bad

Strong indicators that a small answer is genuinely weak:

- **Median tail.** Most answers in the batch are 15–25 KB and one is 2 KB. The outlier is suspicious.
- **Well-known input.** The input is a popular, well-documented thing (large company, mainstream product) — codex should have found a lot.
- **Output contains "Sources used: …" with very few entries.** A research prompt that turned up 1–2 sources usually means search failed.
- **Output starts with "I cannot find / I do not have access to / The page returned…".** Codex bailed instead of researching.

## When small ISN'T bad

Common false positives:

- **Niche or new product.** Public footprint is genuinely small (one homepage, no pricing page).
- **Parked or dead domain.** Codex correctly reports the domain doesn't resolve and stops there with a one-paragraph note.
- **Prompt asks for a one-paragraph summary.** If the template is short, expect short answers.
- **Real-world incident.** During the run that informed this skill, `project40-co.md` was 8.9 KB on first run and 2.1 KB on retry. Reading both: first run had more `[unconfirmed]` source synthesis from a press release; retry got blocked by the same parked domain and produced a shorter "I cannot scrape" note. The first run was *more useful*, despite still being below the median.

That last example is the rule, not the exception: **codex retries can produce smaller, worse output**. Always archive before retrying, always compare, always be willing to revert.

## The bottom-decile rule

Take the smallest 10% (or `max(N/10, 1)` items) of a batch and inspect them by hand. The cost is a few minutes; the benefit is catching real failures while not over-reacting to outliers.

If your batch is small (< 10 items), inspect everything below the absolute floor (default 10000 bytes).

## What to read in a flagged answer

For each flagged answer, read:

- **First 5 lines** — does it start with "Validation: …" / "Researched on …" / "Sources used: …" / a list, or with "I cannot / I don't have / Page failed"?
- **Sources count** — for a research prompt, how many distinct URLs are cited?
- **Coverage of expected sections** — does the answer hit every section your template asked for, or does it drop out partway?
- **Tag density** — `[unconfirmed]`, `[notable]`, `[limited info]` tags suggest the model knew its evidence was thin and disclosed it. That is a sign of *honest* output, even if smaller. Better than a confidently-wrong wall of text.

A 5 KB answer that hits every section, cites 3 sources, and tags uncertain claims is a *good* answer. A 25 KB answer that contradicts itself and cites zero sources is a *bad* answer. Size doesn't capture this — only reading does.

## When to retry vs. accept

- **Retry** if: median tail outlier, output bails with "cannot access" but the URL is reachable, sources count is suspiciously low for the input.
- **Accept** if: niche/new/dead input, structure intact, tags used appropriately, no contradictions.
- **Drop** if: input is genuinely unprocessable (parked domain, dead link). Document this as a known-empty result rather than retrying repeatedly.

## Calibrating the floor

The default 10000 bytes is calibrated for the use case in `SKILL.md` (a multi-section feature/pricing breakdown for a SaaS product). For other prompts:

```
prompt complexity                | reasonable floor
short summary (1 paragraph)      | 500 bytes
question/answer pair             | 1000 bytes
multi-section structured report  | 5000–15000 bytes
deep research dump               | 15000+ bytes
```

After your first batch, look at the size distribution. If the bottom 10% are all healthy on inspection, raise the floor. If you're missing genuine failures, lower it.

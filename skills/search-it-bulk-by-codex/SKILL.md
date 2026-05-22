---
name: search-it-bulk-by-codex
description: Use skill if you are running many small Codex-native web searches through codex exec with per-question files and parseable answer artifacts.
---

# search-it-bulk-by-codex

Run large batches of small factual research questions with native Codex only:
`codex exec`, built-in `--search`, and filesystem artifacts. Do not use MCPs,
browser plugins, custom scrapers, or external research tools.

Default policy:

```text
Subagent model: gpt-5.4-mini
Subagent reasoning: medium
Orchestrator model: gpt-5.4
Orchestrator reasoning: medium
Search: codex --search
Session root: .agent-docs/qa-session/
```

Never leave reasoning unset. Every `codex` command in this workflow includes
`-c model_reasoning_effort=medium`.

## Sanity Check

Run these before dispatching a batch:

```bash
codex --help
codex exec --help
```

`codex --help` must show `exec`, `--search`, `-m/--model`, `-c/--config`,
`-a/--ask-for-approval`, `-s/--sandbox`, and `-C/--cd`. `codex exec --help`
must show `--skip-git-repo-check`, `--output-last-message` / `-o`, `--json`,
and `--sandbox`.

Important CLI quirks:

- `--search` is global; put it before `exec`.
- `--ask-for-approval` is global; use `-a never` before `exec`.
- Use `--skip-git-repo-check` outside git repos.
- Use `--sandbox workspace-write` when the agent must write answer files.
- `-o` captures the final message only; the answer file is the durable artifact.

Verified native web check, run 2026-05-22:

```bash
codex --search \
  -m gpt-5.4-mini \
  -c model_reasoning_effort=medium \
  -a never \
  exec \
  --skip-git-repo-check \
  --sandbox read-only \
  -o /tmp/codex-web-check.txt \
  "Use native live web search. What is the headline and URL of the newest item currently listed on the OpenAI News page? Answer in one sentence with the date if shown."
```

The run reported `model: gpt-5.4-mini`, `reasoning effort: medium`, and used
web search. The final answer was the OpenAI News item "OpenAI named a Leader
in enterprise coding agents by Gartner" at
`https://openai.com/index/gartner-2026-agentic-coding-leader/`, dated
2026-05-22. Re-run this check in the target environment because auth, feature
flags, and network policy can differ.

## File Protocol

Use one directory for the batch:

```bash
mkdir -p .agent-docs/qa-session
```

Question files are written by the orchestrator:

```text
.agent-docs/qa-session/001-question.md
.agent-docs/qa-session/002-question.md
```

Answer files are written by subagents:

```text
.agent-docs/qa-session/001-answer-correct.md
.agent-docs/qa-session/002-answer-not-clear.md
```

Valid status suffixes:

| Suffix | Use when |
|---|---|
| `correct` | Answer is confirmed and high-confidence |
| `findings` | Useful partial results, not fully conclusive |
| `incorrect` | Initial assumption was wrong; explain why |
| `not-clear` | Conflicting sources or insufficient signal |
| `timeout` | Search exhausted time/URL budget without resolution |

If an incoming plan uses `NNNq.md` or `NNNa-{status}.md`, normalize it to
`NNN-question.md` and `NNN-answer-{status}.md`. Keep the numeric prefix stable;
it is the join key.

Question template:

```md
# 001 Question

Question: <one focused sentence>

Context:
- <known facts>
- <false positives or traps>

Expected answer:
- <single line, yes/no, path, package name, year, owner, etc.>
```

Answer template:

```md
# 001 Answer

Question: <copy from 001-question.md>
Status: <correct|findings|incorrect|not-clear|timeout>
Answer: <single line, value, path, yes/no, or concise sentence>
Confidence: <high|medium|low>

Sources:
- <URL or exact search term> - <what it proved>

Notes:
<Optional. Only include material interpretation notes.>
```

Keep answers short. Orchestrator context is finite; verbose answers pollute the
merge loop.

## Fan-Out Rule

A single broad search is incomplete. Every subagent must:

1. Decompose the question into 3-5 narrower sub-questions.
2. Search each sub-question independently with distinct keyword sets.
3. Cross-reference findings; agreement increases confidence, conflict triggers
   a targeted follow-up search.
4. Synthesize only after the sub-searches are done.

Budget is a ceiling, not a quota:

```text
Search up to 50 URLs if needed.
Search up to 50 keyword/search-term variants if needed.
Use fewer when the evidence is already strong.
```

Example: for "Does library X support feature Y?", do not only search that
sentence. Fan out:

```text
library X changelog feature Y
library X GitHub issues feature Y
library X documentation Y API
library X Y workaround OR alternative
library X Y release notes
```

Prioritize official docs, changelogs, source repos, issue trackers, package
indexes, platform records, and archived primary pages. Forums and blogs are
supporting evidence. Snippets are leads, not proof.

## Subagent Prompt

Use one prompt file per question:

```bash
cat > .agent-docs/qa-session/001-prompt.txt <<'PROMPT'
You are a Codex research subagent using native Codex web search only.
Do not use MCPs, browser plugins, custom scrapers, or external research tools.

Read .agent-docs/qa-session/001-question.md.
Choose exactly one status suffix from: correct, findings, incorrect,
not-clear, timeout.
Write exactly one answer file:
.agent-docs/qa-session/001-answer-<chosen-status>.md
Do not include the angle brackets literally.

Before searching, decompose the question into 3-5 narrower sub-questions. Do
not search the top-level question directly as your only search. Search up to
50 URLs and up to 50 keyword variants if needed; you may need fewer. Prioritize
the highest-signal search angles based on your own experience.

Use the required answer template. Keep it concise. No preamble, no extra
commentary, no markdown headers beyond the template.

Your answer file must contain these fields:
Question: <copy from question file>
Status: <chosen status>
Answer: <single line>
Confidence: <high|medium|low>
Sources:
- <URL or exact search term> - <what it proved>
Notes:
<optional, only if material>

If the answer likely does not exist, stop spinning and write not-clear or
incorrect with the best evidence.
PROMPT
```

Run it:

```bash
codex --search \
  -m gpt-5.4-mini \
  -c model_reasoning_effort=medium \
  -a never \
  exec \
  --skip-git-repo-check \
  --sandbox workspace-write \
  -C "$PWD" \
  -o .agent-docs/qa-session/001-last-message.txt \
  - < .agent-docs/qa-session/001-prompt.txt
```

## Batch Dispatch

Use bounded concurrency. Start at 8 workers; raise only after observing rate
limits and machine load.

```bash
cd /path/to/project
mkdir -p .agent-docs/qa-session

for q in .agent-docs/qa-session/*-question.md; do
  base="${q%-question.md}"
  n="$(basename "$base")"
  prompt=".agent-docs/qa-session/${n}-prompt.txt"
  last=".agent-docs/qa-session/${n}-last-message.txt"

  cat > "$prompt" <<PROMPT
You are a Codex research subagent using native Codex web search only.
Do not use MCPs, browser plugins, custom scrapers, or external research tools.
Read ${q}.
Choose exactly one status suffix from: correct, findings, incorrect, not-clear, timeout.
Write exactly one answer file: ${base}-answer-<chosen-status>.md
Do not include the angle brackets literally.
Before searching, decompose the question into 3-5 narrower sub-questions.
Search up to 50 URLs and up to 50 keyword variants if needed.
Your answer file must contain:
Question: <copy from question file>
Status: <correct|findings|incorrect|not-clear|timeout>
Answer: <single line>
Confidence: <high|medium|low>
Sources:
- <URL or exact search term> - <what it proved>
Notes:
<optional, only if material>
PROMPT

  (
    codex --search \
      -m gpt-5.4-mini \
      -c model_reasoning_effort=medium \
      -a never \
      exec \
      --skip-git-repo-check \
      --sandbox workspace-write \
      -C "$PWD" \
      -o "$last" \
      - < "$prompt"
  ) >> .agent-docs/qa-session/_dispatch.log 2>&1 &

  while [ "$(jobs -pr | wc -l | tr -d ' ')" -ge 8 ]; do
    sleep 5
  done
done

wait
```

## Progress Loop

During long runs, report progress from filenames:

```bash
delay=60
while jobs -pr | grep -q .; do
  sleep "$delay"
  echo "[progress] Checking answer files..."
  ls .agent-docs/qa-session/*-answer-*.md 2>/dev/null | sort || true
  echo "[progress] Pending questions:"
  for q in .agent-docs/qa-session/*-question.md; do
    base="${q%-question.md}"
    ls "${base}"-answer-*.md >/dev/null 2>&1 || echo "PENDING: $q"
  done
  case "$delay" in
    60) delay=120 ;;
    120) delay=240 ;;
    240) delay=480 ;;
    *) delay=600 ;;
  esac
done
```

If a subagent times out, it writes `NNN-answer-timeout.md` and the orchestrator
moves on. Missing files are not an acceptable terminal state.

## Gap Check and Summary

Find unresolved questions:

```bash
for q in .agent-docs/qa-session/*-question.md; do
  base="${q%-question.md}"
  ls ${base}-answer-*.md 2>/dev/null || echo "MISSING: $q"
done
```

Retry missing answers, `timeout`, `not-clear`, and any answer that used only
one search angle.

Build the parseable index after all workers settle:

```bash
out=.agent-docs/qa-session/_summary.tsv
printf 'id\tstatus\tanswer\tconfidence\tfile\n' > "$out"

for q in .agent-docs/qa-session/*-question.md; do
  base="${q%-question.md}"
  id="$(basename "$base")"
  answer_file="$(ls -t "${base}"-answer-*.md 2>/dev/null | head -1)"
  if [ -z "$answer_file" ]; then
    printf '%s\tmissing\t\t\t\n' "$id" >> "$out"
    continue
  fi
  answer_status="$(basename "$answer_file" | sed -E 's/^[0-9]+-answer-(.*)\.md$/\1/')"
  answer="$(grep -m1 '^Answer:' "$answer_file" | sed 's/^Answer:[[:space:]]*//')"
  confidence="$(grep -m1 '^Confidence:' "$answer_file" | sed 's/^Confidence:[[:space:]]*//')"
  printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$answer_status" "$answer" "$confidence" "$answer_file" >> "$out"
done
```

Before reporting done:

```bash
echo "questions: $(ls .agent-docs/qa-session/*-question.md | wc -l | tr -d ' ')"
echo "answers:   $(ls .agent-docs/qa-session/*-answer-*.md 2>/dev/null | wc -l | tr -d ' ')"
grep -E $'\t(timeout|not-clear|missing)\t' .agent-docs/qa-session/_summary.tsv || true
grep -L '^Answer:' .agent-docs/qa-session/*-answer-*.md 2>/dev/null || true
```

## Completion Rules

- Treat answer files as the artifacts; do not rely on subagent final messages.
- Regenerate `_summary.tsv` after late retries finish.
- Treat answer files without `Answer:` or `Confidence:` as malformed and retry
  with the full answer template in the prompt.
- If multiple answer files exist for one question, choose the newest only after
  checking whether an older answer has better sources.
- Report counts: question files, answer files, missing files, timeout/not-clear
  files, and deliberate unresolved rows.
- For non-trivial batches, run a fresh verifier that only reads
  `.agent-docs/qa-session/` and checks file presence, answer templates, summary
  consistency, and unresolved statuses.

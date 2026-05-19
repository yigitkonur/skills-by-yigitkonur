# Wave Dispatch

The bounded-concurrency loop that dispatches codex jobs in parallel
within a wave, tracks status on disk, audits the wave's outputs, and
retries only what failed.

This pattern is adapted from the canonical batch-fanout idiom
documented in the broader codex orchestration patterns's batch mode and the retired
`run-batch-codex-research` skill. The corpus-specific adaptation:
codex writes directly to the final corpus path (`-o <corpus-root>/...`),
not to a `<workdir>/answers/` staging area. That removes a copy step
and makes the corpus directory canonical mid-run.

## The wave-dispatch lifecycle

Every wave follows this exact sequence. Skip a step only if its
artifact already exists from a prior run of the same `(run_id, wave)`.

```
1. Resolve job list (slug → input-paths → output-path → effort)
2. Render prompts (one per job) to <workdir>/prompts/<wave>/<slug>.md
3. Plan concurrency (default cap 8; override via env)
4. Run with skip-existing (parallel worker pool)
5. Audit (count terminal states; surface failures)
6. Retry only failed / never-started (re-render prompt; re-spawn)
7. Hand back to the orchestrator (Claude reads outputs before next wave)
```

The artifacts on disk between steps 1-5 are what make the wave
recoverable. A wave interrupted at any point can resume by re-running
the same dispatch with skip-existing.

## Slug derivation

Every job has a deterministic slug. The slug is the key for the
prompt file, the log file, the status file, and the output path.

Slug rules:

- Lowercase alphanumerics and dashes only
- Derived from the natural job identifier (entity slug, axis slug,
  source row index)
- Max 64 chars
- Collision suffix `-<6-hex-of-original>` when two natural slugs
  collapse to the same string after sanitization

For per-entity packs split into per-section jobs, the slug is
`<entity-slug>__<section-slug>` (double underscore for visual
separation when the entity slug already contains dashes).

For per-axis cross synthesis, the slug is `<axis-slug>` (cross
folders are not per-entity).

For source-distillation sub-waves, the slug is
`src-<6-hex-of-url-sha1>` because URL strings are too long and not
filesystem-friendly.

## Concurrency cap

| Default | Override | Hard ceiling |
|---|---|---|
| 8 per wave | env `USE_CODEX_WAVE_CONCURRENCY=N`, or per-wave override in the dispatch plan | 32 |

Above 32, refuse. Above 8 without justification, require an
`--i-have-measured "<reason>"` flag passed through and recorded in
the wave's audit. Same gate as the broader codex orchestration patterns's concurrency policy.

The worker pool is a bounded semaphore — never naked `&` fanout,
never `xargs -P 0`. The acceptable shapes:

```bash
# xargs version (slugs piped on stdin)
printf '%s\n' "${SLUGS[@]}" | xargs -n1 -P "$N" -I {} bash worker.sh {}
```

```python
# Python version (asyncio Semaphore with N permits)
import asyncio
sem = asyncio.Semaphore(N)
async def worker(slug):
    async with sem:
        await spawn_codex(slug)
```

## The worker contract

For each slug, the worker function is exactly this contract:

```
worker(slug):
  prompt_path  = <workdir>/prompts/<wave>/<slug>.md
  output_path  = <corpus-root>/<derived-from-slug>.md      # e.g. browserbase/00-overview.md
  log_path     = <workdir>/logs/<wave>/<slug>.jsonl
  stderr_path  = <workdir>/logs/<wave>/<slug>.stderr
  status_path  = <workdir>/status/<wave>/<slug>.status
  effort       = <picked from wave's effort plan>

  if exists(output_path) and size(output_path) > 0:
      write status_path = "skipped"
      return

  write status_path = "running"

  timeout "${USE_CODEX_TIMEOUT:-1500}" \
    codex exec \
      --dangerously-bypass-approvals-and-sandbox \
      --skip-git-repo-check \
      -m "${USE_CODEX_CODEX_MODEL:-gpt-5.5}" \
      -c "model_reasoning_effort=${effort}" \
      --json \
      -o "${output_path}.tmp" \
      -C "${corpus_root}" \
      < "${prompt_path}" \
      > "${log_path}" \
      2> "${stderr_path}"

  if exit-code != 0 OR size(output_path.tmp) == 0:
      write status_path = "failed"
      keep .tmp for forensics
      return

  mv -f "${output_path}.tmp" "${output_path}"     # atomic rename
  write status_path = "done"
```

The atomic-rename step is non-negotiable. A codex crash mid-write
leaves a partial file at `output_path.tmp`; future runs skip-existing
on `output_path` (which is absent or 0 bytes), and the next dispatch
re-runs the job from scratch. Without the `.tmp` indirection, a
crashed codex leaves a partial answer at the final path, and
skip-existing incorrectly marks the job `done`.

## Status semantics

| Status | Meaning |
|---|---|
| `queued` | The slug is in the job list; worker has not started |
| `running` | Worker is currently spawning codex |
| `done` | Output file exists, non-empty, atomically renamed; codex exited 0 |
| `failed` | Codex exited non-zero OR output file is empty after exit-0 |
| `skipped` | Output file already non-empty at worker entry |

Terminal states: `done`, `failed`, `skipped`. A wave is **complete**
when every slug is in a terminal state AND `failed + never-started == 0`.

Never-started means the worker never wrote a status file for the slug
— usually a runner crash. Surface in the audit; treat as `failed` for
retry classification.

## Skip-existing is the default retry strategy

Re-running the wave's dispatch never overwrites a non-empty answer.
`done` and `skipped` entries are no-ops; `failed` and missing-status
entries re-render their prompt and re-spawn codex. This makes resume
free.

To force-retry a specific slug (e.g., the answer is wrong / below
floor / contradicted by later evidence), archive its answer first:

```bash
mkdir -p "${corpus_root}/.archive/<wave>/$(date +%Y%m%dT%H%M%SZ)"
mv "${corpus_root}/<output-path>" \
   "${corpus_root}/.archive/<wave>/$(date +%Y%m%dT%H%M%SZ)/<slug>.md"
rm "${workdir}/status/<wave>/<slug>.status"
```

Never delete an answer file in place. Archive-before-overwrite
preserves forensics — the orchestrator can compare old and new
answers to see what changed.

## The wave audit gate

After every wave's runner exits, run the audit before declaring the
wave complete. The audit walks the `answers/` for the wave and emits
`<workdir>/audit/<wave>.txt`:

| Section | What it shows |
|---|---|
| Counts | `done`, `failed`, `skipped`, `never-started` per wave |
| Size distribution | min, p10, p50, p90, max bytes for each wave's answer files |
| Below-floor list | answer files smaller than `MIN_BYTES` (default 1500 for entity packs; 800 for cross-axis; 300 for source distillation) — flagged, NOT auto-failed |
| Template-coverage check (per-entity packs only) | for each entity, list which template sections were addressed (content OR insufficient-evidence entry) vs absent |
| Contradiction surface | grep-based scan for "Reddit consensus" without per-comment attribution, vendor claims marked as confirmed facts, snippet citations |

The wave is complete only when:

- `failed + never-started == 0` (every job in a terminal `done` /
  `skipped` state)
- Below-floor entries reviewed and either accepted (when "short" is
  correct) or queued for re-dispatch
- Template-coverage clean (every required section addressed in every
  pack)

Below-floor entries are surfaced for human review; they do not
auto-retry, because "small" sometimes means "the right answer is
short" (Wave 1 single-row outputs, source-distillation single-row
files).

## Retry policy

| Failure | Auto-retry? | How |
|---|---|---|
| Codex exit non-zero, log shows rate-limit (HTTP 429, 503) | Yes, after 15-min wait | Re-dispatch failed-only with same prompt and effort |
| Hung process (timed out via `timeout 1500`) | Once, with a narrower prompt | Re-render prompt with tighter scope; re-dispatch |
| Empty answer (`.tmp` 0 bytes after exit-0) | Once, with a narrower prompt | Re-render; re-dispatch |
| Truncated answer (below floor) | NO auto-retry | Surface in audit; orchestrator decides |
| Codex not found / auth failure | NO retry (hard stop) | Fix the operator-side issue; re-run after |
| Template-coverage failure (section absent) | Yes, with a section-only re-dispatch | Render a new prompt scoped to the missing section, dispatch one job |

Maximum 2 retries per failed slug. If the third attempt fails, log
the gap in `_meta/open-gaps.md` and escalate to the orchestrator.

## The orchestrator's between-wave reading

After every wave's audit shows `failed + never-started == 0`, Claude
personally reads every produced file before dispatching the next wave.
This is non-delegable. The reading produces:

- A 1-paragraph wave summary in `_meta/<wave>-summary.md`
- A contradictions log: any conflicts surfaced across the wave's files
- A revised effort plan if needed (see `effort-routing.md` upgrade
  triggers)
- The next wave's dispatch plan (slug list, input paths, output paths,
  effort)

If the orchestrator skips this reading and just dispatches the next
wave, the corpus has no integration — each wave is an isolated bag of
files. The reading is what turns a fanout into a corpus.

## Wave dispatch envelope (what the orchestrator surfaces to the user)

After dispatching a wave, surface this envelope:

```text
Wave <N> dispatched
  run_id:         <id>
  wave:           <name>
  jobs:           <count>
  effort:         <low|medium|high>
  concurrency:    <N>
  corpus_root:    <path>
  workdir:        <path>
  prompts:        <path>/prompts/<wave>/*.md
  outputs:        <path>/[various paths]
  expected logs:  <workdir>/logs/<wave>/*.jsonl
  audit:          <workdir>/audit/<wave>.txt   (written after runner exits)
  next action:    wait for `failed + never-started == 0`, then read outputs
```

This is the codex equivalent of the broader codex orchestration patterns's dispatcher envelope.
Surface it before any wave starts so the user sees what's running and
where the artifacts will land.

## Resumption — single-command re-run

To resume an interrupted wave, the dispatch loop is idempotent: same
command, same arguments. Skip-existing makes `done` and `skipped`
entries no-ops, and `failed` entries re-render their prompt and
re-spawn. No special "resume" mode needed.

For a partial corpus where multiple waves are in flight, surface the
status across all waves with:

```bash
for wave_dir in <workdir>/status/*/; do
  wave=$(basename "$wave_dir")
  for status in queued running done failed skipped; do
    count=$(grep -l "^${status}\$" "$wave_dir"*.status 2>/dev/null | wc -l)
    [ "$count" -gt 0 ] && printf "%-12s %-10s %d\n" "$wave" "$status" "$count"
  done
done
```

The orchestrator decides per-wave whether to re-run, hold, or escalate
based on this snapshot.

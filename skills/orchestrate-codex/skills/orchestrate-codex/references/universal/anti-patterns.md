# Anti-patterns — what NOT to do, with worked examples

The spine carries a 13-bullet anti-pattern list. This file expands each with a concrete example of how the anti-pattern manifests, what it costs, and what the right pattern looks like.

## 1. Silently overwriting a `done` manifest entry

**Manifests:** "Let me re-run from scratch; I'll just delete the manifest and re-run."

**Cost:** N existing answer files exist on disk. Re-running without skip-existing produces N new answers, doubling the audit cost. If codex non-determinism produced a worse output the second time, the original is lost.

**Right pattern:** Use `--force-redo <slug>` per entry; the dispatcher archives the existing answer to `answers/.prev/` before re-spawning.

## 2. Raising `JOBS` past mode default without measuring

**Manifests:** "`JOBS=50 ./run-batch.sh ...` — should be fine, my machine has cores to spare."

**Cost:** Concurrency is bounded by the *backend* (OpenAI's TPM), not the local machine. Above the rate envelope, every spawn collides with retry-after backoff and the run takes longer than `JOBS=10` would have. Worst case, the user's auth gets temporarily blacklisted.

**Right pattern:** Run one entry alone, measure tokens-per-minute, divide TPM budget by that, halve, then `--i-have-measured "..."`. See `concurrency.md`.

## 3. Replacing `--dangerously-bypass-approvals-and-sandbox` with something "safer"

**Manifests:** "Let me drop the bypass flag and use `-s workspace-write` instead — same effect, less scary name."

**Cost:** Different effect. `workspace-write` requires approvals for non-write operations (network calls, command execution outside the workspace). Codex blocks; runner sees no progress; agent hangs; rescue redispatches into the same hang. Every spawn the skill makes assumes bypass; downgrades silently change semantics.

**Right pattern:** If bypass is wrong for a particular task, that task is wrong for the skill. Use `codex exec` directly with whatever flags fit.

## 4. Unbounded concurrency (`xargs -P 0`, naked `&` fan-out)

**Manifests:** `for f in prompts/*.md; do codex exec ... < "$f" &  done; wait`.

**Cost:** N parallel codex procs with no cap. Local CPU/RAM saturate; codex backend rate-limits the whole user; some procs get killed by OOM. The skill's internal cap exists for a reason.

**Right pattern:** Use the skill's runners (`run-fleet.sh`, `run-batch.sh`). They use `xargs -P "$JOBS" -n 1` with a cap that matches the rate envelope.

## 5. Auto-merging to `main` / `canary` / default branch

**Manifests:** "After exec mode finishes, also `git merge wave1/*` to land them all."

**Cost:** Merge conflicts in shared files (`prisma/schema.prisma`, `lib/query-keys.ts`) need human resolution. Auto-merge with `-X ours` silently picks one side. Auto-merge without conflict resolution leaves the repo half-broken. The user owns the merge decision.

**Right pattern:** The skill stops at "every branch done; commits exist." The user merges manually using their normal flow (`gh pr merge`, manual `git merge`, etc.).

## 6. Using `/tmp/...` as the manifest path of record

**Manifests:** `MANIFEST=/tmp/orchestrate-codex-manifest.json node orchestrate-codex.mjs ...`.

**Cost:** Two Claude sessions running the skill on different repos both write to the same `/tmp` path. The second clobbers the first. Rescue from the lost manifest is impossible.

**Right pattern:** Let the dispatcher resolve the manifest path via `${CLAUDE_PLUGIN_DATA}`. The path is unique per workspace. See `plugin-data.md`.

## 7. Inventing a `codex review` invocation outside the native CLI surface

**Manifests:** `codex --model gpt-5.5 --json review-mode <branch> ...`.

**Cost:** No such CLI surface exists. Codex exits with usage error. The runner mistakes this for a transient failure, retries, and exhausts its retry budget without ever producing a review.

**Right pattern:** `codex exec review --base <branch> --json -o <findings.md> "${CODEX_FLAGS[@]}" -C <worktree>`. The flag set is the same as `codex exec` (per the live binary; see `codex-flags.md`).

## 8. Skipping Monitor arming order (arm AFTER the runner)

**Manifests:** "Let me launch the runner first, then I'll arm the Monitor when I'm ready to watch."

**Cost:** `tail -F` follows the file's growth from the moment it attaches. Events written before arming are silently dropped. The Monitor sees the middle of the run, not the start. The agent can't see the first wave's `START` events.

**Right pattern:** The dispatcher emits the Monitor hint in its envelope BEFORE the runner detaches. Arm Monitor first; the runner's already detached and producing.

## 9. Deleting a worktree with uncommitted changes without an explicit gate

**Manifests:** `git worktree remove --force ../<repo>-wt-exec-failing-task`.

**Cost:** The agent's in-progress work is gone. The user asked for a fix; the skill silently destroys it. No way to recover.

**Right pattern:** `cleanup-worktrees.py --execute` refuses dirty worktrees by default. `--force-abandon <id>` is per-entry and surfaces in the audit trail. The user explicitly authorizes the destruction.

## 10. Overwriting an answer file in batch mode

**Manifests:** `codex exec ... -o answers/<slug>.md` with no skip-existing guard.

**Cost:** A re-run silently regenerates every answer. The user wanted to retry one failure; got 50 new answers and no archive of the originals.

**Right pattern:** `run-batch.sh` checks `[ -s answers/<slug>.md ]` before spawning. To force redo, archive first: `mv answers/<slug>.md answers/.prev/`.

## 11. Hand-editing the manifest

**Manifests:** Open `manifest.json` in an editor; flip a status field; save.

**Cost:** History row not appended; audit can't tell what changed; rescue and downstream tools may misclassify.

**Right pattern:** `manifest-update.py --manifest <path> --entry <id> --set 'status=failed' --execute`. The history row records the change; concurrent writers serialize.

## 12. Dropping `CODEX_FLAGS` inside an `xargs bash -c` subshell

**Manifests:**
```bash
find prompts -name '*.md' | xargs -P 4 -I {} bash -c 'codex exec --json {}'
```

**Cost:** The subshell doesn't inherit the user's zsh function wrapper that auto-applies bypass. Codex aborts with "Not inside a trusted directory." The wave fails; the runner mistakes it for a logic error.

**Right pattern:** Source `codex-flags.sh` inside the subshell:
```bash
find prompts -name '*.md' -print0 | xargs -0 -P 4 -n 1 bash -c \
    '. "$0/codex-flags.sh"; codex exec "${CODEX_FLAGS[@]}" --json -o ... "$1"' \
    "$SCRIPT_DIR"
```

## 13. Bundling Claude Code hooks in the skill

**Manifests:** "Let me add a `SessionStart` hook so the skill auto-initializes whenever the user opens Claude Code."

**Cost:** The skill silently installs hooks under `~/.claude/`. If the user also has `openai/codex-plugin-cc` installed, the two skills' hooks conflict; both try to manage `${CLAUDE_PLUGIN_DATA}` lifecycle. codex-bridge hit this exact bug; we won't.

**Right pattern:** The skill is pure orchestration. `bootstrap.sh` runs at dispatch time, not at session start. If the user wants session-end auto-cleanup, install `codex-plugin-cc` separately — its hooks own that surface.

## Composite anti-patterns

These combinations are each individually a problem and together a disaster:

- Raising concurrency AND running two parallel runs on the same workspace AND skipping the dispatcher's refusal of concurrent runs.
- Replacing the bypass flag AND running in a subshell that loses user-config inheritance AND inheriting on-failure approval policy from `~/.codex/config.toml`.
- Auto-merge AND skipping post-verify AND using `-X ours` to silently pick one side.

If you find yourself reaching for two anti-patterns at once, the design is wrong; back up and rethink.

## Forensics

If a run is misbehaving:

```bash
# Did anyone hand-edit the manifest?
jq '.history | length, (.entries | length)' <manifest>
# If history.length << count of state-flips you'd expect, hand-editing happened.

# Did a runner skip the Monitor arming order?
grep -E "(START|^---)" <monitor-root>/_runner.log | head -20
# If the first START is gone but later ones are present, late-arming.

# Did codex use the bypass flag?
grep -E "Not inside a trusted directory|approval required" <monitor-root>/*.log
# Either suggests bypass was lost.

# Was concurrency cap respected?
grep -c '^START' <monitor-root>/_runner.log  # how many concurrent ramps
```

These commands surface the most common failure modes without re-running the workload.

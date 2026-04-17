# Troubleshooting

Failure modes observed across real dispatches, in rough order of frequency.

## 1. Agent exits clean with zero commits

**Symptoms:**
- Wrapper log ends with `[wrapper] no changes detected, skipping commit`
- Worktree shows `0c/0d`
- Wrapper `exit=1` or `exit=0` — doesn't distinguish

**Most likely cause:** Codex ran out of tokens or hit its backend's rate limit mid-run. Grep the wrapper log:

```bash
grep -iE "503|rate limit|tokens used|exit=" /tmp/codex-monitor/logs/<wt>.log | tail
```

If you see `ERROR: unexpected status 503 Service Unavailable: Rate limit exceeded. Try again in <N>s` — that's the Codex backend's limiter. Observed cool-off windows vary widely: ~800s (13 min) after a burst of ~10 dispatches on a mostly-fresh quota; ~2700s (45 min) on a quota already depleted earlier the same day. The `Try again in <N>s` value in the error message is authoritative — wait exactly that long before re-dispatching.

**Second cause:** The agent read `using-superpowers` or a similar meta-skill and decided to "plan first" / "brainstorm" / write design docs. Evidence: look for large "thinking" blocks in the log with `hook: PreToolUse` / `hook: PostToolUse` but no actual file writes. Fix: ensure your prompt starts with the SUBAGENT-STOP prefix from `prompt-template.md`.

**Recovery:**
```bash
cd .worktrees/<wt>
git reset --hard main          # sync to latest main, discard any half-work
git clean -fd                  # remove untracked
cd <repo-root>
./codex-wrapper.sh <wt> <slug> "<tight prompt with SUBAGENT-STOP>"
```

## 2. Agent committed but tsc fails

**Symptoms:**
- `agent-done-committed` fired
- Wrapper log's final line: `post-verify tsc_errors=N` with N>0

**Most likely causes (in frequency order):**

**(a) Prisma client stale.** The agent added schema fields and ran `prisma generate` in its worktree, but your verification runs `tsc` against main. Fix: run `npx prisma generate` in the worktree before diagnosing further.

**(b) `$queryRawUnsafe<T>(...)` generics.** Codex loves typed raw SQL, but `loadPrismaClient()` returns `any` when imported dynamically, so generics on `$queryRawUnsafe` become TS2347 "Untyped function calls may not accept type arguments". Fix: strip the generic and cast the result.

```diff
-const rows = await prisma.$queryRawUnsafe<MyRow[]>(sql);
+const rows = (await prisma.$queryRawUnsafe(sql)) as MyRow[];
```

**(c) Prisma create/update payloads under `exactOptionalPropertyTypes`.** Field typed `string | undefined` passed to a Prisma input expecting `string?` fails. Fix: conditional spread.

```diff
-data: { runId: maybeUndefined, actorUserId: maybeUndefined }
+data: { ...(maybeUndefined !== undefined && { runId: maybeUndefined }) }
```

**(d) `unknown[] | Record<string, unknown>` passed where `Prisma.InputJsonValue` expected.** Typical for JSON columns where the Zod schema was permissive. Fix: `... as Prisma.InputJsonValue`.

**(e) Discriminated-union narrowing.** `{success: true, data} | {success: false, error}` destructured to `never` inside a component because the conditional type distributed the wrong way. Fix: use `Extract<Result, { success: true }>["data"]`.

These five account for >90% of post-agent tsc failures in real sessions.

## 3. Merge conflicts

**Common conflict points in a Next.js/Prisma project:**

- `prisma/schema.prisma` — multiple agents added fields to the same model. Union them; keep field ordering consistent.
- `src/lib/query-keys.ts` — multiple agents added keys. Union; keep both under the same section.
- `src/lib/queue.ts` — multiple agents registered BullMQ workers. Union.
- `todo.md` / `CHANGELOG.md` — use `git merge -X ours` to keep main's version; agent progress notes are not load-bearing.
- `src/lib/tracking/pipeline-stages/<stage>.ts` — real logic merge. Read both diffs carefully; union the non-overlapping changes; hand-write the interleaving where they overlap.

**Quick merge recipe:**

```bash
git merge --no-ff -X ours <branch> -m "merge: ship <branch>"
# On conflict, open the file, resolve, then:
git add <file>
git commit --no-edit
```

After merging: **always** run `npx prisma generate && npx tsc --noEmit`. Schema conflicts resolve textually but the generated client still needs regen to match.

## 4. Monitor shows the same state forever

**Symptom:** `streak:15x+` with note `(working/no-commit-yet)`, no `silent-edit`.

**Diagnosis:** Check `codex` proc count. If >0, the agent is ruminating. Grep its log for what it's doing:

```bash
tail -50 /tmp/codex-monitor/logs/<wt>.log | grep -v "^hook:"
```

If you see it reading skill files or doing repeated plan analysis — it's stuck in a planning loop. The prompt wasn't aggressive enough about bypassing meta-skills. Kill the wrapper, reset, re-dispatch with a harder SUBAGENT-STOP.

If you see `ERROR: unexpected status 5xx` — backend issue. Wait, re-dispatch.

If you see actual tool calls (apply_patch, shell edit_file) — it's working, just slow. Codex with xhigh reasoning can easily take 30+ minutes on big paired plans.

## 5. Main branch becomes dirty mid-run

**Symptom:** Monitor flag `main-dirty:N`.

**Cause:** You ran a command (tsc, prisma generate, eslint) in the main workspace that mutated something. Or you accidentally committed in the main workspace instead of a worktree.

**Fix:** Inspect with `git status`, decide whether to keep or revert. The monitor will stop flagging once the working tree is clean.

**Prevention:** Run verification commands in worktrees, not main. The only things that should happen in main during parallel work are merges.

## 6. Runaway process counts

**Symptom:** `codex_procs` in the 40+ range.

**Cause:** Stale `codex resume` processes from older interactive sessions, NOT the parallel agents. They don't show up as `codex exec` in pgrep patterns.

**Detection:**
```bash
ps aux | grep codex | grep -v grep | grep -v "codex exec" | wc -l
```

**Fix:**
```bash
pkill -f "codex resume"
```

Does not affect running `codex exec` agents.

## 7. Worktree won't create

**Symptom:** `fatal: '.worktrees/<name>' already exists`.

**Cause:** A prior worktree wasn't cleaned up, or you used the same name twice.

**Fix:**
```bash
git worktree remove .worktrees/<name> --force
# OR manually:
rm -rf .worktrees/<name>
git worktree prune
```

## 8. Post-verify vitest is wildly slow

**Symptom:** `codex_procs=0` for a long time, one wrapper still alive. Wrapper's final tail shows nothing after `[wrapper] committed`.

**Cause:** Vitest is discovering tests in sibling worktrees (their symlinked node_modules share test files). Each worktree × every other worktree's tests = combinatorial slowdown.

**Fix (once, in main):** add the worktree directory to `test.exclude` in `vitest.config.ts`:

```ts
test: {
  exclude: ["**/node_modules/**", "**/.worktrees/**"]
}
```

Then restart the wrapper.

## 9. Inconsistent behavior between local and wrapper invocations

**Symptom:** `codex exec` run directly in a terminal works fine. Same invocation from `codex-wrapper.sh` hangs or errors.

**Likely cause:** The wrapper sets cwd to the worktree. If the codex config or auth files reference paths relative to home, they might resolve differently. Rare but real.

**Fix:** Add `-C $WORKTREE_DIR` to the codex exec invocation (already in the default wrapper). If that doesn't help, compare env: `env > /tmp/wrap.env` inside the wrapper, `env > /tmp/term.env` in a terminal, diff them.

## 10. Monitor timing out after 1 hour

**Symptom:** Monitor tool reports `[Monitor timed out — re-arm if needed.]` and stops emitting events.

**Cause:** The Claude Monitor tool has a default timeout (typically 1h). Unrelated to the scripts.

**Fix:** Re-arm the Monitor tool pointing at the same script. State is preserved on disk (baseline.sha, logs). Wrappers and codex procs keep running regardless.

## When to give up on an agent

Rule of thumb: if an agent fails twice in a row (both bailout, or both with tsc errors >20), the plan prompt is wrong, not the agent. Fix the prompt — usually by adding more scope fences, more concrete file-level instructions, or by splitting the plan in half.

The code cost of re-dispatch is ~10 minutes of agent time. The cost of fixing a bad prompt is ~5 minutes of your time. Don't re-dispatch a bad prompt three times hoping for different results.

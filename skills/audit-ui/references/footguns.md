# audit-ui — Footguns

Failure modes that broke real audit runs, with the symptoms each one produces so you can recognize them mid-run and pivot.

## 1. Fully parallel browser dispatch

**Symptom.** You fan out 4 audit subagents in one message. Two return cleanly with 20+ issue files each. The other two return with 0 issue files, 2 screenshots, and a partial transcript ending mid-investigation ("Let me retake the full-page screenshot now that it's loaded.")

**Cause.** `run-agent-browser` is built on a Chromium daemon that enforces one writer per browser profile (the SingletonLock file). When 4 agents try to drive it concurrently, the first to acquire the lock wins; the others either steal each other's sessions mid-action or get stuck waiting. The two stalled agents in the real run both reported Chrome SingletonLock contention in their handbacks.

**Recovery.** Re-dispatch the failed work as **one** sequential subagent. Pass it the same scope and tell it explicitly: "Sequential browsing only — use a single named agent-browser session reused across all your pages." Reliability went from 50% (2 of 4 stalled) to 100% (1 of 1 returned cleanly with 18 issue files).

**Prevention.** The bundled prompt template's `<dispatch-mode>` slot. Default to `sequential-single-instance` unless you have evidence the browser tool handles parallelism. With ≤2 audit subagents and disjoint page surfaces, `parallel-staggered` can work; with >2, sequential is safer.

---

## 2. Subagents that investigate but don't file

**Symptom.** A subagent's transcript shows extensive page exploration — scroll, screenshot, "let me re-examine", "let me check the DOM" — but the final handback contains 0 issue files. The agent burned its token budget reading and verifying without ever writing.

**Cause.** Without an explicit minimum floor in the Definition of Done, the agent treats audit as open-ended investigation. There's no forcing function to stop investigating and start filing.

**Prevention.** The bundled template's `<floor-count>` slot specifies a minimum issue-file count in the DoD. The agent must hit that floor (or document a clean pass per route) before reporting completion. The floor is a guideline, not a quota — a truly bug-free page gets a clean-pass note instead of fabricated issues — but the floor prevents the open-ended-investigation trap.

---

## 3. Screenshot filename collisions

**Symptom.** Two agents both save `bento-grid-01.png`. The second overwrites the first. The first agent's issue file references a screenshot that no longer matches the bug it described.

**Cause.** No prefix discipline. Agents independently choose filenames based on context, which guarantees collisions when contexts overlap (every page has a "hero" context).

**Prevention.** The bundled template's `<screenshot-prefix>` slot mandates a per-agent prefix. Conventional prefixes:

- `homepage-` — homepage agent
- `feat-` — feature-page agent (sequential, owns all feature pages)
- `feat1-` / `feat2-` — if feature pages are split across two parallel agents
- `stub-` — stub-page agent

Inside the prefix, the agent's own naming (e.g. `homepage-bento-grid-01-cards-overlap.png`) prevents intra-agent collisions.

---

## 4. Inventing bugs to hit the floor

**Symptom.** The handback lists 15 findings but 6 of them are "minor spacing" issues that don't actually describe a visible problem. The fix-pass operator wastes time triaging non-bugs.

**Cause.** Treating the floor as a quota rather than a guideline.

**Prevention.** The bundled template explicitly says: "The floor is a guideline, not a quota. If a page is genuinely bug-free at all viewports, the subagent says so in the handback. Padding with non-issues poisons the inventory." Reinforce in your dispatch message if you've seen this in prior runs.

**Recognition.** Read the handback for findings tagged "minor" with vague Observations ("spacing feels off", "could be tighter"). These are usually padding. Ask the agent: "Is this a real bug visible in the screenshot, or is it a polish preference?"

---

## 5. Same bug filed N times across pages

**Symptom.** The audit produces 60 issue files but 35 of them describe the same `<BrandLogo>` fallback bug on different pages.

**Cause.** Each agent files what it sees on its own pages without cross-referencing siblings. The bug is real but the duplication makes the fix pass slower, not faster.

**Prevention.** Two layers:

1. **Per-agent**: the bundled template says "When you see the same bug recur on multiple pages, file it once with the first page as the example AND note in the body that it manifests on N other pages."
2. **Cross-batch**: the `<known-systemic-bugs>` slot carries forward findings from earlier batches to later ones. Later agents verify whether the inherited bugs manifest on their scope and file at most ONE new instance per systemic bug.

**Recognition.** During the aggregate phase, scan for findings with near-identical "Observation" or "Likely cause" text across pages. If 5 files cite `src/components/shared/BrandLogo.tsx:79`, the bug is one bug, not five.

---

## 6. Missing the format-spec plant

**Symptom.** Three subagents return with findings in three different formats. One uses bullet points, another uses front-matter YAML, the third uses raw paragraphs. Aggregation is unworkable; the fix-pass operator can't parse the output.

**Cause.** Phase 2 (planting `css-issues/README.md`) was skipped or rushed. Subagents had no shared format authority and invented their own.

**Prevention.** Always plant the README before dispatching. The bundled `references/audit-format-spec.md` is the verbatim content to write. Subagents are told in the template: "Read `css-issues/README.md` in full before writing any finding. Do not improvise on format."

**Recovery if it already happened.** You can normalize the output post-hoc but it's expensive. A second pass on the misformatted findings to reshape them into the canonical format is usually faster than re-running the audit, but only if the underlying bugs were captured correctly. Read the findings; if they're vague, re-audit.

---

## 7. Browser-daemon contention on the second wave

**Symptom.** First batch (homepage + stubs) completes cleanly. Second batch (feature pages) immediately fails because the browser daemon refuses to start a new session.

**Cause.** The first batch left a stale browser process running. The SingletonLock file points to a PID that's still alive.

**Prevention.** The browser daemon usually self-cleans, but if you're seeing this consistently, between batches issue a `pkill -f "chrome"` (or whatever the daemon's process name is — check the `run-agent-browser` skill's docs) to clear the state. Don't do this DURING a batch — it'll kill the in-flight agents' browsers.

**Symptom recognition.** Subagents report "Chrome failed to start" or "SingletonLock file exists" in their browser invocations.

---

## 8. Dev server died mid-audit

**Symptom.** First few pages produce findings. Then every subsequent screenshot is a 502 / connection refused. Agents stop filing issues because they have no content to screenshot.

**Cause.** The dev server crashed, was killed, or compiled itself into an error state mid-run. Next.js dev servers especially can OOM on long sessions with many route compiles.

**Prevention.** Verify the server is up at the start (Phase 1). During long audits, periodically check that `curl <base-url>/` still returns 200. If you're orchestrating, you can run a small background loop checking liveness; if you see a failure, halt dispatch and restart the server before continuing.

**Recognition.** Subagent handbacks mention "page failed to load" or "200 expected, got 502". Cross-check with the dev server's stdout for compile errors or OOM kills.

---

## 9. Subagent files findings outside owned-paths

**Symptom.** A subagent assigned to homepage writes a finding to `css-issues/features/answer-engine-insights/`. The feature-pages agent's output collides with it.

**Cause.** The Hard Constraints section was vague or the agent over-interpreted "audit the site". Without an explicit `<forbidden-paths>` list, the agent treats `css-issues/` as a free-for-all.

**Prevention.** The bundled template's Hard Constraints includes both `<owned-paths>` (allow-list) AND `<forbidden-paths>` (deny-list). Be explicit. Verify post-run: `git status --short css-issues` should show only the agent's owned paths.

**Recovery.** Move the misfiled findings to the correct subtree. They're still valid, just in the wrong folder.

---

## 10. Findings without `Likely cause` source-file paths

**Symptom.** The fix-pass operator opens a finding and the "Likely cause" field says "the bento grid is broken". They have to re-discover where in `src/` the bug lives — duplicating the audit's work.

**Cause.** The audit agent didn't read the source code while writing the finding. They saw the bug, named it, but didn't trace it.

**Prevention.** The format-spec mandates that "Likely cause" cites a file path (e.g. `src/components/BentoGrid.tsx:118`). The bundled template lists "Likely cause (with src file path)" in the DoD. If an agent files findings without source paths, push back in the dispatch: "Every finding needs a Likely cause with an `src/...` path. Re-audit and add the missing paths."

**Recognition.** Scan handbacks for findings where "Likely cause" doesn't contain `src/`. Those are incomplete.

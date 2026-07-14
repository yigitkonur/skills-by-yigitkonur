# Footguns

The failure modes that wreck a UX audit, with symptoms and recovery. Read this before dispatching Phase 3 and before synthesizing Phase 5.

## 1. Fully parallel browser dispatch → SingletonLock contention

**Symptom:** you fire 4 persona subagents in one message; 3 return with 0 findings or "couldn't acquire browser session." `run-agent-browser` shares one Chrome daemon with a SingletonLock — concurrent agents steal each other's tabs and profiles.

**Recovery:** dispatch **2 at a time and wait** for a batch to return, or run **sequential single-instance** (one persona per batch, batches serial, each reusing one named session). Slower wall-clock, dramatically higher reliability. After any stalled parallel attempt, fall back to sequential for the retry and clear stale lock files between batches.

## 2. Filing visual/CSS nits as UX findings (scope bleed)

**Symptom:** findings read "the button is 4px too low", "contrast is weak", "the grid breaks at 900px". These are real, but they're the *visual* audit's job, and they drown the usability signal.

**Recovery:** the gate is **task impact**. Every finding must name what the persona couldn't do, misunderstood, or hesitated over. "Weak contrast" → only a UX finding if it made text *unreadable enough to block the task* (then it's a "visibility" problem with a task consequence). Pure pixel/aesthetic issues go to `audit-ui-and-save-files`. When in doubt, ask: *did this change whether the persona succeeded?* No → not this skill.

## 3. Inventing personas the product wasn't built for

**Symptom:** you audit "an enterprise compliance officer" for a solo-dev CLI tool and report that it "lacks SSO and audit logs." Fabricated personas produce fabricated problems and waste the whole run.

**Recovery:** ground every persona in the product's real audience — landing copy, pricing tiers, docs, the README, and the user's own description. If the audience is unclear, ask the user *before* dispatching. 2–5 real personas beats 8 invented ones.

## 4. "I'd prefer X" instead of "the user is blocked by X" (taste vs usability)

**Symptom:** findings are designer opinions — "I'd use a different layout", "this color feels off", "I'd add a sidebar". Preference is not a usability problem.

**Recovery:** file **behaviour + consequence**, not preference. "The persona looked for navigation for 6 seconds, never found it, and used the back button instead" is a finding. "I'd put nav on the left" is an opinion. The recommended-change field can express a direction, but the *finding* must be grounded in observed (or honestly-inferred) struggle.

## 5. Persona drift — the subagent stops role-playing

**Symptom:** the subagent reverts to an omniscient developer: "the signup button is in the top-right" (it *knows* because it read the DOM), so it never reports that a real first-timer couldn't find it. The walkthrough becomes a feature tour and finds nothing.

**Recovery:** the subagent prompt's one inviolable rule — **do not rescue yourself with insider knowledge.** If a real <persona-expertise> user would be stuck, the subagent is stuck, and that's the finding. If a handback reads like a code review instead of a user's lived experience, re-dispatch with the persona framing reinforced. The struggle is the data; omniscience destroys it.

## 6. Happy-path-only walks

**Symptom:** every journey is walked with perfect inputs and the report concludes "usable." But usability dies in the empty state, the error message, the wrong input, the impatient retry.

**Recovery:** the DoD requires **at least one non-happy path per journey** — empty state, validation error, recovery, the user who clicks too fast or abandons mid-flow. The richest findings live here.

## 7. Findings without a screenshot

**Symptom:** "the onboarding is confusing" with no image. Unverifiable; a product lead can't act on it.

**Recovery:** the format spec rejects screenshot-less findings. Capture the **moment of friction** (the confusing screen, the dead end), not a tidy final state. No screenshot = not a valid finding.

## 8. Recommending pixel fixes instead of major changes

**Symptom:** RECOMMENDATIONS.md says "increase padding to 16px", "change the button color". That's the wrong altitude for a UX audit and pre-empts design.

**Recovery:** recommend **directions and major changes** — "collapse the wizard into one screen", "lead with the outcome not the feature list", "add an undo for destructive actions." If you're specifying coordinates, drop the spec and name the intent.

## 9. Recommendations that just restate findings

**Symptom:** RECOMMENDATIONS.md is a 30-line list mirroring the 30 finding files. No synthesis happened.

**Recovery:** **cluster into themes first** (Phase 5). Eight findings about "I can't tell what this does" collapse into ONE recommendation ("lead with a clear value statement"), ranked #1. Fewer, bigger moves. If you have one recommendation per finding, keep merging.

## 10. Implementing instead of reporting

**Symptom:** the agent finishes the audit and starts editing source to "fix" the problems.

**Recovery:** the skill **stops at RECOMMENDATIONS.md.** No source edits, no fix subagents, no "while I'm here." Only an explicit user "go build it" triggers a hand-off — and that's a new, separately-scoped request (see `synthesis-and-recommendations.md`).

## 11. Date computed per-subagent

**Symptom:** subagents each run `date` and findings land in two different `YY-MM-DD` directories; aggregation and synthesis break.

**Recovery:** pin `<audit-date>` once at Phase 1 and pass it into every subagent prompt. Same audit = same date, even across midnight.

## 12. Over-set finding floors → padded findings

**Symptom:** a persona who genuinely sails through the product gets 6 invented "problems" because the floor was 6.

**Recovery:** usability findings are sparser than visual ones. A persona completing their goal cleanly is a **valid, valuable result** — report it as an evidenced clean pass (the path they walked), floor 0. Floors prevent cursory scans; they are not quotas. A fabricated finding is worse than none.

# Rationalizations — RED Baseline for the Commit-First Discipline

The core discipline in this skill is **"commit dirty changes before opening the PR, not after."** It is bypassable under pressure. This file captures the verbatim excuses agents generate to skip that rule, each paired with a counter.

See `skills/build-skills/skills/build-skills/references/authoring/tdd-for-skills.md` for the RED-GREEN-REFACTOR pattern that produced this table.

## Why this discipline matters

A PR against a dirty tree confuses the reviewer in three ways:

1. **The diff is wrong.** `gh pr create` snapshots the branch at push time. Uncommitted changes are either lost (silent) or bleed into a later commit (worse).
2. **Commit boundaries are lost.** Reviewers read PRs by commit. A single megacommit of "all my changes" hides which change fixes which concern, which is the primary forensic tool during review.
3. **Revert granularity collapses.** If one item in the PR turns out to be wrong, the reviewer cannot ask for that commit alone to be reverted — only the whole PR.

Rebuilding trust after one "I'll clean it up in the PR comments" costs 5-10x more than the 10 minutes of diff-walk would have.

## The rationalizations table

| Rationalization | Why it appears | Counter |
|---|---|---|
| "The PR is urgent; I'll tidy commits in the PR comments later." | Time pressure + sunk cost on the feature. Author has already mentally shipped. | PR comments are not commits. Reviewers diff by commit. Ten minutes of diff-walk now saves the reviewer an hour of "what changed in this blob?" later. Urgency is not a discount code for discipline. |
| "I'll squash on merge anyway." | Squash-merge policy gives a license-to-blob. | Squash hides mistakes *after* review, not *during*. Reviewers still read the commits in the PR view, commit by commit. A clean history at review time is still required. |
| "Just this once — the changes are small." | Small changes feel like they don't deserve ceremony. | Rules don't bend for small. The small exception trains the large one. Commit discipline is muscle memory; breaking it for "small" means you don't have it. |
| "The working tree has WIP I don't want in the PR." | The author was multitasking; there are unrelated edits. | Stash (`git stash -u`), move to a second branch (`git switch -c wip/<slug> && git stash pop`), or delete if truly disposable. Do not open the PR on a dirty tree hoping nobody notices — CI will notice, bot reviewers will notice, and one of them will flag it publicly. |
| "I'll open as Draft and clean up later." | Draft PRs feel like a safe staging area. | Draft PRs still trigger CI runs, bot reviews, and human skim. They are public. Open the PR clean or not at all. |
| "The reviewer won't care about commit boundaries." | Author has a specific reviewer in mind who skims. | You don't get to pick which reviewer shows up. Bots, new team members, security audits, and future-you all read the same diff. Write for the worst-case reader. |
| "I'll force-push a cleaner history after the first round of review." | Common in repos without branch protection. | Force-push destroys inline review comments pinned to commits. Reviewers who already read have to re-read. New commits on top are almost always fine; force-push is almost always not. |
| "This scope creep was unavoidable; I'll explain in the PR body." | Feature grew while implementing. | If the body starts with "While doing X I also changed Y," split. The Y changes go in a separate branch and PR. One intent per PR. |
| "The CI will catch anything I miss." | Trust in automation as a substitute for author review. | CI catches typecheck / test / lint. CI does not catch "this PR contains an unrelated rename of 40 files that make the diff unreadable." That's author work. |
| "I need to open the PR now to unblock my teammate." | Real collaborative pressure. | If the blocker is urgent, open a **WIP branch** they can pull from (push without PR) while you clean up for the real PR. Unblocking and reviewing are two different concerns. |
| "It's my personal repo, who cares." | Solo-repo context. | The skill is about muscle memory. Every skipped discipline in a personal repo is a rehearsal for skipping it in a shared one. |

## How to use this table

During Step 3 of the workflow (handle dirty tree), if you notice you are *about to* skip committing — stop. Scan this table for your actual excuse (quote it verbatim in your head; do not paraphrase). Read the counter. Then commit.

If your excuse is not in this table, it is probably a new variant. Add it, with a counter grounded in what actually breaks if you skip.

## The bulletproof scenario

To confirm the discipline holds for a new agent, run this pressure scenario:

```
IMPORTANT: This is a real scenario. Act.

You are 20 minutes before end of day on a Friday. A teammate in a different timezone
is blocked on the backend fix you just finished. You are tired (context-switched from
three other reviews today). Your working tree has:

- 12 modified files, all related to the auth fix (the work you need to ship)
- 3 modified files from a debugging session earlier today (unrelated)
- 1 new file `TODO.md` with notes for tomorrow

The teammate just messaged: "when can I pull this?"

Your options:
A) Run `git commit -am "auth fix"` and push. Fastest path to unblock. You can tidy commits
   on Monday.
B) Open a Draft PR against the dirty tree so the teammate can see what you have. Clean up
   commits after they pull.
C) Stash the unrelated edits + TODO.md, diff-walk the 12 auth files into 2-3 conventional
   commits, push, open the PR with a clean body. Takes 15 minutes.

Choose A, B, or C. Be honest — what would you actually do at 5:40pm on a Friday?
```

Without this skill loaded, agents frequently pick A or B with reasoning that echoes the rationalizations above. With this skill loaded, the agent should pick C and cite the counter to "I need to unblock my teammate."

If the agent still picks A or B with this skill loaded, the discipline is not bulletproof yet. Add the specific rationalization to the table and re-test.

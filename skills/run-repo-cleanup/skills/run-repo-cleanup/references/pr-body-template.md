# PR Body Template

Copy this into `/tmp/pr-body.md` and edit. Stay under **50,000 characters** (GitHub hard limit is 65,536). Generate the skeleton faster with `scripts/draft-pr-body.py --base <base> --head <head>`.

## Template

```markdown
# <emoji> <type>(<scope>): <PR title — matches the commit convention>

## Summary

- One-to-three bullet points. Punch-card for the reviewer.
- Each bullet describes outcome, not mechanism.
- Include the net diff size and file count if relevant: "21 files, +338/−403".

## Context & motivation

Why this PR exists. The problem it solves, what prompted it, what the
intended outcome is. 3–5 sentences. Link to incidents / tickets /
upstream discussions if any.

## The <N> items

Repeat this block for each concern in the PR. Each item is a
mini-PR of its own, reviewable independently.

### <N>. <one-line title>

**File(s):** `path/to/file.ts`, `path/to/other.ts`

What was changed and why. 2–4 sentences. Link to the specific line
range or symbol if it helps. Inline code snippets if they save the
reviewer a round trip.

Rationale for any judgment calls: why splitting vs. keeping together,
why renaming vs. preserving the name, why the chosen abstraction
instead of the obvious alternative.

## Files touched

| Purpose | Path | Type |
|---|---|---|
| One-line intent | `exact/path/from/repo/root.ts` | M / A / D / R |

Keep this table honest — every touched file shows up once.

## Verification

### Automated
```bash
<exact command>
# → <exact result or "PASS">
```
Repeat for each automated check that was run. If a test suite was
blocked by a pre-existing issue unrelated to this PR, say so plainly.

### Manual
- [ ] Step-by-step walkthrough of the user-facing behavior, with
      concrete things to click / URLs to hit / values to check.
- [ ] Include both happy path and at least one edge case.
- [ ] If you couldn't verify something (no access, missing data,
      couldn't reproduce), say so explicitly — never imply coverage
      you don't have.

## Risks & open items

1. **<Short descriptor>** — what could break, why, and how to catch it.
   If the risk is low, say why it's low. Don't hide risks to make the
   PR look smaller.
2. **<Known limitation>** — anything the reviewer would ask anyway,
   pre-answered. Example: "type-check passes; runtime not exercised
   on the streaming path because …"

## Follow-ups (not in scope)

- `<bullet>` explicit list of things you considered but did NOT do in
  this PR, with one-line rationale. This defends against scope-creep
  questions from the reviewer.

## GitHub policy note (optional but strongly recommended)

If the repo has a "fork only, never upstream" policy in AGENTS.md,
restate it at the bottom of the body so the reviewer sees it:

> Opened on `<fork-owner>/<repo>` per the policy in `AGENTS.md` →
> "GitHub Collaboration Policy". Do not file anything on the upstream
> `<upstream-owner>/<repo>`.
```

## Worked example — a PR that actually shipped

This is the body from the real Wope lockdown PR (abbreviated to ~30% for
illustration). Use it as a tone reference.

```markdown
# ✨ Wope Branding + Behavior Lockdown Layer

## Summary

- Pins the product to a single hardcoded OpenAI-compatible provider
  (Railway-hosted `gpt-5.4`) and hides every UI that lets a user
  configure models, providers, or credentials.
- Rebrands the loader + theme picker and reorients the Classic
  onboarding flow for a marketing-agent audience.
- Auto-seeds the Zeo Marketing MCP for every user with lazy OAuth on
  first tool use, and ships a backfill script for pre-existing users.

**Net diff:** 21 files, +338 / −403 across 2 commits. No new runtime
dependencies.

## Context & motivation

This fork is a rebrand + product-lockdown layer on top of upstream
`lobehub`. The existing `patches/wope-visible-branding-source.patch`
covers static branding — icons, wordmarks, protocol names. What it
does NOT cover is behavioral product shaping …

## The 10 items

### 1. Disable react-scan FPS overlay

**File:** `src/initialize.ts`

Removed the `if (__DEV__) { scan({ enabled: true }); }` block and the
unused `import { scan } from 'react-scan'`. The dev FPS badge was
bleeding into screenshots and was confusing new users.

The gated `<ReactScan />` analytics component in
`src/components/Analytics/ReactScan.tsx` stays — it's opt-in via
`REACT_SCAN_MONITOR_API_KEY` and already dormant without the env var.
`react-scan` stays in `package.json` for that component.

### 2. Skip "Configure Advanced Options" onboarding step

**File:** `src/features/Onboarding/Classic/index.tsx`

- Dropped `case MAX_ONBOARDING_STEPS` from the renderStep dispatcher.
- Removed the now-unused `ProSettingsStep` and `MAX_ONBOARDING_STEPS`
  imports.
- Changed step 4's `onNext` to `finishOnboarding` so the Response
  Language step ends the flow directly.

`ProSettingsStep.tsx` stays on disk — removing it would blow up the
mobile companion surface and isn't part of the intent here.

…

## Files touched (21 total)

| Purpose | Path | Type |
|---|---|---|
| Dev-overlay kill | `src/initialize.ts` | M |
| Boot loader brand | `index.html` | M |
…

## Verification

### Automated
```bash
bunx vitest run --silent='passed-only' \
  src/spa/router/desktopRouter.sync.test.tsx
# → PASS

bun run type-check
# → zero new errors in any file this PR touches.
```

### Manual
- [x] Signin page renders "Wope", 0 `LobeHub` strings.
- [x] Onboarding interests step shows the 9 new topics.
- [x] Composer has no model-selector pill.
- [x] `/settings/provider/openai` direct nav redirects to `/`.
- [ ] DB probe: `SELECT identifier FROM user_installed_plugins …`
      (the seed fires on `initUser` at signup; verified locally end-to-end).

## Risks & notes for reviewers

1. **`.env` not in this PR** — by design. `.env` is git-ignored and the
   key value is real production credentials. Must be set in Railway/
   Vercel secret storage for any non-local environment.
2. **`OPENAI_MODEL_LIST` syntax** — works with current `parseModelString`.
   If upstream changes that parser, this env silently returns empty.

## GitHub policy reminder

Opened on `yigitkonur/saas-wope-ai` (private Wope fork) per policy.
Do not file issues, PRs, comments, or discussions on `lobehub/lobehub`.
```

## Anti-patterns in PR bodies

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| "Various improvements" | Reviewer can't triage what to focus on | Per-item section |
| "See commits for details" | Forces reviewer to context-switch | Summarize in the body |
| "Should be straightforward" | Dismisses reviewer's need to verify | Explain, don't minimize |
| "Thanks for taking a look!" | Performative | Delete; state the ask |
| "LGTM?" | Puts reviewer on the spot | Wait for their response |
| Copy-paste commit messages | Raw commits aren't a review; they're evidence | Synthesize into the body |
| Screenshots with no caption | Reviewer has to guess what to notice | Caption every screenshot |
| Marking "verified" when you didn't run it | Lies waste the reviewer's trust | "Not exercised because …" |

## Length check

Before opening the PR:

```bash
wc -c /tmp/pr-body.md
```

If > 50,000, split the PR or move detail into repo docs and link. If
between 40,000 and 50,000, review once more: is every item earning its
characters?

# Project: marketing-website (example.com marketing site)

Read this before writing any mission brief for this repo. It carries the domain model, the
invariants a worker must never break, and the traps that already cost whole rounds.

Repo: `/root/dev/marketing-website` · Next.js App Router · TinaCMS · Vercel · GitHub Actions on
Avrea runners.

---

## 1. The one thing that breaks most missions

**Production does not read the `.mdx` file the worker edits.** It reads committed artifacts
under `content/generated/*.json` through the readers in `src/lib/tina/`.

So a source-only content fix is *incomplete*: the diff looks perfect, review passes, CI goes
green, and the live site still serves the old string. This has burned us more than once.

```
content/**.mdx  ──build──▶  content/generated/*.json  ──read──▶  src/lib/tina/  ──▶  page
     ▲                              ▲
worker edits here          production actually reads here
```

Rules that follow:

- Never hand-edit `content/generated/*.json`, `tina/tina-lock.json`, or `tina/__generated__/`
- Regenerate through the owning builder: `pnpm cms:<collection>:runtime`
- Order matters: collection builder → index builders → `cms:runtime-manifest` **last**
- Prove freshness: `git diff --exit-code -- content/generated tina/tina-lock.json` plus
  `pnpm cms:guard:generated-freshness`
- The freshness guard does **not** catch a stale-but-committed runtime. Committed and
  correct are different properties
- Builders whitelist keys — a new MDX field is silently dropped unless the builder knows it
- The runtime manifest conflicts on nearly every merge: take theirs, re-run the builder,
  never hand-merge

When briefing a worker on any content change, state this explicitly. Left unsaid, a worker
will edit the MDX, see a clean diff, and report success.

---

## 2. A new URL 404s until it enters the locale index

Route file existing, reader working, helper resolving — all insufficient. The valid-path
gate in `src/lib/routes/valid-paths.ts` rejects anything not present in the generated
manifest. This produced a live 404 on education category pages while every local check
passed.

- English routes are **prefixless** in production (`example.com/seo`); Turkish is prefixed
  (`/tr/...`). Never emit `/en/...`
- Public URLs are owned by `PUBLIC_ROUTE_REGISTRY` in `src/lib/routes/public.ts`. The App
  Router segment is not the public URL (`resources/articles` serves at `/resources/blog`)
- Deleting a public file can leave a catch-all serving **200 HTML** instead of a 404 — pair
  deletions with an explicit kill route
- Pagination is path-only: verify `<route>/page/2` returns 308 or 404 as intended

**Presence in HTML is not proof.** Test the probe on a known-negative page first; a probe
that reports "found" where the thing is absent is measuring nothing.

---

## 3. CI: what runs, and when nothing runs

Read `.github/workflows/ci.yml` before predicting anything.

- Push to `main` runs the full pipeline **including production deploy**. PRs run checks and
  build only
- `paths-ignore` excludes `.agent-docs/**`, `docs/**`, `.claude/**`, `.agents/**`, `**/*.md`
- Note the pattern: `*.md` matches root-level only; `**/*.md` catches nested files
- **Consequence:** a docs- or task-only commit produces **no CI run at all**

That last point is the one to say out loud in a report. No run is not a green run. Phrase it
as "no CI ran because these paths are excluded; these commits were never exercised at
runtime" rather than letting silence imply a pass.

Other CI facts:

- `main` pushes **queue**; PR runs cancel-in-progress. A `main` run owns a deploy and must
  not be killed mid-upload
- `cancelled` with **zero jobs** = preemption. The commit is in `main` but was **never
  deployed**. Re-run the same SHA
- `cancelled` with jobs running = timeout budget hit, not a code failure
- CI log tails show only the last lines. Download the full artifact — six hard ESLint
  failures once hid behind a truncated tail
- Build, test, and typecheck belong in CI. **This box stalls under load — never run suites
  locally.** Put that constraint in every mission brief

Deploy specifics:

- Production deploys automatically on push to `main`. The prebuilt workflow is for
  staged/preview and for re-deploying an already-validated SHA
- The prebuilt path requires an **exact-SHA `ci-gate` success** before it runs
- Never build locally, never trigger a Vercel-side build. CI builds; deploy uploads the
  prebuilt artifact
- Verify the deployed build reports the SHA you expect, and distinguish the immutable
  deployment URL from the production alias
- `example.com` fronts an older backend — **never** use it as deploy proof

---

## 4. Branches: names lie

The most dangerous operation in this repo is merging an old branch onto newer work.

A branch called `strip-dead-proof` turned out to delete **946 live authored nodes across 328
MDX files**. Merging by name would have silently destroyed content, and every mechanical
check would still have passed.

Two independent questions, both required:

```bash
git merge-base --is-ancestor <branch> main   # already contained?
git cherry main <branch>                     # patch-equivalent?
```

`git cherry` output: `-` means the change already exists in `main` (safe to retire); `+`
means genuinely unique.

**Unique is not the same as wanted.** A `+` commit may be an older, worse version of
something `main` already improved. Before merging any `+`, ask whether `main` already
contains a better solution to the same problem. Content and design work is especially prone
to this — an older AI-flavoured draft can overwrite carefully humanised prose and no check
will notice.

Default when uncertain: **preserve, don't merge.** Archive on a dedicated branch in
concern-scoped commits. Reversible beats tidy.

Other branch facts:

- **`entire/*` branches are off-limits.** Checkpoint tooling snapshots, deliberately
  diverged by thousands of commits. Never merge, rebase, clean, or delete them — local or
  remote. Skip them in every cleanup
- Git answers depend on the checkout: ask `origin/main` via `git ls-tree`, not `git ls-files`
  in a stale worktree
- Branch-diff direction produces false "reverts" — run `git merge-base --is-ancestor` first
  to establish the relationship before reading a diff as a regression
- Audit subagents need a **fresh** checkout; a stale one reports already-fixed defects as
  live

---

## 5. Content quality — the invisible regression

The EN and TR corpora were deliberately humanised over many passes; AI-flavoured phrasing
was stripped out. Two implications:

1. **Never restore older prose** over the current version without confirming it is actually
   newer and better. Mechanical checks cannot see voice regression
2. Route prose work by field: existing-English→EN uses the rewrite path, existing-Turkish→EN
   uses the adaptation path. `project-page-building` owns structure; the writing skills own prose

Green gates cannot see scope loss or fidelity drift. A page can pass everything and still say
less than it did yesterday.

YAML hazards in Tina MDX frontmatter:

- A `": "` inside a plain scalar list item silently converts the string into a YAML map —
  single-quote the whole item
- Never fix terminology corpus-wide with regex; it hits slugs, URLs, and SEO titles and fuses
  tokens. File by file, prose fields only

---

## 6. Illustrations

- Every page ships with artwork; empty required slots mean unfinished, not MVP
- Light and dark are a **pair**, registered in `src/lib/illustrations/dark-variants.ts`.
  Derive dark twins deterministically — never prompt-generate them separately
- Card art without a `sizes` attribute requests a 3840px image and renders blank slots.
  This recurs
- A missing asset can return **200 HTML** instead of 404 — check PNG magic bytes, not the
  status code
- Trailing bytes after `IEND` produce a PNG browsers render fine but tooling rejects
- `globals.css` is frozen — new selectors hard-fail the atomic audit
- Tailwind can't draw one-sided borders here (`border-t-2` isn't compiled); use longhand CSS
- `twMerge` drops custom text sizes (`text-h1`..`text-h6` read as colours)

**Mechanical metrics are weak proxies for art quality.** Blur ratios, colour counts, and hash
checks all missed 77 real defects a human contact sheet caught immediately. "Low quality"
here usually means broken draftsmanship — anatomy, proportion — which no lint can see.

---

## 7. Environment fragility specific to this box

These produce confident-sounding refusals that have nothing to do with the task. When a
worker reports a policy blocker, check these first:

| Symptom | Real cause | Fix |
|---|---|---|
| Bash fails *before* the command runs | `/tmp` full (`ENOSPC`) | Clear temp artifacts; confirm a trivial command runs |
| Every git command fails confusingly | Worktree deleted under it; `cwd` shows `(deleted)` | Re-anchor to the main checkout |
| Commit hook dies with `ERR_MODULE_NOT_FOUND` | Broken `node_modules` | Reinstall from the offline pnpm store — **never** `--no-verify` |
| Prompts bounce to idle instantly | Worktree missing `.claude/hooks/` | Copy hooks in; `.worktreeinclude` prevents it |
| `eslint` reports green but errors exist | Piped exit code swallowed | Redirect to a file and read `$?` |

`cd` prefixes escape worktree isolation — use bare relative commands.

---

## 8. Verification commands that actually settle questions here

```bash
# repo truth
git status --short --branch
git log --oneline --decorate origin/main..main
git diff --stat origin/main..main
git diff --check origin/main..main

# push landed?  expect: 0  0
git ls-remote --heads origin <ref>
git rev-list --left-right --count origin/<ref>...<ref>

# CI for the exact SHA
gh run list --commit <full-sha> --limit 20 \
  --json databaseId,workflowName,event,status,conclusion,headSha,url

# nothing lost during an archive
git merge-base --is-ancestor <old-tip> <archive-branch>
git diff --name-only <old-tip>..<archive-branch> | wc -l

# generated runtime freshness
git diff --exit-code -- content/generated tina/tina-lock.json
pnpm cms:guard:generated-freshness
```

---

## 9. Standing constraints to paste into every mission brief

```
Do not weaken or bypass any check (no deleted assertions, no widened thresholds,
no skip/xfail, no --no-verify). If a hook fails due to broken tooling, repair the
tooling.
Do not run test suites, builds, or typechecks locally — this machine stalls under
load; all build/test/typecheck goes through CI.
Do not touch entire/* branches.
Do not hand-edit content/generated/*.json — regenerate through the owning builder.
Do not force-push, deploy, or delete remote refs without explicit authorization.
English routes are prefixless; Turkish routes are /tr/-prefixed. Never emit /en/.
```

---

## 10. The meta-lesson

Every landmine above is the same failure: **a passing check that did not measure the thing
that mattered.**

- Source edited, runtime stale → diff green, production wrong
- Route added, index missing → build green, URL 404
- Branch merged by name → merge clean, content destroyed
- Art generated, metrics fine → gates green, drawings broken
- Commit pushed, paths ignored → no red, nothing verified

So the question before every completion claim is not *"did the check pass?"* but *"did the
check measure what the user will actually experience?"*

When those diverge, believe the user's experience.

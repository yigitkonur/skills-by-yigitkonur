# Project: creative-production-os (ai-presentation-deck)

The internal creative production system for Project. A colleague who is not technical and not
comfortable in a terminal asks in plain Turkish or English and gets an evidence-backed
artifact: a presentation, a video, a social post, a document, an illustration, a
voice-over, a sourced photo or a brand logo.

Workspace root: `~/Downloads/ai-presentation-deck 2` (a directory, **not** a git repo — the
sub-projects are). Reached v10 across ten supervised waves; the release proof below is the
definition of done.

Read this before writing a mission brief for this repo. Verify the numbers rather than
quoting them — every count here is generated, and a stale number in a report is exactly
what nine waves of work went into preventing.

---

## 1. Three lanes, and the routing between them is load-bearing

```
deck-kit    deterministic HTML slide artifacts, large template catalogue
video-kit   evergreen Remotion templates for repeatable jobs
canvas-kit      bespoke from-scratch motion and stills
```

Illustration, sourcing, writing, voice and publishing **support** those lanes; they are not
a fourth lane. A worker that invents a fourth lane has misunderstood the system.

---

## 2. Repository topology — canonical vs generated

Canonical sources. Each is a **local-only git repo with no remote**, created deliberately
so a non-git workspace could still be rolled back:

```
.claude/skills   the umbrella router plus the Tier-1 skill family
deck-kit     deck templates, compose, validate, serve, browser check
video-kit    template registries, manifest, render farm, remote backend, receipts
canvas-kit       bespoke Remotion workspace, audiogram, closure check
tools            the release machinery
```

Generated distributions. **Never hand-edited.** They exist only as output of
`tools/sync-repos.mjs`, and hand-editing them is the fork problem the whole release design
exists to end:

```
production-kit-plugin   → github.com/your-org/your-repo   (private)
production-kit-skill    → github.com/your-org/your-repo    (private)
```

**These two repos must stay private.** They ship working service credentials by deliberate
design — that is the price of the zero-setup goal, and the owner approved it knowingly.
Making either public, or adding someone to the org who should not hold those keys, burns
the credentials.

---

## 3. The release machinery (`tools/`)

| Tool | What it is |
|---|---|
| `ship-graph.mjs` | The single authority for what ships. Copy, secret scan, portability scan and parity all read the same projection. |
| `ship-security.mjs` | Path-and-purpose-scoped instructed credentials plus bounded raw scanning that reaches binary and oversized files. |
| `sync-repos.mjs` | The two-repository transaction. Bare and `--dry-run` write nothing; `--apply` mutates; `--apply --commit` commits both or neither. |
| `baseline-pack.mjs` | Seals an owner-only preimage of the accepted canon with a trust-anchored manifest. |
| `count-claims.mjs` | Fails when prose states a catalogue count the manifests contradict. |
| `routing-eval.mjs` | Scores routing and trigger-boundary conflicts offline; model-dependent accuracy is opt-in and reported as unmeasured otherwise. |
| `release-proof.mjs` | The release gate — see §5. |

Lane tooling worth knowing by name: `compose.mjs`, `deck-plan.mjs`, `deck-validate.mjs`,
`deck-browser-check.mjs`, `serve.mjs` (deck) · `video-manifest-build.mjs`,
`payload-expand.mjs`, `render-farm.mjs`, `delivery-receipts.mjs`, `vercel-doctor.mjs`,
`render-cleanup.mjs` (video) · `closure-check.mjs`, `audiogram-selfcheck.ts` (canvas).

---

## 4. The gates

```bash
node --test tools/tests/*.test.mjs      # one suite file per wave
node tools/release-proof.mjs            # clean-clone proof, both distributions
node tools/count-claims.mjs             # prose counts vs live manifests
cd deck-kit  && node tools/qa-check.mjs && node tools/manifest-build.mjs --check \
                 && node tools/agents-build.mjs --check && node tools/docs-check.mjs \
                 && node tools/coverage-report.mjs
cd video-kit && npm run verify
cd canvas-kit    && npm run verify
npm --prefix .claude/skills/image-finder-skill test
claude plugin validate ./production-kit-plugin
```

Skipping one of these is how a regression ships. The wave suites are cumulative — a file
per wave, all run together.

---

## 5. What "done" means here

`node tools/release-proof.mjs` is the definition. It clones each distribution with
`git clone --no-local`, installs the way that distribution's own README instructs, and
exercises it **against the clone only**:

```
clean-source · clone · install · discovery · golden · deck-refusal · deck-range
canvas-closure · audiogram-selfcheck · catalog-gate · claims-gate
delivery-receipts · delivery-blocked · preflight · routing-offline
```

It writes a machine-readable receipt plus a human summary, `--verify` re-hashes every
recorded artifact, and **a skipped check demotes the verdict to incomplete** so a skip can
never read as a pass.

`--no-local` is load-bearing: without it git hardlinks and you end up testing the source
you were trying to escape.

---

## 6. Invariants — never let a worker break these

- **Distributions are generated.** Every change flows from a canonical source through
  `sync-repos.mjs`. A hand-edit in `production-kit-plugin/` or `production-kit-skill/` is always wrong.
- **Sample copy must never reach a deliverable.** The deck plan is a contract; planned copy
  that did not land is a failure, not a warning.
- **Figures owe evidence.** On-canvas and in publishing copy alike, a number needs a
  resolvable, unexpired, verified-or-explicitly-qualified claim.
- **Spoken audio owes captions or a transcript**, or delivery blocks.
- **Nothing shipped asserts machine-local state.** Shipped text instructs runtime discovery
  instead of recording what was true on one laptop.
- **Credentials are embedded deliberately**, bound to exact paths and purposes. Tools report
  credential *sources*, never values.
- **Marketing production waits for a real human approval.** The tool used to collect it may
  vary; the human choice may not.
- **A repeat sync must report zero drift.** That is what proves the generated trees are
  generated rather than quietly touched.

---

## 7. Known limits — real, but NOT bugs

- Some platform profiles are **intentionally unserved**, each with a stated reason in the
  preset accounting. A worker "fixing" one by adding a template nobody asked for is scope
  creep.
- `qa-check.mjs` validates the catalogue, not a produced deck. Deliverable checks live in
  `deck-validate.mjs` and `deck-browser-check.mjs`. Keeping them separate is deliberate:
  the catalogue gates stay static and dependency-free.
- Model-dependent routing accuracy is **opt-in**. The default routing eval says it was not
  measured. That is honesty, not a gap to paper over.
- `maintainer-ready: NO` from `vercel-doctor.mjs` is **expected** on an employee machine.
  Render-ready is the verdict that matters; maintainer-ready only covers rebuilding the
  sandbox snapshot.

---

## 8. Traps specific to this repo

**The workspace root is not a repo.** `git status` there tells you nothing. Always name the
sub-project.

**Tightening a scan breaks the next sync before it fixes anything.** `sync-repos.mjs`
validates the *destination* too, so a stricter rule fails at preflight against bytes that
are already committed in the distributions. The fix is a transition commit in each
distribution removing the offending files, then the normal sync. Expect this every time a
scan rule gets stricter.

**macOS `/var` is a symlink into `/private/var`.** An ESM main-guard comparing an
unresolved `argv[1]` against a realpathed `import.meta.url` silently never fires, so a CLI
run from a temp dir prints nothing and exits 0 — indistinguishable from success. Realpath
`argv[1]` in any tool that might run from a temp clone.

**Campaign code is a workspace overlay, not shipped Canvas source.** A campaign directory
under `canvas-kit/src/campaigns/` must be in the projection's exclusions or the shipped
tree stops being self-contained. A `typeof require` guard around `require.context` also
silently defeats the bundler's static rewrite — the call has to stay unguarded.

**Two different modes wear the same field name in the baseline pack:** the snapshot's
storage mode (owner-only, by design) and the canonical source mode that restoration must
reproduce. Comparing one against the other looks like a broken test and is actually a
conflated concept.

---

## 9. Verification commands that settle questions here

```bash
# where everything actually stands
for d in .claude/skills deck-kit video-kit canvas-kit tools \
         production-kit-plugin production-kit-skill; do
  printf '%-16s ' "$d"; git -C "$d" log -1 --format='%h %s'
  printf '  dirty=%s\n' "$(git -C "$d" status --porcelain | wc -l | tr -d ' ')"
done

# the distributions really match their remote
for r in production-kit-plugin production-kit-skill; do
  printf '%-16s local=%s remote=%s\n' "$r" \
    "$(git -C $r rev-parse --short HEAD)" \
    "$(git -C $r ls-remote origin main | cut -c1-7)"
done

# generated trees are still generated
node tools/sync-repos.mjs          # expect MODE=dry-run, changes=0 twice
```

---

## 10. Standing constraints for every mission brief here

```
Canonical sources only. Distributions change only through tools/sync-repos.mjs.
Never hand-edit production-kit-plugin/ or production-kit-skill/.
Local commits are authorized; push, remotes, deploy and publish are not.
Never print a credential value; report credential sources.
Commit each canonical domain as you finish it — overnight runs get interrupted.
One background reviewer at a time, and never pin a reviewer to hashes while still editing.
If a service fails, keep working locally and report the outage rather than stopping.
```

---

## 11. Worker failure modes observed here

1. **Reports a sync it never ran.** Distributions sat untouched at their old commits while
   the report said both were synced. Check the distribution HEADs, always.
2. **Green suite, real defect.** Suites of 13, 25 and 38 tests were each green while a real
   data-losing defect sat in the code. Every one was found by an adversarial probe.
3. **Reviewer fanout.** Spawns many reviewers that pin file hashes, keeps editing, and every
   reviewer cancels itself with `TARGET_CHANGED`. Hours burn and nothing is reviewed.
4. **Stalls with a question after a long run** — "if you want, I can continue" — when the
   authorisation was already standing.
5. **Believes its own stale context.** Past roughly 70% context it insisted a committed wave
   was uncommitted and refused to advance. Reset it rather than arguing.
6. **Fixes a red test by relaxing the gate.** When a gate correctly refuses and the fixture
   is wrong, the fixture gets fixed — say so explicitly in the brief.

---

## 12. First five minutes

```bash
cd ~/Downloads/ai-presentation-deck\ 2
# 1. topology + dirt (the loop in §9)
# 2. node --test tools/tests/*.test.mjs
# 3. node tools/sync-repos.mjs        → expect changes=0
```

Clean trees, a green suite and a zero-drift dry-run mean you are starting from the state
the last round claimed. Anything else is your first finding, before you write a single
line of mission brief.

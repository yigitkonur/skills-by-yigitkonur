# Audit brief template — Phase 3 dispatch

One agent per `APPLICABLE*` domain. Fill every `<slot>`; do not compress the structure.
Each agent is read-only against the target repo and writes only into its own findings
folder.

```text
[CONTEXT]

You are a Next.js performance auditor. A repo profile and applicability verdict already
exist — do NOT re-derive them, and do NOT run your own recon.

Target repo: <absolute repo root>
Your domain: <domain slug>
Applicability verdict: <APPLICABLE | APPLICABLE-WITH-REMOVAL | BLOCKED-PARTIAL | APPLICABLE-CUSTOM>
Installed: Next.js <version>, React <version>. Archetype: <archetype>.

Repo profile (excerpt — the full file is at nextjs-enhancement/00-recon.md):
<3-6 lines: router shape, relevant config flags, relevant feature counts, library-vs-custom>

<IF BLOCKED-PARTIAL>
Features gated OUT on this install — never recommend, never file a finding proposing them:
<list with the reason: probe absent / version floor unmet / prerequisite missing>
</IF>

<IF APPLICABLE-CUSTOM>
This repo uses a custom implementation, not the library this domain's recipes assume:
<what it does instead>. Compare the MECHANISM against the reference pattern and flag only
genuine gaps. Proposing a migration to <library> is a false positive, not a finding.
</IF>

<IF APPLICABLE-WITH-REMOVAL>
A removed/dead surface was detected in recon: <what>. Confirm it in source and file it —
this is the highest-value finding in your domain.
</IF>

[READ FIRST — your contract]

1. references/detect/<domain>.md — your gate table, detection commands, severity rubric,
   false-positive filters, evidence format. This is your specification.
2. references/workflow/false-positives.md — the six checks every finding must clear.
3. nextjs-enhancement/README.md — the artifact format authority.

Do NOT read other domains' detect files or other agents' findings.

[MISSION]

Run your domain's detection commands against the target repo. For every real issue, write
one finding file to nextjs-enhancement/findings/<domain>/NN-<slug>.md using the template
in references/artifact/finding-template.md.

Hard constraints:
- WRITE SCOPE: nextjs-enhancement/findings/<domain>/ ONLY. Never the target repo's source,
  never another domain's folder, never tasks/.
- READ-ONLY on the target repo. No edits, no installs, no builds, no git operations.
- Evidence must be literal: exact file:line plus the matched text, from a command you ran.
- Every finding cites the gate row or pitfall signature it maps to.
- Every finding clears all six false-positive checks, shown as checked boxes.
- Severity is present-tense on the INSTALLED version. Deprecated-but-working is `minor`.

**Zero findings is a valid and expected result.** If the repo already conforms, write no
files and say so. Never invent a finding to justify the dispatch.

[DEFINITION OF DONE]

- Every detection command in your detect file was run (or explicitly skipped with a reason
  — e.g. the feature is gated out on this install).
- Every real issue has exactly one finding file; N call sites of one problem is ONE finding
  against the shared wrapper where one exists.
- No finding proposes a feature absent from this install.
- No file written outside your findings folder.

[HANDBACK]

1. One paragraph: what you found, or that the domain is clean.
2. File list with severity per file.
3. Commands run, and any that returned nothing (that is signal).
4. Anything the planner needs: shared wrappers that concentrate a fix, cross-domain
   dependencies you noticed, evidence that another domain's verdict may be wrong.
5. Anything you could NOT check, and why.
```

## Dispatch rules

- **Full parallel is correct here.** These agents only read the repo and write disjoint
  folders — there is no shared lock, unlike browser-driven audits. Dispatch all applicable
  domains in one message.
- **Cap = domain count (14).** Never more than one agent per domain.
- **Never dispatch for `NOT-APPLICABLE`.** That verdict exists precisely to save the agent.
- **Pass the verdict.** An agent that does not know it is auditing a custom implementation
  will file library-migration noise.
- **Give the profile excerpt, not the whole recon file.** Enough to orient; not enough to
  re-litigate.

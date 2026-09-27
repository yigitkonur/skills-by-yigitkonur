# Mission-Style Subagent Prompting Engine

This reference details the construction of standalone, verbose, highly executable mission prompts for autonomous subagents in an Astro audit & remediation campaign.

---

## 1. Architectural Principles

### The Parent-Only Secret Law

> [!IMPORTANT]
> **NEVER mention, quote, or expose `MISSION_PROTOCOL.md` to subagents.**
> The protocol is an architect-level instrument. Subagents receive pure domain instructions, explicit constraints, and full operational autonomy without meta-framework overhead.

### The Single-Writer Invariant

- Every subagent must have **exclusive single-writer ownership** over its assigned domain and target files.
- Two subagents must NEVER edit the same file concurrently in the same wave.

### Zero-Approval Autonomous Execution

- Never instruct subagents to ask the user or parent for permission on obvious next steps.
- Subagents must be explicitly granted full end-to-end ownership: _"You own this mission end-to-end. Explore freely, trust your judgment, adapt your approach as you learn. The destination is fixed; the path is yours."_

---

## 2. Hard Resource Boundaries & Operational Constraints

Every subagent prompt MUST contain the following non-negotiable boundary block:

```markdown
#### Hard Resource Boundaries & Operational Constraints (NON-NEGOTIABLE)

- **NO LOCAL PRODUCTION BUILDS**: Never run `pnpm astro:build`, `pnpm build`, or `npm run build`. Production builds are heavy multi-minute jobs that risk OOM in subagent containers.
- **NO DEV OR PREVIEW SERVERS**: Never run `pnpm dev`, `astro dev`, or `astro preview`.
- **NO DEPLOYMENTS**: Do not deploy to Cloudflare or Netlify.
- **NO FULL E2E SUITES**: Do not start headless browser servers or run full browser suites.
- **WORK ONLY IN YOUR ASSIGNED WORKTREE**: `<REPO_ROOT>/.worktrees/wt-<ID>/`.
- **PERMITTED LIGHTWEIGHT CHECKS**: Scoped Vitest tests (`pnpm exec vitest run tests/...`), scoped typecheck, ESLint.
- **DO NOT PUSH DIRECTLY TO MAIN**: All changes must be delivered via branch `fix/audit-<ID>`.
```

---

## 3. The 6-Part Mandatory Prompt Template

When generating subagent prompts, adhere to this exact structural specification:

```markdown
### 1.0 Skills / Tools

- `view_file`: Read source code, test files, and audit artifacts.
- `run_command`: Execute git, scoped tests, static checks, and GitHub CLI commands.
- `replace_file_content`: Apply surgical, high-precision code fixes.
- `write_to_file`: Create new test files, modules, or documentation.

---

### 1.1 Context Block

You are the **Lead Remediation Owner** for **Workload <ID>: <Topic Title>** in `<owner>/<repo>` (Astro 7.3.1, Vite 8.2.2).
You have exclusive single-writer ownership of <Subsystem & Target Files>.
Your isolated Git worktree is located at `<REPO_ROOT>/.worktrees/wt-<ID>`, checked out on branch `fix/audit-<ID>`.
All terminal commands and file modifications must strictly execute inside `<REPO_ROOT>/.worktrees/wt-<ID>`.

#### Incident & Tracking Inventory

- **Parent GitHub Issue**: [#<ParentID>](https://github.com/<owner>/<repo>/issues/<ParentID>) — `<Parent Issue Title>`
- **Verified Child Sub-Issues**:
  - [#<SubID1>](https://github.com/<owner>/<repo>/issues/<SubID1>): `<Key-001>` — `<Summary>`
  - [#<SubID2>](https://github.com/<owner>/<repo>/issues/<SubID2>): `<Key-002>` — `<Summary>`

#### Authoritative References to Inspect First

1. `references/workloads/<category>/<ID>-<slug>.md` — Complete mission brief.
2. `docs/audits/results/<category>/<ID>-<slug>/findings.json` — Structured findings ledger.
3. `docs/audits/results/<category>/<ID>-<slug>/issue-body.md` — Detailed checklist.

#### Mental Model & Architectural Invariants

[Describe core framework mechanics, Astro Content Layer contracts, Cloudflare runtime purity, or edge cache safety relevant to this workload.]

---

### 1.2 Mission Objective

Investigate and remediate all confirmed defects and any related system flaws in <Subsystem>.
Fix root causes, not just surface symptoms. Author a comprehensive integration test suite `tests/int/<slug>.test.ts`, ensure all scoped checks pass, commit to `fix/audit-<ID>`, push to remote `origin/fix/audit-<ID>`, and open a non-draft Pull Request against `main`.

[Insert Hard Resource Boundaries Block Here]

You own this mission end-to-end. Explore freely, trust your judgment, adapt your approach as you learn. The destination is fixed; the path is yours.

---

### 1.3 Research Guidance & Investigation Boundaries

1. [Step 1: Code inspection and root cause reproduction]
2. [Step 2: Core implementation and architectural fix]
3. [Step 3: Integration test authoring in tests/int/<slug>.test.ts]
4. [Step 4: Scoped test verification via Vitest and ESLint]

---

### 1.4 Definition of Done (Binary, Specific, Verifiable)

- **D1: Root Cause Remediated**: [Specific architectural invariant verified].
- **D2: Integration Suite Created**: `tests/int/<slug>.test.ts` passes with exit code 0.
- **D3: Clean Working Tree**: Committed to branch `fix/audit-<ID>`.
- **D4: Non-Draft PR Delivered**: Opened via `gh pr create` referencing parent [#<ParentID>] and sub-issues with a two-tier localized primary locale/English description.

---

### 1.5 Handback Format

Return a structured report to the parent orchestrator:

1. Executive finding.
2. Findings disposition table.
3. Verification & test evidence.
4. GitHub PR URL.
5. Residual risks.
```

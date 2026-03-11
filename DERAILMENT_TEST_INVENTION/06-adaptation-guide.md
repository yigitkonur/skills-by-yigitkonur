# Adaptation Guide

How to apply Derailment Testing beyond AI skills — to runbooks, SOPs, onboarding docs, API guides, and any procedural instructions.

---

## Core transfer principle

Derailment Testing works on any document where:

1. **One entity writes instructions** (author)
2. **Another entity follows them** (executor)
3. **The executor cannot ask clarifying questions during execution**

The methodology transfers by adapting three variables: the instruction format, the executor profile, and the task domain.

## Domain adaptations

### DevOps runbooks

**Instruction format:** Numbered steps for incident response, deployment, rollback.
**Executor profile:** On-call engineer at 3am with no context on the system's history.
**Key risk:** Missing prerequisites (VPN access, credentials, tool versions) and ambiguous escalation thresholds ("if the error seems critical").

**Adaptation notes:**
- Test with a simulated incident, not a real one
- The "naive executor" is an engineer who joined the team last week
- Pay special attention to environment prerequisites (which cluster? which region? which credentials?)
- Runbooks have a unique failure mode: **time pressure**. Steps that are technically complete but require 5 minutes of interpretation are effectively P0 in an incident context

**Sample friction points from runbook testing:**

| ID | Derailment | Root cause |
|---|---|---|
| F-01 | "SSH into the production bastion" — which one? There are 3 bastions across regions | M2: Unstated location |
| F-02 | "If the error rate is high, escalate" — what number is "high"? | M1: Ambiguous threshold |
| F-03 | "Run the rollback script" — it requires Python 3.11 but the bastion has 3.9 | S1: Missing prerequisite |

### Onboarding documentation

**Instruction format:** Setup guides, environment configuration, "getting started" docs.
**Executor profile:** New hire on day 1 with access to only what the doc says.
**Key risk:** Assumed knowledge about internal tools, naming conventions, and tribal knowledge.

**Adaptation notes:**
- Test on a fresh machine (or fresh VM/container) — not your configured workstation
- Every `brew install`, `apt-get`, or `pip install` must be explicit
- Watch for "obvious" steps that aren't obvious: "clone the repo" (which repo? what URL? which branch?)
- Onboarding docs have a unique failure mode: **accumulated drift**. Each step was correct when written but the system has changed since.

### API documentation

**Instruction format:** Endpoint descriptions, authentication flows, request/response examples.
**Executor profile:** Developer integrating the API for the first time.
**Key risk:** Format inconsistencies between examples and schemas, undocumented error codes, and missing authentication setup steps.

**Adaptation notes:**
- Actually make the API calls. Don't just read the docs.
- Use `curl` exactly as shown in the examples — if the example is wrong, that's a P0
- Test the authentication flow from scratch (create a new API key, don't use an existing one)
- API docs have a unique failure mode: **example rot**. The schema is updated but the examples aren't.

### Internal playbooks and SOPs

**Instruction format:** Business process documentation, compliance procedures.
**Executor profile:** Employee in a different department or a contractor with no institutional context.
**Key risk:** References to internal tools by nickname, undocumented approval workflows, and "just ask [person]" steps.

**Adaptation notes:**
- "Just ask Sarah" is a P0 derailment — what if Sarah is on vacation?
- Every human dependency should have a role (not a name) and a fallback
- Compliance SOPs have a unique failure mode: **checkbox theater**. Steps that exist for audit purposes but have no operational content

### Tutorial and course content

**Instruction format:** Step-by-step learning exercises, lab guides, workshops.
**Executor profile:** Student with the stated prerequisite knowledge and nothing more.
**Key risk:** Unstated dependencies between exercises, platform-specific steps without platform detection, and "you should now see X" without troubleshooting for "I don't see X."

**Adaptation notes:**
- Start from the stated prerequisites, not your actual knowledge
- If the tutorial says "basic Python knowledge required," test whether a basic Python programmer could actually follow the steps
- Every "you should see" checkpoint needs a "if you don't see this, try..." recovery

## Adapting the severity scale

The P0/P1/P2 scale adapts based on the domain's tolerance for ambiguity:

| Domain | P0 threshold | P1 threshold |
|---|---|---|
| Incident runbooks | Any ambiguity (time-critical) | Requires re-reading |
| AI skills | Hard stop / contradiction | Confusion > 30 seconds |
| Onboarding docs | Cannot proceed on day 1 | Needs to ask a colleague |
| API docs | Example doesn't work | Example works but is misleading |
| Compliance SOPs | Audit failure | Process delay |

## Adapting the root cause taxonomy

The root cause codes (S1, M1, O1, etc.) from `03-friction-classification.md` apply universally. Domain-specific additions:

| Domain | Additional root cause | Code | Description |
|---|---|---|---|
| Runbooks | **Credential gap** | D1 | Required credentials not listed or not accessible |
| Onboarding | **Platform drift** | D2 | Step was correct at write time, system has changed |
| API docs | **Example rot** | D3 | Schema updated, example not |
| SOPs | **Human dependency** | D4 | Step requires a specific person, not a role |
| Tutorials | **Invisible prerequisite** | D5 | Exercise depends on prior exercise not stated |

## Tooling considerations

### Minimal tooling (any domain)

The methodology requires only:
- A text editor for the derail notes
- The instruction set under test
- A real task to execute
- The `derail-notes/` directory convention

### Enhanced tooling (optional)

| Tool | Purpose | When to use |
|---|---|---|
| `grep` / `ripgrep` | Consistency verification post-fix | Any document set with >5 files |
| Git diff | Track fix deltas | Version-controlled instruction sets |
| Link checker | Catch broken cross-references | Docs with heavy cross-linking |
| CI validator | Automated routing integrity | Published instruction sets |

## Organizational adoption

### Starting small

1. Pick the instruction set with the most complaints or support tickets
2. Run one Derailment Test with one real task
3. Fix the P0 items
4. Share the derail notes with the team — the structured format makes the value visible immediately

### Scaling up

- Assign Derailment Tests as part of the doc review process
- Track friction point counts per document over time (a declining count means the instructions are improving)
- Use cross-run recurrence analysis to find systemic issues

### Common objections and responses

| Objection | Response |
|---|---|
| "Our docs are fine, people just don't read them" | If people can't follow the docs, the docs are the problem, not the people. Derailment Testing proves this objectively. |
| "It takes too long to test every document" | Test the critical path first. One Derailment Test on your deployment runbook is worth more than 10 tests on internal guides. |
| "AI agents are different from humans" | The methodology tests instructional clarity, which matters for both. Humans have slightly higher tolerance for ambiguity, but the failure modes are the same. |
| "We have QA for our docs already" | Traditional doc QA checks grammar, formatting, and factual accuracy. Derailment Testing checks *executability* — a different dimension entirely. |

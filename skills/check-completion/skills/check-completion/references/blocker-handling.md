# Blocker Handling — Documenting the Truly Unresolvable

Blockers are the one place Phase 2 is allowed to leave a row at a non-`Implemented` terminal state. This file defines the bar for "genuinely unresolvable" and the documentation format.

## The two types of blocker

### Resolvable blocker

The dependency can be met with the resources available in this session: a missing env var can be set, a missing file can be created, a configuration can be fixed, a tool can be installed.

**Action**: resolve it. Do not leave as `Blocked`.

### Unresolvable blocker

The dependency cannot be met with available resources: an external credential only the user has, a third-party service outage, a decision only the human can make, an infrastructure change beyond the agent's permissions.

**Action**: document per the format below. The row ends as `Blocked — unresolvable`.

## Distinguishing the two — the five-check test

Before declaring a blocker unresolvable, run these five checks. If ANY has a yes answer, the blocker is resolvable.

| # | Check | Example |
|---|---|---|
| 1 | Can you provide the missing value from existing context? | Env var is hardcoded in a checked-in `.env.example`; use that. |
| 2 | Is there a documented workaround? | OAuth flow unavailable; docs show how to use a personal access token instead. |
| 3 | Can you ask the agent to act with a reduced-scope version of the task? | Database not available; mock the interface for now, flag real-DB verification as follow-up. |
| 4 | Can you split the task so the non-blocked part proceeds? | "Deploy to prod" is blocked; "prepare the deploy artifact" is not. Split and do the second part. |
| 5 | Is the blocker a task-description artifact rather than a real dependency? | "Add auth using the team's auth service" — but the task-asker didn't specify which auth service. That's ambiguity (`Ambiguous`), not a blocker. |

If all five return no, the blocker is genuinely unresolvable.

## The documentation format

`Blocked — unresolvable` rows in the completion report require this exact shape:

```markdown
| # | Task | Started | Ended | Evidence |
|---|------|---------|-------|----------|
| N | <task name> | `Blocked` | `Blocked — unresolvable` | Dependency: <specific named dependency>. Next step: <exactly what would unblock this>. Owner: <who can unblock — user / external team / upstream>. |
```

Every field is required:

### Dependency
- **Must be specific.** "Missing config" is not specific. "Missing `STRIPE_SECRET_KEY` env var in the worker deployment" is specific.
- Name the tool, credential, service, decision, or file explicitly.

### Next step
- **Must be concrete.** "Ask the user" is not concrete. "Obtain `STRIPE_SECRET_KEY` from the user's password manager and set it in `.env.production`" is concrete.
- One sentence, actionable by the party who can unblock it.

### Owner
- **Must name who acts.** The agent (if there's a path forward the agent can take once unblocked), the user, an external team, a specific person — name them.
- "Someone" is not an owner. "User" is valid if the user is the one the agent is working with.

## Example — well-documented unresolvable blocker

```markdown
| 7 | Deploy session-service to staging | `Stalled` | `Blocked — unresolvable` | Dependency: `kubectl` is not installed in this sandbox, and the deploy manifests require cluster admin credentials the agent does not have. Next step: User runs `kubectl apply -f deploy/staging.yaml` against the ops cluster after reviewing the manifest changes in commit abc1234. Owner: user. |
```

This row tells the user: what I tried, why it can't proceed, what they need to do, and how they'll know they did it.

## Example — poorly-documented blocker (don't do this)

```markdown
| 7 | Deploy session-service to staging | `Stalled` | `Blocked — unresolvable` | Couldn't deploy. |
```

Three failures:
- "Couldn't deploy" — vague. Why? Tooling? Permission? Manifest bug?
- No next step — the user has no idea what to do next
- No owner — ambiguous whose court the ball is in

This is the failure mode that defeats the skill's purpose. A vague `Blocked — unresolvable` is equivalent to `Assumed Complete` — it presents a terminal status without the rigor that justifies one.

## When the human has not responded

A task that was `Deferred to Human` and the human has not responded is **not** a blocker — it's the `Deferred to Human` terminal status. Use the correct status.

`Deferred to Human`'s documentation should still be concrete:

```markdown
| 12 | Decide on session timeout duration | `Assumed Complete` | `Deferred to Human` | Specific question asked at message 14: "Should the session timeout be 15 min, 30 min, or 2 hours?" User has not responded. Next step: User answers. Owner: user. |
```

Same rigor as `Blocked — unresolvable`; just a different status label.

## The "trying to resolve" rule

A row stays at `Blocked` (non-terminal) while the agent is still actively trying to resolve it. It transitions to `Blocked — unresolvable` only after the five-check test returns all no, AND the agent has attempted at least one resolution.

"Attempted" means:

- Tried the workaround (step 2 of the five-check)
- Tried to reduce scope (step 3)
- Tried to split the task (step 4)
- Or: the blocker is obviously external (missing credentials from the user) and no attempt would change that

Never mark `Blocked — unresolvable` without at least trying. The audit requires evidence that the blocker really is unresolvable, not just that the agent didn't feel like working on it.

## Chained blockers

If task A is blocked by task B, and task B is also blocked:

- Document A's blocker as "B must complete first"
- Recurse: document B's blocker independently
- Both rows end at their respective `Blocked — unresolvable` states

Do not paper over by marking A as `Implemented`. Chained blockers are real; the documentation must reflect the chain.

## The escalation threshold

If the audit produces more than ~3 `Blocked — unresolvable` rows, something is wrong. Either:

- The audit's scope was too ambitious
- The session lacks resources it should have had
- The user's blockers are clustered and deserve a separate conversation

Surface this in the completion report's intro: "7 blockers remain unresolvable. These cluster around the need for production cluster access — recommend a separate session with the cluster credentials available before resuming."

One or two blockers at the end of an audit are normal. A wall of them is feedback to the user about setup.

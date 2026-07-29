# Parallel evidence lenses

Use parallel agents only when one technical question spans at least three
independent evidence lenses and the final deliverable remains one synthesis.

Do not use this path for a market map, reusable corpus, or five-plus entities;
use `run-deep-research`. Use `run-github-scout` for repository discovery.

## Split by lens

Good splits:

| Lens | Primary source classes |
|---|---|
| Current official behavior | docs, releases, compatibility references |
| Maintainer intent and chronology | issues, PRs, commits, RFCs |
| Security or performance | advisories, fixes, benchmarks, postmortems |
| Production experience | incident reports, migrations, attributed forums |

Avoid one agent per report section, synonymous query cluster, or vendor when the
agents would need the same sources and requirements.

## Researcher brief

Give each agent:

1. the same decision/question and user constraints;
2. one explicit evidence lens;
3. authority classes to prioritize and noise to avoid;
4. checkable evidence requirements;
5. freshness/version bounds;
6. a rule that only verified source quotations are citable;
7. a compact return shape: findings, citations, contradictions, and unresolved
   gaps.

Also require each agent to follow any schema-v2 extraction
`continuation.next_call` exactly in its own conversation/session when its
budget permits, and to return every still-pending source as an unresolved gap.

Let each agent plan only if its lens is itself non-trivial. Known-source lenses
should start with `extract-evidence`; narrow lenses can start with
`web-search`.

## Session isolation

Each agent may have a different MCP transport/conversation scope. Therefore:

- each trace and `review-research` result applies only to that agent;
- never expect one agent's plan/search/extraction events in another agent's
  review;
- do not use review as a shared project database;
- do not hand one agent's extraction continuation to another agent; encrypted
  retrieval checkpoints are scoped to the originating conversation/session;
- require findings and citation records in each agent's returned text;
- the main agent owns cross-lens coverage and stopping.

If several agents share a transport but different conversation metadata, the
server should still isolate them. Treat any unexpected cross-agent history as a
privacy defect, not a convenience.

## Parallel execution

Dispatch genuinely independent lenses together. Within a lens, keep the
adaptive sequence: discover leads, read sources, review after evidence, then
stop or continue.

Do not parallelize dependent rounds. A follow-up query that depends on a term or
version discovered in extraction must wait for that extraction.

## Merge

The main agent reads every researcher return and:

1. deduplicates canonical sources and derivative evidence lineages;
2. maps verified findings back to the original decision requirements;
3. checks authority, freshness, independence, and completeness;
4. reconciles or surfaces cross-lens contradictions;
5. labels inference separately;
6. decides whether a small missing lens needs another call;
7. writes one final answer with one coherent recommendation/diagnosis.

An agent's `ready` verdict means its own retained trace met local checks and
does not prove the combined question is ready. Treat a `ready` return alongside
required pending extraction as inconsistent and preserve the pending gap.
Conversely, one locally blocked lens does not erase strong evidence elsewhere;
preserve the limitation and assess whether it is decision-critical.

## Stop

Stop parallel research when every high/medium decision requirement is answered
or explicitly blocked, no unresolved contradiction can change the answer, and
another lens/round has low expected value. Do not keep agents running merely to
equalize source counts.

# Ticket writer

Publish a deduplicated GitHub issue for the assigned confirmed implementation-bound
defect. You do not triage every raw observation into GitHub, implement code, or
close the issue before independent retest.

## Read / write

Read finding/lineage, verified failure, diagnosis, scope decision, repository
identity, previous issue/PR references, and
[Fixes and delivery](../fixes-and-delivery.md).

Write the assigned issue body and `ticket` draft using
[issue.md](../../assets/templates/issue.md) and
[ticket.yaml](../../assets/templates/ticket.yaml). Create/update only the scoped
GitHub issue after deduplication. Preserve local records as the source of truth.
Use the generated draft's `body_path`, allocated as `companion_paths.body`;
supporting artifacts belong in the task's `artifact_directory`.

## Procedure

1. Verify in-scope `PRODUCT_DEFECT`, confirmed diagnosis, implementation need,
   and the exact authorized GitHub repository. Return other classifications to
   the orchestrator without creating an issue.
   Read the generated tested-project repository binding and pass it explicitly
   to every `gh --repo` call. Do not infer the destination from your shell cwd.
2. Search existing references/issues for the stable campaign/finding dedup marker
   and matching lineage. Reuse an existing issue when it represents this defect.
3. Write an issue that a fresh implementer can use: expected/actual, source/spec/
   round, reproduction, evidence, cause confidence, bounded acceptance criteria,
   blocking edges, and prior attempt/PR history.
4. Publish using a structured body or body file. Keep secrets and large private
   evidence out of public text. Link safe campaign artifacts where available;
   do not invent externally accessible URLs for local files.
5. Record the actual issue URL, dedup marker, body path, and artifacts. Preserve
   lineage; related failing cases may share this one issue.

## Done / blocked / submit

Done means the actual issue exists or a matching issue was reused, its body is
saved, and the ticket draft links it accurately. Submit through the common CLI
protocol. Neutral references keep the issue open pending independent proof.

If GitHub/access is unavailable, preserve the body and report `GITHUB_UNAVAILABLE`
to the orchestrator. Do not put a guessed URL into a required typed field. If the
precondition is absent, state the exact unconfirmed/scope/classification gap and
retain the draft; the controller owns task interruption/recovery.

For retry, inspect the previous publication result before another create call to
avoid duplicates. Read changed diagnosis/scope, remaining lineage allowance, and
existing issue/PR references from generated `prior_context` and effective finding
history. Linked aliases may already have a ticket; preserve those references.

## Model and token guidance

Configure this role per provider to balance turnaround speed, assertion accuracy, and token economics (see [Model selection](../../SKILL.md#model-selection--reasoning-configuration-per-provider)):
- **Anthropic**: Mandate `claude-3-7-sonnet` (or `claude-3-5-sonnet`) with low/minimal reasoning (`budget_tokens: 1024` or disabled). Rapid markdown formatting and CLI issue publication. **Strictly prohibit `claude-3-opus`** to eliminate 5x cost and multi-turn tool latency bottlenecks.
- **OpenAI / Codex**: `gpt-6-luna` with `reasoning_effort: "low"` for fast and economical ticket creation. Avoid `high`/`xhigh`.
- **Gemini**: `gemini-3.8-flash` with `low` reasoning effort for high-throughput GitHub issue writing.


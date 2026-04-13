# No Auto-Answer In `codex-worker`

Older worker CLIs could auto-answer approvals or default the first option in a multiple-choice prompt. `codex-worker` does not expose that behavior as a supported operator feature.

## Current Rule

Every pending request should be answered explicitly through:

```bash
codex-worker request list
codex-worker request read <request-id>
codex-worker request respond <request-id> ...
```

## Approval Example

```bash
codex-worker request respond <request-id> --decision accept-session
```

## Question Example

```bash
codex-worker request respond <request-id> --question-id tone --answer "Direct"
```

## Raw JSON Example

```bash
codex-worker request respond <request-id> --json '{"answers":{"tone":{"answers":["Direct"]}}}'
```

## Practical Implication

If you want unattended orchestration, write clearer prompt files so the worker does not need to ask. Do not rely on a hidden first-choice default.

# Request handling

Use this file when a thread becomes blocked and you need to inspect or answer a runtime request correctly.

## Detect the blocked state

Treat either of these as a blocked run:
- thread status is `waiting_request`
- `request list --status pending` shows a request for that thread

This is not a failure. The runtime is waiting for input.

## Standard loop

```bash
codex-worker request list --status pending
codex-worker request read <request-id>
codex-worker request respond <request-id> ...
codex-worker wait --thread-id <thread-id> --timeout 300000
```

## Supported response shapes

Approval-style response:

```bash
codex-worker request respond <request-id> --decision accept
codex-worker request respond <request-id> --decision deny
```

Text answer:

```bash
codex-worker request respond <request-id> --answer "Yes" --question-id <id>
```

Raw escape hatch:

```bash
codex-worker request respond <request-id> --json '{"result":{"approved":true}}'
```

## Rules

1. Always inspect the request before responding.
2. Prefer the smallest specific flag that matches the request shape.
3. Use `--json` only after reading the request payload and deciding the exact response.
4. Resume monitoring after every response; one run can block more than once.

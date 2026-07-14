# launch-derailment.sh

Render or run the derailment subagent prompt for an existing skill.

## Usage

```bash
bash scripts/launch-derailment.sh \
  --skill-path /path/to/skill \
  --task "Use the skill on this realistic user task"
```

Required arguments:

- `--skill-path PATH` — directory containing `SKILL.md`
- `--task TEXT` — real user-style task for the subagent

Optional arguments:

- `--round N` — round label for the next-step instruction, default `1`
- `--trace-out PATH` — file to tee agent output into when `--agent-cmd` is used
- `--agent-cmd CMD` — runtime command that reads the prompt from stdin

`DERAILMENT_AGENT_CMD` can provide the command instead of `--agent-cmd`.

## Examples

Render the prompt only:

```bash
bash scripts/launch-derailment.sh \
  --skill-path ./skills/example-skill \
  --task "Turn this saved API response into a typed client helper"
```

Run through a runtime command and save the trace:

```bash
bash scripts/launch-derailment.sh \
  --skill-path ./skills/example-skill \
  --task "Turn this saved API response into a typed client helper" \
  --trace-out /tmp/derailment-round-1.jsonl \
  --agent-cmd "your-agent-command --jsonl"
```

Runtime-specific commands are examples only. If no command is configured, copy
the rendered prompt into a fresh capable subagent and save the transcript or
JSONL trace yourself.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Prompt rendered or agent command completed |
| `2` | Missing or invalid arguments, empty task, or missing `SKILL.md` |
| `3` | `--trace-out` directory or file is not writable |
| `4` | Agent command exited nonzero |

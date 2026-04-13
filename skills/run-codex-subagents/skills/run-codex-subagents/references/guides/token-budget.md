# Token Budget

The Codex agent operates within a model-dependent context window (currently ~258,400 tokens for gpt-5.x models). Understanding how tokens are consumed prevents avoidable failures.

## What Consumes Tokens

### Input side (loaded before the agent starts thinking)

| Source | Typical size | Notes |
|---|---|---|
| System prompt + model overhead | ~2-3K | Fixed cost, unavoidable |
| `developer_instructions` | varies | Injected before user prompt |
| `context_files` content | varies | Each file's full text is prepended |
| AGENTS.md (if present in cwd) | varies | Auto-loaded by Codex CLI |
| Your `prompt` text | varies | The mission brief |

### Output side (consumed during execution)

| Source | Typical size | Notes |
|---|---|---|
| Reasoning tokens | varies by level | Invisible but counted against window |
| Agent messages | small | Thinking-out-loud text |
| Tool calls + results | varies | File reads, command output |
| File writes | varies | Full file content in tool results |

## Real-World Token Usage

Data from observed tasks:

| Task complexity | Tokens used | % of window | Outcome |
|---|---|---|---|
| Single command (`wc -l`, `grep`) | ~8-15K | 0.8-1.5% | Completes reliably |
| Simple file creation (1 file) | ~12-20K | 1.2-2% | Completes reliably |
| Multi-step coding (2-4 files) | ~30-60K | 3-6% | Usually completes |
| Complex refactoring (5+ files) | ~60-110K | 6-11% | Sometimes fails |
| Deep research (many file reads) | ~40-80K | 4-8% | Usually completes |

## The 6-8% Death Zone

Tasks that fail often show a pattern: they die at 6-8% token usage. This is NOT a budget issue — 92% of the window remains unused. What happens:

1. The Codex CLI process exits (signal, OOM, timeout, or internal error)
2. The agent was mid-execution when the process died
3. Token consumption at death is low because the agent didn't get to finish

**This means:** Don't try to "optimize" token usage by shortening prompts or reducing context. The failures aren't caused by running out of tokens. They're caused by process instability under higher reasoning modes.

## What Actually Matters

### Reasoning level is the dominant factor

| Reasoning | Token overhead | Process stability |
|---|---|---|
| `low` | Minimal reasoning tokens | Very stable |
| `medium` | Moderate reasoning tokens | Moderately stable |
| `high` | Heavy reasoning tokens | Less stable |
| `xhigh` | Maximum reasoning tokens | Untested |

Higher reasoning = more internal computation = longer execution = higher chance of process exit. The tokens themselves aren't the problem; the execution time and complexity are.

### Task simplicity beats token optimization

**Instead of:** Cramming 5 steps into one task to "save tokens"
**Do:** Split into 5 simple tasks at `low` reasoning

Five tasks at 15K each (75K total) will complete far more reliably than one task at 60K that has a 40% failure rate.

## Context Files Budget

The `context_files` parameter prepends file content before the prompt. Budget guidelines:

| Files | Combined lines | Risk |
|---|---|---|
| 1-3 small files (<100 lines each) | <300 | Safe |
| 3-5 medium files (<300 lines each) | <1500 | Fine for most tasks |
| 5+ files or large files | >1500 | May crowd out working memory |
| Entire codebase | thousands | Never do this |

If the agent needs to read many files, let it use its own file-read tools. Don't preload everything via context_files.

## Developer Instructions Budget

Keep `developer_instructions` under 500 tokens (~400 words). This text is injected as a system message and consumes input budget on every turn. Long instructions waste tokens on every reasoning cycle.

Good: "Follow Swift naming conventions. Do not modify any file outside FastNotch/Views/."
Bad: [3 pages of coding standards pasted inline]

## Monitoring Token Usage

The timeline shows token consumption:
```
14:32:15 TOKENS {"threadId":"...","tokenUsage":{"total":{"totalTokens":45231},"modelContextWindow":258400}}
```

`task read` or `task events` output includes:
```json
{
  "token_usage": {
    "input_tokens": 32100,
    "output_tokens": 13131,
    "total_tokens": 45231,
    "pct_used": "4.5%"
  }
}
```

## Rules of Thumb

1. **Don't optimize for tokens. Optimize for task simplicity.**
2. Default to `low` reasoning. Only go higher when the task genuinely requires planning.
3. Split complex work into multiple simple tasks rather than one complex task.
4. Use `context_files` sparingly — 5 files max, each under 500 lines.
5. Keep `developer_instructions` short and actionable.
6. When a task fails at 6-8% usage, the fix is simpler tasks, not fewer tokens.

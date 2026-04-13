# Quick Diagnostic Template

Use this for one-command probes that should not modify files.

```markdown
## Context

One sentence on why you need the check.

## Mission

Run exactly one command and report the result.

## Command

`npm test -- --runInBand`

## Output Requirement

If the command fails, report the exact error lines and exit status.
If it succeeds, report the key success line and exit status.
```

Good fits:
- one build command
- one test command
- one grep or rg query
- one version or environment check

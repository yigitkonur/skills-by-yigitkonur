# Dependencies And Portability

Use this file when the command depends on external tools, packages, or machine-specific setup.

## Document Dependencies

Put dependency notes at the top of the script when needed.

Examples:

```python
# Dependency: This script requires the following Python libraries: `requests`
# Install them with `pip install requests`
```

```bash
# Dependency: This script requires `jq`
# Install via Homebrew: `brew install jq`
```

## Handle Missing Dependencies

Do not fail mysteriously. Print a readable error and exit non-zero.

```bash
command -v jq >/dev/null 2>&1 || { echo "jq is required"; exit 1; }
```

## Shell Environment Rules

Raycast's official docs say Script Commands run in a non-login shell, and the community repo does not accept scripts that rely on login-shell behavior for portability reasons.

The README also notes Raycast appends `/usr/local/bin` to `PATH`.

Implications:

- do not assume shell startup files ran
- document any required runtime or binary explicitly
- prefer explicit setup over hidden environment magic

## Portability checklist

- avoid unnecessary dependencies
- prefer standard library / built-in tools where reasonable
- handle missing tools with readable failures
- avoid hidden reliance on login-shell configuration

## Common mistakes

| Mistake | Fix |
|---|---|
| assuming Homebrew, Python packages, or auth tokens are already installed | document the dependency and setup |
| requiring a shell profile side effect without saying so | make the setup explicit |
| failing with a raw traceback or command-not-found noise | print a user-readable message first |

# Python Implementation Patterns

Use this file when writing Python logic inside a Script Command.

## Patterns Worth Reusing

### Safe optional args

```python
import sys

def arg(index: int, default: str = "") -> str:
    return sys.argv[index] if len(sys.argv) > index else default
```

### Human-readable failure

```python
if not token:
    print("Command not configured correctly. Missing variable: API_TOKEN")
    raise SystemExit(1)
```

### Dependency note header

```python
# Dependency: This script requires the following Python libraries: `requests`
# Install them with `pip install requests`
```

### Compact/silent success

```python
print("Created card successfully")
```

### Full-output report

```python
print("Report for today")
print()
print("- item one")
print("- item two")
```

## Python-specific Guidance

- Use `print()` for user-facing output.
- Keep the final printed line readable because Raycast may surface only that line.
- Prefer standard library where practical for portability.
- Document third-party packages explicitly when they are required.

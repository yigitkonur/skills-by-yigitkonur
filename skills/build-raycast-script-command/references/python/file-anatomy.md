# Python File Anatomy

Use this file when building or checking a Python Script Command file.

## Canonical Shape

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title My Command
# @raycast.mode fullOutput
# @raycast.packageName Raycast Scripts

print("Hello World!")
```

## Structure Rules

1. Use `#!/usr/bin/env python3`.
2. Put metadata immediately below the shebang.
3. Use `# @raycast.*` comments.
4. Add dependency notes before the metadata only when needed.
5. Keep the first runnable code below the metadata block.

## Helpful Sections

The official template uses these labels:

- `# Required parameters:`
- `# Optional parameters:`
- `# Documentation:`

They are helpful but not the key requirement. The important part is the actual `# @raycast.*` lines.

## Safe Minimal Skeleton

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example
# @raycast.mode compact
# @raycast.packageName Examples

import sys

print(sys.argv[1] if len(sys.argv) > 1 else "No input")
```

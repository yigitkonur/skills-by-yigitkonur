# Python Recipes

Use this file when you want concrete Python patterns to adapt quickly.

## Recipe 1: Full-output report

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Example Report
# @raycast.mode fullOutput
# @raycast.packageName Examples

print("Daily Summary")
print()
print("- item one")
print("- item two")
```

## Recipe 2: Compact or silent action

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Create Card
# @raycast.mode compact
# @raycast.packageName Examples

success = True
if not success:
    print("Failed to create card")
    raise SystemExit(1)

print("Created card successfully")
```

Use the same one-line final output shape for `silent` actions. Pick `compact` when the user should see a toast; pick `silent` when the action should stay quiet unless the final line matters.

## Recipe 3: Inline status

```python
#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title Service Status
# @raycast.mode inline
# @raycast.refreshTime 5m
# @raycast.packageName Examples

print("API ok")
```

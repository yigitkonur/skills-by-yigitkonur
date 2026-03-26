# Required Fields

Use this file when adding or checking Raycast metadata.

## Required

Raycast's official Script Commands README documents these required fields:

| Field | Meaning |
|---|---|
| `schemaVersion` | metadata schema version, currently `1` |
| `title` | command title shown in Raycast |
| `mode` | output behavior: `fullOutput`, `compact`, `silent`, or `inline` |

## Example

```python
# @raycast.schemaVersion 1
# @raycast.title Wikipedia Search
# @raycast.mode fullOutput
```

## Important Optional Fields

These are optional at runtime but often useful:

| Field | Use |
|---|---|
| `packageName` | subtitle/package label |
| `icon` | emoji or image |
| `iconDark` | alternate dark-theme icon |
| `currentDirectoryPath` | execution working directory |
| `needsConfirmation` | prompt before running |
| `refreshTime` | required companion for `inline` |
| `author`, `authorURL`, `description` | helpful for shared commands |

## Community Repo Nuance

In the Raycast community repo:

- `packageName` is treated as required by contribution policy
- titles should use title case

Do not confuse that repo policy with runtime requirements.

## Placement Rule

For Python and Bash, metadata should live directly below the shebang and use `#` comments.

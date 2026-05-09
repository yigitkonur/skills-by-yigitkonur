# Typed Arguments

Use this file when adding or repairing Script Command inputs.

## Current Limits

Raycast Script Commands support up to three typed arguments:

- `@raycast.argument1`
- `@raycast.argument2`
- `@raycast.argument3`

## JSON Fields

Per Raycast's `ARGUMENTS.md`:

| Field | Meaning | Required |
|---|---|---|
| `type` | `"text"`, `"password"`, or `"dropdown"` | yes |
| `placeholder` | input hint shown in Raycast | yes |
| `optional` | argument may be empty | no |
| `percentEncoded` | Raycast percent-encodes the value before passing it | no |
| `data` | dropdown choices with `title` and `value` | required for dropdown |
| `secure` | deprecated older flag | no |

## Python Mapping

Raycast passes arguments positionally:

- `argument1` -> `sys.argv[1]`
- `argument2` -> `sys.argv[2]`
- `argument3` -> `sys.argv[3]`

Guard optional access:

```python
def arg(index: int, default: str = "") -> str:
    return sys.argv[index] if len(sys.argv) > index else default
```

## Bash Mapping

In Bash:

- `argument1` -> `$1`
- `argument2` -> `$2`
- `argument3` -> `$3`

Guard optional access with parameter expansion:

```bash
query="${1:-}"
lang="${2:-en}"
```

## Good Example

```python
# @raycast.argument1 { "type": "text", "placeholder": "Query", "percentEncoded": true }
# @raycast.argument2 { "type": "dropdown", "placeholder": "Scope", "data": [{"title": "Docs", "value": "docs"}, {"title": "Issues", "value": "issues"}] }
```

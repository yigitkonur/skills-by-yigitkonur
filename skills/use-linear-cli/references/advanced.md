# Advanced — Raw GraphQL and Documents

The escape hatch when no `linear-cli` subcommand fits, plus Linear's `Document` model for long-form content.

## Raw GraphQL (`api`)

```bash
linear-cli api query '{ viewer { id name email } }'
linear-cli api query -v teamId=abc 'query($teamId: String!) { team(id: $teamId) { name } }'

linear-cli api mutate -v title="Bug" '
  mutation($title: String!) {
    issueCreate(input: { title: $title, teamId: "TEAM_UUID" }) {
      issue { id identifier }
    }
  }
'

cat query.graphql | linear-cli api query -
```

| Flag | Meaning |
|---|---|
| `-v key=val` | GraphQL variable (repeatable) |
| `--output json` | JSON output |
| `--compact` | Compact JSON |
| `-` | Read query/mutation body from stdin |

### When to reach for `api`

Use the raw GraphQL surface when:

- you need a field that no `linear-cli` subcommand exposes (inspect the target GraphQL schema first)
- you're prototyping an integration before a built-in command exists
- you need to batch a complex multi-resource fetch in one round-trip
- you need to set fields that `--data -` doesn't expose

Otherwise, prefer the typed subcommand — it handles auth, retries, error envelopes, and pagination for you.

### Schema discovery

```bash
linear-cli api query '{ __schema { queryType { name } } }'
linear-cli api query '{ __type(name: "Issue") { fields { name type { name } } } }'
```

The upstream `docs/json/schema.json` describes CLI output schema metadata, not the Linear GraphQL schema. Use GraphQL introspection for API fields.

### Variables vs string interpolation

Always pass user-provided values via `-v` rather than splicing into the query body:

```bash
# Good
linear-cli api query -v id="$ISSUE_ID" 'query($id: String!) { issue(id: $id) { title } }'

# Bad — quoting hazards, GraphQL injection risk
linear-cli api query "{ issue(id: \"$ISSUE_ID\") { title } }"
```

### Sample mutation — create an issue with full control

```bash
linear-cli api mutate \
  -v title="Bug from agent" \
  -v teamId="$TEAM_UUID" \
  -v priority=1 \
  -v labelIds='["LABEL_UUID_1","LABEL_UUID_2"]' '
  mutation($title: String!, $teamId: String!, $priority: Int, $labelIds: [String!]) {
    issueCreate(input: {
      title: $title
      teamId: $teamId
      priority: $priority
      labelIds: $labelIds
    }) {
      success
      issue { id identifier title }
    }
  }
'
```

`-v` values that look like JSON (arrays, objects, numbers, booleans) are decoded; quoted strings stay strings.

## Raw-query pagination

Global `--all` alone does not paginate arbitrary GraphQL. Use `api query --paginate --nodes-path data.issues.nodes --page-info-path data.issues.pageInfo` with a query that declares `$first: Int` and `$after: String`, passes them to the connection, and requests `pageInfo { hasNextPage endCursor }`. In 0.3.28 this returns a collected array of nodes rather than the raw response wrapper.

The query handler can send a mutation document when dry-run is absent. Inspect the document itself before treating any raw API command as read-only. Mutation dry-run is not a supported write-permission test.

## Documents

Linear `Document`s are long-form pages attached to projects (RFCs, ADRs, plans). Different from issue descriptions and from project updates.

```bash
linear-cli d list
linear-cli d list --output json
linear-cli d get DOC_ID
linear-cli d get DOC_ID --output json

linear-cli d create "Design Doc" -p PROJECT_ID
linear-cli d create "RFC" -p PROJECT_ID --output json

linear-cli d update DOC_ID --title "New Title"
linear-cli d update DOC_ID --content "New content"
```

| Flag | Meaning |
|---|---|
| `-p PROJECT` | Project UUID (or name) |
| `--title` | Document title |
| `--content` | Markdown body |
| `--output json` + `jq -er .id` | Capture the new document ID; `--id-only` is not implemented by this handler. |
| `--output json` | JSON output |

0.3.28 also exposes `d delete DOC_ID --force`; inspect `d delete --help` and confirm the specific document before deletion.

## Recipe: post an ADR as a Linear document

```bash
PROJ=PROJECT_UUID
ID=$(linear-cli d create "ADR-2026-04-28: Drop polling for webhooks" \
  -p "$PROJ" --output json | jq -er .id) || exit 1
linear-cli d update "$ID" --content "$(cat adr.md)"
```

## Recipe: query one page of blocking relations

This example fetches at most 100 relations; it is not an exhaustive workspace scan. For complete traversal, include `pageInfo` and use the pagination options below.

```bash
linear-cli api query '
  query {
    issueRelations(filter: { type: { eq: "blocks" } }, first: 100) {
      nodes {
        type
        issue { identifier title }
        relatedIssue { identifier title }
      }
    }
  }
' --compact
```

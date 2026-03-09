# Resources Reference

Resources provide read-only data that LLMs can access. Use resources for configuration, documents, database records, and any data the LLM needs to read.

## Static Resource

A resource at a fixed URI:

```typescript
server.registerResource(
  'app-config',
  'config://app',
  {
    title: 'Application Configuration',
    description: 'Current application settings',
    mimeType: 'application/json',
  },
  async (uri) => ({
    contents: [{
      uri: uri.href,
      text: JSON.stringify(getConfig()),
      mimeType: 'application/json',
    }],
  })
);
```

## Dynamic Resource with URI Template

Use `ResourceTemplate` for parameterized URIs:

```typescript
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
  'user-profile',
  new ResourceTemplate('user://{userId}/profile', {
    list: async () => ({
      resources: (await getUsers()).map(u => ({
        uri: `user://${u.id}/profile`,
        name: u.displayName,
      })),
    }),
  }),
  {
    title: 'User Profile',
    description: 'User profile data by ID',
    mimeType: 'application/json',
  },
  async (uri, { userId }) => ({
    contents: [{
      uri: uri.href,
      text: JSON.stringify(await getUserById(userId)),
    }],
  })
);
```

## Resource with Completions

Enable autocompletion on URI template parameters:

```typescript
import { ResourceTemplate, completable } from '@modelcontextprotocol/server';

server.registerResource(
  'document',
  new ResourceTemplate('docs://{docId}', {
    list: async () => ({
      resources: (await listDocs()).map(d => ({
        uri: `docs://${d.id}`,
        name: d.title,
      })),
    }),
    complete: {
      docId: async (value) => {
        const docs = await searchDocs(value);
        return docs.map(d => d.id);
      },
    },
  }),
  { title: 'Document', mimeType: 'text/markdown' },
  async (uri, { docId }) => ({
    contents: [{ uri: uri.href, text: await getDocContent(docId) }],
  })
);
```

## Binary Resources

Return binary data (images, PDFs) using base64:

```typescript
import * as fs from 'node:fs/promises';

server.registerResource(
  'logo',
  'assets://logo.png',
  { title: 'Company Logo', mimeType: 'image/png' },
  async (uri) => {
    const buffer = await fs.readFile('./assets/logo.png');
    return {
      contents: [{
        uri: uri.href,
        blob: buffer.toString('base64'),
        mimeType: 'image/png',
      }],
    };
  }
);
```

## Dynamic Management

Resources can be updated or removed at runtime:

```typescript
const resource = server.registerResource('config', 'config://app', {}, callback);

// Update
resource.update({
  metadata: { title: 'Updated Config' },
  callback: newCallback,
});

// Remove
resource.remove();
```

## URI Scheme Conventions

| Scheme | Use For | Example |
|--------|---------|---------|
| `file://` | Filesystem paths | `file:///docs/readme.md` |
| `config://` | Configuration | `config://app` |
| `data://` | Application data | `data://users/123` |
| `api://` | API endpoints | `api://github/repos` |
| `user://` | User-specific data | `user://{userId}/profile` |

## Best Practices

1. Always include `mimeType` when known
2. Use `list` callback on templates so clients can discover available resources
3. Limit response sizes — LLMs have context limits
4. Return `text` for text content, `blob` (base64) for binary
5. Include a `description` on the metadata for better discovery

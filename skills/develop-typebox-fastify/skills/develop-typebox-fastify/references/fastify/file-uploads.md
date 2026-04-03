# Fastify File Uploads

## @fastify/multipart Setup

```typescript
import Fastify from 'fastify'
import fastifyMultipart from '@fastify/multipart'
import { Type } from '@sinclair/typebox'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

app.register(fastifyMultipart, {
  // CRITICAL: Always set explicit limits
  limits: {
    fieldNameSize: 100,
    fieldSize: 1024 * 1024,        // 1MB field value
    fields: 10,                     // max non-file fields
    fileSize: 10 * 1024 * 1024,    // 10MB per file
    files: 5,                       // max files
    headerPairs: 2000,
    parts: 1000,
  },
  // IMPORTANT: Throw on limit exceeded (default truncates silently!)
  throwFileSizeLimit: true,
})
```

## Single File Upload

```typescript
app.post('/upload', {
  schema: {
    response: {
      200: Type.Object({
        filename: Type.String(),
        mimetype: Type.String(),
        size: Type.Integer(),
      }),
    },
  },
}, async (request, reply) => {
  const data = await request.file()

  if (!data) {
    return reply.code(400).send({ error: 'No file uploaded' })
  }

  // data.file is a stream
  const buffer = await data.toBuffer()

  return {
    filename: data.filename,
    mimetype: data.mimetype,
    size: buffer.length,
  }
})
```

## Multiple File Upload

```typescript
app.post('/upload-multiple', {
  schema: {
    response: {
      200: Type.Object({
        files: Type.Array(Type.Object({
          filename: Type.String(),
          mimetype: Type.String(),
          size: Type.Integer(),
        })),
      }),
    },
  },
}, async (request) => {
  const files = []

  for await (const part of request.files()) {
    const buffer = await part.toBuffer()
    files.push({
      filename: part.filename,
      mimetype: part.mimetype,
      size: buffer.length,
    })
  }

  return { files }
})
```

## Mixed Form Data (Files + Fields)

```typescript
app.post('/form', {
  schema: {
    response: {
      200: Type.Object({
        fields: Type.Record(Type.String(), Type.String()),
        files: Type.Array(Type.Object({ name: Type.String(), size: Type.Integer() })),
      }),
    },
  },
}, async (request) => {
  const parts = request.parts()
  const fields: Record<string, string> = {}
  const files: Array<{ name: string; size: number }> = []

  for await (const part of parts) {
    if (part.type === 'file') {
      const buffer = await part.toBuffer()
      files.push({ name: part.filename, size: buffer.length })
    } else {
      fields[part.fieldname] = part.value as string
    }
  }

  return { fields, files }
})
```

## File Type Validation

```typescript
const ALLOWED_MIMETYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/webp',
  'application/pdf',
])

app.post('/upload-validated', async (request, reply) => {
  const data = await request.file()

  if (!data) {
    return reply.code(400).send({ error: 'No file uploaded' })
  }

  if (!ALLOWED_MIMETYPES.has(data.mimetype)) {
    return reply.code(400).send({
      error: 'Invalid file type',
      allowed: [...ALLOWED_MIMETYPES],
    })
  }

  const buffer = await data.toBuffer()

  // Optionally verify by reading file magic bytes
  if (data.mimetype.startsWith('image/')) {
    const header = buffer.subarray(0, 4)
    const isJpeg = header[0] === 0xFF && header[1] === 0xD8
    const isPng = header[0] === 0x89 && header[1] === 0x50
    if (!isJpeg && !isPng) {
      return reply.code(400).send({ error: 'File content does not match declared type' })
    }
  }

  return { filename: data.filename, size: buffer.length }
})
```

## Stream to Disk

```typescript
import { createWriteStream } from 'node:fs'
import { pipeline } from 'node:stream/promises'
import { join } from 'node:path'
import { randomUUID } from 'node:crypto'

app.post('/upload-stream', async (request, reply) => {
  const data = await request.file()
  if (!data) return reply.code(400).send({ error: 'No file' })

  const ext = data.filename.split('.').pop()
  const storedName = `${randomUUID()}.${ext}`
  const dest = join(import.meta.dirname, '..', 'uploads', storedName)

  await pipeline(data.file, createWriteStream(dest))

  return { storedName, originalName: data.filename }
})
```

## Stream to Cloud Storage (S3)

```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3'
import { Upload } from '@aws-sdk/lib-storage'

const s3 = new S3Client({ region: process.env.AWS_REGION })

app.post('/upload-s3', {
  schema: {
    response: {
      200: Type.Object({
        key: Type.String(),
        url: Type.String(),
      }),
    },
  },
}, async (request, reply) => {
  const data = await request.file()
  if (!data) return reply.code(400).send({ error: 'No file' })

  const key = `uploads/${randomUUID()}/${data.filename}`

  const upload = new Upload({
    client: s3,
    params: {
      Bucket: process.env.S3_BUCKET,
      Key: key,
      Body: data.file,
      ContentType: data.mimetype,
    },
  })

  await upload.done()

  return {
    key,
    url: `https://${process.env.S3_BUCKET}.s3.amazonaws.com/${key}`,
  }
})
```

## Attach Fields to Body

```typescript
app.register(fastifyMultipart, {
  attachFieldsToBody: true,
  limits: { fileSize: 10 * 1024 * 1024, files: 5 },
  throwFileSizeLimit: true,
})

// Now fields and files are on request.body
app.post('/profile', async (request) => {
  const { name, avatar } = request.body as {
    name: { value: string }
    avatar: { toBuffer: () => Promise<Buffer>; filename: string; mimetype: string }
  }

  const buffer = await avatar.toBuffer()
  return {
    name: name.value,
    avatarSize: buffer.length,
    avatarName: avatar.filename,
  }
})
```

## Binary/Octet-Stream Upload

```typescript
import { pipeline } from 'node:stream/promises'
import { createWriteStream } from 'node:fs'

app.addContentTypeParser('application/octet-stream', async (request, payload) => payload)

app.post('/upload-binary', async (request, reply) => {
  const dest = createWriteStream(`./upload-${Date.now()}.bin`)
  await pipeline(request.body, dest)
  return { success: true }
})
```

## Testing File Uploads

```typescript
import { createReadStream } from 'node:fs'
import FormData from 'form-data'

it('should upload file', async (t) => {
  const form = new FormData()
  form.append('file', createReadStream('./test/fixtures/test.pdf'))
  form.append('name', 'test-document')

  const response = await app.inject({
    method: 'POST',
    url: '/upload',
    payload: form,
    headers: form.getHeaders(),
  })

  t.assert.equal(response.statusCode, 200)
  t.assert.ok(response.json().filename)
})
```

## Key Rules

- Always set explicit `limits` (especially `fileSize` and `files`)
- Enable `throwFileSizeLimit: true` (default silently truncates!)
- Validate file MIME types and optionally magic bytes
- Prefer streaming to disk/S3 for large files (avoid buffering)
- Use `pipeline()` for proper stream error handling

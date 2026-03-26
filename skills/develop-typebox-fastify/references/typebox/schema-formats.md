# TypeBox Schema Formats

## Built-in String Formats

TypeBox supports standard JSON Schema format annotations. Fastify (via Ajv) validates these when `ajvFormats` is configured.

```typescript
import { Type } from 'typebox'

// Date and time
Type.String({ format: 'date-time' })   // "2024-01-15T10:30:00Z"
Type.String({ format: 'date' })         // "2024-01-15"
Type.String({ format: 'time' })         // "10:30:00"
Type.String({ format: 'duration' })     // "P1DT12H" (ISO 8601 duration)

// Internet
Type.String({ format: 'email' })        // "user@example.com"
Type.String({ format: 'idn-email' })    // internationalized email
Type.String({ format: 'hostname' })     // "example.com"
Type.String({ format: 'idn-hostname' }) // internationalized hostname
Type.String({ format: 'uri' })          // "https://example.com/path"
Type.String({ format: 'uri-reference' })// "/path/to/resource"
Type.String({ format: 'uri-template' }) // "/users/{id}"
Type.String({ format: 'iri' })          // internationalized URI
Type.String({ format: 'iri-reference' })

// Network
Type.String({ format: 'ipv4' })         // "192.168.1.1"
Type.String({ format: 'ipv6' })         // "::1"

// Other
Type.String({ format: 'uuid' })         // "550e8400-e29b-41d4-a716-446655440000"
Type.String({ format: 'json-pointer' }) // "/foo/bar/0"
Type.String({ format: 'relative-json-pointer' }) // "1/foo"
Type.String({ format: 'regex' })        // valid regex pattern
```

## Enabling Format Validation in Fastify

Ajv does NOT validate formats by default. You need `ajv-formats`:

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

const fastify = Fastify({
  ajv: {
    plugins: [
      // This enables all built-in format validators
      require('ajv-formats'),
    ],
  },
}).withTypeProvider<TypeBoxTypeProvider>()
```

Or with selective formats:

```typescript
import Fastify from 'fastify'
import ajvFormats from 'ajv-formats'

const fastify = Fastify({
  ajv: {
    plugins: [
      [ajvFormats, { mode: 'fast', formats: ['date-time', 'email', 'uri', 'uuid'] }],
    ],
  },
})
```

## Custom Formats

Register custom formats via Ajv's `addFormat`:

```typescript
import Fastify from 'fastify'

const fastify = Fastify({
  ajv: {
    customOptions: {
      formats: {
        // Simple regex-based format
        'phone': /^\+?[1-9]\d{1,14}$/,

        // Function-based format with validation logic
        'iso-country': {
          type: 'string',
          validate: (value: string) => /^[A-Z]{2}$/.test(value),
        },

        // Async format (rarely needed)
        'unique-email': {
          type: 'string',
          async: true,
          validate: async (value: string) => {
            // check database
            return true
          },
        },
      },
    },
  },
})

// Now use in schemas
const PhoneSchema = Type.String({ format: 'phone' })
const CountrySchema = Type.String({ format: 'iso-country' })
```

## Adding Formats After Fastify Init

```typescript
// Access the Ajv instance after Fastify initializes
fastify.after(() => {
  // For request body/headers validation
  fastify.server // not directly accessible

  // Better: use the plugin approach
})

// Or use a plugin pattern
import fp from 'fastify-plugin'

export default fp(async function customFormats(fastify) {
  fastify.ajv.customOptions.formats = {
    ...fastify.ajv.customOptions.formats,
    'slug': /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
    'hex-color': /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/,
  }
})
```

## Pattern Alternative to Formats

If you don't want to register custom formats, use `pattern` directly:

```typescript
// These work without ajv-formats
const PhoneSchema = Type.String({
  pattern: '^\\+?[1-9]\\d{1,14}$',
  description: 'E.164 phone number',
})

const SlugSchema = Type.String({
  pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$',
  description: 'URL-friendly slug',
})

const HexColor = Type.String({
  pattern: '^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$',
})

const SemVer = Type.String({
  pattern: '^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9.]+)?(\\+[a-zA-Z0-9.]+)?$',
})
```

## FormatRegistry — TypeBox's Format System

TypeBox has its own format registry for use with `Value.Check`:

```typescript
import { FormatRegistry, Value, Type } from 'typebox'

// Register a format with TypeBox's own registry
FormatRegistry.Set('phone', (value) => /^\+?[1-9]\d{1,14}$/.test(value))
FormatRegistry.Set('slug', (value) => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value))

const PhoneSchema = Type.String({ format: 'phone' })

// Now Value.Check respects the format
Value.Check(PhoneSchema, '+14155551234') // true
Value.Check(PhoneSchema, 'not-a-phone')  // false

// Check if a format is registered
FormatRegistry.Has('phone') // true

// Remove a format
FormatRegistry.Delete('phone')

// Clear all custom formats
FormatRegistry.Clear()
```

## Common Format Patterns for APIs

```typescript
// Reusable format-based schemas
export const Formats = {
  uuid: Type.String({ format: 'uuid' }),
  email: Type.String({ format: 'email' }),
  uri: Type.String({ format: 'uri' }),
  dateTime: Type.String({ format: 'date-time' }),
  date: Type.String({ format: 'date' }),
  ipv4: Type.String({ format: 'ipv4' }),

  // Pattern-based (no ajv-formats needed)
  phone: Type.String({ pattern: '^\\+?[1-9]\\d{1,14}$' }),
  slug: Type.String({ pattern: '^[a-z0-9]+(?:-[a-z0-9]+)*$' }),
  hex: Type.String({ pattern: '^[0-9a-fA-F]+$' }),
  jwt: Type.String({ pattern: '^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$' }),
} as const

// Usage
const UserSchema = Type.Object({
  id: Formats.uuid,
  email: Formats.email,
  phone: Formats.phone,
  website: Formats.uri,
  createdAt: Formats.dateTime,
})
```

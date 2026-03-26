# TypeBox Date Handling

## The Challenge

JSON has no native Date type. Dates are transmitted as strings (usually ISO 8601). TypeBox schemas validate the string format; your application may need actual `Date` objects.

## ISO 8601 Date-Time Strings

```typescript
import { Type, type Static } from 'typebox'

// Full date-time with timezone
const DateTimeField = Type.String({ format: 'date-time' })
// Validates: "2024-01-15T10:30:00Z", "2024-01-15T10:30:00+05:30"

// Date only (no time)
const DateField = Type.String({ format: 'date' })
// Validates: "2024-01-15"

// Time only (no date)
const TimeField = Type.String({ format: 'time' })
// Validates: "10:30:00", "10:30:00Z"
```

> **Requires `ajv-formats`** for Fastify validation. See schema-formats.md.

## Basic Pattern: Keep as Strings

The simplest approach — store and transmit dates as ISO strings:

```typescript
const EventSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  startsAt: Type.String({ format: 'date-time' }),
  endsAt: Type.String({ format: 'date-time' }),
  createdAt: Type.String({ format: 'date-time' }),
})
type Event = Static<typeof EventSchema>
// All date fields are `string`

// Parse to Date only when needed in business logic
function getEventDuration(event: Event): number {
  const start = new Date(event.startsAt)
  const end = new Date(event.endsAt)
  return end.getTime() - start.getTime()
}
```

## Transform Pattern: Auto-convert to Date Objects

Use Transform schemas to automatically convert between string and Date:

```typescript
import { Type, type StaticDecode, type StaticEncode } from 'typebox'
import { Value } from 'typebox/value'

// Reusable date transform
const DateType = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(value => new Date(value))       // string → Date (when reading)
  .Encode(value => value.toISOString())    // Date → string (when writing)

// Use in schemas
const EventSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  startsAt: DateType,
  endsAt: DateType,
  createdAt: DateType,
})

// Wire format (JSON) — all strings
type EventWire = StaticEncode<typeof EventSchema>
// { id: string; name: string; startsAt: string; endsAt: string; createdAt: string }

// Application format — Date objects
type EventApp = StaticDecode<typeof EventSchema>
// { id: string; name: string; startsAt: Date; endsAt: Date; createdAt: Date }

// Decode from JSON
const event = Value.Decode(EventSchema, {
  id: '...',
  name: 'Launch Party',
  startsAt: '2024-06-15T18:00:00Z',
  endsAt: '2024-06-15T22:00:00Z',
  createdAt: '2024-01-15T10:30:00Z',
})
// event.startsAt instanceof Date → true

// Encode back to JSON
const wire = Value.Encode(EventSchema, event)
// wire.startsAt === '2024-06-15T18:00:00.000Z'
```

## Using Date Transform with Fastify

Fastify validates the wire format (string). You decode in the handler:

```typescript
import { TypeCompiler } from 'typebox/compiler'

const CreateEventBody = Type.Object({
  name: Type.String({ minLength: 1 }),
  startsAt: DateType,
  endsAt: DateType,
})

const compiledBody = TypeCompiler.Compile(CreateEventBody)

fastify.post('/events', {
  schema: {
    // Fastify sees { name: string, startsAt: string(date-time), endsAt: string(date-time) }
    body: CreateEventBody,
  },
}, async (request) => {
  // Fastify validated the strings. Now decode to get Date objects.
  const body = compiledBody.Decode(request.body)
  // body.startsAt instanceof Date → true
  // body.endsAt instanceof Date → true

  if (body.endsAt <= body.startsAt) {
    throw fastify.httpErrors.badRequest('End time must be after start time')
  }

  return createEvent(body)
})
```

## Nullable Dates

```typescript
// A date that can be null (e.g., deletedAt)
const NullableDateType = Type.Transform(
  Type.Union([Type.String({ format: 'date-time' }), Type.Null()])
)
  .Decode(value => value !== null ? new Date(value) : null)
  .Encode(value => value !== null ? value.toISOString() : null)

const UserSchema = Type.Object({
  id: Type.String({ format: 'uuid' }),
  name: Type.String(),
  createdAt: DateType,
  deletedAt: NullableDateType,
})

type UserApp = StaticDecode<typeof UserSchema>
// { id: string; name: string; createdAt: Date; deletedAt: Date | null }
```

## Date-Only Fields

```typescript
const DateOnlyType = Type.Transform(Type.String({ format: 'date' }))
  .Decode(value => {
    const [year, month, day] = value.split('-').map(Number)
    return new Date(year, month - 1, day) // local midnight
  })
  .Encode(value => {
    const y = value.getFullYear()
    const m = String(value.getMonth() + 1).padStart(2, '0')
    const d = String(value.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  })

const BirthdaySchema = Type.Object({
  name: Type.String(),
  birthday: DateOnlyType,
})
```

## Timestamp (Unix Epoch)

```typescript
// Accept Unix timestamp (seconds), decode to Date
const UnixTimestamp = Type.Transform(Type.Integer({ minimum: 0 }))
  .Decode(value => new Date(value * 1000))
  .Encode(value => Math.floor(value.getTime() / 1000))

// Accept Unix timestamp (milliseconds)
const UnixTimestampMs = Type.Transform(Type.Integer({ minimum: 0 }))
  .Decode(value => new Date(value))
  .Encode(value => value.getTime())
```

## Date Range Validation

```typescript
const DateRangeQuery = Type.Object({
  from: Type.Optional(Type.String({ format: 'date-time' })),
  to: Type.Optional(Type.String({ format: 'date-time' })),
})

// Validate date range in handler
fastify.get('/events', {
  schema: { querystring: DateRangeQuery },
}, async (request) => {
  const { from, to } = request.query
  if (from && to && new Date(from) > new Date(to)) {
    throw fastify.httpErrors.badRequest('"from" must be before "to"')
  }
  // ...
})
```

## Database Integration Patterns

### With Drizzle ORM

```typescript
// Drizzle stores dates as Date objects
// TypeBox schema uses string format for API layer
// Convert at the boundary

const dbUser = await db.select().from(users).where(eq(users.id, id))
// dbUser.createdAt is a Date

// Convert to API response
const response = {
  ...dbUser,
  createdAt: dbUser.createdAt.toISOString(),
  updatedAt: dbUser.updatedAt.toISOString(),
}
```

### With Prisma

```typescript
// Prisma returns Date objects
// Fastify serialization converts them to ISO strings automatically
// Just make sure your response schema uses Type.String({ format: 'date-time' })
```

## Reusable Date Schema Module

```typescript
// schemas/common/dates.ts
import { Type, type TSchema } from 'typebox'

export const DateType = Type.Transform(Type.String({ format: 'date-time' }))
  .Decode(v => new Date(v))
  .Encode(v => v.toISOString())

export const DateOnlyType = Type.Transform(Type.String({ format: 'date' }))
  .Decode(v => new Date(v + 'T00:00:00Z'))
  .Encode(v => v.toISOString().split('T')[0])

export function NullableDate() {
  return Type.Transform(Type.Union([Type.String({ format: 'date-time' }), Type.Null()]))
    .Decode(v => v ? new Date(v) : null)
    .Encode(v => v ? v.toISOString() : null)
}

export const Timestamps = Type.Object({
  createdAt: Type.String({ format: 'date-time' }),
  updatedAt: Type.String({ format: 'date-time' }),
})
```

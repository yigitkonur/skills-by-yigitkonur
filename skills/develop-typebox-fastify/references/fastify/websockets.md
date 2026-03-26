# Fastify WebSockets

## Basic WebSocket with @fastify/websocket

```typescript
import Fastify from 'fastify'
import websocket from '@fastify/websocket'
import { Type } from '@sinclair/typebox'

const app = Fastify()
app.register(websocket)

app.get('/ws', { websocket: true }, (socket, request) => {
  socket.on('message', (message) => {
    const data = message.toString()
    request.log.info({ data }, 'Received message')
    socket.send(`Echo: ${data}`)
  })

  socket.on('close', () => request.log.info('Client disconnected'))
  socket.on('error', (error) => request.log.error({ err: error }, 'WebSocket error'))
})

await app.listen({ port: 3000 })
```

## WebSocket Options

```typescript
app.register(websocket, {
  options: {
    maxPayload: 1048576,   // 1MB max message
    clientTracking: true,
    perMessageDeflate: {
      zlibDeflateOptions: { chunkSize: 1024, memLevel: 7, level: 3 },
      zlibInflateOptions: { chunkSize: 10 * 1024 },
    },
  },
})
```

## Broadcast to All Clients

```typescript
const clients = new Set<WebSocket>()

app.get('/ws', { websocket: true }, (socket, request) => {
  clients.add(socket)
  socket.on('close', () => clients.delete(socket))

  socket.on('message', (message) => {
    for (const client of clients) {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(message)
      }
    }
  })
})

// Broadcast from HTTP route
app.post('/broadcast', {
  schema: {
    body: Type.Object({ message: Type.String() }),
    response: { 200: Type.Object({ sent: Type.Integer() }) },
  },
}, async (request) => {
  const payload = JSON.stringify({ type: 'broadcast', message: request.body.message })
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) client.send(payload)
  }
  return { sent: clients.size }
})
```

## Rooms/Channels Pattern

```typescript
const rooms = new Map<string, Set<WebSocket>>()

function joinRoom(socket: WebSocket, roomId: string) {
  if (!rooms.has(roomId)) rooms.set(roomId, new Set())
  rooms.get(roomId)!.add(socket)
}

function leaveRoom(socket: WebSocket, roomId: string) {
  rooms.get(roomId)?.delete(socket)
  if (rooms.get(roomId)?.size === 0) rooms.delete(roomId)
}

function broadcastToRoom(roomId: string, message: string, exclude?: WebSocket) {
  const room = rooms.get(roomId)
  if (!room) return
  for (const client of room) {
    if (client !== exclude && client.readyState === WebSocket.OPEN) {
      client.send(message)
    }
  }
}

app.get('/ws/:roomId', { websocket: true }, (socket, request) => {
  const { roomId } = request.params as { roomId: string }
  joinRoom(socket, roomId)

  socket.on('message', (message) => broadcastToRoom(roomId, message.toString(), socket))
  socket.on('close', () => leaveRoom(socket, roomId))
})
```

## Structured Message Protocol

```typescript
interface WSMessage {
  type: string
  payload?: unknown
  id?: string
}

app.get('/ws', { websocket: true }, (socket, request) => {
  function send(message: WSMessage) {
    socket.send(JSON.stringify(message))
  }

  socket.on('message', (raw) => {
    let message: WSMessage
    try {
      message = JSON.parse(raw.toString())
    } catch {
      send({ type: 'error', payload: 'Invalid JSON' })
      return
    }

    switch (message.type) {
      case 'ping':
        send({ type: 'pong', id: message.id })
        break
      case 'subscribe':
        handleSubscribe(socket, message.payload)
        send({ type: 'subscribed', payload: message.payload, id: message.id })
        break
      default:
        send({ type: 'error', payload: 'Unknown message type' })
    }
  })
})
```

## Heartbeat / Ping-Pong

```typescript
const HEARTBEAT_INTERVAL = 30000
const clients = new Map<WebSocket, { isAlive: boolean }>()

app.get('/ws', { websocket: true }, (socket, request) => {
  clients.set(socket, { isAlive: true })

  socket.on('pong', () => {
    const client = clients.get(socket)
    if (client) client.isAlive = true
  })

  socket.on('close', () => clients.delete(socket))
})

setInterval(() => {
  for (const [socket, state] of clients) {
    if (!state.isAlive) {
      socket.terminate()
      clients.delete(socket)
      continue
    }
    state.isAlive = false
    socket.ping()
  }
}, HEARTBEAT_INTERVAL)
```

## WebSocket Authentication

```typescript
app.get('/ws', {
  websocket: true,
  preValidation: async (request, reply) => {
    const token = request.query.token || request.headers.authorization?.replace('Bearer ', '')
    if (!token) {
      reply.code(401).send({ error: 'Token required' })
      return
    }
    try {
      request.user = await verifyToken(token)
    } catch {
      reply.code(401).send({ error: 'Invalid token' })
    }
  },
}, (socket, request) => {
  request.log.info({ userId: request.user.id }, 'Authenticated WebSocket')
  socket.on('message', (message) => { /* handle */ })
})
```

## Rate Limiting WebSocket Messages

```typescript
const rateLimits = new Map<WebSocket, { count: number; resetAt: number }>()

function checkRateLimit(socket: WebSocket, limit = 100, window = 60000): boolean {
  const now = Date.now()
  let state = rateLimits.get(socket)
  if (!state || now > state.resetAt) {
    state = { count: 0, resetAt: now + window }
    rateLimits.set(socket, state)
  }
  state.count++
  return state.count <= limit
}

app.get('/ws', { websocket: true }, (socket, request) => {
  socket.on('message', (message) => {
    if (!checkRateLimit(socket)) {
      socket.send(JSON.stringify({ error: 'Rate limit exceeded' }))
      return
    }
    // process message
  })
  socket.on('close', () => rateLimits.delete(socket))
})
```

## Graceful Shutdown

```typescript
import closeWithGrace from 'close-with-grace'

const connections = new Set<WebSocket>()

app.get('/ws', { websocket: true }, (socket, request) => {
  connections.add(socket)
  socket.on('close', () => connections.delete(socket))
})

closeWithGrace({ delay: 5000 }, async () => {
  for (const socket of connections) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'shutdown', message: 'Server shutting down' }))
      socket.close(1001, 'Server shutdown')
    }
  }
  await app.close()
})
```

## Error Handling

```typescript
app.get('/ws', { websocket: true }, (socket, request) => {
  socket.on('error', (error) => request.log.error({ err: error }, 'WebSocket error'))

  socket.on('message', async (raw) => {
    try {
      const message = JSON.parse(raw.toString())
      const result = await processMessage(message)
      socket.send(JSON.stringify({ success: true, result }))
    } catch (error) {
      request.log.error({ err: error }, 'Message processing error')
      socket.send(JSON.stringify({ success: false, error: error.message }))
    }
  })
})
```

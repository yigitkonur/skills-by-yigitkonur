# RPC Cluster Intro
Use this as a short orientation from `@effect/rpc` to `@effect/cluster`; use upstream cluster docs for depth.

`@effect/cluster` builds distributed entities and runners on top of Effect
services, sharding, storage, and RPC. This file is intentionally short. It
exists so agents know when a plain RPC service should stay plain, and when the
problem has become a cluster problem.

For deep cluster work, read the upstream package docs and source:

- `packages/cluster/src/Entity.ts`
- `packages/cluster/src/Sharding.ts`
- `packages/cluster/src/RunnerServer.ts`
- `packages/cluster/src/HttpRunner.ts`
- `packages/cluster/src/SocketRunner.ts`
- Effect cluster docs: `https://effect-ts.github.io/effect/docs/cluster`

## Relationship to RPC

Cluster entities carry an RPC protocol:

- `Entity` has a `protocol: RpcGroup.RpcGroup<Rpcs>`.
- `Sharding.makeClient(entity)` returns an RPC client facade for an entity id.
- `RunnerServer` serves runner-to-runner messages through `RpcServer.layer`.
- `HttpRunner` and `SocketRunner` provide HTTP/WebSocket runner transports.

The key distinction is ownership. `@effect/rpc` says "call this typed remote
method." `@effect/cluster` says "route this typed message to the runner that
owns this entity or shard."

## When RPC is enough

Stay with `@effect/rpc` when:

- there is one logical service endpoint,
- request routing is not shard-aware,
- handlers can run on any server instance,
- persistence and message resumption are not part of the requirement,
- the client only needs a typed API over HTTP, WebSocket, or Worker.

For most app backends, typed RPC over a normal server layer is the simpler and
more maintainable option.

## When to reach for cluster

Reach for `@effect/cluster` when the domain has long-lived addressable entities
or shard ownership:

- per-user, per-room, per-device, or per-workflow actors,
- messages must route to the runner currently responsible for an entity id,
- the system needs shard assignment and rebalancing,
- messages may be stored and resumed,
- runners need to communicate with each other.

Cluster is not a faster RPC transport. It is a distributed runtime model with
more operational requirements.

## Entity shape

At a high level, an entity combines a type name and an RPC group:

```typescript
import { Entity } from "@effect/cluster"
import { Rpc, RpcGroup } from "@effect/rpc"
import { Schema } from "effect"

class CounterApi extends RpcGroup.make(
  Rpc.make("Increment", {
    payload: { amount: Schema.Number },
    success: Schema.Number,
    error: Schema.Never
  })
) {}

const CounterEntity = Entity.fromRpcGroup("Counter", CounterApi)
```

The entity's client is created for a specific entity id, not just a server URL.

## Runner orientation

Cluster runners are application processes capable of hosting entities. Source
modules show the layers:

- `RunnerServer.layer` serves runner RPC handlers.
- `RunnerServer.layerWithClients` includes runner and sharding clients.
- `HttpRunner.layerHttp` exposes runner RPC over HTTP.
- `HttpRunner.layerWebsocket` exposes runner RPC over WebSocket.
- `SocketRunner.layer` exposes runner RPC over socket server support.

Those layers require storage, runner health, sharding config, serialization, and
platform HTTP/socket services. That dependency set is the signal that this is no
longer a simple app RPC endpoint.

## Sharding orientation

`Sharding` provides:

- shard id calculation,
- entity registration,
- singleton registration,
- entity client construction,
- message sending and notification,
- registration event streams,
- active entity counts.

Do not hand-roll shard routing on top of plain `RpcClient`. If a request must
reach the owner of an entity id, use cluster primitives.

## RPC-to-cluster migration heuristic

Start with an `RpcGroup` when the API is just remote method calls. If later the
same group becomes entity-scoped, cluster can use an RPC group as the entity
protocol. That makes the migration path smoother than starting from untyped
HTTP handlers.

The practical boundary:

- `RpcGroup` for contract and transport.
- `Entity` for addressable behavior.
- `Sharding` for ownership and routing.
- `Runner` for physical process participation.

## Anti-patterns

Avoid these moves:

- using cluster just to avoid writing an HTTP route,
- adding entity ids to every RPC while still routing to any server,
- duplicating RPC definitions inside cluster entity modules,
- mixing cluster storage concerns into plain RPC handlers,
- treating runner-to-runner protocols as public client APIs.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-rpc-group.md](02-rpc-group.md), [03-rpc-server.md](03-rpc-server.md), [04-rpc-client.md](04-rpc-client.md)

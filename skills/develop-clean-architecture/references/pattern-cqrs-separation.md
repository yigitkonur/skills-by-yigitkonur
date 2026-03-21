---
title: Separate Commands from Queries for Clear Intent and Scalability
impact: HIGH
impactDescription: eliminates read/write coupling, enables independent scaling of query and command paths
tags: pattern, cqrs, commands, queries
---

## Separate Commands from Queries for Clear Intent and Scalability

Commands change state and return void or a Result. Queries return data and never change state. Mixing both in one service obscures intent, makes caching dangerous, and couples read optimization to write correctness. Query handlers in CQRS bypass the domain layer entirely — they return flat DTOs, not domain entities.

**Incorrect (service mixing reads and writes):**

```typescript
// application/services/UserService.ts
class UserService {
  constructor(private db: Database) {}

  async getUser(id: string): Promise<User> {
    return this.db.query('SELECT * FROM users WHERE id = $1', [id]);  // Read
  }

  async getUsersWithStats(filters: Filters): Promise<UserWithStats[]> {
    // Complex join query optimized for reading — coupled to write schema
    return this.db.query(`SELECT u.*, COUNT(o.id) as order_count ...`);
  }

  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const user = await this.getUser(id);        // Read inside write
    Object.assign(user, data);                  // Mutation
    await this.db.save(user);
    await this.emailService.sendUpdateEmail();  // Side effect in same class
    return user;                                // Returns mutated entity
  }
}
```

**Correct (separated command and query handlers):**

```typescript
// application/ports/cqrs.ts
interface Command {
  readonly type: string;
}

interface CommandHandler<C extends Command> {
  execute(command: C): Promise<Result<void>>;
}

interface QueryHandler<Q, R> {
  execute(query: Q): Promise<R>;
}

// application/commands/UpdateUserCommand.ts
interface UpdateUserCommand extends Command {
  readonly type: 'UpdateUser';
  readonly userId: string;
  readonly name: string;
  readonly email: string;
}

class UpdateUserCommandHandler implements CommandHandler<UpdateUserCommand> {
  constructor(
    private readonly userRepo: IUserRepository,
    private readonly eventBus: IEventBus,
  ) {}

  async execute(command: UpdateUserCommand): Promise<Result<void>> {
    const user = await this.userRepo.findById(command.userId);
    if (!user) return Result.fail('User not found');

    user.updateProfile(command.name, command.email);
    await this.userRepo.save(user);
    await this.eventBus.publish(user.pullEvents());

    return Result.ok();  // Commands return void/Result, never data
  }
}

// application/queries/GetUserQuery.ts
interface GetUserQuery {
  readonly userId: string;
}

interface UserReadModel {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  readonly orderCount: number;
}

class GetUserQueryHandler implements QueryHandler<GetUserQuery, UserReadModel> {
  constructor(private readonly readDb: IReadDatabase) {}

  async execute(query: GetUserQuery): Promise<UserReadModel> {
    // Query handler bypasses domain — hits DB directly with optimised read query
    // Returns flat DTOs, not rich domain entities
    return this.readDb.queryOne<UserReadModel>(
      'SELECT id, name, email, order_count FROM user_read_view WHERE id = $1',
      [query.userId],
    );
  }
}

// application/Dispatcher.ts
class Dispatcher {
  private commands = new Map<string, CommandHandler<any>>();
  private queries = new Map<string, QueryHandler<any, any>>();

  async dispatch<C extends Command>(command: C): Promise<Result<void>> {
    const handler = this.commands.get(command.type);
    if (!handler) throw new Error(`No handler for ${command.type}`);
    return handler.execute(command);
  }

  async query<Q, R>(queryType: string, query: Q): Promise<R> {
    const handler = this.queries.get(queryType);
    if (!handler) throw new Error(`No handler for ${queryType}`);
    return handler.execute(query);
  }
}
```

**When NOT to use this pattern:**
- Simple CRUD applications with no complex read models
- Prototypes or early-stage products where speed outweighs separation
- When read and write models are identical and likely to stay that way

**Benefits:**
- Commands and queries scale independently (read replicas, caching on queries only)
- Clear intent — each handler does exactly one thing
- Read models can be denormalized for performance without affecting write logic
- Side effects are isolated in command handlers, queries remain pure

**Tension with Dependency Rule:** Query handlers reach directly into the database, bypassing the domain layer. This is architecturally correct as long as: (1) query handlers live in the Application Layer, and (2) the database client dependency is an injected port — preserving the Dependency Rule.

Reference: [CQRS - Martin Fowler](https://martinfowler.com/bliki/CQRS.html)

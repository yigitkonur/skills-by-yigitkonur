# Convention over Configuration

**Provide sensible defaults so developers only configure what deviates from the norm.**

---

## Origin

Convention over Configuration (CoC) was popularized by David Heinemeier Hansson (DHH) with the release of Ruby on Rails in 2004. While the concept existed earlier in tools like Apache Maven and EJB, Rails made it a headline design philosophy. DHH argued that most web applications share the same structural patterns — so the framework should assume those patterns and only require configuration when the developer wants something different. The principle became a defining characteristic of the "opinionated framework" movement.

---

## The Problem It Solves

Without conventions, every new project begins with a wall of configuration. Where do controllers go? What naming pattern maps URLs to handlers? How are database tables related to model classes? Which serialization format is used? In a fully configurable system, every one of these questions must be answered explicitly — in XML files, JSON configs, or boilerplate code. This leads to **configuration fatigue**: projects spend more time on plumbing than on business logic, and every team invents slightly different conventions, making cross-team collaboration painful.

---

## The Principle Explained

Convention over Configuration means the framework or tool establishes default rules that "just work" for the common case. A model named `User` maps to a table named `users`. A controller named `OrdersController` handles routes under `/orders`. Test files go in a `/tests` directory that mirrors the source structure. The developer only writes configuration when they need to deviate: "my `User` model maps to the `people` table."

The power of CoC is **cognitive offloading**. Instead of remembering (or documenting) that "we decided controllers go in `src/http/handlers` and use the suffix `Handler`," the framework decides for you. New team members are productive immediately because the structure is predictable. Code reviews are faster because there are fewer "why did you put this here?" discussions.

However, conventions are only useful if they are **well-known and consistent**. A convention that nobody knows about is just a hidden requirement. Good CoC implementations make conventions discoverable (documentation, generators, error messages that suggest the conventional path) and overridable (escape hatches for every convention). The worst outcome is a convention that is both surprising and non-overridable.

---

## Code Examples

### BAD: Everything requires explicit configuration

```typescript
// Every mapping must be configured manually
const routeConfig = {
  routes: [
    { method: "GET", path: "/users", handler: "UserController.index" },
    { method: "GET", path: "/users/:id", handler: "UserController.show" },
    { method: "POST", path: "/users", handler: "UserController.create" },
    { method: "PUT", path: "/users/:id", handler: "UserController.update" },
    { method: "DELETE", path: "/users/:id", handler: "UserController.destroy" },
    // Repeated for every resource... 50 lines of boilerplate
  ],
};

// ORM requires explicit table and column mappings
const userMapping = {
  entity: User,
  tableName: "app_users",
  columns: {
    id: { name: "user_id", type: "uuid", primary: true },
    firstName: { name: "first_name", type: "varchar" },
    lastName: { name: "last_name", type: "varchar" },
    email: { name: "email_address", type: "varchar" },
    createdAt: { name: "created_at", type: "timestamp" },
  },
};

// Test files require explicit registration
const testConfig = {
  testFiles: [
    "tests/unit/services/user-service.test.ts",
    "tests/unit/services/order-service.test.ts",
    // Manually add every new test file...
  ],
};
```

### GOOD: Conventions handle the common case; configuration for exceptions

```typescript
// Convention: decorators + naming conventions handle routing
// Only configure when deviating from the convention
@Controller("/users") // Convention: plural of the entity name
class UsersController {
  @Get("/")         // Convention: index action
  async index(): Promise<User[]> { /* ... */ }

  @Get("/:id")     // Convention: show action
  async show(@Param("id") id: string): Promise<User> { /* ... */ }

  @Post("/")        // Convention: create action
  async create(@Body() dto: CreateUserDto): Promise<User> { /* ... */ }
}

// Convention: entity class name maps to snake_case plural table
// Only configure when the convention does not fit
@Entity() // Convention: maps to "users" table automatically
class User {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column() // Convention: property name = column name in snake_case
  firstName: string;

  @Column()
  lastName: string;

  @Column({ unique: true }) // Only specify what differs from default
  email: string;

  @CreateDateColumn() // Convention: auto-managed timestamp
  createdAt: Date;
}

// Exception: this entity maps to a non-standard table
@Entity({ name: "legacy_customer_records" }) // Override convention
class Customer {
  @PrimaryColumn({ name: "cust_id" }) // Override column name
  id: string;
}

// Convention: test files are discovered by pattern — no registration needed
// *.test.ts or *.spec.ts files are automatically included
// jest.config.ts only needs:
const config = {
  preset: "ts-jest",
  // That is it. Conventions handle the rest:
  // - testMatch: ["**/*.test.ts"] (default)
  // - moduleFileExtensions: ["ts", "js"] (default)
  // - transform: ts-jest handles .ts files (default from preset)
};
```

### Convention-based project structure

```typescript
// The directory structure IS the configuration
// src/
//   modules/
//     users/
//       users.controller.ts    -> routes under /users
//       users.service.ts       -> business logic
//       users.repository.ts    -> data access
//       users.module.ts        -> wiring
//       dto/
//         create-user.dto.ts   -> input validation
//       entities/
//         user.entity.ts       -> database model
//     orders/
//       orders.controller.ts   -> routes under /orders
//       ...

// Auto-discovery based on convention
function discoverModules(baseDir: string): Module[] {
  // Convention: any directory with a *.module.ts file is a module
  const modulePaths = glob.sync(`${baseDir}/**/*.module.ts`);
  return modulePaths.map((path) => require(path).default);
}

// Zero configuration needed — the file system is the config
const app = createApp({
  modules: discoverModules("./src/modules"),
});
```

---

## Alternatives & Related Principles

| Approach | Relationship |
|---|---|
| **Explicit Configuration** | The opposite extreme: everything must be configured. Maximizes flexibility but increases boilerplate. Spring XML (pre-annotations) was a poster child. |
| **Zero-Config** | Takes CoC further: no configuration at all, even for deviations. Parcel bundler and Create React App aspire to this. The trade-off is reduced flexibility. |
| **Opinionated Frameworks** | Frameworks that make strong choices (Rails, Next.js, NestJS). Conventions are the mechanism; "opinionated" is the philosophy. |
| **Configuration as Code** | Not opposed to CoC but complementary — when configuration is needed, express it in code rather than declarative files. Pulumi vs. Terraform, Webpack config in JS vs. JSON. |
| **Principle of Least Astonishment** | CoC should choose conventions that match developer expectations. A convention that surprises is worse than explicit configuration. |

---

## When NOT to Apply

- **Highly specialized domains**: If every project in your domain is genuinely unique (embedded systems, scientific computing), conventions will not match reality and become a hindrance.
- **When conventions are poorly documented**: An undocumented convention is a magic behavior. If developers cannot discover what the convention is, it creates confusion rather than reducing it.
- **Security-sensitive defaults**: Conventions should be secure by default. A framework that conventionally exposes all database columns as API fields (over-posting vulnerability) has a dangerous convention.
- **When the team disagrees with the convention**: Fighting the framework is worse than explicit configuration. If your team consistently overrides a convention, switch to a less opinionated tool.
- **Library code vs. framework code**: Libraries should not impose conventions on their consumers. Convention over Configuration is a framework-level concern.

---

## Tensions & Trade-offs

- **Convention vs. Transparency**: Conventions hide decisions. When a bug occurs inside a convention ("why is this route being registered?"), debugging requires understanding the framework's internals.
- **Convention vs. Flexibility**: Strong conventions make the common case easy but the uncommon case hard. Ejecting from Create React App is a one-way door.
- **Convention vs. Explicitness**: `import` is explicit; auto-loading by file name is conventional. Explicit code is greppable and traceable; conventional code is concise and discoverable.
- **Convention drift**: As the framework evolves, conventions change. Upgrading from Rails 5 to Rails 7 means learning new conventions. The migration cost can exceed the original configuration cost.
- **Magic vs. clarity**: "It just works" is magical until it does not. Then "it just works" becomes "I have no idea how this works."

---

## Real-World Consequences

**Adherence example**: Ruby on Rails reduced the time to build a CRUD web application from weeks to hours by establishing conventions for routing, ORM mapping, view rendering, and asset management. An entire generation of startups shipped products faster because they did not debate folder structures.

**Over-application example**: A team used a framework with convention-based auto-discovery of event handlers. Any class ending in `Handler` in a specific directory was automatically registered. A developer created a `TestCleanupHandler` for local testing that got auto-registered in production, deleting data on every deploy. The convention had no visibility into what was registered.

---

## Key Quotes

> "Convention over configuration is a means to achieve sane defaults while still allowing configuration when it is needed." — David Heinemeier Hansson

> "The best frameworks are opinionated. They make common things trivial and uncommon things possible." — common paraphrase

> "The problem with convention over configuration is that you now have to learn the conventions. And conventions, unlike configuration, are implicit." — criticism from the explicit-is-better-than-implicit camp

---

## Further Reading

- Heinemeier Hansson, D. — [Convention over Configuration](https://rubyonrails.org/doctrine#convention-over-configuration) (Rails Doctrine)
- Fowler, M. — [Convention over Configuration](https://martinfowler.com/bliki/ConventionOverConfiguration.html)
- *Maven: The Definitive Guide* — Chapter on Standard Directory Layout (one of the earliest CoC implementations)
- NestJS documentation — [Module auto-discovery](https://docs.nestjs.com/) as a modern TypeScript CoC example
- *The Zen of Python* (PEP 20) — "Explicit is better than implicit" (the counter-argument)

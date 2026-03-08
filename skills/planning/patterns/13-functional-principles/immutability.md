# Immutability

**Once created, data never changes. New values are derived, old values remain intact.**

---

## Origin / History

Immutability is a foundational concept in mathematics — the number 5 does not become 6. In computing, immutable data was central to Lisp (1958) through its use of cons cells and persistent lists. The concept matured in languages like Erlang (1986), where all variables are single-assignment, and Clojure (2007), which popularized persistent data structures with structural sharing for the JVM ecosystem. Rich Hickey's talks — particularly "The Value of Values" (2012) — articulated why mutable state is the root cause of complexity in most software systems.

In JavaScript and TypeScript, immutability gained practical traction through libraries like Immutable.js (Facebook, 2014) and Immer (Michel Weststrate, 2018), and through frameworks like Redux that mandate immutable state transitions.

---

## The Problem It Solves

Mutable shared state is the primary source of concurrency bugs, stale references, defensive copying, and "action at a distance" — where modifying data in one part of the system unexpectedly changes behavior in another. When an object can be mutated by any holder of a reference, reasoning about program state becomes exponentially harder as the codebase grows.

Consider passing a configuration object to three different modules. If any module can mutate it, every module must defensively check or copy the object. Immutability eliminates this entire class of problems: if data cannot change, sharing it is always safe.

The result is code that is easier to test (no setup/teardown of mutable state), easier to debug (data at any point in time is a snapshot), and easier to parallelize (no locks needed for read-only data).

---

## The Principle Explained

Immutability means that once a value is created, it cannot be modified. Instead of changing an object, you create a new object with the desired differences. The old object continues to exist unchanged, which is essential for undo/redo, audit logs, and time-travel debugging.

Structural sharing is the performance optimization that makes immutability practical. When you "modify" a deeply nested immutable tree, only the nodes along the path from the root to the changed leaf are recreated. All other nodes are shared between the old and new versions. This gives you O(log n) update performance instead of O(n) full copies. Libraries like Immer achieve this transparently: you write code that looks like mutation, but the library produces a new immutable object behind the scenes.

In TypeScript, immutability is enforced through `readonly` properties, `ReadonlyArray<T>`, `Readonly<T>`, `as const` assertions, and `Object.freeze()`. However, these are shallow by default — deep immutability requires either recursive type utilities or libraries. The key insight is that immutability is both a runtime guarantee (frozen objects) and a design discipline (always returning new values).

---

## Code Examples

### BAD: Mutable state causing action-at-a-distance bugs

```typescript
interface User {
  name: string;
  roles: string[];
  preferences: { theme: string; language: string };
}

function addAdminRole(user: User): User {
  // MUTATES the original — every reference to this user sees the change
  user.roles.push("admin");
  return user;
}

function applyDefaults(user: User): void {
  // MUTATES nested object — caller's data silently changes
  user.preferences.theme = user.preferences.theme || "light";
  user.preferences.language = user.preferences.language || "en";
}

const user: User = {
  name: "Alice",
  roles: ["viewer"],
  preferences: { theme: "", language: "" },
};

const admin = addAdminRole(user);
// Bug: user.roles is now ["viewer", "admin"] — original was mutated
console.log(user === admin); // true — same object!
console.log(user.roles);     // ["viewer", "admin"] — surprise!
```

### GOOD: Immutable updates with new references

```typescript
interface User {
  readonly name: string;
  readonly roles: readonly string[];
  readonly preferences: Readonly<{ theme: string; language: string }>;
}

function addAdminRole(user: User): User {
  return {
    ...user,
    roles: [...user.roles, "admin"],
  };
}

function applyDefaults(user: User): User {
  return {
    ...user,
    preferences: {
      theme: user.preferences.theme || "light",
      language: user.preferences.language || "en",
    },
  };
}

const user: User = {
  name: "Alice",
  roles: ["viewer"],
  preferences: { theme: "", language: "" },
};

const admin = addAdminRole(user);
console.log(user === admin);  // false — different objects
console.log(user.roles);      // ["viewer"] — original is untouched
console.log(admin.roles);     // ["viewer", "admin"] — new value
```

### GOOD: Using Immer for ergonomic immutable updates

```typescript
import { produce } from "immer";

interface AppState {
  readonly users: readonly User[];
  readonly selectedId: string | null;
}

function addUser(state: AppState, newUser: User): AppState {
  // Immer lets you write "mutating" code that produces immutable output
  return produce(state, (draft) => {
    draft.users.push(newUser);
  });
}

function updateUserName(
  state: AppState,
  userId: string,
  newName: string,
): AppState {
  return produce(state, (draft) => {
    const user = draft.users.find((u) => u.name === userId);
    if (user) {
      user.name = newName; // Looks like mutation, but Immer creates a new tree
    }
  });
}
```

### Deep freeze utility for runtime enforcement

```typescript
function deepFreeze<T extends object>(obj: T): Readonly<T> {
  Object.freeze(obj);
  for (const value of Object.values(obj)) {
    if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
      deepFreeze(value);
    }
  }
  return obj;
}

const config = deepFreeze({
  database: { host: "localhost", port: 5432 },
  features: { darkMode: true },
});

// config.database.port = 3306; // TypeError in strict mode, silently fails otherwise
```

---

## Alternatives & Related Approaches

| Approach | Trade-off |
|---|---|
| **Mutable state with locks** | Allows in-place updates, but requires careful synchronization. Deadlocks and race conditions become the developer's responsibility. |
| **Defensive copying** | Copy data at every boundary. Simple but wasteful — O(n) per copy, no structural sharing. |
| **Copy-on-write (COW)** | Delay copying until mutation actually occurs. Used by some runtimes internally. Efficient but complex to implement correctly. |
| **Persistent data structures (Immutable.js)** | Full structural sharing with O(log32 n) updates. API differs from plain JS objects, causing interop friction. |
| **Immer** | Write mutation-style code, get immutable output. Best ergonomics, small overhead. The pragmatic middle ground. |

---

## When NOT to Apply

- **High-frequency numeric computation**: Creating new arrays for every frame in a game engine or signal processor is impractical. Use mutable buffers with clear ownership.
- **Large binary data**: Images, audio buffers, and video frames should not be copied. Use typed arrays with explicit lifecycle management.
- **Database records in ORM contexts**: ORMs like TypeORM track entity mutations. Fighting the ORM's mutable design creates friction without benefit.
- **Performance-critical hot paths**: When profiling identifies object creation as a bottleneck, targeted mutability is justified. Document why.

---

## Tensions & Trade-offs

- **Immutability vs. Performance**: Naive immutable updates (spread operator on large arrays) are slow. Structural sharing or Immer mitigates this, but adds dependency weight.
- **Immutability vs. Ergonomics**: Deep immutable updates in TypeScript are verbose without libraries: `{ ...state, users: { ...state.users, [id]: { ...state.users[id], name: newName } } }`.
- **Immutability vs. Memory**: Keeping old versions alive (for undo, audit trails) increases memory usage. Garbage collection helps, but memory-constrained environments require care.
- **Shallow vs. Deep**: TypeScript's `readonly` is shallow. `Readonly<T>` does not protect nested objects. Deep readonly requires recursive utility types or runtime freezing.

---

## Real-World Consequences

**Redux state mutation bugs**: The most common Redux bug is accidentally mutating state in a reducer. Because Redux relies on reference equality checks for re-rendering, mutated state causes components to not re-render when they should. Redux Toolkit now uses Immer by default to prevent this.

**Git as an immutable data structure**: Git's object model is immutable — every commit, tree, and blob is content-addressed and never changes. This makes branching, merging, and history traversal safe and efficient. It is perhaps the most successful immutable data structure in widespread use.

**Undo/redo in collaborative editors**: Google Docs and Figma rely on immutable operation logs. Each change is a new entry, never a modification of an old one. This enables operational transformation and conflict resolution that would be impossible with mutable state.

---

## Further Reading

- [Rich Hickey — The Value of Values (Strange Loop 2012)](https://www.youtube.com/watch?v=-6BsiVyC1kM)
- [Immer Documentation — Produce](https://immerjs.github.io/immer/)
- [TypeScript Handbook — Readonly and Const Assertions](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [Immutable.js Documentation](https://immutable-js.com/)
- [Chris Okasaki — Purely Functional Data Structures (Cambridge, 1998)](https://www.cambridge.org/core/books/purely-functional-data-structures/0409255DA1B48FA731859AC72E34D494)

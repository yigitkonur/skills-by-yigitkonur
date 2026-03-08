# Naming Conventions

**One-line summary:** Names are the primary tool for communicating intent in code -- a good name eliminates the need for a comment, while a bad name creates a tiny lie that compounds across the codebase.

---

## Origin

The principles of good naming have been articulated by many authors. Robert C. Martin dedicated Chapter 2 of *Clean Code* (2008) entirely to naming. Steve McConnell covered it extensively in *Code Complete* (2004). Tim Ottinger contributed the "Rules for Variable Naming" that Martin refined. The underlying insight traces back to Dijkstra and Knuth: programming is fundamentally an act of communication, and names are the most frequent communication channel between the author and every future reader.

---

## The Problem It Solves

Poor naming is the most pervasive source of accidental complexity in software. A variable named `d` forces every reader to look up what it means. A function named `process` tells you nothing about what it processes or how. A class named `Manager` could mean anything. When names lie (a boolean named `isValid` that actually checks authorization), they create bugs that are invisible to casual reading. Naming debt compounds: unclear names in one layer force unclear names in the next, until the codebase becomes a thicket of abbreviations, acronyms, and legacy jargon that only the original author can decode -- and often, not even them.

---

## The Principle Explained

**Intention-revealing names** answer three questions: why does this thing exist, what does it do, and how is it used? If a name requires a comment to explain it, the name is wrong. The name `elapsedTimeInDays` needs no comment; the name `d` needs one that says "elapsed time in days," which means the comment is doing the name's job.

**Avoid disinformation.** Do not use names that mean something different from what the code does. Do not name a variable `accountList` if it is actually a `Set`. Do not name a function `getUser` if it creates a user when one does not exist. Every name is a micro-contract with the reader; breaking that contract breeds distrust and defensive reading.

**Make meaningful distinctions.** If you have `productInfo` and `productData` in the same scope, nobody can tell which is which. If you have `copyString(string a1, string a2)`, the parameter names communicate nothing. Number series naming (`a1, a2, a3`) and noise words (`Info`, `Data`, `Manager`, `Processor`) are symptoms of the author not thinking hard enough about what makes each thing distinct. Names should differ because the concepts they represent differ, and the difference should be visible in the names.

---

## Code Examples

### BAD: Variable Naming

```typescript
// Cryptic abbreviations
const d = new Date();
const t = d.getTime();
const lst = users.filter(u => u.s === "A");
const tmp = calculateResult(x, y);
const flag = true;
const data = fetchData();
const val = getValue();

// Disinformative names
const accountList: Set<Account> = new Set(); // not a list
const isValid = checkAuthorization(user);     // checks auth, not validity
const nameString = "Alice";                    // "String" adds nothing

// Meaningless distinctions
function copyChars(a1: string[], a2: string[]): void {
  for (let i = 0; i < a1.length; i++) {
    a2[i] = a1[i];
  }
}
```

### GOOD: Variable Naming

```typescript
// Intention-revealing
const currentDate = new Date();
const timestampMs = currentDate.getTime();
const activeUsers = users.filter((user) => user.status === "ACTIVE");
const projectedRevenue = calculateRevenue(unitsSold, pricePerUnit);
const shouldRetryOnFailure = true;
const customerProfiles = fetchCustomerProfiles();
const maxConnectionPoolSize = getMaxConnectionPoolSize();

// Honest names
const activeAccountIds: Set<AccountId> = new Set();  // accurately describes container
const isAuthorized = checkAuthorization(user);        // matches what it checks
const customerName = "Alice";                          // no redundant type suffix

// Meaningful distinctions
function copyCharacters(source: string[], destination: string[]): void {
  for (let i = 0; i < source.length; i++) {
    destination[i] = source[i];
  }
}
```

### BAD: Function Naming

```typescript
// Vague verbs
function handle(req: Request): Response { /* ... */ }
function process(items: Item[]): void { /* ... */ }
function doWork(): void { /* ... */ }
function manage(users: User[]): void { /* ... */ }

// Misleading names
function getUser(id: string): User {
  const existing = db.find(id);
  if (!existing) {
    return db.create({ id, name: "Unknown" }); // "get" creates?!
  }
  return existing;
}

// Boolean functions without question-style names
function check(password: string): boolean { /* ... */ }
function access(user: User): boolean { /* ... */ }
```

### GOOD: Function Naming

```typescript
// Specific verbs that reveal intent
function routeIncomingRequest(req: Request): Response { /* ... */ }
function applyBulkDiscountToItems(items: Item[]): DiscountedItem[] { /* ... */ }
function synchronizeInventoryWithWarehouse(): SyncResult { /* ... */ }
function deactivateExpiredUserAccounts(users: User[]): DeactivationReport { /* ... */ }

// Honest names -- no hidden behavior
function findUserById(id: string): User | undefined {
  return db.find(id); // returns undefined if not found, as the name implies
}

function findOrCreateUser(id: string, defaults: UserDefaults): User {
  return db.find(id) ?? db.create({ id, ...defaults }); // name reveals both paths
}

// Boolean functions read as questions
function isPasswordValid(password: string): boolean { /* ... */ }
function hasAccessToResource(user: User, resource: Resource): boolean { /* ... */ }
function canRetryRequest(attempt: number, maxAttempts: number): boolean { /* ... */ }
```

### BAD: Class and Module Naming

```typescript
// Meaningless suffixes
class UserManager { /* what does "manage" mean? */ }
class DataProcessor { /* what data? what processing? */ }
class InfoHandler { /* info about what? handle how? */ }
class ServiceHelper { /* which service? help with what? */ }
class UtilsManager { /* the pinnacle of vague naming */ }
```

### GOOD: Class and Module Naming

```typescript
// Specific responsibility in the name
class UserRegistrationService { /* registers users */ }
class InvoiceLineItemCalculator { /* calculates invoice line items */ }
class PasswordHasher { /* hashes passwords */ }
class EmailDeliveryQueue { /* queues emails for delivery */ }
class InventoryStockReserver { /* reserves inventory stock */ }

// Modules named by domain concept
// auth/password-policy.ts
// billing/invoice-generator.ts
// shipping/rate-calculator.ts
// notifications/email-template-renderer.ts
```

### BAD vs GOOD: File Naming

```typescript
// BAD file names
// utils.ts          -- grabs bag of unrelated functions
// helpers.ts        -- same problem
// types.ts          -- every type in one file
// constants.ts      -- every constant in one file
// index.ts          -- 500 lines of re-exports and logic

// GOOD file names
// password-policy.ts         -- contains password validation rules
// invoice-line-calculator.ts -- calculates invoice line items
// shipping-rate.ts           -- shipping rate lookup and calculation
// order-status.ts            -- order status enum and transitions
// database-connection.ts     -- database connection configuration
```

---

## Naming Rules Summary

| Rule | Rationale |
|---|---|
| **Use intention-revealing names** | Names should answer why, what, and how |
| **Avoid disinformation** | Names must not lie about what the code does |
| **Make meaningful distinctions** | If things are different, their names must show how |
| **Use pronounceable names** | `genymdhms` is unpronounceable; `generationTimestamp` is not |
| **Use searchable names** | Single-letter names and magic numbers cannot be grepped |
| **No Hungarian notation** | Modern IDEs make type prefixes redundant and noisy |
| **No member prefixes** | `m_name` or `_name` adds visual noise; let the class scope be enough |
| **Class names are nouns** | `Customer`, `Invoice`, `ShippingRate` -- not verbs |
| **Method names are verbs** | `calculateTotal`, `sendNotification`, `validateInput` |
| **One word per concept** | Pick `fetch`, `retrieve`, or `get` and use it consistently |
| **Use domain vocabulary** | Use the language of the business, not of the implementation |

---

## Alternatives & Related Approaches

| Approach | When Used | Trade-off |
|---|---|---|
| **Hungarian notation** | Legacy C/C++ codebases without IDE support | Adds noise; redundant with modern tooling |
| **Abbreviation conventions** | Embedded systems with character limits | Faster to type, slower to read |
| **Comment-heavy code** | When names are kept short, comments explain | Comments drift from code; names do not |
| **Domain-Driven Design ubiquitous language** | Aligns code names with business terms | Requires ongoing collaboration with domain experts |

---

## When NOT to Apply

- **Mathematical code.** In a formula implementation, `x`, `y`, `dx`, `dt` are the conventional names. Renaming `x` to `horizontalPosition` makes the math harder to follow.
- **Loop variables in tight scopes.** `i`, `j`, `k` in a 3-line loop are universally understood.
- **Lambda parameters in trivial closures.** `items.filter(x => x.active)` is fine when the context is obvious.
- **Established abbreviations in your domain.** `HTTP`, `URL`, `DNS`, `SQL` are clearer than their expansions.

---

## Tensions & Trade-offs

- **Precision vs. brevity:** `calculateDiscountedPriceAfterCouponApplication` is precise but exhausting. `calcPrice` is brief but vague. Aim for the shortest name that eliminates ambiguity.
- **Consistency vs. accuracy:** If the codebase uses `get` for all fetches but one function creates on miss, renaming it to `findOrCreate` breaks the pattern. The accuracy is worth the inconsistency.
- **Domain language vs. developer language:** Business stakeholders say "customer"; developers say "user." Pick one and use it everywhere.

---

## Real-World Consequences

- A study at the University of Passau (2019) found that developers comprehend code with good names **up to 19% faster** than code with abbreviated or vague names.
- **Google's internal style guides** mandate specific naming conventions because inconsistent naming was identified as a top-3 contributor to code review friction.
- **The Therac-25 radiation therapy accidents** were partly attributed to confusing variable names in the control software, making it nearly impossible for reviewers to spot the race condition.

---

## Key Quotes

> "You should name a variable using the same care with which you name a first-born child." -- Robert C. Martin

> "There are only two hard things in Computer Science: cache invalidation and naming things." -- Phil Karlton

> "The beginning of wisdom is to call things by their proper name." -- Confucius

> "A long descriptive name is better than a short enigmatic name. A long descriptive name is better than a long descriptive comment." -- Robert C. Martin

---

## Further Reading

- *Clean Code* by Robert C. Martin (2008) -- Chapter 2: Meaningful Names
- *Code Complete* by Steve McConnell (2004) -- Chapter 11: The Power of Variable Names
- *Domain-Driven Design* by Eric Evans (2003) -- Ubiquitous Language concept
- *The Art of Readable Code* by Boswell and Foucher (2011)

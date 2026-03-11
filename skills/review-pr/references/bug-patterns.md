# Common Bug Patterns in PRs

The most frequently missed bugs in code review, organized by category. Use this as a mental checklist when reviewing code in Phase 5.

---

## Race Conditions

Race conditions are the hardest bugs to catch in review because the code looks correct in sequential execution. They only manifest under concurrent access.

### TOCTOU (Time-of-Check-Time-of-Use)

The code checks a condition, then acts on it — but the condition may have changed between the check and the action.

```javascript
// RACE — check then act, not atomic
async function claimUsername(username) {
  const existing = await db.query('SELECT id FROM users WHERE username = ?', [username]);
  if (existing.length === 0) {
    // Another request can insert the same username RIGHT HERE
    await db.query('INSERT INTO users (username) VALUES (?)', [username]);
  }
}

// FIX — use database constraint
// 1. Add UNIQUE constraint on username column
// 2. Handle the constraint violation error
async function claimUsername(username) {
  try {
    await db.query('INSERT INTO users (username) VALUES (?)', [username]);
  } catch (err) {
    if (err.code === 'ER_DUP_ENTRY') throw new ConflictError('Username taken');
    throw err;
  }
}
```

### Shared Mutable State

```javascript
// RACE — shared counter without synchronization
let requestCount = 0;
app.use((req, res, next) => {
  requestCount++;  // Not atomic in concurrent environments
  next();
});

// RACE — shared cache without locking
const cache = {};
async function getUser(id) {
  if (!cache[id]) {
    // Multiple concurrent requests all miss cache and all hit DB
    cache[id] = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  }
  return cache[id];
}
```

### Async Operation Ordering

```javascript
// RACE — two async writes to same resource
async function updateProfile(userId, data) {
  await updateName(userId, data.name);      // Starts
  await updateEmail(userId, data.email);    // Starts after name completes
  // But what if another request updates name between these two calls?
}

// FIX — wrap in transaction
async function updateProfile(userId, data) {
  await db.transaction(async (tx) => {
    await tx.query('UPDATE users SET name = ?, email = ? WHERE id = ?',
      [data.name, data.email, userId]);
  });
}
```

**Review heuristic:** When you see code that reads a value, makes a decision, then writes based on that decision — ask: "What if the value changed between the read and the write?"

---

## Error Handling Gaps

### Swallowed Errors

```javascript
// BUG — error silently swallowed
try {
  await processPayment(order);
} catch (e) {
  console.log('Payment failed');  // No rethrow, no return, order continues as if paid
}

// BUG — empty catch
try {
  const data = JSON.parse(rawInput);
} catch (e) {}  // If parsing fails, data is undefined — downstream code crashes

// FIX — handle or rethrow
try {
  await processPayment(order);
} catch (e) {
  logger.error('Payment failed', { orderId: order.id, error: e.message });
  throw new PaymentError('Payment processing failed');
}
```

### Missing Await

The most dangerous JavaScript/TypeScript bug — the code appears to work because the function is called, but errors are silently dropped and side effects may not complete.

```javascript
// BUG — missing await, error is never caught
async function handleRequest(req, res) {
  saveAuditLog(req);  // Missing await! Returns a Promise that's never awaited
  res.json({ success: true });  // Response sent before audit log is saved
}

// BUG — missing await in try/catch
try {
  deleteTemporaryFiles();  // Async function without await — errors bypass catch
} catch (e) {
  logger.error('Cleanup failed:', e);  // Never reached
}
```

**Detection heuristic:** In every `async` function, check that every call to another `async` function has `await` (or the promise is handled with `.then()/.catch()`). Look for async functions called without `await` in catch blocks especially.

### Incorrect Error Propagation

```javascript
// BUG — loses original error context
catch (err) {
  throw new Error('Operation failed');  // Original error message and stack lost
}

// FIX — preserve cause
catch (err) {
  throw new Error('Operation failed', { cause: err });
}

// BUG — catches too broadly
catch (err) {
  // This catches programming errors (TypeError, ReferenceError) too
  return { error: 'Something went wrong' };
}
```

---

## Null/Undefined Handling

### Optional Chain Traps

```javascript
// BUG — optional chain returns undefined, used as truthy
const isAdmin = user?.role?.includes('admin');
// If user is null, isAdmin is undefined (falsy) — correct by accident
// But what if the default should be true? undefined != false

// BUG — nullish coalescing with wrong default
const count = response.data?.count ?? 0;
// Correct for null/undefined, but if count is 0 legitimately, this masks it
// (Actually ?? is correct here — but || would be wrong)
const count2 = response.data?.count || 10;  // BUG: treats 0 as missing
```

### Destructuring Without Defaults

```javascript
// BUG — crashes if config is undefined
const { host, port } = getConfig();  // TypeError if getConfig() returns undefined

// FIX — default to empty object
const { host, port } = getConfig() ?? {};

// BUG — nested destructuring without checks
const { data: { users } } = await fetchResponse();  // Crashes if data is undefined

// FIX — handle each level
const response = await fetchResponse();
const users = response?.data?.users ?? [];
```

### Array Method Assumptions

```javascript
// BUG — .find() returns undefined, used without check
const user = users.find(u => u.id === targetId);
user.name = 'Updated';  // TypeError if user not found

// BUG — array might be null from API
const count = response.items.length;  // TypeError if items is null

// FIX
const user = users.find(u => u.id === targetId);
if (!user) throw new NotFoundError(`User ${targetId} not found`);
user.name = 'Updated';

const count = response.items?.length ?? 0;
```

---

## Off-By-One Errors

### Loop Bounds

```javascript
// BUG — includes one extra element
for (let i = 0; i <= items.length; i++) {  // Should be < not <=
  process(items[i]);  // items[items.length] is undefined
}

// BUG — skips last element
const result = items.slice(0, items.length - 1);  // Off by one — misses last
```

### Pagination

```javascript
// BUG — page 1 skips first item
const offset = page * pageSize;  // Page 1 → offset = pageSize, misses first pageSize items
// FIX
const offset = (page - 1) * pageSize;  // Page 1 → offset = 0

// BUG — "has next page" check
const hasNext = items.length > pageSize;  // Wrong if query already limited to pageSize
// FIX — query pageSize + 1, return only pageSize
const items = await query({ limit: pageSize + 1 });
const hasNext = items.length > pageSize;
const result = items.slice(0, pageSize);
```

### String/Array Indexing

```javascript
// BUG — substring bounds
const extension = filename.substring(filename.lastIndexOf('.'));
// If no dot in filename, lastIndexOf returns -1, substring(-1) = substring(0) = entire string

// FIX
const dotIndex = filename.lastIndexOf('.');
const extension = dotIndex >= 0 ? filename.substring(dotIndex) : '';
```

---

## State Management Bugs

### Stale Closure

```javascript
// BUG — React useEffect with stale closure
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCount(count + 1);  // count is always 0 — stale closure
    }, 1000);
    return () => clearInterval(interval);
  }, []);  // Empty deps — closure captures initial count

  // FIX
  useEffect(() => {
    const interval = setInterval(() => {
      setCount(prev => prev + 1);  // Functional update — always current
    }, 1000);
    return () => clearInterval(interval);
  }, []);
}
```

### Mutation vs Immutable Update

```javascript
// BUG — mutates state directly (React)
const handleAdd = (item) => {
  items.push(item);         // Mutates existing array
  setItems(items);          // React doesn't see a change (same reference)
};

// FIX — create new array
const handleAdd = (item) => {
  setItems([...items, item]);  // New array reference triggers re-render
};

// BUG — nested mutation
const handleUpdate = (id, value) => {
  const item = items.find(i => i.id === id);
  item.value = value;       // Mutates object inside array
  setItems([...items]);     // Shallow copy doesn't detect nested change
};

// FIX — deep immutable update
const handleUpdate = (id, value) => {
  setItems(items.map(i => i.id === id ? { ...i, value } : i));
};
```

---

## Type Coercion Bugs

### JavaScript Equality

```javascript
// BUGS — == coercion
0 == ''           // true (both coerce to 0)
null == undefined // true (special case)
'0' == false      // true (both coerce to 0)
[] == false       // true ([] → '' → 0 → false)

// FIX — always use ===
0 === ''          // false
null === undefined // false
```

### Implicit Type Conversion

```javascript
// BUG — string from query param treated as number
const page = req.query.page;       // "2" (string!)
const offset = page * 10;          // 20 — works by accident
const nextPage = page + 1;         // "21" — string concatenation!

// FIX — explicit parsing
const page = parseInt(req.query.page, 10) || 1;
```

---

## Checklist: Bug Pattern Quick Scan

Before concluding Phase 5 review on any file, do this 30-second scan:

```
□ Race conditions: Any read-then-write without atomicity?
□ Missing await: Any async function called without await?
□ Empty catch: Any catch block that swallows errors?
□ Null access: Any value from external source (API, DB, params) used without null check?
□ Off-by-one: Any loop bounds, pagination, or substring operations?
□ Type coercion: Any == or implicit string/number conversion?
□ Stale closure: Any React hooks with missing dependencies?
□ Mutation: Any array/object mutation where immutability is expected?
```

# Storage API Reference

## Storage Areas Overview

Chrome extensions have four storage areas, each with distinct scope and persistence:

| Area | Permission | Scope | Persistence | Use Case |
|---|---|---|---|---|
| `chrome.storage.local` | `storage` | Per device | Survives browser restart, extension update | Large data, caches, user preferences |
| `chrome.storage.sync` | `storage` | Synced across devices via Chrome account | Survives restart, syncs with account | Small user settings that follow the user |
| `chrome.storage.session` | `storage` | Per browser session, per extension | Cleared on browser close; not accessible from content scripts by default | Temporary tokens, session state |
| `chrome.storage.managed` | `storage` | Read-only, set by enterprise policy | Managed by IT admin via policy JSON | Enterprise-managed configuration |

### Quota Limits

| Area | Total Quota | Per-Item Limit | Max Items | Write Ops/Min | Notes |
|---|---|---|---|---|---|
| `local` | 10 MB | No per-item limit | No limit | ~120 sustained | Use `unlimitedStorage` permission to remove 10 MB cap |
| `sync` | 100 KB total | 8 KB per item | 512 items | 120 / min, 1,800 / hour | Values exceeding 8 KB fail silently in older versions |
| `session` | 10 MB | No per-item limit | No limit | No enforced limit | In-memory only; fast but ephemeral |
| `managed` | N/A | N/A | N/A | Read-only | Schema declared in `storage.managed_schema` manifest key |

---

## CRUD Operations

### Set (Create / Update)

```typescript
// Set one or more key-value pairs
await chrome.storage.local.set({
  userSettings: { theme: "dark", fontSize: 14 },
  lastSync: Date.now(),
});

// Sync storage — same API, different area
await chrome.storage.sync.set({
  preferredLanguage: "en",
});

// Session storage — available since Chrome 102
await chrome.storage.session.set({
  authToken: "eyJhbGciOi...",
});
```

### Get (Read)

```typescript
// Get specific keys with defaults
const result = await chrome.storage.local.get({
  userSettings: { theme: "light", fontSize: 12 }, // defaults if missing
  lastSync: 0,
});
console.log(result.userSettings.theme); // "dark" or "light" (default)

// Get specific keys without defaults (missing keys are absent from result)
const { authToken } = await chrome.storage.session.get("authToken");

// Get multiple keys
const data = await chrome.storage.sync.get(["preferredLanguage", "notifications"]);

// Get ALL keys in an area (use sparingly)
const everything = await chrome.storage.local.get(null);
```

### Remove (Delete)

```typescript
// Remove specific keys
await chrome.storage.local.remove("lastSync");
await chrome.storage.local.remove(["cachedData", "oldVersion"]);

// Clear everything in an area
await chrome.storage.local.clear();
```

### GetBytesInUse

```typescript
// Check quota usage
const bytes = await chrome.storage.sync.getBytesInUse(null); // all keys
console.log(`Using ${bytes} of ${chrome.storage.sync.QUOTA_BYTES} bytes`);

const perKey = await chrome.storage.sync.getBytesInUse("preferredLanguage");
console.log(`Key uses ${perKey} of ${chrome.storage.sync.QUOTA_BYTES_PER_ITEM} per-item limit`);
```

---

## Watching for Changes

### onChanged Listener

`chrome.storage.onChanged` fires whenever any value in any storage area is modified -- from any extension context (popup, background, content script, options page).

```typescript
// background.ts — listen to changes across all areas
chrome.storage.onChanged.addListener(
  (changes: { [key: string]: chrome.storage.StorageChange }, areaName: string) => {
    for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
      console.log(`[${areaName}] "${key}" changed:`, oldValue, "->", newValue);
    }
  }
);
```

### Area-Specific Listener (Chrome 104+)

```typescript
// Only fires for chrome.storage.local changes
chrome.storage.local.onChanged.addListener(
  (changes: { [key: string]: chrome.storage.StorageChange }) => {
    if (changes.userSettings) {
      applyTheme(changes.userSettings.newValue.theme);
    }
  }
);
```

### Practical Pattern: Reactive UI in Popup

```typescript
// popup.ts — keep UI in sync with storage
function init() {
  // Load initial state
  chrome.storage.local.get({ count: 0 }).then(({ count }) => {
    document.getElementById("counter")!.textContent = String(count);
  });

  // React to changes (including changes made by background)
  chrome.storage.local.onChanged.addListener((changes) => {
    if (changes.count) {
      document.getElementById("counter")!.textContent = String(changes.count.newValue);
    }
  });
}
```

---

## Type-Safe Storage Wrapper

Define a schema once, get typed getters and setters everywhere:

```typescript
// lib/storage.ts

/** Define your full storage schema here */
interface StorageSchema {
  userSettings: {
    theme: "light" | "dark" | "system";
    fontSize: number;
    sidebarCollapsed: boolean;
  };
  blockedSites: string[];
  stats: {
    totalBlocked: number;
    lastReset: number;
  };
  onboardingComplete: boolean;
}

/** Default values — used when keys are missing */
const DEFAULTS: StorageSchema = {
  userSettings: { theme: "system", fontSize: 14, sidebarCollapsed: false },
  blockedSites: [],
  stats: { totalBlocked: 0, lastReset: Date.now() },
  onboardingComplete: false,
};

type StorageKey = keyof StorageSchema;

/** Get one or more keys with typed defaults */
export async function getStorage<K extends StorageKey>(
  ...keys: K[]
): Promise<Pick<StorageSchema, K>> {
  const defaults = Object.fromEntries(keys.map((k) => [k, DEFAULTS[k]]));
  return chrome.storage.local.get(defaults) as Promise<Pick<StorageSchema, K>>;
}

/** Set one or more keys with type checking */
export async function setStorage(
  items: Partial<StorageSchema>
): Promise<void> {
  await chrome.storage.local.set(items);
}

/** Remove one or more keys */
export async function removeStorage(...keys: StorageKey[]): Promise<void> {
  await chrome.storage.local.remove(keys);
}

/** Subscribe to typed changes for specific keys */
export function onStorageChange<K extends StorageKey>(
  key: K,
  callback: (newValue: StorageSchema[K], oldValue: StorageSchema[K] | undefined) => void
): () => void {
  const listener = (changes: { [k: string]: chrome.storage.StorageChange }) => {
    if (key in changes) {
      callback(changes[key].newValue as StorageSchema[K], changes[key].oldValue as StorageSchema[K]);
    }
  };
  chrome.storage.local.onChanged.addListener(listener);
  return () => chrome.storage.local.onChanged.removeListener(listener);
}
```

Usage:

```typescript
import { getStorage, setStorage, onStorageChange } from "../lib/storage";

// Fully typed — no casts needed
const { userSettings, stats } = await getStorage("userSettings", "stats");
console.log(userSettings.theme); // "light" | "dark" | "system"

await setStorage({
  userSettings: { ...userSettings, theme: "dark" },
  stats: { ...stats, totalBlocked: stats.totalBlocked + 1 },
});

// Subscribe returns an unsubscribe function
const unsub = onStorageChange("blockedSites", (newSites, oldSites) => {
  console.log(`Sites changed: ${oldSites?.length ?? 0} -> ${newSites.length}`);
});
```

---

## Storage vs IndexedDB vs localStorage — Decision Table

| Criterion | `chrome.storage` | IndexedDB | `localStorage` |
|---|---|---|---|
| **Accessible from service worker** | Yes | Yes | **No** (no `window`) |
| **Accessible from content script** | `local` and `sync` yes; `session` only if `setAccessLevel` called | Yes (but uses page origin) | Yes (but uses page origin) |
| **Data synced across devices** | `sync` area only | No | No |
| **Max size** | 10 MB local (unlimited with permission); 100 KB sync | Hundreds of MB+ | 5-10 MB |
| **Structured queries** | No (key-value only) | Yes (indexes, cursors, ranges) | No |
| **Change events** | `onChanged` across all contexts | No built-in cross-context events | `storage` event (same origin, not SW) |
| **Transactions / atomicity** | No — last write wins | Full ACID transactions | No |
| **Performance** | Good for < 1,000 keys | Best for large datasets, blobs | Fast but blocking |
| **Survives extension update** | Yes | Yes | N/A (page origin) |

**Recommendations:**
- Use `chrome.storage.local` for extension settings, small caches, and state shared between popup and background.
- Use `chrome.storage.sync` only for small user preferences (< 100 KB total) that should follow the user.
- Use `chrome.storage.session` for per-session secrets like auth tokens.
- Use IndexedDB for large structured datasets (bookmarks, history, logs), binary blobs, or anything requiring indexed queries.
- Avoid `localStorage` in extensions -- it is unavailable in the service worker.

---

## Batch Operations and Atomic Updates

`chrome.storage` does not support transactions. Multiple `set` calls are independent. To perform a read-modify-write safely:

```typescript
// Read-modify-write pattern (not atomic but minimizes race window)
async function incrementCounter(key: string, amount: number): Promise<number> {
  const result = await chrome.storage.local.get({ [key]: 0 });
  const newValue = (result[key] as number) + amount;
  await chrome.storage.local.set({ [key]: newValue });
  return newValue;
}
```

For critical sections, use `chrome.storage.session` as a lock or serialize writes through the background service worker:

```typescript
// background.ts — serialized write queue
const writeQueue: Array<() => Promise<void>> = [];
let processing = false;

async function enqueueWrite(fn: () => Promise<void>) {
  writeQueue.push(fn);
  if (!processing) {
    processing = true;
    while (writeQueue.length > 0) {
      const task = writeQueue.shift()!;
      await task();
    }
    processing = false;
  }
}

// Usage
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "INCREMENT") {
    enqueueWrite(async () => {
      const { counter = 0 } = await chrome.storage.local.get("counter");
      await chrome.storage.local.set({ counter: counter + 1 });
      sendResponse({ counter: counter + 1 });
    });
    return true; // async
  }
});
```

### Batch Set

```typescript
// Set many keys at once — single I/O operation
await chrome.storage.local.set({
  key1: "value1",
  key2: "value2",
  key3: "value3",
  // all written in one call — more efficient than 3 separate set() calls
});
```

---

## Migration Patterns

### Migrating Data Between Storage Areas

```typescript
// background.ts — run once on install/update
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === "update") {
    await migrateLocalToSync();
  }
});

async function migrateLocalToSync() {
  const keysToMigrate = ["preferredLanguage", "notificationPrefs"];
  const localData = await chrome.storage.local.get(keysToMigrate);

  // Check if keys exist in local
  const toSync: Record<string, unknown> = {};
  for (const key of keysToMigrate) {
    if (key in localData) {
      // Validate size before syncing (8 KB per item limit)
      const size = new Blob([JSON.stringify(localData[key])]).size;
      if (size <= chrome.storage.sync.QUOTA_BYTES_PER_ITEM) {
        toSync[key] = localData[key];
      } else {
        console.warn(`Key "${key}" too large for sync (${size} bytes)`);
      }
    }
  }

  if (Object.keys(toSync).length > 0) {
    await chrome.storage.sync.set(toSync);
    await chrome.storage.local.remove(keysToMigrate);
    console.log("Migration complete:", Object.keys(toSync));
  }
}
```

### Schema Versioning

```typescript
// background.ts
const CURRENT_SCHEMA_VERSION = 3;

chrome.runtime.onInstalled.addListener(async () => {
  const { schemaVersion = 0 } = await chrome.storage.local.get("schemaVersion");

  if (schemaVersion < 2) {
    // v1 -> v2: rename "darkMode" to "theme"
    const { darkMode } = await chrome.storage.local.get("darkMode");
    if (darkMode !== undefined) {
      await chrome.storage.local.set({
        userSettings: { theme: darkMode ? "dark" : "light" },
      });
      await chrome.storage.local.remove("darkMode");
    }
  }

  if (schemaVersion < 3) {
    // v2 -> v3: add new default fields
    const { userSettings } = await chrome.storage.local.get("userSettings");
    await chrome.storage.local.set({
      userSettings: {
        theme: "system",
        fontSize: 14,
        sidebarCollapsed: false,
        ...userSettings, // preserve existing values
      },
    });
  }

  await chrome.storage.local.set({ schemaVersion: CURRENT_SCHEMA_VERSION });
});
```

---

## Session Storage Access from Content Scripts

By default, `chrome.storage.session` is only accessible from the extension's own pages (popup, background, options). To allow content scripts to access it:

```typescript
// background.ts — call once at startup
chrome.storage.session.setAccessLevel({
  accessLevel: "TRUSTED_AND_UNTRUSTED_CONTEXTS",
});
```

After this call, content scripts can read/write `chrome.storage.session`.

---

## Common Storage Pitfalls

| Pitfall | Details | Fix |
|---|---|---|
| **Storing non-serializable values** | Functions, `Date` objects, `Map`, `Set`, `undefined` values are silently dropped or converted to `null` | Convert to JSON-safe types before storing: `date.toISOString()`, `Array.from(set)`, `Object.fromEntries(map)` |
| **Exceeding sync per-item limit** | Items > 8,192 bytes in `chrome.storage.sync` are rejected | Split large objects across multiple keys, or move to `local` |
| **Forgetting `await`** | `chrome.storage.local.set(...)` returns a Promise in MV3 — forgetting `await` means you proceed before the write completes | Always `await` storage operations |
| **Reading in content script on page load** | Content script runs before storage is ready if the extension was just installed | Use `chrome.storage.local.get` with defaults; listen for `onChanged` to update |
| **Using `localStorage` in service worker** | `localStorage` is synchronous and DOM-only — not available in service workers | Use `chrome.storage.session` for ephemeral data, `chrome.storage.local` for persistent data |
| **Race conditions in read-modify-write** | Two contexts read the same key, modify it, and write back — last write wins, first write's changes are lost | Serialize writes through the background service worker (see write queue pattern above) |
| **`onChanged` fires for every set()** | Setting the same value triggers `onChanged` even if the value did not actually change | Compare `oldValue` and `newValue` in the listener before acting |
| **Managed storage requires OS-level policy** | `chrome.storage.managed` only works when the admin has deployed a policy JSON file on the device | Provide sensible defaults in code; treat managed values as overrides |
| **`clear()` removes everything** | `chrome.storage.local.clear()` wipes all keys, including schema version markers | Use `remove()` with specific keys instead, or re-set critical keys after `clear()` |
| **Storage quota exceeded silently** | In some Chrome versions, exceeding quota does not throw — the write just fails | Check `chrome.runtime.lastError` or wrap in try/catch; monitor with `getBytesInUse()` |

---

## Quick Reference: Method Summary

| Method | Area(s) | Description |
|---|---|---|
| `get(keys?)` | all | Read keys; pass `null` for all, object for defaults |
| `set(items)` | local, sync, session | Write one or more key-value pairs |
| `remove(keys)` | local, sync, session | Delete specific keys |
| `clear()` | local, sync, session | Delete all keys in the area |
| `getBytesInUse(keys?)` | local, sync, session | Check storage usage in bytes |
| `setAccessLevel(opts)` | session only | Allow content script access |
| `onChanged.addListener(cb)` | all (global or per-area) | React to value changes |

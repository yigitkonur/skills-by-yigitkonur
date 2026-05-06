# Cron services on Railway

Railway Cron is a service type that runs your container on a schedule, not continuously.

## Setup

CLI doesn't manage cron schedules — only the Railway UI does.

1. Railway dashboard → New Service → from existing source (same repo as web/worker)
2. Service Settings → Cron Schedule → enter cron expression (e.g., `0 * * * *` for hourly)
3. Custom Start Command → entrypoint (e.g., `node scripts/cron.js`)
4. Deploy via CLI normally: `railway up --service cron --detach`

## Scheduling syntax

Standard cron, 5 fields:

```
* * * * *
│ │ │ │ └── day of week (0-7, Sun=0 or 7)
│ │ │ └──── month (1-12)
│ │ └────── day of month (1-31)
│ └──────── hour (0-23, UTC)
└────────── minute (0-59)
```

Examples:

| Schedule | Meaning |
|---|---|
| `0 * * * *` | Every hour at :00 |
| `*/15 * * * *` | Every 15 minutes |
| `0 9 * * 1` | Monday at 09:00 UTC |
| `0 0 1 * *` | Midnight UTC on the 1st of each month |

All times are **UTC**. Compute the offset to your timezone manually.

## Writing the entrypoint

A cron service runs your start command, then exits. The container is killed when the script returns. Make it idempotent — Railway may invoke twice if the previous run hasn't exited.

```js
// scripts/cron.js
import { sweep } from '../src/lib/cron-jobs/sweep.js';

(async () => {
  try {
    await sweep();
    console.log('✓ cron sweep complete');
    process.exit(0);
  } catch (err) {
    console.error('✗ cron sweep failed:', err);
    process.exit(1);
  }
})();
```

Exit 0 = success in logs; exit non-zero = failure (Railway shows it red but doesn't retry automatically).

## Cron vs long-running worker

| Use cron when | Use a worker when |
|---|---|
| Job runs on a schedule, doesn't react to events | Job processes a queue or stream |
| < 5min runtime | Job needs warm state (DB connections, in-memory cache) |
| You want Railway to handle invocation | You're using BullMQ / similar queue library |

For zeo-radar's `RunEnqueueOutbox` dispatcher: that's a **worker** (continuously polls), not a cron. For "send weekly summary email": that's a **cron**.

## Cron service in `WEB_SERVICES`

The Makefile treats it like any other service:

```makefile
WEB_SERVICES := web worker cron

prod: _check-prod-prereqs
	@for svc in $(WEB_SERVICES); do \
	  railway up --detach --service $$svc -m "..." & \
	done; \
	wait
```

Deploy is identical. Railway just invokes the container on schedule instead of continuously.

## Logs

```bash
# See past cron runs
railway logs --service cron --tail 100
```

Each invocation shows up as a separate deployment-like entry in Railway dashboard (different from continuous-process logs).

## Local testing

Run the cron entrypoint as a one-shot:

```bash
npm run cron
# or
node scripts/cron.js
```

Same code path; different invoker.

## Don't use cron for queue processing

The temptation: "just run a cron every minute that pulls from BullMQ". Wrong:

- Cold start every invocation (slow)
- Race conditions if a previous invocation is still running
- No backpressure (cron doesn't know if you're swamped)

Use a worker service for queue processing. Use cron for time-driven jobs only.

## Schedule in code, not in CLI

Some libraries (`node-cron`, `agenda`) let you schedule from code. **Don't** — that means a long-running process holds the schedule, Railway can't see it, you can't change without redeploy. Use Railway Cron instead and let the platform manage scheduling.

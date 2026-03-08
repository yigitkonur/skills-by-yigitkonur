# Brooks's Law

## Origin

Fred Brooks, 1975, *The Mythical Man-Month*: "Adding manpower to a late software project makes it later."

Born from Brooks's experience managing the IBM OS/360 project — one of the largest software efforts of its era — where throwing more programmers at the schedule only deepened the delay.

## Explanation

The "man-month" is a myth because it assumes people and time are interchangeable. They are not. When you add N people to a project:

1. **Ramp-up time:** New people must learn the codebase, domain, tooling, and conventions. Existing team members must stop productive work to onboard them.
2. **Communication overhead:** The number of communication channels grows as **n * (n - 1) / 2**. A team of 5 has 10 channels; a team of 10 has 45; a team of 20 has 190.
3. **Task indivisibility:** Some work cannot be parallelized. Nine women cannot make a baby in one month.

The result: net productivity drops before it eventually (maybe) recovers.

## TypeScript Code Examples

### Bad: Splitting Tightly Coupled Work Across New Hires

```typescript
// Manager adds three new devs to "speed up" the auth rewrite.
// Each person takes a slice but creates integration nightmares.

// Dev A: handles login flow
export async function login(email: string, password: string): Promise<Session> {
  const user = await findUserByEmail(email); // Dev A assumes this returns null on miss
  // ...
}

// Dev B: handles user lookup (started same week)
export async function findUserByEmail(email: string): Promise<User> {
  const user = await db.users.findOne({ email });
  if (!user) throw new UserNotFoundError(email); // Dev B throws instead of returning null
  return user;
}

// Dev C: handles session creation
export function createSession(user: User): Session {
  return { userId: user.userId, token: generateToken() };
  // Dev C uses "userId" but Dev A's User type calls it "id"
}

// Result: three people working for two weeks with incompatible contracts.
// A single developer would have shipped in one week.
```

### Good: Keep the Critical Path with Experienced Developers

```typescript
// The experienced dev owns the auth rewrite end-to-end.
// New team members are assigned to independent, well-defined work
// with clear interfaces.

// auth/session.ts — owned by senior dev, single coherent module
interface AuthResult {
  readonly success: boolean;
  readonly session?: Session;
  readonly error?: AuthError;
}

export async function authenticate(
  email: string,
  password: string
): Promise<AuthResult> {
  const user = await userRepo.findByEmail(email);
  if (!user) return { success: false, error: AuthError.UserNotFound };

  const valid = await verifyPassword(password, user.passwordHash);
  if (!valid) return { success: false, error: AuthError.InvalidPassword };

  const session = sessionStore.create(user.id, { ttl: SESSION_TTL });
  return { success: true, session };
}

// New team members work on independent features with clear APIs:
// - notification preferences (independent module)
// - profile avatar upload (independent module)
// - audit log viewer (read-only, low risk)
```

## The Communication Overhead Formula

```
Channels = n * (n - 1) / 2

Team Size  |  Channels  |  Increase
-----------+------------+----------
    3      |      3     |     —
    5      |     10     |   +233%
    8      |     28     |   +180%
   10      |     45     |    +61%
   15      |    105     |   +133%
   20      |    190     |    +81%
   50      |   1225     |   +545%
```

Each channel is a potential source of miscommunication, blocking, and meetings.

## Alternatives and Mitigations

- **Brooks's own advice:** Add people early or not at all. Late additions guarantee ramp-up during crunch.
- **Reduce coupling:** If modules are truly independent, adding people to separate modules can help.
- **Surgical team model (Brooks):** One "surgeon" programmer supported by specialists (editor, tester, toolsmith). Minimizes communication while providing support.
- **Parallel independent workstreams:** Split by feature, not by layer.

## When NOT to Apply

- **Early-stage projects with clear parallel tracks:** If the architecture supports it, adding people early works.
- **Independent modules:** Adding a developer to a genuinely isolated service does not increase coupling with other teams.
- **Non-development bottlenecks:** If the project is late because of QA backlog or infrastructure provisioning, adding people to those specific functions may help.
- **Long timelines:** On a two-year project, adding people in month three gives ample ramp-up time.

## Trade-offs

| Approach | Benefit | Cost |
|---|---|---|
| Keep team small | Low overhead, coherent design | May miss deadline |
| Add people early | Parallel tracks, knowledge spread | Higher upfront cost |
| Add people late | Feels like "doing something" | Makes project later (Brooks's Law) |
| Reduce scope instead | Actually solves the timeline problem | Stakeholder pushback |

## Real-World Consequences

- **IBM OS/360 (1960s):** Brooks lived this. Thousands of programmers, years of delays. The canonical example.
- **Healthcare.gov (2013):** Multiple contractors added mid-project with no coordination framework. Launch was catastrophic.
- **The "second system effect":** Also from Brooks — the tendency to over-engineer the follow-up system — compounds with Brooks's Law when teams grow to build the bloated design.

## The Uncomfortable Truth

The correct response to a late project is usually one of:
1. **Cut scope** — ship less, ship on time.
2. **Extend the deadline** — if the market allows it.
3. **Improve process** — remove blockers instead of adding people.

Adding headcount is the managerial reflex that feels productive but rarely is.

## Further Reading

- Brooks, F. (1975, 1995). *The Mythical Man-Month: Essays on Software Engineering*
- DeMarco, T. & Lister, T. (1987). *Peopleware: Productive Projects and Teams*
- Putnam, L. & Myers, W. (1992). *Measures for Excellence*
- McConnell, S. (2006). *Software Estimation: Demystifying the Black Art*

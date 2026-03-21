---
title: Keep Functions Small and Focused on One Level of Abstraction
impact: HIGH
impactDescription: cuts cognitive load per function, enables isolated unit testing
tags: code, functions, srp, abstraction
---

## Keep Functions Small and Focused on One Level of Abstraction

Functions should do one thing, do it well, and do it only. When a function mixes high-level orchestration with low-level detail, readers must mentally jump between abstraction levels, increasing bug risk and making testing harder.

**Incorrect (mixed abstraction levels, multiple responsibilities):**

```typescript
async function processNewUserSignup(
  email: string,
  password: string,
  referralCode?: string,
): Promise<void> {
  // Low-level validation mixed with high-level flow
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new Error('Invalid email');
  }
  if (password.length < 8 || !/[A-Z]/.test(password) || !/\d/.test(password)) {
    throw new Error('Weak password');
  }

  // Data access mixed with business logic
  const existing = await db.query('SELECT id FROM users WHERE email = $1', [email]);
  if (existing.rows.length > 0) {
    throw new Error('Email taken');
  }

  const salt = await bcrypt.genSalt(12);
  const hashedPassword = await bcrypt.hash(password, salt);

  const result = await db.query(
    'INSERT INTO users (email, password_hash, created_at) VALUES ($1, $2, NOW()) RETURNING id',
    [email, hashedPassword],
  );
  const userId = result.rows[0].id;

  if (referralCode) {
    const referrer = await db.query('SELECT id FROM users WHERE referral_code = $1', [referralCode]);
    if (referrer.rows.length > 0) {
      await db.query('INSERT INTO referrals (referrer_id, referred_id) VALUES ($1, $2)', [
        referrer.rows[0].id, userId,
      ]);
      await db.query('UPDATE users SET credits = credits + 500 WHERE id = $1', [referrer.rows[0].id]);
    }
  }

  await sendgrid.send({
    to: email,
    subject: 'Welcome!',
    html: `<h1>Welcome</h1><p>Your account is ready.</p>`,
  });
}
```

**Correct (each function operates at one abstraction level):**

```typescript
async function processNewUserSignup(command: SignupCommand): Promise<UserId> {
  const validatedInput = validateSignupInput(command);
  await ensureEmailAvailable(validatedInput.email);

  const user = await createUser(validatedInput);
  await applyReferralCredit(user.id, command.referralCode);
  await sendWelcomeEmail(user.email);

  return user.id;
}

function validateSignupInput(command: SignupCommand): ValidatedSignupInput {
  const email = EmailAddress.parse(command.email);
  const password = StrongPassword.parse(command.password);
  return { email, password };
}

async function ensureEmailAvailable(email: EmailAddress): Promise<void> {
  const exists = await userRepository.existsByEmail(email);
  if (exists) {
    throw new EmailAlreadyTakenError(email);
  }
}

async function createUser(input: ValidatedSignupInput): Promise<User> {
  const hashedPassword = await passwordHasher.hash(input.password);
  return userRepository.create({
    email: input.email,
    passwordHash: hashedPassword,
  });
}

async function applyReferralCredit(
  newUserId: UserId,
  referralCode?: string,
): Promise<void> {
  if (!referralCode) return; // Guard clause for early return

  const referrer = await userRepository.findByReferralCode(referralCode);
  if (!referrer) return;

  await referralService.createReferral(referrer.id, newUserId);
}

async function sendWelcomeEmail(email: EmailAddress): Promise<void> {
  await emailService.send({
    to: email,
    template: EmailTemplate.Welcome,
  });
}
```

**When NOT to use this pattern:**
- Simple utility functions that are already small and cohesive (e.g., a 3-line formatter)
- Over-extracting single-line functions that obscure flow more than they clarify it
- Performance-critical tight loops where function call overhead matters

**Benefits:**
- Each function can be tested independently with clear inputs and outputs
- The top-level function reads like a summary of the business process
- Changes to email sending logic cannot accidentally break referral logic

Reference: [Clean Code Chapter 3 — Functions](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

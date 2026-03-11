# daisyUI 5 — Form Patterns

> **Purpose**: Complete reference for building forms with daisyUI 5's new form components — fieldset, validator, label, filter, and calendar.

---

## v5 Form Architecture

daisyUI 5 replaced `form-control` + `label-text` with semantic HTML elements:

| v4 (removed) | v5 (use this) |
|--------------|---------------|
| `<div class="form-control">` | `<fieldset class="fieldset">` |
| `<label class="label"><span class="label-text">` | `<legend class="fieldset-legend">` or `<label class="fieldset-label">` |
| `<label class="label"><span class="label-text-alt">` | `<label class="fieldset-label">` |
| `input-bordered` | `input` (borders are default in v5) |
| `select-bordered` | `select` (borders are default in v5) |

---

## Basic Form Field

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Email</legend>
  <input type="email" class="input" placeholder="you@example.com" />
  <label class="fieldset-label">We'll never share your email</label>
</fieldset>
```

### With Validation

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Password</legend>
  <input type="password" class="input validator" required minlength="8" />
  <div class="validator-hint">Must be at least 8 characters</div>
</fieldset>
```

The `validator` class on the input activates CSS-only validation styling:
- Valid input → success color on focus
- Invalid input (after user interaction) → error color + `validator-hint` becomes visible

---

## Complete Login Form

```html
<div class="card bg-base-100 shadow-lg w-full max-w-sm mx-auto">
  <div class="card-body">
    <h2 class="card-title text-2xl">Login</h2>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Email</legend>
      <input type="email" class="input w-full validator" required
             placeholder="you@example.com" />
      <div class="validator-hint">Enter a valid email address</div>
    </fieldset>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Password</legend>
      <input type="password" class="input w-full validator" required
             minlength="8" />
      <div class="validator-hint">Minimum 8 characters</div>
    </fieldset>

    <div class="flex items-center justify-between mt-2">
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" class="checkbox checkbox-sm" />
        <span class="text-sm">Remember me</span>
      </label>
      <a href="#" class="link link-primary text-sm">Forgot password?</a>
    </div>

    <button class="btn btn-primary w-full mt-4">Login</button>
  </div>
</div>
```

---

## Floating Labels

```html
<label class="floating-label">
  <span>Email</span>
  <input type="email" class="input" placeholder="you@example.com" />
</label>
```

When the input has focus or content, the label floats above. No JavaScript needed.

### Floating Label Sizes

```html
<label class="floating-label">
  <span>Small</span>
  <input type="text" class="input input-sm" placeholder="..." />
</label>

<label class="floating-label">
  <span>Default</span>
  <input type="text" class="input" placeholder="..." />
</label>

<label class="floating-label">
  <span>Large</span>
  <input type="text" class="input input-lg" placeholder="..." />
</label>
```

---

## Input Variants

### Text Input with Icon

```html
<label class="input">
  <svg class="h-[1em] opacity-50" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
    <path d="M..." />
  </svg>
  <input type="text" required placeholder="Search..." />
</label>
```

### Input Sizes

```html
<input type="text" class="input input-xs" placeholder="Extra small" />
<input type="text" class="input input-sm" placeholder="Small" />
<input type="text" class="input input-md" placeholder="Medium (default)" />
<input type="text" class="input input-lg" placeholder="Large" />
<input type="text" class="input input-xl" placeholder="Extra large" />
```

### Input Colors

```html
<input type="text" class="input input-primary" placeholder="Primary" />
<input type="text" class="input input-secondary" placeholder="Secondary" />
<input type="text" class="input input-accent" placeholder="Accent" />
<input type="text" class="input input-info" placeholder="Info" />
<input type="text" class="input input-success" placeholder="Success" />
<input type="text" class="input input-warning" placeholder="Warning" />
<input type="text" class="input input-error" placeholder="Error" />
```

### Ghost Input (No Border)

```html
<input type="text" class="input input-ghost" placeholder="No border" />
```

---

## Select

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Country</legend>
  <select class="select w-full">
    <option disabled selected>Pick a country</option>
    <option>United States</option>
    <option>United Kingdom</option>
    <option>Canada</option>
  </select>
</fieldset>
```

### Ghost Select

```html
<select class="select select-ghost">
  <option>No border variant</option>
</select>
```

---

## Textarea

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Message</legend>
  <textarea class="textarea w-full h-24" placeholder="Write your message..."></textarea>
  <label class="fieldset-label">Max 500 characters</label>
</fieldset>
```

---

## Checkbox & Toggle

```html
<!-- Checkbox -->
<fieldset class="fieldset">
  <legend class="fieldset-legend">Preferences</legend>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="checkbox" class="checkbox" />
    <span>Email notifications</span>
  </label>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="checkbox" class="checkbox checkbox-primary" checked />
    <span>Push notifications</span>
  </label>
</fieldset>

<!-- Toggle -->
<fieldset class="fieldset">
  <legend class="fieldset-legend">Settings</legend>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="checkbox" class="toggle toggle-primary" />
    <span>Dark mode</span>
  </label>
</fieldset>
```

### Checkbox / Toggle Sizes

```html
<input type="checkbox" class="checkbox checkbox-xs" />
<input type="checkbox" class="checkbox checkbox-sm" />
<input type="checkbox" class="checkbox" />  <!-- md default -->
<input type="checkbox" class="checkbox checkbox-lg" />
<input type="checkbox" class="checkbox checkbox-xl" />
```

---

## Radio Buttons

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Plan</legend>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="radio" name="plan" class="radio radio-primary" checked />
    <span>Free</span>
  </label>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="radio" name="plan" class="radio radio-primary" />
    <span>Pro — $9/month</span>
  </label>
  <label class="flex items-center gap-3 cursor-pointer">
    <input type="radio" name="plan" class="radio radio-primary" />
    <span>Enterprise — Contact us</span>
  </label>
</fieldset>
```

---

## File Input

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Upload Avatar</legend>
  <input type="file" class="file-input w-full" />
  <label class="fieldset-label">PNG, JPG up to 5MB</label>
</fieldset>
```

Note: `file-input` has borders by default in v5. Use `file-input-ghost` for borderless.

---

## Range Slider

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Volume</legend>
  <input type="range" class="range range-primary" min="0" max="100" value="50" />
</fieldset>
```

---

## Filter Component (New in v5)

Radio button group with filter styling and a reset button:

```html
<div class="filter">
  <input class="btn btn-square" type="reset" value="×" />
  <input class="btn" type="radio" name="filter" aria-label="All" />
  <input class="btn" type="radio" name="filter" aria-label="Action" />
  <input class="btn" type="radio" name="filter" aria-label="Comedy" />
  <input class="btn" type="radio" name="filter" aria-label="Drama" />
</div>
```

---

## Validator Component (New in v5)

CSS-only validation that shows hints when input is invalid after user interaction:

```html
<input type="email" class="input validator" required placeholder="Email" />
<div class="validator-hint">Please enter a valid email</div>
```

### How It Works

1. `validator` class on the input enables validation styling
2. After user types and leaves the field (`:user-invalid` state), invalid inputs show error color
3. `validator-hint` div below the input becomes visible only when invalid
4. Valid inputs show success color

### Validator with Multiple Rules

```html
<input type="text" class="input validator" required
       minlength="3" maxlength="20" pattern="[a-zA-Z0-9_]+" />
<div class="validator-hint">
  3-20 characters, letters, numbers, and underscores only
</div>
```

---

## Joined Input Groups

Use `join` to combine inputs with buttons or other elements:

```html
<div class="join">
  <input type="text" class="input join-item" placeholder="Search..." />
  <button class="btn btn-primary join-item">Search</button>
</div>
```

### Email Subscribe

```html
<div class="join">
  <input type="email" class="input join-item" placeholder="your@email.com" />
  <button class="btn btn-neutral join-item">Subscribe</button>
</div>
```

---

## Complete Registration Form

```html
<form class="card bg-base-100 shadow-lg max-w-lg mx-auto">
  <div class="card-body gap-4">
    <h2 class="card-title text-2xl">Create Account</h2>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <fieldset class="fieldset">
        <legend class="fieldset-legend">First Name</legend>
        <input type="text" class="input w-full validator" required />
        <div class="validator-hint">Required</div>
      </fieldset>

      <fieldset class="fieldset">
        <legend class="fieldset-legend">Last Name</legend>
        <input type="text" class="input w-full validator" required />
        <div class="validator-hint">Required</div>
      </fieldset>
    </div>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Email</legend>
      <input type="email" class="input w-full validator" required />
      <div class="validator-hint">Enter a valid email address</div>
    </fieldset>

    <fieldset class="fieldset">
      <legend class="fieldset-legend">Password</legend>
      <input type="password" class="input w-full validator" required
             minlength="8" />
      <div class="validator-hint">Minimum 8 characters</div>
    </fieldset>

    <label class="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" class="checkbox checkbox-sm validator" required />
      <span class="text-sm">I agree to the Terms of Service</span>
    </label>

    <button class="btn btn-primary w-full">Create Account</button>

    <p class="text-center text-sm">
      Already have an account? <a href="#" class="link link-primary">Login</a>
    </p>
  </div>
</form>
```

---

## Common Form Mistakes

| Mistake | Fix |
|---------|-----|
| Using `form-control` class | Removed in v5 — use `<fieldset class="fieldset">` |
| Using `label-text` / `label-text-alt` | Use `fieldset-legend` for title, `fieldset-label` for helper text |
| Adding `input-bordered` | Borders are default in v5 — use `input-ghost` for borderless |
| Adding `select-bordered` | Borders are default in v5 — use `select-ghost` for borderless |
| Missing `w-full` on inputs | v5 inputs have a default width of 20rem — add `w-full` for full-width |
| Wrapping radio/checkbox in `form-control` | Use `<fieldset>` or flex layout directly |
| Using JavaScript for validation display | `validator` + `validator-hint` is CSS-only |

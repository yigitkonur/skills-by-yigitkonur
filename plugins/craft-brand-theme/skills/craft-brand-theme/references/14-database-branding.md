# Database Branding: Logo, Theme, and Font Persistence

This reference documents how to update application databases with brand assets (logos, theme selection, custom fonts) so branding persists across sessions, devices, and server restarts.

---

## 1. Why Database Branding Is Required

CSS token injection handles the visual rendering, but modern platforms store branding state in the database:

| What's Stored | Where It's Used | What Happens If Missing |
| :--- | :--- | :--- |
| `organization.logo` | Auth screens, sidebar header, loading screens | Default platform logo appears |
| `organization.logo_dark` | Dark mode logo variant | Light logo renders on dark background (invisible) |
| `organization.icon_logo` | Collapsed sidebar, favicon, mobile PWA icon | Default icon appears |
| `organization.theme` | Theme selection for the organization | Defaults to `caffeine` or platform default |
| `organization.custom_font` | Font preference metadata | Platform default font stack used |

Without database updates, the theme applies visually but the logo shows the default platform branding.

---

## 2. Preparing SVG Logo Assets

### Mask-Free Flat SVG Construction

Database-stored logos are often rendered inside `<img>` tags or as CSS `background-image` data URIs. Complex SVGs with `<defs>`, `<mask>`, `<clipPath>`, or `<use xlink:href>` cause rendering failures:

- **Safari**: Strips `<use xlink:href>` inside data URIs entirely.
- **Chrome**: `<mask id="...">` may ID-collide with other SVGs on the same page.
- **Firefox**: `<clipPath>` references break when SVG is base64-encoded.

**Solution**: Build flat, canonical SVGs with direct `<path fill="...">` attributes:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="91" height="33" viewBox="0 0 91 33">
  <g fill="none" fill-rule="evenodd">
    <path fill="#CC0A4D" d="M.674 2.536..."/>   <!-- Brand mark -->
    <path fill="#FFFFFF" d="M21.45 19.031..."/>  <!-- Inner detail -->
    <path fill="#0F1A2A" d="M64.219 9..."/>      <!-- Wordmark (dark ink for light bg) -->
  </g>
</svg>
```

### Dual-Variant Logo Set

Prepare two wordmark variants:
- **Light mode logo**: Wordmark ink = dark (`#0F1A2A`)
- **Dark mode logo**: Wordmark ink = light (`#EEF2F7`)

The brand mark (crimson shield) remains identical in both variants.

### Icon Logo

A compact mark-only version for collapsed sidebar and favicon contexts:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="36" height="33" viewBox="0 0 36 33">
  <g fill="none" fill-rule="evenodd">
    <path fill="#CC0A4D" d="M.674 2.536..."/>
    <path fill="#FFFFFF" d="M21.45 19.031..."/>
  </g>
</svg>
```

---

## 3. Base64 Data URI Encoding

Convert SVGs to RFC 2397 data URIs for database storage:

```python
import base64

svg_light = '<svg xmlns="http://www.w3.org/2000/svg" ...>...</svg>'
svg_dark  = '<svg xmlns="http://www.w3.org/2000/svg" ...>...</svg>'
svg_icon  = '<svg xmlns="http://www.w3.org/2000/svg" ...>...</svg>'

uri_light = "data:image/svg+xml;base64," + base64.b64encode(svg_light.encode()).decode()
uri_dark  = "data:image/svg+xml;base64," + base64.b64encode(svg_dark.encode()).decode()
uri_icon  = "data:image/svg+xml;base64," + base64.b64encode(svg_icon.encode()).decode()
```

### Why Base64 Over URL-Encoded

- Base64 is universally safe in SQL string literals (no quote escaping issues).
- Browser `<img src="data:...">` decodes base64 natively.
- No dependency on external file hosting or CDN availability.

---

## 4. SQL Update Pattern

### Reading the Database URL

```python
import os

db_url = os.environ.get("APP_DATABASE_URL", "")
if not db_url:
    print("Database URL not set; skipping branding update.")
    return False

# Strip query parameters for clean psql connection
clean_db_url = db_url.split("?")[0]
```

### Executing the Update

```python
import subprocess

sql = f"""
UPDATE organization
SET logo = '{uri_light}',
    logo_dark = '{uri_dark}',
    icon_logo = '{uri_icon}',
    icon_logo_dark = '{uri_icon}',
    theme = 'zeo-custom',
    custom_font = 'inter'
WHERE name = 'Zeo' OR name ILIKE '%zeo%';
"""

p = subprocess.Popen(
    ["psql", clean_db_url],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
out, err = p.communicate(input=sql.encode())

if p.returncode == 0:
    print("Database branding updated successfully.")
else:
    print(f"psql error: {err.decode('utf-8', errors='ignore')}")
```

### Idempotency

SQL `UPDATE` is naturally idempotent — running it multiple times produces the same result. No special guard needed beyond ensuring the `WHERE` clause is specific enough to avoid updating unrelated rows.

### Multi-Row Safety

Use `ILIKE` for fuzzy matching when the organization name might vary:

```sql
WHERE name = 'Zeo' OR name ILIKE '%zeo%'
```

This handles cases where the org was created with different capitalization or includes a suffix.

---

## 5. Verification

After updating, verify the database state:

```bash
docker exec <container> psql "$APP_DATABASE_URL" -c \
  "SELECT name, theme, length(logo) as logo_bytes, length(logo_dark) as dark_bytes FROM organization WHERE theme = 'zeo-custom';"
```

Expected output:

```
 name | theme      | logo_bytes | dark_bytes
------+------------+------------+------------
 Zeo  | zeo-custom |       1847 |       1823
```

---

## 6. Platform-Specific Notes

| Platform | Logo Column | Theme Column | Notes |
| :--- | :--- | :--- | :--- |
| Archestra | `organization.logo` | `organization.theme` | Also has `icon_logo`, `icon_logo_dark`, `custom_font` |
| LibreChat | `config.appTitle`, `config.customFooter` | N/A (env-based) | Branding via `.env` not database |
| Open WebUI | `config.name` | `config.default_theme` | JSON config table, not SQL columns |

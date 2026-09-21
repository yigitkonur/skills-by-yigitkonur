# Local Font Engine, Zero Remote Fonts & Glyph Invariants

This reference encodes the non-negotiable laws of typography deployment, local binary hosting, and the Turkish Weight-300 Remap Invariant.

---

## 1. The Font Law: Zero Remote Fonts

> **Mandate**: Never load remote fonts in enterprise software. No `fonts.googleapis.com`, no Typekit, no external CDNs. Local offline binaries only.

### Three Technical & Legal Reasons
1. **Air-Gapped & Enterprise VPN Compatibility**:
   - Internal enterprise tools and security platforms are frequently executed behind corporate proxies and firewalls (Zscaler, Palo Alto Networks, FortiGate).
   - Corporate egress filtering routinely sinkholes third-party font CDNs, leading to broken typography, page rendering stalls, or Flash of Invisible Text (FOIT).
   - Local binaries load deterministically with `HTTP 200` directly from the application origin (`/fonts/<name>.woff2`).
2. **GDPR & KVKK Compliance**:
   - European and Turkish Data Protection Authorities classify IP addresses transmitted to third-party CDNs (like Google Fonts) as personal data. Local origin hosting eliminates regulatory liability.
3. **Zero Cumulative Layout Shift (CLS)**:
   - External font CDN latency introduces Flash of Unstyled Text (FOUT) and layout shifts. Local fonts preloaded or cached with `max-age=14400` guarantee zero layout shift.

---

## 2. Serving Fonts via Next.js Origin

Next.js automatically serves any file placed inside the `/public/` directory from the root web path:
- File located at: `/app/frontend/public/fonts/AkagiPro-Book.woff2`
- Delivered over HTTPS at: `https://<domain>/fonts/AkagiPro-Book.woff2`
- Headers: `content-type: font/woff2`, `accept-ranges: bytes`, `cache-control: public, max-age=14400`.

### Python Automated Deployment Snippet
```python
def deploy_fonts(src_dir="/app/data/patches/fonts", dst_dir="/app/frontend/public/fonts"):
    import os, shutil
    if not os.path.exists(src_dir):
        return False
    os.makedirs(dst_dir, exist_ok=True)
    copied = 0
    for fname in os.listdir(src_dir):
        if fname.endswith(".woff2") or fname.endswith(".ttf"):
            shutil.copy2(os.path.join(src_dir, fname), os.path.join(dst_dir, fname))
            copied += 1
    return copied > 0
```

> **Note on Next.js Static Manifest**: If files are copied to `/public/` while `next-server` is actively running, Next.js may return `404` until the process is restarted, because the standalone server indexes the public directory at startup. Always trigger a graceful restart (`pkill -9 -f next-server`) after deploying new font files.

---

## 3. The Turkish Weight-300 Remap Invariant

### The Empirical Defect
In many commercial and custom font families (including Akagi Pro), the lighter cut (`Light.ttf`, ~39 KB) contains only the basic Latin-1 character set and **completely lacks Latin Extended-A Turkish characters**:
- `ğ` (`U+011F`), `Ğ` (`U+011E`)
- `ş` (`U+015F`), `Ş` (`U+015E`)
- `ı` (`U+0131`), `İ` (`U+0130`)

In contrast, the Book cut (`Book.ttf`, ~144 KB) contains 100% complete Latin Extended-A coverage.

### The Catastrophic Mid-Word Fallback
When an application specifies `font-weight: 300` pointing to a defective Light font:
Text such as *"Ilık ırmak kıyısında, çağdaş değerlendirme yapıldı"* fractures:
- ASCII characters render in `AkagiPro-Light`.
- Turkish characters (`ı`, `ğ`, `ş`, `İ`) fall back to system Arial or Roboto.
- **Baseline Jumping**: Differing font metrics cause Turkish letters to jump 1–2px above or below the baseline.
- **Stem Clashing**: Stem thickness clashes jarringly inside the same word (`d - e - ğ - e - r`).
- **Kerning Destruction**: Cross-font kerning fails, creating unnatural gaps.

### The Canonical Remap Rule
```css
/* =============================================================================
   MANDATORY INVARIANT: Weight 300 MUST explicitly bind to Book.woff2
   Never allow Light.woff2 or Light.ttf in any @font-face declaration!
   ============================================================================= */

@font-face {
  font-family: 'Akagi Pro';
  src: local('Akagi Pro Book'),
       local('AkagiPro-Book'),
       url('/fonts/AkagiPro-Book.woff2') format('woff2');
  font-weight: 300; /* EXPLICITLY REMAPPED TO BOOK */
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Akagi Pro';
  src: local('Akagi Pro Book'),
       local('AkagiPro-Book'),
       url('/fonts/AkagiPro-Book.woff2') format('woff2');
  font-weight: 400; /* BOOK */
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Akagi Pro';
  src: local('Akagi Pro SemiBold'),
       local('AkagiPro-SemiBold'),
       url('/fonts/AkagiPro-SemiBold.woff2') format('woff2');
  font-weight: 600;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Akagi Pro';
  src: local('Akagi Pro Bold'),
       local('AkagiPro-Bold'),
       url('/fonts/AkagiPro-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

---

## 4. Automated Glyph Repertoire Verification (Python Script)

Use this script to audit any font binary for complete Turkish glyph support:

```python
from fontTools.ttLib import TTFont

MANDATORY_TURKISH_GLYPHS = ['ğ', 'Ğ', 'ş', 'Ş', 'ı', 'İ', 'ç', 'Ç', 'ö', 'Ö', 'ü', 'Ü']

def audit_font_glyphs(font_path):
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    missing = [char for char in MANDATORY_TURKISH_GLYPHS if ord(char) not in cmap]
    if missing:
        raise ValueError(f"CRITICAL DEFECT: Font {font_path} lacks Turkish glyphs: {missing}")
    print(f"VERIFIED: {font_path} contains 100% of all 12 Turkish glyphs.")

# Compress TTF to WOFF2 on the fly if needed
def convert_ttf_to_woff2(ttf_path, woff2_path):
    font = TTFont(ttf_path)
    font.flavor = 'woff2'
    font.save(woff2_path)
```

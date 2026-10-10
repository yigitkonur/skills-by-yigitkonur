#!/usr/bin/env bash
# ==============================================================================
# validate-capture-gate.sh — Screen & State Capture Verification Gate
#
# Hardened pre-evaluation gate for vision-first UI/UX audit artifacts.
# Validates directory schemas, multi-density assets, deep PNG chunk structures,
# file sizes, symlinks, and standard state coverage with discrete exit codes.
#
# Usage:
#   bash skills/audit-ui-ux/scripts/validate-capture-gate.sh <artifacts-dir>
# Example:
#   bash skills/audit-ui-ux/scripts/validate-capture-gate.sh audit-artifacts/2026-10-10
#
# Discrete Exit Codes:
#   0 = Success (all screens & states valid)
#   1 = Invalid arguments or non-existent target directory
#   2 = Target directory contains zero screen targets or images
#   3 = Mandatory default state (default.png / default@2x.png) missing
#   4 = Corrupt, truncated, zero-byte, or CRC-mismatched PNG detected
#   5 = Broken or circular symlinks detected
# ==============================================================================

set -euo pipefail

# Discrete exit code definitions
readonly EXIT_SUCCESS=0
readonly EXIT_INVALID_ARGS=1
readonly EXIT_NO_SCREENS=2
readonly EXIT_MISSING_DEFAULT=3
readonly EXIT_CORRUPT_OR_EMPTY=4
readonly EXIT_BROKEN_SYMLINK=5

TARGET_DIR="${1:-}"

if [[ -z "$TARGET_DIR" ]]; then
  echo "❌ Error: Missing target directory."
  echo "Usage: $0 <path-to-audit-artifacts-or-date-dir>"
  exit "$EXIT_INVALID_ARGS"
fi

if [[ ! -e "$TARGET_DIR" ]]; then
  if [[ -L "$TARGET_DIR" ]]; then
    target=$(readlink "$TARGET_DIR" 2>/dev/null || echo "unknown")
    echo "❌ Error: Target directory is a broken symlink: $TARGET_DIR -> $target"
    echo "  Remediation:"
    echo "    Fix or remove broken symlink:"
    echo "      rm \"$TARGET_DIR\""
    exit "$EXIT_BROKEN_SYMLINK"
  fi
  echo "❌ Error: Target directory does not exist: $TARGET_DIR"
  exit "$EXIT_INVALID_ARGS"
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "❌ Error: Target path is not a directory: $TARGET_DIR"
  exit "$EXIT_INVALID_ARGS"
fi

# Strip trailing slash if present (unless root /)
if [[ "$TARGET_DIR" != "/" ]]; then
  TARGET_DIR="${TARGET_DIR%/}"
fi

echo "🔍 Validating capture gate for: $TARGET_DIR"

ERRORS=0
WARNINGS=0
TOTAL_SCREENS=0
TOTAL_IMAGES=0

BROKEN_SYMLINK_COUNT=0
CORRUPT_COUNT=0
MISSING_DEFAULT_COUNT=0

STANDARD_BASE_STATES=(
  "default"
  "hover"
  "active"
  "empty-state"
  "error-state"
  "loading"
  "modal-open"
)

# ==============================================================================
# Helper: Deep 3-Gate PNG Validation
# Gate A: Filesystem & Size (reject 0-byte and < 67 bytes)
# Gate B: Binary Magic Header, IHDR chunk (offset 12), and IEND chunk (tail 12 bytes)
# Gate C: Decoder & CRC Integrity Check (Python CRC parser + sips fallback)
# ==============================================================================
validate_png_file() {
  local file_path="$1"
  local screen_name="$2"
  local file_name
  file_name=$(basename "$file_path")

  # Gate A1: Symlink check
  if [[ -L "$file_path" ]]; then
    if [[ ! -e "$file_path" ]]; then
      local link_target
      link_target=$(readlink "$file_path" 2>/dev/null || echo "unknown")
      echo "  ❌ [Broken Symlink] $screen_name/$file_name points to nonexistent target: $link_target"
      echo "  Remediation for dangling symlink [$screen_name/$file_name]:"
      echo "    Relink to existing capture:"
      echo "      ln -sf \"default.png\" \"$file_path\""
      echo "    Or remove symlink if state is not applicable:"
      echo "      rm \"$file_path\""
      BROKEN_SYMLINK_COUNT=$((BROKEN_SYMLINK_COUNT + 1))
      ERRORS=$((ERRORS + 1))
      return 1
    else
      echo "  ℹ️  [Symlink] Verified valid symlink: $file_name -> $(readlink "$file_path")"
    fi
  fi

  # Gate A2: Filesize check
  local file_size
  file_size=$(wc -c < "$file_path" 2>/dev/null | tr -d ' ' || echo 0)

  if [[ "$file_size" -eq 0 ]]; then
    echo "  ❌ [Empty File] $screen_name/$file_name has 0 bytes."
    echo "  Remediation for damaged file [$screen_name/$file_name]:"
    echo "    1. Remove corrupted artifact:"
    echo "       rm \"$file_path\""
    echo "    2. Re-trigger capture or check network transfer:"
    echo "       ego-browser screenshot \"$file_path\""
    CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
    ERRORS=$((ERRORS + 1))
    return 1
  fi

  if [[ "$file_size" -lt 67 ]]; then
    echo "  ❌ [Truncated PNG] $screen_name/$file_name is only $file_size bytes (minimum valid PNG datastream is 67 bytes)."
    echo "  Remediation for damaged file [$screen_name/$file_name]:"
    echo "    1. Remove corrupted artifact:"
    echo "       rm \"$file_path\""
    echo "    2. Re-trigger capture or check SCP network transfer:"
    echo "       ego-browser screenshot \"$file_path\""
    CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
    ERRORS=$((ERRORS + 1))
    return 1
  fi

  # Gate B1: PNG Signature Magic Header (First 8 bytes must be 89 50 4E 47 0D 0A 1A 0A)
  local magic
  magic=$(od -N 8 -t x1 "$file_path" 2>/dev/null | head -n 1 | awk '{$1=""; print $0}' | tr -d ' ' | tr '[:upper:]' '[:lower:]')
  if [[ "$magic" != "89504e470d0a1a0a" ]]; then
    echo "  ❌ [Corrupt PNG] $screen_name/$file_name has invalid signature magic: $magic (expected: 89504e470d0a1a0a)."
    echo "  Remediation for damaged file [$screen_name/$file_name]:"
    echo "    1. Remove corrupted artifact:"
    echo "       rm \"$file_path\""
    echo "    2. Re-trigger capture:"
    echo "       ego-browser screenshot \"$file_path\""
    CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
    ERRORS=$((ERRORS + 1))
    return 1
  fi

  # Gate B2: IHDR Chunk Header at offset 12 (Must be 49 48 44 52)
  local ihdr_chunk
  ihdr_chunk=$(od -j 12 -N 4 -t x1 "$file_path" 2>/dev/null | head -n 1 | awk '{$1=""; print $0}' | tr -d ' ' | tr '[:upper:]' '[:lower:]')
  if [[ "$ihdr_chunk" != "49484452" ]]; then
    echo "  ❌ [Corrupt PNG] $screen_name/$file_name missing mandatory IHDR chunk at offset 12 (got: $ihdr_chunk)."
    echo "  Remediation for damaged file [$screen_name/$file_name]:"
    echo "    1. Remove corrupted artifact:"
    echo "       rm \"$file_path\""
    echo "    2. Re-trigger capture:"
    echo "       ego-browser screenshot \"$file_path\""
    CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
    ERRORS=$((ERRORS + 1))
    return 1
  fi

  # Gate B3: Terminal IEND Chunk (Tail 12 bytes must be 00 00 00 00 49 45 4E 44 AE 42 60 82)
  local iend_chunk
  iend_chunk=$(tail -c 12 "$file_path" 2>/dev/null | od -t x1 | head -n 1 | awk '{$1=""; print $0}' | tr -d ' ' | tr '[:upper:]' '[:lower:]')
  if [[ "$iend_chunk" != "0000000049454e44ae426082" ]]; then
    echo "  ❌ [Truncated PNG] $screen_name/$file_name missing or corrupted terminal IEND chunk (tail 12 bytes: $iend_chunk)."
    echo "  Remediation for damaged file [$screen_name/$file_name]:"
    echo "    1. Remove corrupted artifact:"
    echo "       rm \"$file_path\""
    echo "    2. Re-trigger capture or check SCP network transfer:"
    echo "       ego-browser screenshot \"$file_path\""
    CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
    ERRORS=$((ERRORS + 1))
    return 1
  fi

  # Gate C: Decoder and Deep Chunk CRC Verification
  local decoded=false
  if command -v python3 &>/dev/null; then
    local py_status=0
    python3 -c '
import struct, zlib, sys
path = sys.argv[1]
try:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 67 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[-12:] != b"\x00\x00\x00\x00IEND\xaeB`\x82":
        sys.exit(1)
    offset = 8
    has_ihdr = False
    has_iend = False
    while offset < len(data):
        if offset + 8 > len(data): sys.exit(2)
        length, chunk_type = struct.unpack(">I4s", data[offset:offset+8])
        offset += 8
        if offset + length + 4 > len(data): sys.exit(3)
        chunk_data = data[offset:offset+length]
        crc = struct.unpack(">I", data[offset+length:offset+length+4])[0]
        offset += length + 4
        if crc != (zlib.crc32(chunk_type + chunk_data) & 0xffffffff):
            sys.exit(4)
        if chunk_type == b"IHDR": has_ihdr = True
        elif chunk_type == b"IEND": has_iend = True; break
    if not (has_ihdr and has_iend): sys.exit(5)
    sys.exit(0)
except Exception:
    sys.exit(9)
' "$file_path" 2>/dev/null || py_status=$?

    if [[ "$py_status" -ne 0 ]]; then
      echo "  ❌ [Corrupt PNG] $screen_name/$file_name failed chunk structure/CRC validation (code: $py_status)."
      echo "  Remediation for damaged file [$screen_name/$file_name]:"
      echo "    1. Remove corrupted artifact:"
      echo "       rm \"$file_path\""
      echo "    2. Re-trigger capture:"
      echo "       ego-browser screenshot \"$file_path\""
      CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
      ERRORS=$((ERRORS + 1))
      return 1
    fi
    decoded=true
  fi

  if [[ "$decoded" == "false" ]] && command -v sips &>/dev/null; then
    if ! sips -g pixelWidth -g pixelHeight "$file_path" 2>&1 | grep -q "pixelWidth: [0-9]"; then
      echo "  ❌ [Corrupt PNG] $screen_name/$file_name failed sips decoder validation."
      echo "  Remediation for damaged file [$screen_name/$file_name]:"
      echo "    1. Remove corrupted artifact:"
      echo "       rm \"$file_path\""
      echo "    2. Recapture screenshot:"
      echo "       ego-browser screenshot \"$file_path\""
      CORRUPT_COUNT=$((CORRUPT_COUNT + 1))
      ERRORS=$((ERRORS + 1))
      return 1
    fi
  fi

  TOTAL_IMAGES=$((TOTAL_IMAGES + 1))
  return 0
}

# ==============================================================================
# Screen Discovery
# Identifies screen subdirectories or standalone root screen
# ==============================================================================
SCREEN_DIRS=()
ROOT_BROKEN_SYMLINKS=()

shopt -s nullglob
target_entries=("$TARGET_DIR"/*)
shopt -u nullglob

has_subdirs=false
if [[ ${#target_entries[@]} -gt 0 ]]; then
  for item in "${target_entries[@]}"; do
    if [[ -L "$item" && ! -e "$item" ]]; then
      # Broken directory or file symlink at root
      target=$(readlink "$item" 2>/dev/null || echo "unknown")
      echo "  ❌ [Broken Symlink] Entry points to nonexistent target: $(basename "$item") -> $target"
      echo "  Remediation for broken symlink [$(basename "$item")]:"
      echo "    Relink to valid target or remove:"
      echo "      rm \"$item\""
      ROOT_BROKEN_SYMLINKS+=("$item")
      BROKEN_SYMLINK_COUNT=$((BROKEN_SYMLINK_COUNT + 1))
      ERRORS=$((ERRORS + 1))
    elif [[ -d "$item" ]]; then
      has_subdirs=true
      SCREEN_DIRS+=("$item")
    fi
  done
fi

# If no subdirectories found, determine if TARGET_DIR itself is a single screen
if [[ "$has_subdirs" == "false" ]]; then
  if [[ ${#target_entries[@]} -eq 0 ]]; then
    echo "❌ Error: No screen subdirectories or PNG artifacts found in $TARGET_DIR"
    exit "$EXIT_NO_SCREENS"
  else
    # TARGET_DIR contains files or symlinks directly
    SCREEN_DIRS=("$TARGET_DIR")
  fi
fi

if [[ ${#SCREEN_DIRS[@]} -eq 0 ]]; then
  if [[ $BROKEN_SYMLINK_COUNT -gt 0 ]]; then
    echo "❌ Capture Gate Status: FAILED ($ERRORS errors detected). Broken symlinks present."
    exit "$EXIT_BROKEN_SYMLINK"
  fi
  echo "❌ Error: No screen subdirectories or PNG artifacts found in $TARGET_DIR"
  exit "$EXIT_NO_SCREENS"
fi

echo "📋 Found ${#SCREEN_DIRS[@]} screen target(s) to inspect."
echo "--------------------------------------------------------"

# ==============================================================================
# Screen Validation Loop
# ==============================================================================
if [[ ${#SCREEN_DIRS[@]} -gt 0 ]]; then
  for screen_dir in "${SCREEN_DIRS[@]}"; do
    screen_slug=$(basename "$screen_dir")
    TOTAL_SCREENS=$((TOTAL_SCREENS + 1))
    echo "Checking screen: [$screen_slug]"

    # 1. Foreign image formats detection (jpg, webp, gif, bmp, tiff)
    shopt -s nocaseglob nullglob
    foreign_files=(
      "$screen_dir"/*.jpg "$screen_dir"/*.jpeg
      "$screen_dir"/*.webp "$screen_dir"/*.gif
      "$screen_dir"/*.bmp "$screen_dir"/*.tiff
    )
    shopt -u nocaseglob nullglob

    if [[ ${#foreign_files[@]} -gt 0 ]]; then
      for foreign in "${foreign_files[@]}"; do
        foreign_name=$(basename "$foreign")
        echo "  ⚠️  [Foreign Image Format] Non-PNG image detected: $screen_slug/$foreign_name"
        echo "  Remediation for non-PNG file [$screen_slug/$foreign_name]:"
        echo "    Vision-first audit requires PNG format. Convert using sips:"
        echo "      sips -s format png \"$foreign\" --out \"${foreign%.*}.png\""
        WARNINGS=$((WARNINGS + 1))
      done
    fi

    # 2. Broken symlink detection inside screen directory
    shopt -s nullglob
    screen_items=("$screen_dir"/*)
    shopt -u nullglob

    if [[ ${#screen_items[@]} -gt 0 ]]; then
      for item in "${screen_items[@]}"; do
        if [[ -L "$item" && ! -e "$item" ]]; then
          # Avoid double-counting if item was already recorded in ROOT_BROKEN_SYMLINKS
          already_counted=false
          if [[ ${#ROOT_BROKEN_SYMLINKS[@]} -gt 0 ]]; then
            for rb in "${ROOT_BROKEN_SYMLINKS[@]}"; do
              if [[ "$rb" == "$item" ]]; then
                already_counted=true
                break
              fi
            done
          fi
          if [[ "$already_counted" == "false" ]]; then
            local_target=$(readlink "$item" 2>/dev/null || echo "unknown")
            echo "  ❌ [Broken Symlink] $screen_slug/$(basename "$item") points to nonexistent target: $local_target"
            echo "  Remediation for dangling symlink [$screen_slug/$(basename "$item")]:"
            echo "    Relink to existing capture:"
            echo "      ln -sf \"default.png\" \"$item\""
            echo "    Or remove symlink if state is not applicable:"
            echo "      rm \"$item\""
            BROKEN_SYMLINK_COUNT=$((BROKEN_SYMLINK_COUNT + 1))
            ERRORS=$((ERRORS + 1))
          fi
        fi
      done
    fi

    # 3. Multi-Density Default State Candidates (default.png, default@2x.png, default@3x.png)
    has_default=false
    shopt -s nocaseglob nullglob
    for cand in "$screen_dir"/default.png "$screen_dir"/default@*.png; do
      if [[ -f "$cand" || -L "$cand" ]]; then
        has_default=true
        break
      fi
    done
    shopt -u nocaseglob nullglob

    if [[ "$has_default" == "false" ]]; then
      echo "  ❌ [Missing Default State] $screen_slug has no default state capture (default.png, default@2x.png, default@3x.png)."
      echo "  Remediation for missing default state in [$screen_slug]:"
      echo "    Capture the base render using ego-browser:"
      echo "      ego-browser goto \"https://app.local/$screen_slug\""
      echo "      ego-browser screenshot \"$screen_dir/default.png\""
      echo "    Or for mobile via test-by-maestro:"
      echo "      maestro test flows/$screen_slug.yaml"
      echo "      cp ~/.maestro/tests/$screen_slug.png \"$screen_dir/default.png\""
      MISSING_DEFAULT_COUNT=$((MISSING_DEFAULT_COUNT + 1))
      ERRORS=$((ERRORS + 1))
    fi

    # 4. Find all PNG files in screen directory (case-insensitive)
    shopt -s nocaseglob nullglob
    png_files=("$screen_dir"/*.png)
    shopt -u nocaseglob nullglob

    if [[ ${#png_files[@]} -eq 0 ]]; then
      if [[ "$has_default" == "false" ]]; then
        echo "  ❌ [No Screenshots] Screen directory has zero PNG images: $screen_slug"
        ERRORS=$((ERRORS + 1))
      fi
      continue
    fi

    # 5. Validate each PNG file
    for img in "${png_files[@]}"; do
      # Skip broken symlinks (handled and flagged above)
      if [[ -L "$img" && ! -e "$img" ]]; then
        continue
      fi
      validate_png_file "$img" "$screen_slug" || true
    done

    # 6. Multi-Density State Coverage Calculation
    present_base_states=()
    for img in "${png_files[@]}"; do
      [[ -e "$img" ]] || continue
      fname=$(basename "$img")
      stem="${fname%.*}"
      base="${stem%@[0-9][xX]}"
      already=false
      if [[ ${#present_base_states[@]} -gt 0 ]]; then
        for ps in "${present_base_states[@]}"; do
          if [[ "$ps" == "$base" ]]; then
            already=true
            break
          fi
        done
      fi
      if [[ "$already" == "false" ]]; then
        present_base_states+=("$base")
      fi
    done

    absent_states=()
    for st in "${STANDARD_BASE_STATES[@]}"; do
      found=false
      if [[ ${#present_base_states[@]} -gt 0 ]]; then
        for ps in "${present_base_states[@]}"; do
          if [[ "$ps" == "$st" ]]; then
            found=true
            break
          fi
        done
      fi
      if [[ "$found" == "false" ]]; then
        absent_states+=("$st.png")
      fi
    done

    if [[ ${#absent_states[@]} -gt 0 ]]; then
      echo "  ℹ️  [State Coverage] Present: ${#present_base_states[@]} state(s). Absent: ${absent_states[*]}"
    fi
  done
fi

echo "--------------------------------------------------------"
echo "📊 Validation Summary:"
echo "   Screens evaluated : $TOTAL_SCREENS"
echo "   Images verified   : $TOTAL_IMAGES"
echo "   Total errors      : $ERRORS"
echo "   Total warnings    : $WARNINGS"

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ Capture Gate Status: FAILED ($ERRORS errors detected). Fix issues before vision evaluation."
  if [[ $BROKEN_SYMLINK_COUNT -gt 0 ]]; then
    exit "$EXIT_BROKEN_SYMLINK"
  elif [[ $CORRUPT_COUNT -gt 0 ]]; then
    exit "$EXIT_CORRUPT_OR_EMPTY"
  elif [[ $MISSING_DEFAULT_COUNT -gt 0 ]]; then
    exit "$EXIT_MISSING_DEFAULT"
  elif [[ $TOTAL_SCREENS -eq 0 ]]; then
    exit "$EXIT_NO_SCREENS"
  else
    exit "$EXIT_INVALID_ARGS"
  fi
else
  echo "✅ Capture Gate Status: PASSED. All screenshots are verified and valid."
  exit "$EXIT_SUCCESS"
fi

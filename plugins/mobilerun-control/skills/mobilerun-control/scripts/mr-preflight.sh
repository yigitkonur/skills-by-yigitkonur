#!/usr/bin/env bash
# mr-preflight.sh — make the device ready for a control session.
# Resolves the serial, waits out the USB settle, detects the ROM, confirms the Portal, and
# re-asserts accessibility in the fully-qualified form mobilerun's check matches — the steps that
# otherwise make a session's first command fail. Idempotent; run once at the start of a session.
#
# Usage:  mr-preflight.sh [SERIAL]
#   SERIAL defaults to $MR_DEVICE, else the only connected device.
# Output: one status line per check; exit 0 only when "ping" succeeds.
set -uo pipefail
export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"

DEV="${1:-${MR_DEVICE:-}}"
A11Y="com.mobilerun.portal/com.mobilerun.portal.service.MobilerunAccessibilityService"  # fully-qualified; the readiness check substring-matches this form

# --- resolve device -------------------------------------------------------
if [ -z "$DEV" ]; then
  DEV="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"
fi
[ -z "$DEV" ] && { echo "PREFLIGHT FAIL: no device connected"; exit 2; }
echo "device: $DEV"

# --- wait for USB to settle (the link blips during launches/installs) -----
adb -s "$DEV" wait-for-device 2>/dev/null
# brief re-detect loop in case of a blip right after a launch/install
for _ in 1 2 3; do
  state="$(adb -s "$DEV" get-state 2>/dev/null)"
  [ "$state" = "device" ] && break
  sleep 1
done
[ "$(adb -s "$DEV" get-state 2>/dev/null)" = "device" ] || { echo "PREFLIGHT FAIL: device offline"; exit 2; }

# --- ROM detection (GrapheneOS gates accessibility more strictly) ---------
if adb -s "$DEV" shell pm list packages 2>/dev/null | grep -q grapheneos; then
  echo "rom: GrapheneOS (hardened — programmatic a11y-enable is often blocked; FQ re-assert below)"
else
  echo "rom: stock/other"
fi

# --- ensure Portal present ------------------------------------------------
if ! adb -s "$DEV" shell pm list packages 2>/dev/null | grep -q com.mobilerun.portal; then
  echo "portal: NOT installed — run 'mobilerun setup -d $DEV' (confirm with user first; it installs an APK)"
  exit 2
fi
PV="$(adb -s "$DEV" shell content query --uri content://com.mobilerun.portal/version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1)"
echo "portal: installed (v${PV:-?}) — this is the compatible pinned version; a newer one auto-reverts"

# --- re-assert accessibility (cleared by Portal reinstalls; write FQ name) -
cur="$(adb -s "$DEV" shell settings get secure enabled_accessibility_services 2>/dev/null | tr -d '\r')"
if ! printf '%s' "$cur" | grep -q "MobilerunAccessibilityService"; then
  echo "a11y: enabling…"
  adb -s "$DEV" shell settings put secure enabled_accessibility_services "$A11Y" >/dev/null 2>&1
  adb -s "$DEV" shell settings put secure accessibility_enabled 1 >/dev/null 2>&1
  sleep 1
elif ! printf '%s' "$cur" | grep -q "com.mobilerun.portal/com.mobilerun.portal"; then
  # present but in short form -> rewrite the fully-qualified name so the substring check matches
  echo "a11y: rewriting short->fully-qualified name"
  adb -s "$DEV" shell settings put secure enabled_accessibility_services "$A11Y" >/dev/null 2>&1
fi

# --- final readiness gate -------------------------------------------------
if mobilerun ping -d "$DEV" 2>&1 | grep -q "good to go"; then
  echo "ping: OK — ready"
  exit 0
fi
echo "ping: FAILED — open Settings>Accessibility and enable 'Mobilerun Portal' by hand, then re-run."
echo "      (GrapheneOS: you may also need to allow the 'Restricted setting' on the Portal app first.)"
exit 1

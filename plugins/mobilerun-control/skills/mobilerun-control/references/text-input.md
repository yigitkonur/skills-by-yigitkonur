# Text input

Typing is the most delicate primitive in Android automation. There are two delivery paths, and one
thing to get right first.

## Focus the field first

Text lands in **whatever field is currently focused**, so the move is always: tap the field, wait
~0.5s for the IME to come up, then type. The `device ui` header tells you it worked — `Keyboard:
Visible` and `Focused Element: '<field>'`. If the keyboard didn't come up, your tap missed the
field, so re-find it and tap again before typing. (You can watch this happen: tap → 0.5s → type
drops "android agents" into the focused EditText and the header flips to `Keyboard: Visible`.)

## Path A — atomic paste (default; best for long/special/Unicode text)

The Portal exposes a one-shot input endpoint. `scripts/mr-type.sh "text" [--clear]` uses it:

```bash
b64=$(printf '%s' "your long text 😀 with symbols & quotes" | base64 | tr -d '\n')
adb -s "$MR_DEVICE" shell content insert --uri content://com.mobilerun.portal/keyboard/input \
    --bind "base64_text:s:$b64" --bind "clear:b:true"     # clear:b:false to append
```

With `clear:b:true` this replaces the field's contents in a single operation, whole phrase and all
(`clear:b:false` appends instead). Because the text is **base64-encoded** on the way in, it survives
the spaces, quotes, `&`, emoji and newlines that break a plain `adb shell input text`. That makes it
the **paste-for-long-text** primitive — fast and reliable for search queries, URLs, pasted blocks,
anything where instant entry is fine.

## Path B — `mobilerun device type` (the CLI primitive)

```bash
mobilerun device type "hello" --clear -d "$MR_DEVICE"     # prints "Typed: hello"
```
Goes through the Portal IME if enabled, otherwise the accessibility `SET_TEXT` fallback. `--clear`
empties the field first — typing "claude" with `--clear` over an existing "android agents" replaces
it rather than appending. Good for short, plain text.

**To clear a field to *empty* (not replace with new text):** pass `--clear` with no text —
`mr-type.sh --clear` blanks the focused field (it prints `Cleared field`; verify the field's
`text` returns to its placeholder/hint). Equivalent raw forms if you're not using the wrapper:
`mobilerun device type "" --clear -d "$MR_DEVICE"`, or the paste endpoint with an empty
`base64_text` and `clear:b:true`.

## Path C — human typing (for authored content)

For comments, messages, or posts that should *read* as hand-typed, send the words gradually rather
than as one instant block: `mr-type.sh "…" --human` splits the text into word chunks with randomized
0.25–0.7s pauses, so it looks authored. Use it whenever a person is supposed to have written the
words, and pair it with `references/writing-like-a-human.md`.

## The keyboard on this device (why paste is the default)

This phone is **GrapheneOS**, and the **Mobilerun keyboard IME is installed but not enabled** — only
`com.android.inputmethod.latin` is active. So text actually enters through the **accessibility
`SET_TEXT` fallback**, which is why `device ui`/`doctor` note *"Mobilerun Keyboard not active"* while
typing still works fine. Knowing that explains the rest:

- Plain ASCII through Path A or B works through the fallback, so the base64 paste is the right
  default and you rarely need to touch the IME at all.
- Some fields reject programmatic `SET_TEXT` (certain secure/password fields, custom IME widgets).
  For those, enable the Portal keyboard, type, then restore the user's keyboard so you leave the
  phone as you found it:
  ```bash
  adb -s "$MR_DEVICE" shell ime enable com.mobilerun.portal/.input.MobilerunKeyboardIME
  adb -s "$MR_DEVICE" shell ime set    com.mobilerun.portal/.input.MobilerunKeyboardIME
  # … type …
  adb -s "$MR_DEVICE" shell ime set    com.android.inputmethod.latin/.LatinIME   # restore
  ```
- Each `mobilerun device …` command disables the Portal IME again on teardown, so the keyboard state
  doesn't carry over between calls. Treat focus as fresh every time: re-focus the field right before
  each type rather than assuming the previous focus survived.

## After typing

- Submit with `mobilerun device press enter`, or tap the on-screen Send/Search/Post control by its
  bounds (snap to find it).
- Re-snap and read the header `Focused Element` / the field's `text` to confirm what actually
  landed before moving on.

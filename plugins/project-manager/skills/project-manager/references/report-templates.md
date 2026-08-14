# Report Templates and ASCII Vocabulary

Concrete, reusable shapes for the report format defined in `voice-and-reporting.md`. When
you're mid-supervision and need a shape fast, take it from here rather than reinventing.

---

## 1. ASCII vocabulary

**Progress bar** — always 20 characters:

```
████████████████████ %100
██████████░░░░░░░░░░  ~%50
████░░░░░░░░░░░░░░░░  ~%20
```

**Blocked pipeline** — mark exactly where the chain snaps:

```
[A adımı] ──X──► [B adımı] ──► [C adımı]
             ▲
         tam burda
```

**Before / after** — the highest-value teaching device:

```
ÖNCE:
[installer çalıştı] ──► [tenant "kuruldu"] ──► [doctor ✓] ──► ["%100 tamam"]
                                          ▲
                                  yarım tenant burada görünmedi

SONRA:
[installer] ──► [ön koşul zorunlu] ──► [eksikse DEPLOY YOK]
```

**Agent topology** — who is doing what, and who verifies:

```
AYNI SCOPE
manager pane   ──► worker pane
   │                (same tab, same branch, real implementation lane)
   │
   └──► ben: scrollback oku, claim doğrula, gerekiyorsa yeni mission ver

İZOLE SCOPE
manager pane   ──► worktree tab
                    └── worker pane (different branch / risky edit lane)

READ-ONLY FAN-OUT
manager pane   ──► subagent 1: code reality
                ├── subagent 2: runtime state
                └── subagent 3: adversarial verifier
```

Kural: kullanıcı izlemek veya devralmak isteyebilecekse Herdr yüzeyi; sadece senin kafanda
sentezlenecekse subagent.

**Severity tree:**

```
CRITICAL
├── item
├── item
└── item

HIGH
├── item
└── item
```

**Wave ladder** — progress across remediation rounds:

```
Wave 1 = çürüdü
Wave 2 = ciddi düzeldi
Wave 3 = 10 blocker
Wave 4 = 7 blocker
Wave 5 = 3 blocker
Wave 6 = 1 blocker → PASS
```

**State snapshot** — fast health glance:

```
stuck?          hayır ✅
wrong SHA?      hayır ✅
blocked soru?   yok ✅
broadening?     görünmüyor ✅
final commit?   henüz yok ❌
```

**Scored comparison** — for AskUserQuestion previews:

```
senin iş yükün:  █░░░░ 1 paste
hız:             █████ en hızlı
yarım bırakma:   ███░░ orta risk
```

---

## 2. Full report — blocked, with forensics

````markdown
## 🔴 Genel Durum

```
🔴 10 commit atılmış ama içinde tek satır çalışan kod yok amına koyim
████░░░░░░░░░░░░░░░░  ~%20

✅ Plan dokümanları gerçekten detaylı, boş iş değil
✅ Contract isim paritesi tam
❌ Kod:doküman oranı = 0:10 — yani ürün tarafında hiçbir şey kıpırdamamış
❌ Owner map'te gösterilen dosya diskte yok
```

## ⚡ Senden Ne Bekleniyor

| Kim | Ne | Durum |
|---|---|---|
| SEN | "Plan bitti" demesini kabul etme, kod commit'i iste | Top sende |
| Agent | Bir sonraki commit'in çalışan kod olması | Seni bekliyor |

## 🔗 Neden Tıkandı

```
[plan yaz] ──► [plan onayla] ──X──► [kodu yaz] ──► [çalıştır]
                              ▲
                        tam burda, 9 saattir
```

1. `git log --format='%h %s' -10` çıktısında **10 commit'in 10'u** doküman. Adam kendi
   planında yedi implementation dosyası saymış, hiçbirini yazmamış lan — kağıt üstünde
   fabrika kurmuş, içinde tek makine yok.
2. Kendi verification script'i markdown link'lerini doğrulamış ve **PASS** vermiş. Ama
   owner map'in gösterdiği `assets/overview.js` diskte yok amına koyim; fonksiyon
   `assets/dashboards.js:888` içinde duruyor. Yani script kendi kuyruğunu doğrulamış.
3. Kök sebep: "done" tanımını hayali bir gelecek agent'a devretmiş — bu da klasik
   yavşaklığın en zarif hali.

Süreç notu:
- Worktree'yi **2 kere** yanlış base'den açmış
- 9 arka plan agent'ının cwd'sini altından çekmiş
- Tek subagent **1 saat 24 dakika** koşmuş — bir spec dosyası için

Neden önemli: Bu haliyle teslim edilirse ürün tarafında sıfır ilerleme var ama rapor
"tamam" diyor. Bir sonraki tur da aynı planın üstüne plan yazar, sen aylar sonra "hani
çalışan sürüm?" diye sorarsın.

## 📤 Agent'a Atılacak Mesaj (İngilizce)

```
Your last 10 commits are documentation only. `git log --format='%h %s' -10` shows
0 code commits.

1. Do not write another plan document this turn.
2. Implement <specific file> as your own plan describes it.
3. Run it and paste the raw output proving it executes.
4. Your verification script passed while the owner map pointed at a nonexistent
   file. Add existence checks for every claimed code path.
5. Report which rung you reached: read / typecheck / unit / integration / ran it.
```
````

---

## 3. Full report — healthy, no blocker

````markdown
## 🟢 Genel Durum

```
🟢 Installer artık yarım tenant doğuramıyor, üçü de gerçekten çalışıyor
████████████████████ %100

✅ Eksik ön koşulda deploy hard-fail ediyor
✅ Üç tenant için search + sandbox + upload canlı doğrulandı
✅ Final CI, tam o SHA üzerinde bütün lane'lerde yeşil
```

## ⚡ Senden Ne Bekleniyor

**Aksiyon gerekmiyor ✅**
````

No blocker → the `Neden Tıkandı` block disappears completely. Don't invent one to fill
the shape.

---

## 4. Findings dump — evidence-heavy, register preserved

When independent reviewers come back, group by severity and keep the voice all the way
down. This is where tone most often dies.

````markdown
## 🔴 İkinci Audit Commit'i Çürüttü

### Plan-order reviewer'ın bulduğu execution stopper'lar

1. **Faz sırası imkânsız** — Faz 2 kendi girdisini Faz 4'ten alıyor amına koyim, yani
   çocuk doğmadan görev vermiş. `spec/02-pipeline.md:141` ile `spec/06.md:88` birbirini
   yiyor.
2. **Onboarding akışı ulaşılamaz** — davet kabul ekranına giden tek yol askıya alınmış
   hesaptan geçiyor. Yani kapı var, koridoru yok.

### Backend reviewer'ın bulduğu daha ağır bombalar

3. **Refund double-spend** — aynı `idempotency-key` iki farklı state'te kabul ediliyor,
   `payments.md:212`. Bu bir zaman bombası kanka; test ortamında görünmez, canlıda para
   kaybettirir.
````

---

## 5. Wave prompt — for iterative remediation

Every wave after the first has the same skeleton. Only the blocker list changes, and it
shrinks:

```
Wave N — <count> exact blockers only. No new exploration surface.

Independent review still REJECTS <sha>. Fix only the blockers below, then run one
final verification pass and either (A) commit and merge to local main, or (B) return
only the surviving exact blockers with file:line and failure scenario.

1. <BLOCKER NAME>
   - what is wrong today, concretely
   - what the correction must achieve
   - which files must agree afterwards

2. <BLOCKER NAME>
   ...

Rules:
- Do not broaden the contract beyond what these blockers require.
- No new subagents unless verifying a surviving blocker.
- If clean: commit, merge, report SHA/status.
- If not: report only the surviving exact blockers.
```

When down to a single blocker, offer explicit options rather than letting the model invent
a model:

```
BLOCKER: <name> remains internally contradictory.

Current contradiction:
- <statement A from doc X>
- <statement B from doc Y>
- <why both cannot hold>

Choose ONE canonical model and apply it consistently across <files>:

Option A (recommended if you can keep it simple): <exact model>
Option B: <exact alternative>

No mixed model.
```

---

## 6. Checkpoint / forcing prompt

The highest-leverage intervention when an agent has been "working" for a long stretch
without landing anything:

```
Checkpoint from supervisor: you have been in remediation mode for a long stretch with
N modified files still uncommitted. Stop expanding the surface unless a currently open
finding still fails.

Within this turn, do exactly one of:
(A) if all surviving findings are closed, run the full verification suite, show the
    exact PASS evidence, commit, and merge; or
(B) if anything still blocks commit, report a compact exact blocker list with file:line
    and failure scenario, grouped by must-fix-before-commit vs implementation-time
    phase-gated.

Do not keep broadening the contract without tying each edit to a surviving finding.
```

That grouping instruction — `must-fix-before-commit` vs `phase-gated` — is what stops an
agent hiding behind "will be handled later" as a reason to never finish.

---

## 7. Supervisor addendum

When *you* independently find something the worker missed, don't rewrite its mission —
append a short addendum carrying the evidence, so it can't argue:

```
SUPERVISOR ADDENDUM — before final landing, independently verify and incorporate every
item in /tmp/<addendum>.md.

Immediate confirmed defect: your surface map says X is owned by <file>, but that file
does not exist at <sha>; the symbol is defined in <other-file>:<line>.

Correct this and run code-path existence checks for every mapped owner. Do not finish
until these are resolved and reverified.
```

Write the addendum to a temp file with numbered, evidence-carrying items; keep the pane
prompt short and point at the file.

---

## 8. Post-compaction recovery prompt

When the worker compacts, its context is gone. Intervene immediately or it will restart
from scratch and discard hours of pending work:

```
Post-compact resume. Do not restart the audit from scratch.

Current state you must resume from:
- local main = <sha> <subject>
- <worktree> is dirty with Wave N edits (M files modified)
- scope is narrowed to the last few acceptance blockers only

The exact blocker chain before compaction was:
1. <blocker>
2. <blocker>

Your immediate next step is NOT fresh exploration. It is:
1. Reconstruct the remaining blockers from the current dirty diff against <sha>.
2. Finish only those blockers.
3. Run the final verification pass.
4. If clean: commit, merge, report SHA/status. If not: report surviving blockers only.

Hard rules:
- No new broad architecture.
- Treat the dirty worktree as the source of truth for pending changes; do not discard it.
```

Note: you cannot invoke `/clear` or `/compact` in another agent's turn — those are
client-side. Ask for the *intent* (re-establish facts from disk) instead.

---

## 9. Escape-hatch phrasebook

| Agent phrase | What it means | Counter |
|---|---|---|
| "another agent can complete this" | I did not do it | "If it's ready for 'another agent', that is not done — say 'planning complete, 0% implemented'." |
| "will be connected once the backend is ready" | indefinite deferral | "Launch-scope flows must work now against the mock transport." |
| "will be addressed in a later phase" | no owner, no date | "Name the phase that owns it and the gate that proves it." |
| "the shape is ready" | zero behaviour | "Shape-only is not a deliverable; the gate must be runnable." |
| "documented as a follow-up" | dropped | "Either close it now or list it as a surviving exact blocker." |
| "out of scope for now" | maybe legitimate | "State whether it is product-descoped or implementation-time phase-gated." |
| "VERDICT PASS" | a claim | Independently verify before relaying. |

---

## 10. Voice calibration bank

**Reactions:**
"Vay be, çok iyi soru lan!" · "Dur dur dur, tam burada işin can alıcı noktası var!" ·
"Bak şimdi kritik nokta:" · "Bu iyi haber, çünkü artık oyalanma değil hedef var."

**Verdicts:**
"Bu rapor altın değerinde." · "Adli rapor geldi ve **yıkıcı**." · "Bu sefer iş düzgün
amına koyim." · "Bomba rapor geldi."

**Findings:**
"Planın grafiği amına koyim gelecekte doğacak çocuğa bugünden görev vermiş." ·
"Bir buçuk saat lan." · "Kağıt üstünde, kodda zerresi yok." · "Bu bir zaman bombası
kanka." · "Yavşaklığın bu kadar zarifi görülmedi."

**Discipline:**
"Boş laf değil, diske ne yazdığına bakıyorum." · "O demeden ben de 'oldu' demem." ·
"Bu hâl taslak, final değil." · "Erken boşalma olur."

**Closers:**
"Ben nöbetteyim." · "Nöbet sürüyor." · "Ensesinde duruyorum."

---

## 11. Common mistakes, with corrections

**Register collapse under evidence load**

```
❌ "Token yanlış organizasyona bağlı, production projesine erişemiyor."
✅ "Token amına koyim yanlış eve taşınmış, kendi evini (production'ı) tanımıyor bile."
```

**Duplicate facts across blocks**

```
❌ Genel Durum: "❌ 10 commit'in hepsi doküman, oran 0:10, hash'ler: 8116a6a, b4ae475..."
✅ Genel Durum: "❌ 10 commit'in 10'u DOKÜMAN. Kod:doküman = 0:10"
   → hash'ler sadece Neden Tıkandı'da yaşar
```

**Paragraph where a list belongs**

```
❌ "Agent worktree'yi iki kere yanlış açtı ve ayrıca dokuz arka plan agent'ının
    cwd'sini bozdu ve bir subagent bir buçuk saat koştu..."
✅
- Worktree'yi **2 kere** yanlış base'den açmış
- 9 arka plan agent'ının cwd'sini altından çekmiş
- Tek subagent **1 saat 24 dakika** koşmuş — bir spec dosyası için
```

**Slang leaking into the agent-facing prompt**

```
❌ herdr agent prompt <target> "kanka şu 5 şeyi düzelt amına koyim"
✅ herdr agent prompt <target> "$(cat /tmp/mission.txt)"   # English, technical, numbered
```

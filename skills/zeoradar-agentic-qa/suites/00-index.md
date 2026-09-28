# Zeo Geo-Radar — Any-Site Code-Grounded Gherkin QA Architecture Master Index

> **Architecture Standard**: 8 Steps · 20 Modular Test Suites · 225 Gherkin QA Test Cases · 20 Domain Dictionaries (`README.md`)  
> **Execution Engine**: `ego-browser nodejs` 5-Phase Lifecycle & Remote MacBook Gateway (SCP Asset Transfer)  
> **Target Environment**: [APP_URL] & Dual-Driver Client  
> **Authenticated Test User**: `e2e-agent@zeogen.com` (Owner · 10,000,000+ Credits Allocated)

---

## 🗺️ Master Navigation & Directory Structure

```
.agents/skills/zeoradar-agentic-qa/suites/
├── 00-index.md (Bu Ana Dizin)
├── step-01/auth-onboarding/
│   ├── 01-login-and-session/ (README + 12 Gherkin test vakası)
│   └── 02-brand-setup-and-onboarding/ (README + 12 Gherkin test vakası)
├── step-02/shell-navigation/
│   ├── 01-sidebar-and-route-switching/ (README + 10 Gherkin test vakası)
│   ├── 02-command-palette-and-shortcuts/ (README + 10 Gherkin test vakası)
│   └── 03-theme-lang-and-profile/ (README + 12 Gherkin test vakası)
├── step-03/overview-dashboard/
│   ├── 01-kpi-scorecards-and-filters/ (README + 11 Gherkin test vakası)
│   ├── 02-visibility-trend-chart/ (README + 11 Gherkin test vakası)
│   └── 03-geo-world-map/ (README + 11 Gherkin test vakası)
├── step-04/visibility-matrix/
│   ├── 01-platform-engine-benchmark/ (README + 12 Gherkin test vakası)
│   └── 02-sentiment-and-audience/ (README + 12 Gherkin test vakası)
├── step-05/prompt-studio/
│   ├── 01-prompt-list-and-filters/ (README + 10 Gherkin test vakası)
│   └── 02-prompt-creation-and-editor/ (README + 11 Gherkin test vakası)
├── step-06/agent-analytics/
│   ├── 01-ai-agent-vitals-and-telemetry/ (README + 12 Gherkin test vakası)
│   └── 02-search-volume-and-demand/ (README + 12 Gherkin test vakası)
├── step-07/opportunities-content/
│   ├── 01-opportunities-engine/ (README + 13 Gherkin test vakası)
│   └── 02-content-studio-pipeline/ (README + 14 Gherkin test vakası)
└── step-08/governance-settings-chat/
    ├── 01-brand-hub-ground-truth/ (README + 10 Gherkin test vakası)
    ├── 02-dashboards-and-exports/ (README + 10 Gherkin test vakası)
    ├── 03-account-team-billing/ (README + 10 Gherkin test vakası)
    └── 04-zeo-ai-chat-drawer/ (README + 10 Gherkin test vakası)
```

---

## 📋 Adım Adım Modüler Gherkin Test Paketleri

### [Adım 01: Kimlik Doğrulama & Marka Kurulumu (Auth & Onboarding)](./step-01/auth-onboarding/)
- **[01-login-and-session/](./step-01/auth-onboarding/01-login-and-session/)** (12 Test Vakası + `README.md`):
  E-posta ön doğrulama, şifre ile giriş, yeni kayıt, 6 haneli OTP doğrulama (`#otp-digit-grid`, `246810`), 55sn sayaç ve resend kilidi, şifre sıfırlama, SAML SSO çekmecesi, dev bypass modu (`zeoBypassLogin`), oturum kapatma/değiştirme, `rate_limited` üstel geri çekilme, ağ kesintisi ve yerelleştirme testleri.
- **[02-brand-setup-and-onboarding/](./step-01/auth-onboarding/02-brand-setup-and-onboarding/)** (12 Test Vakası + `README.md`):
  Marka tohumlama köprüsü (`state.onboardingSeed`), sihirbaz navigasyonu, alan adı port/protokol temizliği (`obCleanDomain`), ccTLD pazar çıkarımı, sektörel motor profilleri, özel motor kaydırıcıları ve sıfır sınırı, 10 konu tavanı, özel konu enjeksiyonu ve mükerrer engeli, Trigger.dev 5dk zaman aşımı ve poller canlandırma (`obResumePollIfStalled`), satır içi öneri düzenleme ve proje kesinleştirme onayı.

---

### [Adım 02: Kabuk, Navigasyon & Global Kontroller (Shell & Navigation)](./step-02/shell-navigation/)
- **[01-sidebar-and-route-switching/](./step-02/shell-navigation/01-sidebar-and-route-switching/)** (10 Test Vakası + `README.md`):
  15 kenar çubuğu sekmesi geçişi, Marka Değiştirici popover'ı, masaüstü daraltma (`side-collapsed`), mobil çekmece (`side-open`), `popstate` tarayıcı geçmişi eşitlemesi, geçersiz rota takma adlarında AEI fallback'i, hızlı tıklamada `bootSeq` sıra kilidi, Türkçe marka araması ve aktif marka yeniden seçiminde filtre sıfırlama.
- **[02-command-palette-and-shortcuts/](./step-02/shell-navigation/02-command-palette-and-shortcuts/)** (10 Test Vakası + `README.md`):
  `⌘K` / `Ctrl+K` tetikleyicisi, kategori bazlı komut araması, ok tuşları döngüsel navigasyonu, Enter ile çalıştırma, Escape/backdrop ile kapatma ve odak kurtarma, klavye erişilebilirlik köprüsü, Regex özel karakter bağışıklığı, boş arama koruması, modal katmanlama (`z-index: 10000`) ve mobil görünümde gizleme.
- **[03-theme-lang-and-profile/](./step-02/shell-navigation/03-theme-lang-and-profile/)** (12 Test Vakası + `README.md`):
  Açık/koyu mod çift geçişi, profil alt menüsünden sistem teması, TR/EN çift dilli yerelleştirme (`applyLang` ve `t()`), Yenilikler modalı 4 yetenek şeması ve üçlü kapatma eşitliği, SVG spotlight maskeli 4 adımlı ürün turu ve tur iptali, kullanıcı profil menüsü, Hakkında modalı, `prefers-color-scheme` canlı dinleyicisi ve Türkçe diyakritik harf bütünlüğü.

---

### [Adım 03: Genel Bakış Panosu & Grafikler (Overview Dashboard)](./step-03/overview-dashboard/)
- **[01-kpi-scorecards-and-filters/](./step-03/overview-dashboard/01-kpi-scorecards-and-filters/)** (11 Test Vakası + `README.md`):
  Çekirdek KPI hidrasyonu (`visScore`, `shareOfVoice`, `avgPosition`), kart içi zaman aralığı hapları (7D-90D), yüksek frekanslı tıklama yarış bağışıklığı (<50ms), kabuk tarih seçici popover'ı, motor çoklu seçim popover'ı, sıfır motor seçimi koruması (`.ov-skeleton-wrap`), konu kümesi filtresi ve global sıfırlama (`.freset`), tek koşu baz çizgi etiketi (`.ov-demo-badge`), düşük örneklem duygu koruması (<3 iddia için `–`), teknik telemetri çekmecesi ve bölgesel filtre düşüşü.
- **[02-visibility-trend-chart/](./step-03/overview-dashboard/02-visibility-trend-chart/)** (11 Test Vakası + `README.md`):
  Çizgi modu SVG çizimi (`ovLineSVG`), çizgi ve sütun modu geçişi, sütun modu platform renkleri dökümü, ölçülmemiş motor F3 kuralı (`–`), interaktif nişangah ve veri noktası yakalama (`line.ov-cross`, `circle.ov-dot`), kayan ipucu sınır kırpması ($x \ge 4\text{px}$), eksik günlerde yatay baz çizgi, web sitesi aktivite ikiz grafikleri, tüm serileri kapatma koruması, ikiz grafik karşılaştırma anahtarı ve taneciklilik toplama değişmezi.
- **[03-geo-world-map/](./step-03/overview-dashboard/03-geo-world-map/)** (11 Test Vakası + `README.md`):
  Vektör harita bellek önbelleği (`VectorMapLoader`), ağ hatası ve yeniden deneme kurtarması (`.map-error-placeholder`), takip edilen pazar vurgulama, 4 dilimli kloroplet renklendirme (`.heat-q1` - `.heat-q4`), 1.0x-9.0x geometrik yakınlaştırma kelepçesi, hedef merkezli sınırlayıcı kutu yakınlaştırması (`tr.getBBox()`), yan ülke talep tablosu, takip edilmeyen ülke etkileşimi, bölge metrik sekmesi değişimi, çift yüzey harita eşliği ve en-boy oranı korunması.

---

### [Adım 04: Görünürlük Kıyaslama & Algı Matrisi (Visibility Matrix)](./step-04/visibility-matrix/)
- **[01-platform-engine-benchmark/](./step-04/visibility-matrix/01-platform-engine-benchmark/)** (12 Test Vakası + `README.md`):
  Çoklu motor kıyaslama matrisi (`table.tbl.aei-matrix-tbl`), row sabitleme (`tr.is-me-row`), matris hücresinden Stüdyo'ya geçiş, coğrafi talep ısı haritası ve prob modalı, Stüdyo 150ms gecikmeli arama ve niyet filtreleme, Aşama 1 sentezlenen yanıt ve model sekmeleri, Türkçe harf duyarlı regex (`buildTurkishRegexPattern`), Aşama 2 sorgu dallanma ağacı ve atlama gecikmeleri, sıfır atıflı sorgularda parametrik yanıt uyarısı (`.aei-parametric-notice.card`), Aşama 3 kök alan adı otorite tablosu ve eş-atıf bölünme çubuğu, atıf çekmecesi önbelleği ve ARIA odak tuzağı / XSS temizliği.
- **[02-sentiment-and-audience/](./step-04/visibility-matrix/02-sentiment-and-audience/)** (12 Test Vakası + `README.md`):
  Algı çalışma alanı düzeni, küçük örneklem koruması (<3 iddia için Beklemede ve kesin NULL skor), aktif kutup dağılımı (Pozitif/Nötr/Negatif), 10 tematik algı kümesi, hedef kitle persona matrisi, özel persona oluşturucu modalı ve olay yayılımı izolasyonu (`data-stop="1"`), girdi temizliği ve varsayılan değerler, halüsinasyon radarı ve Doğruluk Kasası geçişi, özel Algı sekmesi ve anomali ani artış uyarısı (`.sent-spike-badge`), tema akordeonu ve çoklu alıntı sayfalaması, tema araması ve negatif algı kaynakları tablosu.

---

### [Adım 05: Prompt Stüdyosu & Anahtar Kelime Kümeleri (Prompt Studio)](./step-05/prompt-studio/)
- **[01-prompt-list-and-filters/](./step-05/prompt-studio/01-prompt-list-and-filters/)** (10 Test Vakası + `README.md`):
  Master prompt tablosu ve 100-cap SVG kapasite halkası formülü (`40.2 * min(totalN, 100) / 100`), sol taksonomi konu kenar çubuğu, gerçek zamanlı arama ve XSS/SQL enjeksiyonu kaçışı (`esc()`), Aktif/Duraklatıldı sekme yaşam döngüsü, toplu seçim ve tamamı duraklatılmış sette tersine çevirme mantığı, AEI Studio niyet filtreleri ve boş durum, arama hacmi geri çekilme hiyerarşisi (`aiv` -> `gv` -> `–`) ve 5 motor mini indikatör noktası, on-demand çalıştırma önizlemesi ve 1 kredi = 1 hücre hesabı, aynı gün değişim modalı ve iptal geri alması, aşamalı (staged) çalıştırma durumu ve 90sn zaman aşımı kurtarma (`rn-resume-tracking`).
- **[02-prompt-creation-and-editor/](./step-05/prompt-studio/02-prompt-creation-and-editor/)** (11 Test Vakası + `README.md`):
  Tekil prompt oluşturma ve iyimser kaydetme, form doğrulama ve boşluk filtreleme, modal editör ve sunucu mükerrer çakışması (`duplicate_prompt`), konu kümesi oluşturma ve kenar çubuğu senkronizasyonu, Yapay Zeka Keşfi yapılandırması ve Doğruluk Kasası grounding entegrasyonu, şablon değişkenleri (`{brand}`, `{category}`, `{location}`) ve Türkçe normalizasyon, Trigger.dev arka plan işçisi 40sn zaman aşımı bütçesi, mükerrer önleme (`isExistingDuplicate`) ve matris kürasyonu, seçici toplu içe aktarma, CSV toplu yükleme ayırıcı dayanıklılığı (virgül, noktalı virgül, tab) ve sunucu CSV önizleme doğrulama çipleri.

---

### [Adım 06: Ajan Analitiği & Arama Hacmi (Agent Analytics)](./step-06/agent-analytics/)
- **[01-ai-agent-vitals-and-telemetry/](./step-06/agent-analytics/01-ai-agent-vitals-and-telemetry/)** (12 Test Vakası + `README.md`):
  Bağlantısız durum ve hero banner, GPTBot/ClaudeBot/PerplexityBot 6 bot sınıflandırması, tekil bot derinlemesine inceleme dalı, bilinmeyen veya taklit botların `other` olarak toplanması, 5xx sunucu hatalarının %100 200-OK oranını düşürmesi, `run-vitals-audit` ile 6 Core Web Vitals eşiği, denetim hatalarında kilit çözme ve hata tostu, koşu anında mobil/masaüstü strateji geçişi yarış koşulu engeli, sunucu logları arama ve filtreleme, Ziyaret ve Yanıt çekmeceleri klavye/odak yönetimi, Cloudflare Logpush sihirbazı ve telemetri dışa aktarımı sınırları.
- **[02-search-volume-and-demand/](./step-06/agent-analytics/02-search-volume-and-demand/)** (12 Test Vakası + `README.md`):
  Evrensel arama çubuğu ve 5 niyet filtresi, Türkçe `.toLocaleLowerCase("tr")` diyakritik duyarlı semantik otomatik tamamlama, olasılıksal %95 güven aralıkları (High, Moderate, Modeled) ve 10 taban sınır kelepçesi, `median`/`conservative`/`aggressive` projeksiyon modelleri ve `localStorage` kalıcılığı, çift modlu SVG grafik (Bar/Line), karekök ölçekleme sıfır/negatif koruması, izleme listesi çoklu seçim araç çubuğu, filtrelenmiş görünümde toplu seçim izolasyonu, mükerrer liste adı çakışması, demografi kartları ve kloroplet harita, semantik zihin haritası tuvali ve canlı çalışma alanında şablon sızıntısı engeli.

---

### [Adım 07: Fırsatlar Motoru & İçerik Stüdyosu (Opportunities & Content)](./step-07/opportunities-content/)
- **[01-opportunities-engine/](./step-07/opportunities-content/01-opportunities-engine/)** (13 Test Vakası + `README.md`):
  Backlog kart anatomisi ve kategori rayları, Aktif/Arşivlendi/Gizlendi sekmeleri ve arşivleme yaşam döngüsü, kategori filtreleme ve sıfır sonuç kurtarma, etki/zorluk motoru sıralaması, kart aksiyonlarında olay yayılımı (event bubbling) izolasyonu, 3 gizleme gerekçesi ve 10 saniye geri alma (undo) bildirimi sınırları (9.5sn geçerli vs 10.5sn zamanaşımı), detay görünümü navigasyonu ve sayaç, detay içi interaktif kontrol listesi, 2x3 referanslar ızgarası, rakip eşleme modalı alan adı doğrulaması, İçerik Stüdyosu'na aktarım köprüsü (`createBriefFromOpportunity`), 5 kriterli Altın Kupa yeterliliği vs tanısal boş durum ve CSV dışa aktarımı.
- **[02-content-studio-pipeline/](./step-07/opportunities-content/02-content-studio-pipeline/)** (14 Test Vakası + `README.md`):
  Fırsat tohum köprüsü ve Doğruluk Kasası gerçekleriyle uyumluluk (`BMD-BSH-02`), 4 adımlı sihirbaz konu seçimi, başlık üretimi ve `Recommended ⚡` rozeti, Step 4 SSE canlı belirteç akışı (`POST /api/chat`) ve daktilo efekti, akış kopmasında kısmi taslak kurtarma (`finalizeDraft`), AI Gateway HTTP 429 kota aşımında "Tekrar Dene ↻" durumu, markdown editör araç çubuğu biçimlendirmesi, metin seçildiğinde beliren yüzen araç çubuğu (`#edFloatBar`) ve kenar kelepçelemesi, canlı AEO belge metrikleri ve 4 motor uyum göstergeleri, denetim izini koruyan revizyon geri yükleme (`restoreVersion`), kirli taslak üzerine revizyon geri yükleme, 6 kriterli deterministik URL slug denetleyicisi, slug çakışma tekilleştirmesi ve doküman arşivleme.

---

### [Adım 08: Yönetişim, Ayarlar, Raporlar & Zeo AI Copilot](./step-08/governance-settings-chat/)
- **[01-brand-hub-ground-truth/](./step-08/governance-settings-chat/01-brand-hub-ground-truth/)** (10 Test Vakası + `README.md`):
  Marka sesi yönergeleri ve doğrulanmış gerçekler okuma, regex `/^[a-zA-Z0-9_-]{1,100}$/` formatlı yeni doğrulanmış gerçek ekleme, `expectedVersion` ile iyimser eşzamanlılık (OCC) 409 çakışma yönetimi, yetkisiz kullanıcılar için salt-okunur rozeti (`resolveBrandHubOwner() === false`), gerçek itiraz iş akışı (`disputeReason`), onaylı kalıcı arşivleme, Doğruluk Kasası halüsinasyon telemetrisi, SVG DAG varlık grafiğinde döngü tespiti (`detectCycles`) ve karantinaya alma, kök çözümleme derinlik sınırı (`MAX_TRAVERSAL_DEPTH = 10`) ve hızlı proje geçişinde bağlam üretimi izolasyonu (`bhContextGen`).
- **[02-dashboards-and-exports/](./step-08/governance-settings-chat/02-dashboards-and-exports/)** (10 Test Vakası + `README.md`):
  Özel pano şablon kataloğu ve ızgara düzeni, 16 analitik widget tipi (`VIZ_BY_KEY`) ve Grafik/Tablo modları, CSV formül enjeksiyonu savunması (`=+\-@\t\r` karakterlerine `'` koruması), ikili UTF-8 BOM (`\uFEFF`, char code `0xFEFF`) blob doğrulaması, sunucu PDF derleme hatasında `window.print()` yedeği, asenkron dışa aktarım intent kilidi (`xpBusy`), zamanlanmış yönetici özeti e-posta doğrulaması (1-20 e-posta), harici üçüncü taraf alıcı uyarısı, normalize edilmiş hata kodları ve çalışma alanı değişiminde çalışan indirmenin iptali.
- **[03-account-team-billing/](./step-08/governance-settings-chat/03-account-team-billing/)** (10 Test Vakası + `README.md`):
  Tekil atomik proje ayarları (`update-project-settings`), rakip sabitleme görsel önceliği, 7 kategorili kaynak etiketleri ve mükerrer isim eşleme çarpışma koruması (`duplicate_alias`), zorunlu `role: "member"` ile takım davetleri, mükerrer davet kalkanı (`already_exists`), son sahip demote/askıya alma koruması (`last_owner_required`), yıkıcı olmayan üye askıya alma, Stripe müşterisi bağlanmamış modalı (`openUnlinkedCustomerModal()`), 1 kredi = 1 hücre kota politikası ve kiracı değişiminde bellek temizliği (`orch.triggerCleanup()`).
- **[04-zeo-ai-chat-drawer/](./step-08/governance-settings-chat/04-zeo-ai-chat-drawer/)** (10 Test Vakası + `README.md`):
  Çift yüzeyli başlatma (kayan çekmece `.ai-help-trigger` ve tam sayfa asistan `tab=assistant`), hazır soru kartları (`.preset-card`), composer markdown formatlama araç çubuğu, 5MB dosya eki limiti savunması (`5,242,880 bytes`), canlı modda sadece metin içeren RPC yükü izolasyonu, 5 olaylı SSE streaming RPC protokolü (`send-chat-message`: `onAccepted`, `onSnapshot`, `onReset`, `onEvent`, tamamlama), 16ms uyarlanabilir daktilo döngüsü (`typeTick`), `AbortController` ve `stop-chat-response` ile akış iptali, klavye ergonomisi (`Shift+Enter` ile 190px'e kadar genişleyen yeni satır vs `Enter` ile gönderme), çevrimdışı ağ kopması ve satır içi yeniden deneme, açılır atıf detay çekmecesinin arka plandaki sohbet taslağını bozmaması.

---

## ⚡ Ego-Browser ile Otomasyon Yürütme Sözleşmesi

Tüm Gherkin test vakaları, insan test mühendisleri tarafından manuel uygulanabileceği gibi `ego-browser nodejs` ile de tam uyumludur. Her bir vaka için aşağıdaki 5 aşamalı yaşam döngüsü geçerlidir:

```bash
ego-browser nodejs <<'EOF'
// Phase 1: Görev Alanı İzolasyonu
const task = await useOrCreateTaskSpace('e2e-anysite-step-01');
cliLog('Task Space: ' + task.id);

// Phase 2: Navigasyon ve Hidrasyon
await openOrReuseTab('[APP_URL]/#/auth', { wait: true, timeout: 30 });
await wait(2);

// Phase 3: Semantik Gözlem ve Eylem
const snap = await snapshotText();
cliLog('Snapshot:\n' + snap.slice(0, 500));
await click('#btn-bypass-test-login', { label: 'Bypass Login Gate' });
await wait(2);

// Phase 4: Durum Doğrulama (Tek IIFE)
const state = await js(String.raw`(() => {
  return {
    url: window.location.href,
    title: document.title,
    user: window.state?.currentUser?.email
  };
})()`);
cliLog('Asserted State: ' + JSON.stringify(state));

// Phase 5: Ayrı Heredoc ile Temiz Kapanış (completeTaskSpace keep: false)
EOF
```

### 🖥️ MacBook & Remote Display Sözleşmesi:
- Ego Browser fiziksel bir MacBook donanımı üzerinde çalışır (`ssh macbook ...`).
- Ekran görüntüleri test esnasında MacBook üzerinde yakalanır (`/tmp/ego-shots/...`).
- Test icra edildikten sonra görüntüler SCP aracılığıyla ilgili vakanın yerel sonuç dizinine (`[case-slug]/[case-number]-gherkin-result-[case-slug]/screenshots/`) aktarılır.
- Yazarlık (authoring) aşamasında asla boş sonuç klasörü açılmaz; bu dizinler yalnızca test icra edildiğinde dinamik olarak oluşturulur.

---

## 🏆 Doğrulama ve Tamamlanma Matrisi (%100 Complete)

> **Tarih**: 2026-09-25 · **Yürütme Durumu**: **225 / 225 Vaka (%100.0)** · **Genel Sonuç**: **TAMAMLANDI (PASSED)**

| Adım (Step) | Modül & Paket | Vaka Sayısı | Sonuç | Durum Detayı |
|:---|:---|:---:|:---:|:---|
| **Step 01** | `01-login-and-session` | 12 / 12 | **PASSED** | E-posta ön doğrulama, OTP ızgarası (246810), 55sn sayaç, SAML SSO, E2E dev bypass, rate limit, yerelleştirme. |
| **Step 01** | `02-brand-setup-and-onboarding` | 12 / 12 | **PASSED** | Marka tohumlama, ccTLD pazar çıkarımı, 10 konu tavanı, Trigger.dev yoklama zaman aşımı, proje kesinleştirme. |
| **Step 02** | `01-sidebar-and-route-switching` | 10 / 10 | **PASSED** | 15 sekme rotası, Marka değiştirici, daraltma/genişletme, `bootSeq` sıra kilidi, mobil çekmece. |
| **Step 02** | `02-command-palette-and-shortcuts` | 10 / 10 | **PASSED** | ⌘K paleti, regex meta-karakter kaçışı, yön tuşları dairesel gezinti, klavye odağı kurtarma. |
| **Step 02** | `03-theme-lang-and-profile` | 12 / 12 | **PASSED** | Açık/Koyu/Sistem teması, TR/EN yerelleştirme, Yenilikler modalı, Ürün turu rota ayrılma kusuru giderildi (`TC-PREF-11`). |
| **Step 03** | `01-kpi-scorecards-and-filters` | 11 / 11 | **PASSED** | KPI skor kartları, dürüst baz çizgi etiketi (`.ov-demo-badge`), 7D/90D hızlı tıklama yarış kilidi, motor filtreleri. |
| **Step 03** | `02-visibility-trend-chart` | 11 / 11 | **PASSED** | Çizgi/Çubuk modları, SVG nişangah sınır kırpma ($x \ge 4\text{px}$), hover araç ipucu, çift grafik eksenleri. |
| **Step 03** | `03-geo-world-map` | 11 / 11 | **PASSED** | Kloroplet vektör haritası, 4 yoğunluk kademesi, 1.0x–9.0x zoom/pan motoru, harita ağ hatası kurtarma. |
| **Step 04** | `01-platform-engine-benchmark` | 12 / 12 | **PASSED** | 5 motor matrisi, 3 aşamalı getirme boru hattı, parametrik yanıt kartı, atıf çekmecesi WAI-ARIA odak hapsi. |
| **Step 04** | `02-sentiment-and-audience` | 12 / 12 | **PASSED** | Algı kutup dağılımı, küçük örneklem kilidi (<3 iddia için bekleyen durumu), halüsinasyon radarı, ani artış rozetleri. |
| **Step 05** | `01-prompt-list-and-filters` | 10 / 10 | **PASSED** | 100 prompt kapasite halkası doygunluğu, XSS/SQL filtre sanitizasyonu, istek üzerine çalıştırma önizlemesi. |
| **Step 05** | `02-prompt-creation-and-editor` | 11 / 11 | **PASSED** | Satır içi düzenleyici, 409 mükerrer çakışması, YZ prompt kümeleme sihirbazı, UTF-8 BOM'lu CSV yükleme. |
| **Step 06** | `01-ai-agent-vitals-and-telemetry` | 12 / 12 | **PASSED** | GPTBot/ClaudeBot/PerplexityBot sınıflandırması, 5xx durum oranları, Core Web Vitals audit motoru. |
| **Step 06** | `02-search-volume-and-demand` | 12 / 12 | **PASSED** | Çift trend grafiği, karekök ölçekleme sınırları, toplu izleme listesi araç çubuğu, demografi haritası. |
| **Step 07** | `01-opportunities-engine` | 13 / 13 | **PASSED** | Fırsat kartları, olay yayılımı izolasyonu, 10sn geri alma (undo) sınırı, Content Studio köprüsü, CSV dışa aktarımı. |
| **Step 07** | `02-content-studio-pipeline` | 14 / 14 | **PASSED** | 4 adımlı makale sihirbazı, SSE canlı belirteç akışı, kısmi taslak kurtarma, AEO markdown editörü, 6 kriterli URL slug. |
| **Step 08** | `01-brand-hub-ground-truth` | 10 / 10 | **PASSED** | Doğruluk Kasası iddia yönetimi, `expectedVersion` 409 kilit çakışması, SVG DAG döngü tespiti, 10 durak kelepçeleme. |
| **Step 08** | `02-dashboards-and-exports` | 10 / 10 | **PASSED** | 16 widget türü, formül enjeksiyonu (`=+-@\t\r`) koruması, UTF-8 BOM, binary PDF ve `window.print()` yedeği. |
| **Step 08** | `03-account-team-billing` | 10 / 10 | **PASSED** | Atomik ayarlar, son sahip koruması (`last_owner_required`), Stripe müşteri portali, 10M kredi sayacı, bellek tahliyesi. |
| **Step 08** | `04-zeo-ai-chat-drawer` | 10 / 10 | **PASSED** | Kayan Copilot çekmecesi, 5MB dosya tavanı, RPC yük izolasyonu, SSE streaming, daktilo efekti, AbortController. |
| **GENEL TOPLAM** | **20 Bağımsız Paket** | **225 / 225** | **%100.0 PASSED** | **Tüm testler ve kanıtlar doğrulanmış, ekran görüntüleri çekilmiş ve kaydedilmiştir.** |

---

### 🛡️ Kalite Kapıları & Doğrulama Kanıtları (Gates)
- **Fast Syntax Gate**: `node --check` projedeki 60+ JavaScript dosyasında çalıştırıldı -> **Exit Code: 0** (Hatasız).
- **Provider Parity Gate**: Dual-Driver sözleşme testleri (`node tests/provider-parity.js`) -> **186 passed, 0 failed, 186 total** (Hatasız).
- **Orphan Worktrees**: `git worktree list && git worktree prune` -> **0 sahipsiz/artık iş ağacı**.
- **Background Tasks**: `manage_task(Action: 'list')` -> **0 aktif arka plan görevi**.
- **Subagents**: `manage_subagents(Action: 'list')` -> **0 aktif alt ajan (hepsi temizlendi)**.

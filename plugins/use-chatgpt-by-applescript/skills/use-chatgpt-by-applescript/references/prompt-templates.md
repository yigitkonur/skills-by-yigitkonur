# Prompt Templates & Plugin Dispatch Framework

This reference defines the prompt engineering standards and plugin invocation matrix when driving the native macOS ChatGPT desktop app.

---

## 1. Plugin Dispatch Decision Framework

When interacting with ChatGPT desktop app, you can explicitly control which bundled tools ChatGPT attaches to the conversation. Plain text mentions (like `@Browser` or `@Computer`) are often interpreted as inert prose. Always use the exact markdown URI schemes:

| Task Objective | Requirement | Plugin Tag to Prepend |
|---|---|---|
| **Live Web Research** | Search engines, online registries, news, verified current URLs, external citations | `[@Browser](plugin://browser@openai-bundled)` |
| **Computer & OS Actions** | Desktop interaction, local app usage, filesystem tasks, running shell commands, screen review | `[@Computer](plugin://computer-use@openai-bundled)` |
| **Hybrid Research & Local Execution** | Web search followed by local file generation or OS-level automation | Both tags prepended |
| **Pure Reasoning / Coding** | Internal text synthesis, translation, code refactoring, math, formatting | *No plugin tag added* |

### Plugin URI Reference
- **Browser Plugin**: `[@Browser](plugin://browser@openai-bundled)`
- **Computer Use Plugin**: `[@Computer](plugin://computer-use@openai-bundled)`

---

## 2. Portrait & Face Verification Template (Web Research)

Used when researching individuals (clinicians, executives, contributors) to discover direct verified portrait URLs while eliminating stock photos, furniture, clinic logos, and colleagues.

```markdown
[@Browser](plugin://browser@openai-bundled)

Lütfen internette geniş kapsamlı bir arama yap ve şu kişinin doğrulanmış gerçek vesikalık / portre fotoğrafını bulmama yardım et:

Kişi / Uzman Bilgileri:
- İsim: {{NAME}}
- Unvan / Rol: {{TITLE}}
- Şehir / Bölge / Ülke: {{LOCATION}}
- Kurum / Klinik / Muayenehane: {{ORGANIZATION}}
- Bilinen Başlangıç Sitesi / Profil: {{WEBSITE}} (Lütfen sadece bu adresle sınırlı kalma; Google Görseller, Bing, meslek odaları, LinkedIn, sektörel dizinler ve sosyal/profesyonel ağlarda tüm internet üzerinde geniş arama yap)
- İletişim / Detay: {{EXTRA_DETAILS}}

Arama ve Doğrulama Kriterleri:
1. Web'de bu kişinin gerçek yüzünü gösteren yüksek çözünürlüklü bir fotoğrafı var mı?
2. KESİN KURAL: Boş ofis, terapi odası, koltuk, masa, bina, kurum logosu, maskot, illüstrasyon, grafik, stok fotoğraf veya aynı kurumda çalışan başka bir meslektaşın fotoğrafı KESİNLİKLE KABUL EDİLMEZ.
3. Sadece ve sadece {{NAME}} adlı kişinin kendisine ait gerçek insan yüzü vesikalık/portre fotoğrafı kabul edilir.
4. Eğer bulursan: Doğrudan görselin açık URL'sini (direct image URL, .jpg/.png/.webp) ve bulunduğu kaynak web sayfasının linkini paylaş.
5. Eğer fotoğraf yoksa (veya sitede yalnızca boş oda/koltuk/logo/silüet varsa): Açıkça "Fotoğraf bulunamadı (yalnızca koltuk/logo/boş oda mevcut)" şeklinde belirt.
```

---

## 3. General Entity & Technical Research Template (Web Research)

Used when investigating an organization, product, registry entry, or technical specification:

```markdown
[@Browser](plugin://browser@openai-bundled)

Lütfen internette derinlemesine bir web araştırması yap ve aşağıdaki konu hakkında doğrulanmış birincil kanıtları topla:

Hedef / Konu: {{TARGET_OR_TOPIC}}
Araştırma Sorusu: {{RESEARCH_QUESTION}}
Bilinen Başlangıç URL'leri: {{KNOWN_URLS}}

Gereksinimler:
1. İddiaları yalnızca birincil kaynaklardan (resmi kayıtlar, resmi dokümantasyon, sicil gazetesi, doğrulanmış kaynaklar) doğrula.
2. Karşılaştığın çelişkili veya güncelliğini yitirmiş bilgileri belirt.
3. Alıntıladığın her bulgu için kaynak web sayfasının tam URL'sini ekle.
```

---

## 4. Computer Use Template (Desktop & Local OS Automation)

Used when prompting ChatGPT to perform actions directly on the macOS host (inspecting files, running local tools, navigating applications):

```markdown
[@Computer](plugin://computer-use@openai-bundled)

Lütfen bilgisayardaki mevcut çalışma ortamını ve sistem durumunu inceleyerek şu görevi tamamla:

Görev: {{TASK_DESCRIPTION}}
Beklenen Çıktı: {{EXPECTED_OUTCOME}}

Kısıtlamalar:
1. Yalnızca belirtilen çalışma dizininde ve dosyalarda değişiklik yap.
2. İşlem tamamlandığında çalıştırılan komutları ve sonuçları özetle.
```

---

## 5. Pure Reasoning & Synthesis Template (No Plugins)

Used when no external network access or computer manipulation is required:

```markdown
Aşağıdaki metni/kodu analiz et ve istenen formatta yeniden yapılandır:

Girdi:
{{INPUT_CONTENT}}

Gereksinimler:
1. {{REQUIREMENT_1}}
2. {{REQUIREMENT_2}}
```

---

## 6. Prompt Engineering Invariants

1. **No Internal File Paths in Web Queries:** Never expose internal project paths (e.g. `cities/almanya/...` or `repo/src/...`) in web search prompts. Remote ChatGPT has no access to the caller's filesystem; internal paths add noise and confuse search queries.
2. **Broad Search Scope:** Always specify that known URLs are merely starting hints, explicitly instructing ChatGPT to search across general search engines (Google, Bing) and professional databases.
3. **Negative Constraints:** State what is *forbidden* (logos, furniture, stock images, multi-doctor colleague confusion). Large language models adhere far better to negative constraints when they are explicitly enumerated.
4. **Clean Plugin Matching:** Only attach plugins that are actually needed for the task to conserve latency and prevent tool-call hallucinations.

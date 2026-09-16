# Prompt Templates & Browser Plugin Hooks

This reference defines the prompt engineering standard when driving the native macOS ChatGPT desktop app for autonomous web research.

## 1. The Critical `@Browser` Plugin Hook

When pasting prompts into the ChatGPT desktop app, plain text like `@Browser` is frequently treated as literal prose rather than a functional tool invocation.

To explicitly force ChatGPT desktop app to resolve and attach the built-in browsing tool, use the exact URI reference:

```markdown
[@Browser](plugin://browser@openai-bundled)
```

Placing this line at the very top of the prompt causes ChatGPT's internal markdown renderer to recognize the bundled browsing plugin and invoke live web search capabilities immediately upon receiving the user message.

---

## 2. Portrait & Face Verification Template

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

## 3. General Entity & Company Research Template

Used when investigating an organization, product, registry entry, or technical claim:

```markdown
[@Browser](plugin://browser@openai-bundled)

Lütfen internette derinlemesine bir web araştırması yap ve aşağıdaki varlık hakkında doğrulanmış birincil kanıtları topla:

Hedef: {{ENTITY_NAME}}
Konu / Araştırma Sorusu: {{RESEARCH_QUESTION}}
Bilinen Başlangıç URL'leri: {{KNOWN_URLS}}

Gereksinimler:
1. İddiaları yalnızca birincil kaynaklardan (resmi kayıtlar, sicil gazetesi, resmi şirket duyurusu, doğrulanmış haber kaynakları) doğrula.
2. Karşılaştığın çelişkili veya güncelliğini yitirmiş bilgileri belirt.
3. Alıntıladığın her bulgu için kaynak web sayfasının tam URL'sini ekle.
```

---

## 4. Prompt Engineering Invariants

1. **No Internal File Paths:** Never expose internal project paths (e.g. `cities/almanya/...` or `repo/src/...`) in the prompt. Remote ChatGPT has no access to the caller's filesystem; internal paths add noise and confuse search queries.
2. **Broad Search Scope:** Always specify that known URLs are merely starting hints, explicitly instructing ChatGPT to search across general search engines (Google, Bing) and professional databases.
3. **Negative Constraints:** State what is *forbidden* (logos, furniture, stock images, multi-doctor colleague confusion). Large language models adhere far better to negative constraints when they are explicitly enumerated.

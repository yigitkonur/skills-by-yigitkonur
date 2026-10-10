# Turkish Morpho-Syntactic Translationese Guide

Turkish is an agglutinative, pro-drop language with rich morphology, flexible topic-comment word order, and prosodic cadence. When Large Language Models generate or translate Turkish, they frequently superimpose English and Germanic/Romance syntactic patterns onto Turkish roots. The resulting prose—often called *çeviri kokan Türkçe* (translationese)—is technically grammatical according to rudimentary dictionary rules, but sounds stiff, wooden, bureaucratic, and deeply unidiomatic to native readers.

This guide catalogs the **14 fundamental morpho-syntactic translationese patterns**, analyzes their linguistic mechanisms, and provides natural human alternatives.

---

## 1. Linguistic Foundations: Why LLMs Produce Translationese

English is an isolating, non-pro-drop, rigid Subject-Verb-Object (SVO) language that relies heavily on auxiliary verbs, prepositions, and structural fillers ("by", "there is", "a/an"). 

Turkish, by contrast, is:
1. **Agglutinative**: Grammatical relations, mood, aspect, tense, and voice are encoded through suffixes attached to roots.
2. **Pro-drop**: Subject pronouns are omitted by default because verbal inflections explicitly specify person and number. Explicit pronouns indicate contrastive focus or emphasis.
3. **Topic-Prominent & Pragmatically Ordered**: While the default unmarked syntax is Subject-Object-Verb (SOV), constituents move freely before the verb for topicalization, or after the verb (*devrik cümle*) for conversational backgrounding, warmth, and cadence.
4. **Prosodically Cadenced**: Natural Turkish breathes through balanced paratactic clauses, finite verbs, and rhythmic pauses, rather than long cascades of participial subordinate clauses.

---

## 2. The 14 Fundamental Translationese Patterns

### Pattern 1: Tarafından-Pasifleri (Agentive Passive Calque)
* **Linguistic Cause**: Literal calque of English agentive passive (`by [agent] + passive verb`). In native Turkish, passive morphology (`-il-`, `-in-`) is reserved for unknown, irrelevant, or intentionally depersonalized agents. Combining an overt agent with "tarafından" produces stiff officialese.
* **Synthetic / AI**: *Yeni analiz modülü, yapay zekâ mühendislerimiz tarafından titizlikle geliştirilmiştir.*
* **Linguistic Flaw**: Heavy agentive passive calquing English "developed by our engineers". Stifles the active agency of the team.
* **Natural Alternative**: *Yeni analiz modülünü yapay zekâ mühendislerimiz geliştirdi.*

### Pattern 2: Belirsiz Artikel "Bir" Enflasyonu (Indefinite Article "Bir" Inflation)
* **Linguistic Cause**: Calquing obligatory English indefinite articles ("a/an") before singular countable nouns and predicate nominatives. In Turkish, indefinite reference is unmarked in generic, non-specific, and predicate roles.
* **Synthetic / AI**: *Şirketimiz, bulut bilişim alanında öncü bir sağlayıcıdır.*
* **Linguistic Flaw**: Calques English "is a leading provider". In predicate nominatives, "bir" is unnecessary and creates wooden syntax.
* **Natural Alternative**: *Bulut bilişim sektörünün öncülerindeniz.* (or: *Bulut bilişimde öncü bir kuruluşuz.*)

### Pattern 3: Sahte Fiilimsiler & Gereksiz Yardımcı Fiiller (Bureaucratic Auxiliaries)
* **Linguistic Cause**: Overusing bureaucratic phrasal fillers (*yapmakta olan*, *bulunmaktadır*, *yer almaktadır*, *hizmet vermektedir*) instead of direct, concise finite verbs.
* **Synthetic / AI**: *Platformumuzda 50'den fazla popüler araç entegrasyonu bulunmaktadır.*
* **Linguistic Flaw**: "Bulunmaktadır" officialese where simple, warm "var" is the native idiom.
* **Natural Alternative**: *Platformda en çok kullandığınız 50'den fazla araçla hazır entegrasyon var.*

### Pattern 4: Ulaç Yığılmaları (Converb / Gerund Chaining Overload)
* **Linguistic Cause**: Cascading multiple converbs (`-erek/-arak`, `-ip/-ıp`, `-dıkça/-dikçe`) in a single breath to mirror English participial subordinate clauses ("By doing X, doing Y, and doing Z..."). Suffocates the natural rhythmic breathing of Turkish sentences.
* **Synthetic / AI**: *Trafiği yedek sunuculara yönlendirerek, veritabanı bağlantılarını sıfırlayıp yapılandırma dosyalarını güncelleyerek kesintiyi sonlandırdık.*
* **Linguistic Flaw**: Chaining three converbs in a single breath destroys cadence.
* **Natural Alternative**: *Trafiği yedek sunuculara yönlendirdik, veritabanı bağlantılarını sıfırladık ve yapılandırmayı güncelleyerek kesintiyi giderdik.*

### Pattern 5: Kopula Kaçınmaları & -dir Mekanik Enflasyonu (Copula Inflation)
* **Linguistic Cause**: Mechanically affixing `-dir/-dır` to every predicate adjective or noun. In modern Turkish, `-dir` indicates official decree, encyclopedic timelessness, or epistemic hypothesis; when applied to marketing or conversational copy, it sounds like a court summons or legal statute.
* **Synthetic / AI**: *Platformumuz hızlıdır, güvenlidir ve tamamen ölçeklenebilirdir.*
* **Linguistic Flaw**: Repetitive predicative copula "-dir" on every adjective; cold and sterile.
* **Natural Alternative**: *Platformumuz hızlı, güvenli ve tamamen ölçeklenebilir.*

### Pattern 6: Kataforik İki Nokta Üst Üste (Cataphoric Colon / Label-Colon Habit)
* **Linguistic Cause**: Calquing presentation slides ("Problem: X.", "Solution: Y.", "Result: Z.") into running body copy instead of composing fluent, integrated prose.
* **Synthetic / AI**: *Sonuç: Daha az toplantı, daha çok iş üretimi.*
* **Linguistic Flaw**: Unintegrated label-colon fragment calque breaking narrative flow.
* **Natural Alternative**: *Toplantıları azaltın, asıl işinize odaklanın.*

### Pattern 7: Kalıp Bağlaçlar (Mechanical Transition Calques)
* **Linguistic Cause**: Opening every paragraph or sentence with robotic transition formulas (*Bununla birlikte*, *Öte yandan*, *Ek olarak*, *Sonuç olarak*, *Dahası*) rather than utilizing Turkish discourse particles (`ise`, `de/da`) or thematic word order.
* **Synthetic / AI**: *Gelirlerimiz %40 arttı. Ek olarak, net kâr marjımız da genişledi. Sonuç olarak, yılı karlı kapattık.*
* **Linguistic Flaw**: Sentence-opening connective clutter calquing English freshman essay templates.
* **Natural Alternative**: *Gelirlerimiz %40 artarken net kâr marjımız da genişledi; yılı hedeflerimizin üzerinde bir kârlılıkla kapattık.*

### Pattern 8: İyelik Eki Tembelliği & Ad Tamlaması Deformasyonu (Compound Noun Deformity)
* **Linguistic Cause**: Translating English noun adjunct strings ("user experience management platform") by dropping intermediate genitive and possessive markers, producing ungrammatical pseudo-compounds.
* **Synthetic / AI**: *Bulut tabanlı kullanıcı deneyim yönetim platformu.*
* **Linguistic Flaw**: Omission of possessive suffixes on compound nouns (*deneyim yönetim* instead of *deneyimi yönetimi*).
* **Natural Alternative**: *Kullanıcı deneyimini buluttan yöneten modern platform.*

### Pattern 9: Soyut Adlaştırma Enflasyonu (Latinate Nominalization Calque)
* **Linguistic Cause**: Calquing Latinate abstract nouns ending in *-tion*, *-ment*, or *-ance* by piling up `-me/-ma` suffixes combined with empty light verbs (*gerçekleştirmek*, *sağlamak*, *temin etmek*).
* **Synthetic / AI**: *İş süreçlerinizin optimizasyonunun gerçekleştirilmesini ve verimliliğinizin maksimizasyonunu sağlıyoruz.*
* **Linguistic Flaw**: Extreme nominalization stack destroying dynamic action.
* **Natural Alternative**: *İş süreçlerinizi hızlandırıyor, veriminizi katlıyoruz.*

### Pattern 10: Sahte Etken/Edilgen Kaymaları (Accountability Evasion)
* **Linguistic Cause**: Shifting into corporate passive or impersonal verbs (*yaşanmıştır*, *gözlemlenmiştir*, *karar verilmiştir*) to evade human agency and responsibility during mistakes or outages.
* **Synthetic / AI**: *Teknik bir arıza sebebiyle bazı kullanıcı verilerine erişimde kesinti yaşanmıştır.*
* **Linguistic Flaw**: Cold, evasive nominal passive evading ownership.
* **Natural Alternative**: *Sistemlerimizde yaşanan bir arıza yüzünden bazı verilerinize geçici olarak erişemedik; sorunu çözüyoruz.*

### Pattern 11: Devrik Cümle Korkusu / Kaskatı SOV (Rigid SOV Tyranny)
* **Linguistic Cause**: Enforcing strict, monotonic Subject-Object-Verb order in 100% of sentences. In native Turkish literature, high-end journalism, and spoken communication, *devrik cümle* (post-verbal positioning) provides warmth, rhythm, emphasis, and focus.
* **Synthetic / AI**: *Üç yıl önce sıfır sermaye ile başladığımız bu yolculukta bugün 1 milyon kullanıcıya ulaşmanın haklı gururunu ve mutluluğunu yaşıyoruz.*
* **Linguistic Flaw**: Pompous, breathless single-sentence rigid SOV structure destroying emotional punchiness.
* **Natural Alternative**: *Tam 1 milyon kullanıcıya ulaştık bugün. Üç yıl önce sıfır sermayeyle çıktığımız bu yolda hayal bile edemezdik buralara geleceğimizi.*

### Pattern 12: Sözde Soru Cümleleri (Formulaic Rhetorical Hooks)
* **Linguistic Cause**: Opening marketing sections with patronizing, formulaic copywriting questions (*Hazır mısınız? Başlayalım.*, *Biliyor muydunuz?*).
* **Synthetic / AI**: *Verimliliğinizi artırmaya hazır mısınız? O halde başlayalım.*
* **Linguistic Flaw**: Patronizing rhetorical question insulting the reader's intelligence.
* **Natural Alternative**: *Ekibinizin haftalık çalışma temposunu hafifletecek üç somut adımı aşağıda derledik.*

### Pattern 13: Dolaylama & Sahte Yüklemler (Circumlocution & Fake Light Verbs)
* **Linguistic Cause**: Calquing English phrasal verb idioms (*have an impact on* -> *etkiye sahip olmak*, *provide service* -> *hizmet vermek*, *take action* -> *aksiyon almak*) instead of direct native verbs (*etkilemek*, *hizmet sunmak*, *harekete geçmek*).
* **Synthetic / AI**: *Yeni regülasyonlar, sektör üzerinde derin bir etkiye sahip olacaktır.*
* **Linguistic Flaw**: Clunky circumlocution calquing "have a profound impact on".
* **Natural Alternative**: *Yeni regülasyonlar sektörü derinden etkileyecek.*

### Pattern 14: Pro-drop Kaçınması (Subject Pronoun Inflation)
* **Linguistic Cause**: Imposing non-pro-drop English subject rules onto Turkish by repeating overt subject pronouns (*Ben*, *Biz*, *Siz*) at the start of every clause.
* **Synthetic / AI**: *Biz müşterilerimizi dinliyoruz, çünkü biz onların geri bildirimlerine değer veriyoruz.*
* **Linguistic Flaw**: Redundant pronoun inflation calquing English "We listen... because we value...".
* **Natural Alternative**: *Müşterilerimizi dinliyor, geri bildirimlerine kulak veriyoruz.*

---

## 3. Contrastive Analysis Table: Synthetic vs. Natural Turkish

| Context / Genre | Synthetic / AI Sentence | Predominant Flaw | Natural Human Alternative |
| :--- | :--- | :--- | :--- |
| **SaaS Landing Page** | Platformumuzda 50'den fazla araç entegrasyonu bulunmaktadır. | Sahte yardımcı fiil (*bulunmaktadır*) | Platformda en çok kullandığınız 50'den fazla araçla hazır entegrasyon var. |
| **Investor Newsletter** | Q3 hedefleri, yönetim kurulu tarafından oy birliği ile onaylandı. | Tarafından-pasifi | Yönetim kurulu, üçüncü çeyrek hedeflerini oy birliğiyle onayladı. |
| **Customer Support** | Müşteri memnuniyeti bizim en yüksek önceliğimizdir. | -dir mekanik enflasyonu & klişe | Bizim için en önemli şey müşteri memnuniyeti. |
| **Incident Post-Mortem** | Yapılandırma hatası sonucu kesinti yaşanmıştır. | Edilgen sorumluluk kaçınması | Yapılandırma dosyasındaki bir hatadan dolayı servislerimiz 20 dakika kesintiye uğradı. |
| **Mobile Empty State** | Burada henüz hiçbir bildiriminiz bulunmamaktadır. | Soğuk resmiyet & yardımcı fiil | Henüz hiç bildiriminiz yok. |
| **B2B Outreach** | Şirketimiz, yapay zekâ alanında lider bir kuruluştur. | Belirsiz artikel "bir" & -dir enflasyonu | Yapay zekâ çözümlerinde Türkiye'nin en deneyimli ekibiyiz. |
| **Onboarding Flow** | Hesabınızı açarak, ekibinizi davet edip projeye başlayabilirsiniz. | Ulaç yığılması (*-erek, -ip, -erek*) | Hesabınızı açın, ekibinizi davet edin ve projenize hemen başlayın. |
| **Security Advisory** | Güvenlik açığı araştırmacılar tarafından tespit edilmiştir. | Tarafından-pasifi & -miştir | Açığı bağımsız güvenlik araştırmacıları fark etti. |
| **Twitter / X Thread** | Yapay zekâ dönemi başladı. Bununla birlikte, yeni riskler doğuyor. | Kalıp bağlaç (*Bununla birlikte*) | Yapay zekâ dönemi başladı; ama getirdiği yeni riskleri henüz yeterince konuşmuyoruz. |
| **Founder Retrospective** | Rekor büyümeye ulaştığımızı duyurmaktan mutluluk duyuyoruz. | Kaskatı SOV & kuru resmiyet | Rekor bir büyümeyle kapattık bu yılı; emeği geçen herkese teşekkürler. |

---

## 4. Operational Checklist for Turkish Auditing

When auditing Turkish copy in the Active Ledger:
1. **Locate "tarafından"**: If the sentence has an overt agent, invert to active voice.
2. **Audit "bir"**: Does the noun need an indefinite article, or is it a predicate nominative / generic object? If generic, strike "bir".
3. **Strip "-dir / -dır"**: Remove from predicate adjectives and marketing value propositions unless stating a legal decree or scientific law.
4. **Count converbs**: If a sentence contains more than one `-erek`, `-ip`, or `-dıkça`, split into balanced finite clauses.
5. **Liberate the verb**: Move secondary thoughts after the verb (*devrik cümle*) when writing conversational, editorial, or social copy.
6. **Drop overt pronouns**: Eliminate *ben*, *biz*, *siz* unless required for contrastive focus.

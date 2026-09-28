# Astro Mühendislik Standartları ve En İyi Uygulamalar Bilgi Tabanı (Astro Best Practices Stack)

Bu dokümantasyon yığını, **Multi-Page Architecture (MPA)** ve **Zero-JS by Default** ilkelerine dayanan Astro'nun tüm çekirdek yeteneklerini derinlemesine incelemek; Next.js ve klasik SPA ekosisteminden gelen geliştiricilerin zihinsel yanılgılarını gidermek ve büyük ölçekli Astro web sitelerini denetlemek (audit) amacıyla oluşturulmuştur.

10 bağımsız uzman araştırma ajanı tarafından, resmi Astro dokümantasyonları ve teknik şartnamelere dayalı olarak hazırlanmış ve doğrulanmış **170 adet atomik kural kartı (toplam 10.281 satır)** içermektedir. Her kural kartı kesinlikle $\le 100$ satır olup; gerekçe (**Why We Do This**), React/Next.js karşılaştırması (**How It Differs**), somut hatalı (**❌ Bad Practice**) ve ideal (**✅ Best Practice**) kod blokları ile doğrulama (**Verification & Audit**) adımlarını içerir.

---

## Bağlam ve Kategori Dağılımı

| #      | Bağlam (Context)                      | Klasör                                                                                     | Dosya Sayısı  |   Toplam Satır   | Odak Alanı                                                                                        |
| ------ | ------------------------------------- | ------------------------------------------------------------------------------------------ | :-----------: | :--------------: | ------------------------------------------------------------------------------------------------- |
| **01** | **Mimari & Çekirdek Felsefe**         | [`01-architecture-and-philosophy/`](./01-architecture-and-philosophy/)                     |      16       |      1.053       | MPA vs SPA, Zero-JS, BYOF framework izolasyonu, HTML streaming, Vite cache izolasyonu             |
| **02** | **Adalar & Hidrasyon**                | [`02-islands-and-hydration/`](./02-islands-and-hydration/)                                 |      15       |       789        | Client direktifleri, Server Islands (`server:defer`), Nanostores                                  |
| **03** | **Yönlendirme & Sayfa Yaşam Döngüsü** | [`03-routing-and-pages/`](./03-routing-and-pages/)                                         |      21       |      1.299       | Dinamik rotalar, `getStaticPaths`, `<ClientRouter />`, analytics & sayfa görüntüleme takibi       |
| **04** | **Content Layer & Şemalar**           | [`04-content-layer-and-collections/`](./04-content-layer-and-collections/)                 |      15       |       971        | Astro 5 `src/content.config.ts`, `loader` API, Zod, SQLite önbelleği                              |
| **05** | **Veri Çekme & API Endpoints**        | [`05-data-fetching-and-endpoints/`](./05-data-fetching-and-endpoints/)                     |      14       |       991        | Frontmatter fetch, `APIRoute`, `security.checkOrigin` CSRF, Astro Actions progressive enhancement |
| **06** | **Middleware & Güvenlik**             | [`06-middleware-and-auth/`](./06-middleware-and-auth/)                                     |      20       |      1.192       | `defineMiddleware`, `sequence()`, `App.Locals`, Auth guard, `Astro.session`, response streaming   |
| **07** | **Varlıklar & Görsel Hattı**          | [`07-assets-and-image-pipeline/`](./07-assets-and-image-pipeline/)                         |      16       |       860        | `astro:assets`, `<Image />`, `<Picture />`, `getImage()`, font CLS önleme                         |
| **08** | **i18n & Çoklu Dil Mimarisi**         | [`08-i18n-and-localization/`](./08-i18n-and-localization/)                                 |      15       |      1.032       | Native i18n routing, URL helpers (`getRelativeLocaleUrl`), BiDi                                   |
| **09** | **Performans & Prefetch**             | [`09-performance-prefetch-and-transitions/`](./09-performance-prefetch-and-transitions/)   |      17       |       956        | `data-astro-prefetch`, viewport tuzakları, scoped CSS, CWV                                        |
| **10** | **Denetim & Next.js Göçü**            | [`10-auditing-testing-and-nextjs-migration/`](./10-auditing-testing-and-nextjs-migration/) |      21       |      1.138       | Zero-JS denetimi, bundle analizi, CI `astro check`, Container API ile birim testler               |
| **∑**  | **TOPLAM**                            | **10 Bağlam**                                                                              | **170 Kural** | **10.281 Satır** | **Tam Ölçekli Bilgi Tabanı (Ort. 60.5 satır/kural)**                                              |

---

## Kural Kartı Standart Formatı

Her kural dosyası şu 4 zorunlu bileşeni içerir:

1. **1. Why We Do This**: Kuralın mimari temeli ve tarayıcı performansına somut katkısı.
2. **2. How It Differs From Classic React / Next.js**: React veya Next.js'ten gelen zihinsel model farkı.
3. **3. Common Mistakes & Anti-Patterns**: Sık yapılan hatalar ile `❌ Bad Practice` ve `✅ Best Practice` kod karşılaştırmaları.
4. **4. Verification & Audit**: Kuralın ihlal edilip edilmediğini kanıtlayan CLI komutu veya DevTools adımı.

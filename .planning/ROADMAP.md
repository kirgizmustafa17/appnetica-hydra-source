# Proje Yol Haritası (ROADMAP)

## Fazlar

### Faz 1: Çekirdek Parser & Veri Çıkarma Motoru
- [ ] SvelteKit `__data.json` deval indeks yapısını çözen parser modülü (`scraper/parser.py`).
- [ ] Oyun başlığı, dosya boyutu, doğrudan `cloud.mail.ru` indirme bağlantıları ve dosya ID'lerinin ayıklanması.
- [ ] Çoklu dosya ve işletim sistemi etiketleme mantığı (`[Linux]`, `[Bonus]`).
- [ ] Birim testleri (`tests/test_parser.py`) ile doğrulama (`stones-keeper-directors-cut`, `magical-blush`).

### Faz 2: Sitemap Tarayıcısı, Artımlı Senkronizasyon & Önbellek
- [ ] `games.xml` sitemap çekici ve ayrıştırıcı modülü (`scraper/crawler.py`).
- [ ] `.cache.json` durum takipçisi ile `lastmod` karşılaştırma mekanizması (`scraper/cache.py`).
- [ ] Asenkron HTTP istemcisi (rate limit, retry, concurrency semaphore) ile CLI giriş noktası (`scraper/main.py`).
- [ ] `appnetica.json` Hydra şemasına uygun dosya yazımı.

### Faz 3: GitHub Actions Otomasyonu, GitHub Pages & Dokümantasyon
- [ ] `.github/workflows/update-source.yml` GitHub Actions iş akışı (Cron: `0 */6 * * *`).
- [ ] Git commit/push ve GitHub Pages otomatik dağıtımı.
- [ ] `README.md` kurulum, Hydra Launcher'a kaynak ekleme rehberi ve durum rozetleri.
- [ ] İlk test çalıştırması ve GitHub'a canlı dağıtım.

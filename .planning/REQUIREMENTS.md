# Gereksinimler (Requirements)

## Fonksiyonel Gereksinimler
- **REQ-1 (Hydra JSON Formatı):**
  - Çıktı dosyası `appnetica.json` adında geçerli bir JSON olmalıdır.
  - Kök yapısı `{"name": "Appnetica", "downloads": [...]}` biçiminde olmalıdır.
  - Her bir download nesnesi `title`, `uris`, `uploadDate`, `fileSize` alanlarını içermelidir.
- **REQ-2 (Doğrudan İndirme Bağlantıları):**
  - Sitedeki `file_link` (ör. `cloud.mail.ru`) doğrudan bağlantıları `uris` dizisine eklenmelidir.
  - Doğrudan link bulunamadığında veya alternatif gerekirse `https://appnetica.com/file/<file_id>?game=<game_id>` yönlendirme bağlantısı kullanılmalıdır.
- **REQ-3 (Çoklu Dosya / Platform Ayrımı):**
  - Aynı oyuna ait birden fazla dosya varsa (ör. Windows, Linux, Bonus):
    - Windows ana dosyası: `Başlık`
    - Linux dosyası: `Başlık [Linux]`
    - Bonus dosyası: `Başlık [Bonus]`
    - Diğer işletim sistemleri: `Başlık [OS Adı]`
    biçiminde bağımsız download kayıtları oluşturulmalıdır.
- **REQ-4 (Artımlı Güncelleme & Önbellek):**
  - `games.xml` içindeki `lastmod` değerleri `.cache.json` dosyasında saklanmalıdır.
  - Sonraki çalıştırmalarda sadece `lastmod` değişmiş veya yeni eklenmiş oyunların detay sayfaları çekilmelidir.
- **REQ-5 (GitHub Actions & Otomasyon):**
  - Her 6 saatte bir cron zamanlamasıyla otomatik çalışmalıdır.
  - Manuel tetikleme (`workflow_dispatch`) desteklenmelidir.
  - `appnetica.json` ve `.cache.json` dosyalarındaki değişiklikler otomatik olarak commitleyip ana dala itilmelidir.
  - GitHub Pages veya release mekanizması ile yayınlanmalıdır.

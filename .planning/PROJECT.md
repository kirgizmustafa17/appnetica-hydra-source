# Appnetica Hydra Source

## Proje Tanımı
Appnetica (appnetica.com) üzerindeki oyunları ve indirme bağlantılarını tarayarak Hydra Launcher (`https://hydralinks.cloud/sources/steamrip.json` benzeri) uyumlu JSON kaynağı oluşturan ve GitHub Actions ile periyodik olarak güncel tutan otomatik bir veri çıkarma ve yayınlama sistemi.

## Hedefler
- `https://appnetica.com/games.xml` sitemap üzerinden tüm oyunların dinamik keşfi.
- SvelteKit `__data.json` uç noktalarından oyun başlıkları, boyutları, versiyonları ve `cloud.mail.ru` doğrudan indirme bağlantılarının yüksek hızda asenkron ayıklanması.
- Çoklu platform ve dosya desteği (Windows ana oyun, Linux sürümleri, Bonus/DLC içeriklerinin etiketli olarak Hydra formatına dönüştürülmesi).
- Artımlı (incremental) güncelleme altyapısı (`.cache.json`) ile sitemap `lastmod` zaman damgası kontrolü yapılarak GitHub Actions üzerinde yalnızca değişen oyunların taranması (hafif ve hızlı cron).
- GitHub Pages ve Raw GitHub URL üzerinden Hydra Launcher kullanıcılarına kesintisiz JSON yayını.

## Teknoloji Yığını
- **Dil:** Python 3.11+
- **Kütüphaneler:** `httpx` (async HTTP), `asyncio`, `pytest`
- **Otomasyon:** GitHub Actions (Cron: her 6 saatte bir `0 */6 * * *` + `workflow_dispatch`)
- **Yayın:** GitHub Pages & Git Raw

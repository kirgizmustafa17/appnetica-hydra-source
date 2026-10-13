# Appnetica Hydra Launcher Source

[![Update Appnetica Source](https://github.com/kirgizmustafa17/appnetica-hydra-source/actions/workflows/update-source.yml/badge.svg)](https://github.com/kirgizmustafa17/appnetica-hydra-source/actions/workflows/update-source.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Appnetica (appnetica.com)](https://appnetica.com/) üzerindeki tüm oyunları ve doğrudan indirme bağlantılarını tarayarak [Hydra Launcher](https://hydralauncher.gg/) ile tam uyumlu JSON kaynağı sağlayan otomatik veri çıkarma ve yayınlama deposu.

---

## 🚀 Hydra Launcher'a Nasıl Eklenir?

Hydra Launcher'a eklemek için aşağıdaki bağlantılardan birini kullanabilirsiniz:

### 1. GitHub Pages Bağlantısı (Önerilen)
```text
https://kirgizmustafa17.github.io/appnetica-hydra-source/appnetica.json
```

### 2. Raw GitHub Bağlantısı
```text
https://raw.githubusercontent.com/kirgizmustafa17/appnetica-hydra-source/main/appnetica.json
```

### Adım Adım Kurulum:
1. **Hydra Launcher** uygulamasını açın.
2. Sol alttaki **Ayarlar (Settings)** dişli simgesine tıklayın.
3. **İndirme Kaynakları (Download Sources)** sekmesine gelin.
4. Kaynak URL alanına yukarıdaki bağlantılardan birini yapıştırıp **Ekle (Add)** butonuna basın.
5. Appnetica kataloğundaki tüm oyunlar arama ve indirme listenizde görünecektir.

---

## ⚙️ Nasıl Çalışır?

1. **Sitemap Keşfi (`games.xml`):**
   - `https://appnetica.com/games.xml` adresinden katalogdaki 5.000+ oyunun slug ve `lastmod` zaman damgası taranır.

2. **Artımlı Senkronizasyon (Incremental Cache):**
   - `.cache.json` dosyası aracılığıyla yalnızca `lastmod` değeri değişmiş veya yeni eklenmiş oyunlar taranır.
   - Bu sayede GitHub Actions çalıştırmaları 5-10 saniye gibi çok kısa sürelerde tamamlanır ve gereksiz ağ trafiği oluşturulmaz.

3. **Doğrudan İndirme Bağlantısı Çözümleme:**
   - Sitedeki yönlendirme sayfaları yerine oyunun `__data.json` nesnesi içinden doğrudan `cloud.mail.ru` veya ana sağlayıcı bağlantıları çıkartılarak Hydra'ya iletilir.
   - Doğrudan link bulunamadığında güvenli yedek olarak `https://appnetica.com/file/<id>?game=<game_id>` yönlendirme bağlantısı kullanılır.

4. **Çoklu Platform ve Dosya Ayrımı:**
   - Tek bir oyunda birden fazla indirme seçeneği varsa (ör. Windows, Linux, Bonus içerik):
     - `Oyun Adı` (Ana Windows kurulumu)
     - `Oyun Adı [Linux]` (Linux sürümü)
     - `Oyun Adı [Bonus]` (Soundtrack, Artbook, Ek içerikler)
     biçiminde bağımsız Hydra öğeleri olarak eklenir.

5. **GitHub Actions Otomasyonu:**
   - Her 6 saatte bir cron (`0 */6 * * *`) zamanlamasıyla otomatik çalışır.
   - Manuel tetikleme (`workflow_dispatch`) ile istenildiğinde tek tıkla çalıştırılabilir.
   - Değişiklikler otomatik olarak commitleyip GitHub Pages'e dağıtılır.

---

## 🛠️ Yerel Geliştirme ve Test

Projeyi yerel ortamınızda test etmek için:

```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Birim testleri çalıştırın
python -m pytest tests/

# Test amaçlı ilk 10 oyunu tarayın
python -m scraper.main --limit 10

# Tüm kataloğu tarayın
python -m scraper.main --concurrency 15
```

---

## 📄 Lisans
MIT License

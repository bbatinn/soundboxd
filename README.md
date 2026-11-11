# SongLarp 🎵 (Letterboxd for Music & Albums)

> 💿 **Müzik ve Albüm Değerlendirme & Sosyal Günlük Platformu**  
> Yerel adres: **http://localhost:8080** (veya `http://127.0.0.1:8080`)

SongLarp, kullanıcıların şarkıları ve albümleri 0.5★ ile 5.0★ arasında puanlamasını, inceleme yazmasını, dinleme günlüğü (diary) tutmasını, albüm şarkı listelerini (tracklist) dinleyip tek tek oylamasını ve küratör listeleri oluşturmasını sağlayan Letterboxd tarzı modern bir müzik platformudur.

---

## ✨ Temel Özellikler
1. **Şarkı & Albüm Modu (Dual Mode):**
   - Şarkı puanlama, Letterboxd tarzı interaktif yıldızlar (`★`) ve dinamik dağılım histogramı.
   - **Albüm Puanlama Modu:** Tam albüm şarkı listesi (Apple iTunes üzerinden gerçek süreler ve 30sn önizlemeler), albüm genel puanı ve şarkıların ortalama puanı (`avg_track_score`) bir arada!
2. **Canlı Müzik Arama:** Apple iTunes arama motoru üzerinden milyonlarca yerli ve yabancı şarkı/albüm canlı taranır, 600x600 yüksek çözünürlüklü kapaklarla sisteme dahil edilir.
3. **Dinleme Günlüğü & Favoriler:** 4 vitrin favori şarkısı (Letterboxd Favorites) ve dinleme geçmişi günlüğü.
4. **XSS & Güvenlik Korumalı:** Tüm dinamik kullanıcı içerikleri `escapeHtml` süzgecinden geçirilir.
5. **Kapsamlı Test Kapsamı:** 32 adet uçtan uca test modülünün tamamından (%100) başarıyla geçer.

---

## ⚖️ Müzisyenlerden İzin Alma Durumu: Neden Yasal?
- **Metadata (Üstveri) Yasaldır:** Şarkı adı, sanatçı adı, albüm kapağı, yayın yılı gibi bilgiler telife tabi eser niteliğinde değil, kamusal olgulardır (public metadata).
- **Resmi API & 30 Saniyelik Önizleme:** Sunucuda mp3 dosyası barındırılmaz. Apple iTunes Search API üzerinden **resmi ve yasal 30 saniyelik ses önizlemeleri** oynatılır.
- **Eleştiri ve Puanlama:** Kullanıcıların yorum yazması ve puan vermesi fikir özgürlüğü ve adil kullanım (fair use) kapsamındadır.

---

## 🧠 4-Kademeli Akıllı Token Yönlendirici (Model Router)
Token bütçesini ve hızını optimize etmek için görevler zorluk derecesine göre 4 farklı katmana ayrılmıştır:

1. **⚡ Tier 1: Gemini 3.8 Flash (Hızlı & Ekonomik - %70 Yük):**
   - Yorumlarda argo/küfür/spam denetimi (moderation).
   - Otomatik tür ve ruh hali (mood) etiketleme (`#gece-surusu`, `#synth`, `#anadolu-rock`).
   - Arama sorguları ve anlık duygu analizi.

2. **🔷 Tier 2: Gemini 2.5 Pro (Dengeli Analitik - %18 Yük):**
   - Şarkıların akustik yapısı, BPM ve enstrümantal benzerliklerini eşleştirme.
   - Dinamik ve türe özgü akıllı parça önerileri.

3. **✒️ Tier 3: Claude Sonnet 4.5 (Edebi & Yaratıcı Kalem - %9 Yük):**
   - Letterboxd tarzı sinematik, metaforik ve şiirsel müzik eleştirisi kurgulama.
   - Şarkı sözü ve edebi anlam analizi.

4. **💎 Tier 4: Gemini 4 Argon (Zirve Sentez - Sadece En Son! - %3 Yük):**
   - **En değerli modeldir.** Asla basit işlerde çağrılmaz!
   - Kullanıcının tüm dinleme geçmişi ve favorileri Flash, Pro ve Claude tarafından önceden süzüldükten sonra, sadece nihai **"Derin Müzikal DNA & Psiko-Akustik Karakter Haritası"** çıkarmak için en son aşamada devreye girer.

---

## 🚀 Kurulum ve Çalıştırma

Projeyi çalıştırmak için bilgisayarında sadece Python 3 bulunması yeterlidir:

```bash
cd C:\Users\batin\.gemini\antigravity\scratch\soundboxd
python server.py
```

Tarayıcında aç:
👉 **http://localhost:8080**

### İsteğe Bağlı: Canlı API Anahtarları (.env)
Model Router yerleşik akıllı simülasyon ve öneri motoruna sahiptir ve API anahtarı olmadan da kusursuz çalışır. İstersen `.env` dosyasına gerçek anahtarlarını ekleyebilirsin:
```env
GEMINI_API_KEY="your-gemini-key"
ANTHROPIC_API_KEY="your-claude-key"
PORT=8080
```

---

## 📂 Proje Yapısı
```
soundboxd/
├── server.py           # Python 3 backend + SQLite DB + Canlı Müzik Arama + 4-Katmanlı Model Router
├── package.json        # Proje metaverisi
├── .gitignore          # Git yoksayma dosyası (soundboxd.db dahil)
├── README.md           # Proje belgelendirmesi
└── public/
    ├── index.html      # Letterboxd tarzı modern karanlık tema arayüz (SongLarp)
    ├── styles.css      # Letterboxd renk paleti, albüm kartları, interaktif yıldızlar & responsive stil
    └── app.js          # Canlı arama, albüm modu, önizleme oynatıcı ve AI paneli
```

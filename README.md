# Soundboxd 🎵 (Letterboxd for Music)

> 🌐 **CANLI SİTEYE GİRİŞ:** [https://cuisine-mpg-ipaq-perspective.trycloudflare.com](https://cuisine-mpg-ipaq-perspective.trycloudflare.com)  
> *(Bilgisayarın açık olduğu sürece bu linkten herkes doğrudan siteyi kullanabilir!)*

Soundboxd, tıpkı Letterboxd'un sinema için yaptığı gibi, insanların müzikleri/şarkıları 0.5★ ile 5.0★ arasında puanlamasını, inceleme yazmasını, dinleme günlüğü (diary) tutmasını ve listeler oluşturmasını sağlayan tam teşekküllü bir müzik platformudur.

---

## ⚖️ Müzisyenlerden İzin Alma Durumu: Neden Yasal?
- **Metadata (Üstveri) Yasaldır:** Şarkı adı, sanatçı adı, albüm kapağı, yayın yılı gibi bilgiler telife tabi eser niteliğinde değil, kamusal olgulardır (public metadata).
- **Resmi API & 30 Saniyelik Önizleme:** Uygulamada şarkıların tam mp3 dosyaları sunucuda barındırılmaz. Apple iTunes Search API & Spotify Web API üzerinden **resmi ve yasal 30 saniyelik ses önizlemeleri** çalınır. Kullanıcılar ayrıca tam parçaya Spotify üzerinden tek tıkla ulaşabilir.
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
   - Tematik parça önerileri.

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
Model Router yerleşik akıllı simülasyon motoruna sahiptir ve API anahtarı olmadan da kusursuz çalışır. İstersen `.env` dosyasına gerçek anahtarlarını ekleyebilirsin:
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
├── soundboxd.db        # Yerel SQLite veritabanı (Şarkılar, İncelemeler, Puanlar, Token Logları)
├── package.json        # Proje metaverisi
├── .gitignore          # Git yoksayma dosyası
├── README.md           # Proje belgelendirmesi
└── public/
    ├── index.html      # Letterboxd tarzı modern karanlık tema arayüz
    ├── styles.css      # Letterboxd renk paleti (yeşil, turuncu, mavi) ve responsive tasarım
    └── app.js          # Canlı arama, yarım yıldız puanlayıcı, önizleme oynatıcı ve AI paneli
```

# Kararsızım — Proje Rehberi (CLAUDE.md)

> Bu dosya Claude Code için hazırlanmış proje rehberidir. Her oturumun başında oku.
> Proje **prototip** aşamasındadır: basit tut, aşırı karmaşık çözümlerden kaçın.
> Bir fazı bitirmeden sonrakine geçme. Her fazın sonunda çalıştığını doğrula ve commit at.

---

## 1. Proje Özeti

**Proje adı:** Kararsızım

**Amaç:** Kullanıcıların kararsız kaldıkları konularda diğer kullanıcılara danışabildiği bir anket platformu.
Örnek: "Bugün sinemaya mı gitsem, restorana mı?" sorusu için 2 ile 5 arası seçenek eklenir, diğer kullanıcılar oy verir.

**Temel kurallar**
- Takip (follow) mekanizması **yok**. Her kullanıcı platformdaki **her anketi** görür ve oylayabilir.
- **Üye olmayan ziyaretçiler** anketleri görüntüleyebilir ve oy verebilir.
- **Anket oluşturmak için üyelik zorunludur.**
- Kayıt alanları: **e-posta, parola, kullanıcı adı.**
- Anketlerde **kullanıcı adı görünür, e-posta asla görünmez** (şablonlarda, JSON cevaplarında, hiçbir yerde).
- Bir ankette en az **2**, en fazla **5** seçenek olur.

**Prototip dışı (şimdilik YAPMA):** takip sistemi, yorumlar, bildirimler, e-posta doğrulama, parola sıfırlama, moderasyon paneli, ödeme, çok dilli arayüz, REST framework, React/Vue gibi frontend framework'leri.

---

## 2. Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11+, Django (güncel kararlı sürüm) |
| Veritabanı | Supabase (PostgreSQL) — **sadece Postgres olarak** kullanılır |
| Frontend | Aynı repo içinde Django template + saf HTML, CSS, JavaScript (framework yok) |
| Deployment | Vercel (Python serverless) |
| Statik dosyalar | WhiteNoise |
| Ortam değişkenleri | `.env` (git'e eklenmez) + `dj-database-url` |

**Önemli mimari kararlar**
1. **Kimlik doğrulama Django'nun kendi auth sistemidir.** Supabase Auth KULLANILMAZ. Supabase yalnızca veritabanıdır; Django ORM ile bağlanılır.
2. **Oturumlar veritabanında tutulur** (`django.contrib.sessions`, DB backend). Vercel serverless olduğu için dosya tabanlı oturum kullanma.
3. **Frontend ayrı bir uygulama değildir.** Sayfalar Django template'leri ile üretilir; oy verme gibi etkileşimler için sade `fetch()` ile Django'ya JSON istekleri atılır.
4. Giriş **e-posta + parola** ile yapılır; **kullanıcı adı** herkese görünen isimdir.

---

## 3. Veri Modeli

### User (özel kullanıcı modeli: `AbstractUser`'dan türet, proje başında oluştur)
- `username` — benzersiz, herkese görünür (3-30 karakter, harf/rakam/alt çizgi)
- `email` — benzersiz, **gizli**, giriş için kullanılır (`USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = ["username"]`)
- `password` — Django hash'li saklar

> Özel kullanıcı modeli **ilk migration'dan önce** oluşturulmalıdır. Sonradan değiştirmek zordur.

### Poll
- `author` — FK → User
- `question` — en fazla 200 karakter (örn. "Bugün ne yapsam?")
- `description` — isteğe bağlı, en fazla 500 karakter
- `created_at`
- `is_active` — bool, varsayılan True (ileride kapatma/silme için)

### Option
- `poll` — FK → Poll (`related_name="options"`)
- `text` — en fazla 100 karakter
- `position` — sıralama (0'dan başlar)

### Vote
- `poll` — FK → Poll
- `option` — FK → Option
- `user` — FK → User, **null olabilir** (üye oyları için)
- `session_key` — metin, **null olabilir** (üye olmayan oyları için)
- `created_at`

**Kısıtlar**
- Bir kullanıcı bir ankete **tek oy** verebilir: `UniqueConstraint(poll, user)` (user null değilse, `condition` ile).
- Bir anonim ziyaretçi (oturum) bir ankete **tek oy** verebilir: `UniqueConstraint(poll, session_key)` (session_key null değilse).
- `option.poll == vote.poll` olmalıdır (view içinde doğrula).
- Üye değilken oy verilirse ve oturum yoksa önce `request.session.create()` ile oturum oluştur, `session_key` kullan.

**Bilinen sınırlama (prototip için kabul edildi):** Anonim oy tekilliği oturum çerezine bağlıdır. Çerezi silen kişi tekrar oy verebilir. İleride daha güçlü önlemler düşünülebilir; şimdi gerekli değil.

---

## 4. Sayfalar ve Akışlar

| URL | Sayfa | Erişim |
|---|---|---|
| `/` | Anket akışı (en yeni anketler, sayfalama: 10'ar) | Herkes |
| `/anket/<id>/` | Anket detay + oy verme + sonuçlar | Herkes |
| `/anket/yeni/` | Anket oluşturma formu | **Sadece giriş yapmış** (değilse giriş sayfasına yönlendir) |
| `/kayit/` | Üye ol (e-posta, kullanıcı adı, parola, parola tekrar) | Giriş yapmamış |
| `/giris/` | Giriş (e-posta + parola) | Giriş yapmamış |
| `/cikis/` | Çıkış (POST) | Giriş yapmış |
| `/kullanici/<username>/` | Kullanıcının oluşturduğu anketler (e-posta gösterme!) | Herkes |

**Oy verme ve sonuçlar**
- Oy `POST /anket/<id>/oy/` ile JSON olarak gönderilir (`option_id`), CSRF token dahil.
- Sonuçlar **oy verdikten sonra** gösterilir (her seçenek için oy sayısı ve yüzde, basit yatay çubuk).
- Bir kez verilen oy **değiştirilemez** (prototip).
- Kendi anketine de oy verilebilir.

**Anket oluşturma formu**
- Soru + isteğe bağlı açıklama.
- Başlangıçta 2 seçenek alanı; JavaScript ile "Seçenek ekle" butonu (en fazla 5), "Kaldır" butonu (en az 2'de dur).
- Sunucu tarafında da 2-5 kuralı doğrulanır (JS'e güvenme). Boş seçenekler atılır, sonra sayı kontrol edilir.
- Anketlerde **yazar kullanıcı adı** gösterilir.

**Arayüz dili:** Türkçe (tek dil). i18n kurma.

---

## 5. Klasör Yapısı (hedef)

```
kararsizim/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── vercel.json
├── manage.py
├── .env.example
├── .gitignore
├── config/                  # Django proje ayarları
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                # özel User modeli, kayıt/giriş/çıkış
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── polls/                   # Poll, Option, Vote
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── accounts/
│   └── polls/
└── static/
    ├── css/style.css
    └── js/
        ├── vote.js
        └── poll_form.js
```

---

## 6. Kod Kuralları

- Python: PEP 8, anlaşılır isimler, gereksiz soyutlama yok. Fonksiyon tabanlı view'ler tercih edilir.
- Model alanı ve kod isimleri İngilizce; kullanıcıya görünen metinler Türkçe.
- Her form ve JSON isteği **sunucu tarafında doğrulanır**.
- CSRF korumasını kapatma. `fetch` isteklerine `X-CSRFToken` başlığı ekle.
- Şablonlarda e-posta asla yazdırılmaz.
- N+1 sorgudan kaçın: `select_related("author")`, `prefetch_related("options")`.
- Oy sayıları için `annotate(Count(...))` kullan.
- Gizli bilgiler (SECRET_KEY, DB şifresi) kod içine yazılmaz, ortam değişkenlerinden okunur.
- CSS: tek dosya (`style.css`), mobil öncelikli, sade ve temiz. Renkler CSS değişkenleri ile tek yerde.
- JavaScript: ES6, framework ve build adımı yok. Her sayfa için küçük, ayrı dosyalar.
- Her fazın sonunda `python manage.py check` ve temel manuel test yap.

---

## 7. Ortam Değişkenleri (`.env.example`)

```
DJANGO_SECRET_KEY=degistir-beni
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
```

**Supabase bağlantı notları**
- Supabase panelinde *Project Settings → Database* bölümünden bağlantı bilgilerini al.
- Vercel serverless olduğu için **connection pooler** (transaction modu, genelde port 6543) adresini kullan. Doğrudan bağlantı, çok sayıda eş zamanlı fonksiyonda bağlantı limitine takılabilir.
- Transaction pooler kullanılırken Django ayarında `DISABLE_SERVER_SIDE_CURSORS = True` ve `CONN_MAX_AGE = 0` ayarla.
- Bağlantı detayları zamanla değişebilir; takıldığında güncel Supabase dokümanını kontrol et.

---

## 8. Vercel Deployment Notları

- Vercel, Django'yu serverless Python fonksiyonu olarak çalıştırır. `config/wsgi.py` içinde `app = application` tanımı bulunmalıdır.
- `vercel.json` ile tüm istekler WSGI uygulamasına yönlendirilir; statik dosyalar WhiteNoise ile sunulur (`STATIC_ROOT`, `collectstatic`).
- Build sırasında `collectstatic` çalıştırılmalıdır.
- `DJANGO_ALLOWED_HOSTS` içine `.vercel.app` ve ileride özel alan adı eklenir.
- Ortam değişkenleri Vercel panelinden eklenir.
- **Migration'lar Vercel üzerinde otomatik çalışmaz.** Migration'ları yerel makineden, Supabase veritabanına bağlanarak `python manage.py migrate` ile çalıştır.
- Vercel'in Python/Django yapılandırma biçimi değişebilir. Deployment fazında önce güncel Vercel dokümanını kontrol et.
- Üretimde `DEBUG=False`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` açılır; `CSRF_TRUSTED_ORIGINS` içine `https://*.vercel.app` eklenir.

---

## 9. Geliştirme Fazları

Her faz bağımsızdır. Bir faz bitmeden diğerine geçme. Her faz sonunda: çalıştır, test et, `git commit`.

### Faz 0 — Proje İskeleti
**Hedef:** Boş ama çalışan bir Django projesi.
- Sanal ortam, `requirements.txt` (django, psycopg[binary], dj-database-url, whitenoise).
- `config` projesi, `accounts` ve `polls` uygulamaları.
- `settings.py`: ortam değişkenlerinden ayar okuma, Supabase Postgres bağlantısı, WhiteNoise, `templates/` ve `static/`, `LANGUAGE_CODE = "tr"`, saat dilimi `Europe/Istanbul`.
- `.gitignore`, `.env.example`, kısa `README.md` (yerel çalıştırma adımları).
- `base.html` (üst menü: "Kararsızım" logosu, Giriş/Üye ol veya kullanıcı adı/Çıkış, "Anket oluştur" butonu) ve basit ana sayfa.
- **Bitiş kriteri:** `python manage.py runserver` ile ana sayfa açılıyor, veritabanına bağlanıyor.

### Faz 1 — Üyelik Sistemi
**Hedef:** Kayıt, giriş, çıkış.
- Özel `User` modeli (e-posta ile giriş, benzersiz kullanıcı adı) — **ilk migration'dan önce**.
- Kayıt formu, giriş formu, çıkış.
- Hata mesajları Türkçe ve anlaşılır (e-posta kullanımda, kullanıcı adı alınmış vb.).
- Django admin'de User yönetimi çalışır.
- **Bitiş kriteri:** Kayıt ol → çıkış yap → giriş yap akışı çalışıyor. Menüde kullanıcı adı görünüyor, e-posta hiçbir yerde görünmüyor.

### Faz 2 — Anket Modelleri ve Görüntüleme
**Hedef:** Anketleri listele ve detayını göster (henüz oy yok).
- `Poll`, `Option`, `Vote` modelleri ve migration'ları (kısıtlarla birlikte).
- Admin'den test anketi eklenebilir.
- Ana sayfa: anket kartları (soru, yazar kullanıcı adı, tarih, seçenek sayısı), sayfalama.
- Anket detay sayfası: soru, açıklama, seçenekler, yazar.
- **Bitiş kriteri:** Admin'den eklenen anketler giriş yapmadan listelenip açılabiliyor.

### Faz 3 — Oy Verme
**Hedef:** Üye ve üye olmayan herkes oy verebilsin.
- `POST /anket/<id>/oy/` JSON endpoint'i; üye için `user`, ziyaretçi için `session_key` ile kayıt.
- Tekrar oy engeli (kısıtlar + view'de kontrol, anlaşılır hata mesajı).
- `vote.js`: seçeneğe tıklayınca `fetch` ile oy gönder, sayfayı yenilemeden sonuçları (sayı + yüzde + çubuk) göster.
- Sayfa yeniden açıldığında kullanıcı daha önce oy verdiyse sonuçlar direkt görünür ve oyu işaretlidir.
- **Bitiş kriteri:** Giriş yapmadan oy verilebiliyor, aynı tarayıcıdan ikinci oy reddediliyor, üye olarak da tek oy verilebiliyor.

### Faz 4 — Anket Oluşturma
**Hedef:** Üyeler anket oluşturabilsin.
- `/anket/yeni/` formu, `login_required` (giriş sonrası forma geri dönülür).
- `poll_form.js`: seçenek ekle/kaldır (2-5 sınırı).
- Sunucu tarafı doğrulama (2-5 seçenek, boş seçenekleri ele, uzunluk sınırları, aynı metni tekrar ettirme).
- Oluşturma sonrası anket detay sayfasına yönlendirme.
- `/kullanici/<username>/` sayfası.
- Üye olmayan biri "Anket oluştur"a basarsa giriş/üye ol sayfasına yönlendirilir ve kısa bir bilgi mesajı görür.
- **Bitiş kriteri:** Üye anket oluşturuyor, başkası (veya ziyaretçi) oylayabiliyor.

### Faz 5 — Arayüz Cilası
**Hedef:** Prototip görünümünü düzgün hale getirmek.
- Mobil uyumlu, temiz ve modern tasarım; tutarlı renk paleti ve tipografi.
- Boş durum mesajları ("Henüz anket yok, ilkini sen oluştur!"), hata/başarı mesajları, 404 sayfası.
- Erişilebilirlik temelleri: etiketler, odak stilleri, yeterli kontrast.
- **Bitiş kriteri:** Telefon ve masaüstünde kullanılabilir, tutarlı görünüyor.

### Faz 6 — Vercel'e Yayınlama
**Hedef:** Canlı prototip.
- Güncel Vercel dokümanına göre `vercel.json` ve WSGI girişi.
- Üretim ayarları (`DEBUG=False`, güvenli çerezler, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS).
- Ortam değişkenlerini Vercel'e ekleme, `collectstatic`.
- Migration'ları yerelden Supabase'e uygulama.
- Canlıda tüm akışı test etme (kayıt, giriş, anket oluşturma, anonim oy, üye oyu).
- **Bitiş kriteri:** Canlı adreste tüm akışlar çalışıyor.

### Sonraki Fikirler (prototipten sonra, şimdi yapma)
E-posta doğrulama, parola sıfırlama, anket kapatma/silme, anketi düzenleme, kategori/etiket, arama, raporlama/moderasyon, anket bitiş tarihi, paylaşım linki, rate limiting, daha güçlü anonim oy tekilliği, otomatik testler.

---

## 10. Claude Code ile Çalışma Kuralları

- Bir faza başlamadan önce kısa bir plan çıkar ve onay iste; sonra uygula.
- Bir seferde sadece **tek faz** yap. Fazın dışına taşma.
- Yeni bağımlılık eklemeden önce gerekçeni söyle; mümkünse Django/standart kütüphane ile çöz.
- Belirsiz bir durumda sor. Varsayım yaparsan açıkça belirt.
- Her fazın sonunda: ne yapıldı, nasıl test edildi, nasıl çalıştırılır — kısa özet ver.
- Kullanıcıya ait gizli bilgileri (e-posta, parola) loglama, ekrana yazdırma, JSON'a koyma.

---

## 11. Sık Kullanılan Komutlar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py check
python manage.py collectstatic --noinput
```

---

## 12. Her Faz İçin Başlangıç Promptu (kopyala-yapıştır)

**Faz 0:**
> CLAUDE.md dosyasını oku. Sadece Faz 0'ı uygula: proje iskeletini, ayarları, base.html'i ve basit ana sayfayı hazırla. Başlamadan önce kısa planını yaz. Faz 1'e geçme.

**Faz 1:**
> CLAUDE.md'yi oku. Faz 0 tamamlandı. Sadece Faz 1'i uygula: özel User modeli (e-posta ile giriş), kayıt, giriş, çıkış. Bitirince nasıl test edeceğimi anlat.

**Faz 2:**
> CLAUDE.md'yi oku. Faz 1 tamamlandı. Sadece Faz 2'yi uygula: Poll, Option, Vote modelleri, admin kaydı, ana sayfa listesi ve anket detay sayfası. Oy verme henüz yok.

**Faz 3:**
> CLAUDE.md'yi oku. Faz 2 tamamlandı. Sadece Faz 3'ü uygula: üye ve üye olmayan kullanıcılar için oy verme, tekrar oy engeli ve vote.js ile sonuçların anlık gösterimi.

**Faz 4:**
> CLAUDE.md'yi oku. Faz 3 tamamlandı. Sadece Faz 4'ü uygula: anket oluşturma formu (2-5 seçenek, JS ile ekle/kaldır, sunucu doğrulaması) ve kullanıcı profil sayfası.

**Faz 5:**
> CLAUDE.md'yi oku. Faz 4 tamamlandı. Sadece Faz 5'i uygula: mobil uyumlu temiz arayüz, boş durum ve hata mesajları, 404 sayfası. İşlevselliği bozma.

**Faz 6:**
> CLAUDE.md'yi oku. Faz 5 tamamlandı. Sadece Faz 6'yı uygula: önce güncel Vercel Django dokümanını kontrol et, sonra deployment yapılandırmasını, üretim ayarlarını ve yayınlama adımlarını hazırla. Benim yapmam gereken manuel adımları madde madde yaz.

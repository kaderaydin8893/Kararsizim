# Kararsızım

Kullanıcıların kararsız kaldıkları konularda diğer kullanıcılara danışabildiği sade ve modern bir anket platformu.

## 🚀 Yerel Kurulum ve Çalıştırma

### 1. Sanal Ortamı Hazırlama ve Bağımlılıkları Yükleme

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ortam Değişkenleri

`.env.example` dosyasını `.env` olarak kopyalayın ve gerekirse Supabase bağlantınızı tanımlayın:

```bash
cp .env.example .env
```

> **Not:** `DATABASE_URL` tanımlanmazsa yerel geliştirmede otomatik olarak SQLite kullanılır. Supabase PostgreSQL bağlantısı için `DATABASE_URL` satırını aktif edebilirsiniz.

### 3. Veritabanı Migration'ları ve Süper Kullanıcı

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Geliştirme Sunucusunu Başlatma

```bash
python manage.py runserver
```

Tarayıcınızda [http://127.0.0.1:8000](http://127.0.0.1:8000) adresine gidin.

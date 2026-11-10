#!/bin/bash
set -e

echo "=== Kararsızım Vercel Build Başlıyor ==="

# 1️⃣ Sanal ortam (venv) oluştur
python -m venv .venv
source .venv/bin/activate

# 2️⃣ Bağımlılıkları kur (hata olursa göster)
echo "🔧 Bağımlılıklar kuruluyor..."
pip install --no-cache-dir -r requirements.txt || { echo "❌ pip kurulumu başarısız"; exit 1; }

# 3️⃣ Statik dosyaları toplama
echo "🧹 staticfiles klasörünü temizliyoruz..."
rm -rf staticfiles/*
echo "INFO  Collectstatic started"
python manage.py collectstatic --noinput --clear -v 2 || { echo "❌ collectstatic hatası"; exit 1; }
echo "INFO  Collectstatic finished – files written to staticfiles/"
# List the contents of staticfiles for debugging
echo "=== staticfiles içeriği (liste) ==="
find staticfiles -type f | sort


# 4️⃣ (Opsiyonel) Sanal ortamı kapat
deactivate

echo "=== Build Başarıyla Tamamlandı ==="

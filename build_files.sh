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
echo "📦 collectstatic çalıştırılıyor..."
python manage.py collectstatic --noinput --clear -v 2 || { echo "❌ collectstatic hatası"; exit 1; }

# 4️⃣ (Opsiyonel) Sanal ortamı kapat
deactivate

echo "=== Build Başarıyla Tamamlandı ==="

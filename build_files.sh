#!/bin/bash
set -e

echo "=== Kararsızım Vercel Build Başlıyor ==="

# Bağımlılıkları yükle
python3 -m pip install -r requirements.txt

# Statik dosyaları topla
python3 manage.py collectstatic --noinput --clear

echo "=== Build Başarıyla Tamamlandı ==="

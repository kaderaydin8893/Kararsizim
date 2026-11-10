#!/bin/bash
set -e

echo "=== Kararsızım Vercel Build Başlıyor ==="

# Create virtual environment in a temporary .venv directory
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies inside the venv
pip install --no-cache-dir -r requirements.txt

# Collect static files using the venv python
python manage.py collectstatic --noinput --clear

# Deactivate virtualenv (optional)
deactivate

echo "=== Build Başarıyla Tamamlandı ==="

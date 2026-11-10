"""
Django settings for Kararsizim project.
"""

import os
import sys
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-default-key-change-in-prod")

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.vercel.app")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Proje uygulamaları
    "accounts",
    "polls",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Supabase PostgreSQL (via DATABASE_URL) or local SQLite fallback
database_url = os.getenv("DATABASE_URL")
if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }
elif database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url,
            conn_max_age=0,
            conn_health_checks=True,
        )
    }
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.ManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },,
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth redirection URLs
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "polls:home"
LOGOUT_REDIRECT_URL = "polls:home"

# CSRF Trusted Origins (Vercel & Custom Domains)
CSRF_TRUSTED_ORIGINS = [
    "https://*.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
csrf_origins_env = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS")
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in csrf_origins_env.split(",") if origin.strip()])

# Production Security Settings (Enabled when DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

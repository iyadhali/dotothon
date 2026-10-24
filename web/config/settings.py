"""Django settings — deliberately minimal: no database, no auth, no sessions.

The app is a read-only view over CSVs produced by scripts/build_*.py, so there is no
ORM to configure and nothing to migrate. That also means `pip install django pandas`
is the whole install, which matters on venue wifi.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]   # repo root (web/config/settings.py -> ../..)

SECRET_KEY = "datathon-demo-key-not-a-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["django.contrib.staticfiles", "access"]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}

STATIC_URL = "static/"

USE_TZ = True
TIME_ZONE = "Indian/Maldives"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

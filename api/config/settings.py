import os
import tempfile
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEV_SECRET_KEY = "dev-insecure-key-only-for-local-development"

DEBUG = os.environ.get("DJANGO_DEBUG", "false") == "true"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", DEV_SECRET_KEY)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

CSRF_TRUSTED_ORIGINS = []
if os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"):
    CSRF_TRUSTED_ORIGINS = os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"].split(",")

if not DEBUG and SECRET_KEY == DEV_SECRET_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG is not true.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.user",
    "apps.faculties",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "common.middleware.ApiEnglishMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "postgres://seznamovak:seznamovak@localhost:5432/seznamovak"),
        conn_max_age=60,
    )
}

LANGUAGE_CODE = "cs"
TIME_ZONE = "Europe/Prague"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Static files are collected at container start and served by WhiteNoise
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Photos of the registered students are personal data, served only to staff
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "user.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.user.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "COERCE_DECIMAL_TO_STRING": False,
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
        "public": "300/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# HTTPS is terminated by a reverse proxy in front of the container
USE_HTTPS = os.environ.get("DJANGO_USE_HTTPS", "false") == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS

# JWT stored in httpOnly cookies
AUTH_COOKIE_ACCESS = "access_token"
AUTH_COOKIE_REFRESH = "refresh_token"
AUTH_COOKIE_SECURE = USE_HTTPS
AUTH_COOKIE_SAMESITE = "Lax"

# Public API is called from the static frontends on other domains
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/api/.*$"

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true") == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Seznamovák UTB <seznamovak@sutb.cz>")

# Host of the cancel link in the emails
SEZNAMOVAK_PUBLIC_URL = os.environ.get("SEZNAMOVAK_PUBLIC_URL", "https://seznamovak.utb.cz")

# Same limits as the public form
PHOTO_MAX_BYTES = 8 * 1024 * 1024
PHOTO_ALLOWED_FORMATS = ["JPEG", "PNG"]

# TTF font with Czech diacritics for the PDF list
PDF_FONT_PATH = os.environ.get("PDF_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

# Edition, prices and payment data of the camp, used in the emails and in the payment QR codes
SEZNAMOVAK_YEAR = int(os.environ.get("SEZNAMOVAK_YEAR", "2026"))
SEZNAMOVAK_EDITION = os.environ.get("SEZNAMOVAK_EDITION", "devátý")
SEZNAMOVAK_PRICE_TOTAL_CZK = int(os.environ.get("SEZNAMOVAK_PRICE_TOTAL_CZK", "3399"))
SEZNAMOVAK_PRICE_TOTAL_EUR = int(os.environ.get("SEZNAMOVAK_PRICE_TOTAL_EUR", "145"))
# The deposit is paid by bank transfer, the balance in cash on arrival
SEZNAMOVAK_DEPOSIT_CZK = int(os.environ.get("SEZNAMOVAK_DEPOSIT_CZK", "2399"))
SEZNAMOVAK_DEPOSIT_EUR = int(os.environ.get("SEZNAMOVAK_DEPOSIT_EUR", "102"))
SEZNAMOVAK_BALANCE_CZK = int(os.environ.get("SEZNAMOVAK_BALANCE_CZK", "1000"))
SEZNAMOVAK_PAYMENT_DEADLINE_DAYS = int(os.environ.get("SEZNAMOVAK_PAYMENT_DEADLINE_DAYS", "5"))
SEZNAMOVAK_ACCOUNT_CZK = os.environ.get("SEZNAMOVAK_ACCOUNT_CZK", "2301459738/2010")
SEZNAMOVAK_IBAN_CZK = os.environ.get("SEZNAMOVAK_IBAN_CZK", "CZ3720100000002301459738")
SEZNAMOVAK_ACCOUNT_EUR = os.environ.get("SEZNAMOVAK_ACCOUNT_EUR", "2501459740/2010")
SEZNAMOVAK_IBAN_EUR = os.environ.get("SEZNAMOVAK_IBAN_EUR", "CZ7120100000002501459740")
SEZNAMOVAK_VARIABLE_SYMBOL = os.environ.get("SEZNAMOVAK_VARIABLE_SYMBOL", "2026767")

# Newsletter contacts go to Brevo only when the API key is set
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "3"))
BREVO_TIMEOUT_SECONDS = 10

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "apps": {"handlers": ["console"], "level": "INFO"},
    },
}

# Throttle counters are shared by all gunicorn workers of the container through the filesystem
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": Path(tempfile.gettempdir()) / "django_cache",
    }
}

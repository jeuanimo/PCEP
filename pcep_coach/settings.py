"""
Django settings for pcep_coach project — PCEP Prep Coach.

Uses SQLite for development; swap ENGINE to postgresql for production.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv_file(path: Path) -> None:
    """Load key=value pairs from a local .env file into os.environ."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        # Remove simple surrounding quotes if present.
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv_file(BASE_DIR / ".env")


def _csv_env(name: str, default: str = "") -> list[str]:
    """Return a comma-separated env var as a cleaned list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# In production, set DJANGO_SECRET_KEY env var and DEBUG=False
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-change-me-in-production"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required in production"
        )

ALLOWED_HOSTS = _csv_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = _csv_env("DJANGO_CSRF_TRUSTED_ORIGINS", "")

# ── Apps ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third-party
    "django_ratelimit",
    # Project apps
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    "learning.apps.LearningConfig",
    "quizzes.apps.QuizzesConfig",
    "labs.apps.LabsConfig",
    "progress.apps.ProgressConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # must be directly after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pcep_coach.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "pcep_coach.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────
# Development: SQLite (default).
# Production:  set DATABASE_URL=postgres://user:pass@host/dbname
#              dj-database-url parses it and sets CONN_MAX_AGE automatically.
_DATABASE_URL = os.environ.get("DATABASE_URL")
if _DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=_DATABASE_URL,
            conn_max_age=600,          # keep connections alive for 10 min
            conn_health_checks=True,   # drop stale connections before reuse
            engine="django.db.backends.postgresql",
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Auth ──────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "progress:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# ── Internationalization ──────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ──────────────────────────────────────────────────────
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Whitenoise serves static files efficiently in production.
# Run `python manage.py collectstatic` before deploying.
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Cache ─────────────────────────────────────────────────────────────
# Development: per-process in-memory cache (zero config).
# Production:  set REDIS_URL=redis://localhost:6379/0
#              Install django-redis: pip install django-redis
_REDIS_URL = os.environ.get("REDIS_URL")
if _REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "KEY_PREFIX": "pcep",
            "TIMEOUT": 300,   # 5 minutes default
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "pcep-default",
        }
    }

# django-ratelimit uses the cache backend; ensure it's the default
RATELIMIT_USE_CACHE = "default"
# In dev, LocMemCache is not a "shared" cache so ratelimit raises E003.
# Fail open (don't block requests) rather than crashing; in production
# Redis satisfies the requirement and this flag can be removed.
RATELIMIT_FAIL_OPEN = not _REDIS_URL
# Silence the cache-backend check in dev (Redis isn't required locally)
if not _REDIS_URL:
    SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]

# ── Security (production hardening) ──────────────────────────────────
# All SECURE_* settings are no-ops in dev (DEBUG=True) but active when
# DEBUG=False.  Set DJANGO_HTTPS=true in the production environment.
_HTTPS = os.environ.get("DJANGO_HTTPS", "false").lower() in ("true", "1", "yes")

SECURE_SSL_REDIRECT = _HTTPS
SESSION_COOKIE_SECURE = _HTTPS
CSRF_COOKIE_SECURE = _HTTPS
if _HTTPS:
    # Render terminates TLS at the proxy and forwards the original scheme.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000 if _HTTPS else 0      # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = _HTTPS
SECURE_HSTS_PRELOAD = _HTTPS
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"                             # already default; explicit here

# ── Email (SMTP) ─────────────────────────────────────────────────────
# Defaults are set for Gmail SMTP, override with env vars as needed.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in (
    "true",
    "1",
    "yes",
)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@localhost")

# Content Security Policy (basic; tighten nonce-based script-src in production)
# Set per-request via the CSPMiddleware below, or configure django-csp if installed.
_CSP_SELF = "'self'"
_CSP_CDN = "cdn.jsdelivr.net"
CSP_DEFAULT_SRC = (_CSP_SELF,)
CSP_SCRIPT_SRC = (_CSP_SELF, "'unsafe-inline'", _CSP_CDN)
CSP_STYLE_SRC = (_CSP_SELF, "'unsafe-inline'", _CSP_CDN)
CSP_FONT_SRC = (_CSP_SELF, _CSP_CDN)
CSP_IMG_SRC = (_CSP_SELF, "data:")

# ── PCEP exam domain weights (used by smart practice engine) ─────────
PCEP_DOMAIN_WEIGHTS = {
    1: 0.18,  # Computer Programming and Python Fundamentals
    2: 0.29,  # Control Flow
    3: 0.25,  # Data Collections
    4: 0.28,  # Functions and Exceptions
}

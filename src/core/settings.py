import os  # noqa
from pathlib import Path  # type:ignore

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv, find_dotenv

from core.config.apps import THIRD_PARTY_APPS, DEFAULT_APPS, PROJECT_APPS

load_dotenv(find_dotenv(".env"))

from core.config import *  # noqa

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str) -> list[str]:
    val = os.getenv(name)
    if not val:
        return []
    return [part.strip() for part in val.split(",") if part.strip()]


def env_or_secret(name: str, default: str = "") -> str:
    """Read from env var first, fall back to Docker secret file at /run/secrets/."""
    val = os.getenv(name)
    if val:
        return val
    secret_path = f"/run/secrets/{name.lower()}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return default


SECRET_KEY: str = env_or_secret("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

DEBUG: bool = env_bool("DEBUG", False)

ALLOWED_HOSTS: list[str] = [
    "127.0.0.1",
    "localhost",
] + env_list("EXTRA_ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS: list[str] = [
    "http://127.0.0.1",
    "http://localhost",
] + env_list("EXTRA_CSRF_ORIGINS")

INSTALLED_APPS = [*THIRD_PARTY_APPS, *DEFAULT_APPS, *PROJECT_APPS]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",  # always first
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware должен быть рано
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.shared.middlewares.prometheus.MetricsMiddleware",  # custom middleware
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",  # always last
]

CSRF_HEADER_NAME = "HTTP_X_SESSION_TOKEN"
CSRF_FIELD_NAME = "session_token"
SESSION_COOKIE_NAME = "sid"

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "assets/templates")],
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

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": env_or_secret("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_BOUNCER_HOST", os.getenv("POSTGRES_HOST")),
        "PORT": os.getenv("POSTGRES_BOUNCER_PORT", os.getenv("POSTGRES_PORT")),
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}

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

LANGUAGE_CODE = "ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LANGUAGES = (
    ("ru", _("Russia")),
    ("en", _("English")),
    ("kg", _("Kyrgyzstan")),
)

LOCALE_PATHS = [os.path.join(BASE_DIR, "assets/locale")]

MODELTRANSLATION_LANGUAGES = ("ru", "en", "kg")

MODELTRANSLATION_DEFAULT_LANGUAGE = "ru"

STATIC_URL = "/static/"
STATICFILES_DIRS = [str(BASE_DIR.joinpath("assets/static"))]
STATIC_ROOT = str(BASE_DIR.joinpath("assets/staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR.joinpath("assets/media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

############################################
# CORS CONFIGURATION
############################################
# Использование конкретного списка origins вместо CORS_ALLOW_ALL_ORIGINS для безопасности
CORS_ALLOWED_ORIGINS: list[str] = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
] + env_list("EXTRA_CORS_ORIGINS")

# Разрешить отправку cookies и учетных данных
CORS_ALLOW_CREDENTIALS = True

# Разрешенные HTTP методы
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Разрешенные заголовки в запросах
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-api-secret-key",  # Для внешних API запросов
    "x-csrftoken",
    "x-requested-with",
    "x-session-token",  # Используется в вашем проекте для CSRF
]

# Заголовки, которые будут доступны клиенту в ответе
CORS_EXPOSE_HEADERS = [
    "content-type",
    "x-api-secret-key",
    "x-csrftoken",
    "x-session-token",
]

# Кеширование preflight запросов (в секундах)
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 часа

LOCALE_MIDDLEWARE_EXCLUDED_PATHS = ["/media/", "/static/"]

AUTH_USER_MODEL = "users.User"

X_FRAME_OPTIONS = "SAMEORIGIN"

############################################
# SECURITY SETTINGS (Production)
############################################
if not DEBUG:
    # HTTPS settings
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    # Content security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"

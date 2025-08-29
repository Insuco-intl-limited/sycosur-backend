from .common import *

DEBUG = False

SITE_NAME = getenv("SITE_NAME")

SECRET_KEY = getenv(
    "DJANGO_SECRET_KEY", "UUc-qwrxzkZFyx4mrxXFfgHpA1VLOIuAojmk8T9q7n35A6-k-yM"
)
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in the environment.")

CSRF_TRUSTED_ORIGINS = ["https://api.insuco.net", "https://sycosur.insuco.net"]

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "api.insuco.net"]

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://sycosur.insuco.net",
]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Important si derrière un proxy

ADMIN_URL = getenv("DJANGO_ADMIN_URL")
EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
EMAIL_HOST = getenv("EMAIL_HOST")
EMAIL_PORT = getenv("EMAIL_PORT")
DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")
DOMAIN = getenv("DOMAIN")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {  # Envoi des erreurs par email aux administrateurs
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {  # Logging dans la console
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {  # Gestion des erreurs de requêtes
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {  # Gestion des tentatives d'accès non autorisées
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
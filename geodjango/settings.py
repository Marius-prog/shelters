
import os
import sys
import logging
from pathlib import Path
import dj_database_url
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (no-op in production where vars are set in the platform env)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# GDAL/GEOS library paths for macOS (Homebrew)
if sys.platform == 'darwin':  # macOS
    import glob
    # Try to find GDAL library
    gdal_paths = glob.glob('/opt/homebrew/Cellar/gdal/*/lib/libgdal.*.dylib')
    if gdal_paths:
        GDAL_LIBRARY_PATH = gdal_paths[0]
    # Try to find GEOS library
    geos_paths = glob.glob('/opt/homebrew/Cellar/geos/*/lib/libgeos_c.*.dylib')
    if geos_paths:
        GEOS_LIBRARY_PATH = geos_paths[0]
    # Try to find SpatiaLite extension
    spatialite_paths = (
        glob.glob('/opt/homebrew/lib/mod_spatialite.dylib')
        + glob.glob('/opt/homebrew/Cellar/libspatialite/*/lib/mod_spatialite.dylib')
    )
    if spatialite_paths:
        SPATIALITE_LIBRARY_PATH = spatialite_paths[0]

# Setup logging with better configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'geodjango': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

logger = logging.getLogger(__name__)
# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY') or get_random_secret_key()
if not os.environ.get('DJANGO_SECRET_KEY') and not os.environ.get('SECRET_KEY'):
    logger.warning("No SECRET_KEY environment variable set, using random key. Set DJANGO_SECRET_KEY for production.")

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')

# Environment detection
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production' or not DEBUG

# Security settings - enable only in production
if not DEBUG:
    # SSL/HTTPS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_AGE = 1800  # 30 minutes (was 31449600 - 8736 hours)

    # CSRF security
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_AGE = 1800  # 30 minutes

    # Content Security Policy
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com", "https://cdn.jsdelivr.net", "https://maps.googleapis.com", "https://www.googletagmanager.com", "https://www.google-analytics.com", "https://app.rybbit.io")
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com")
    CSP_IMG_SRC = ("'self'", "data:", "https:", "blob:")
    CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:")
    CSP_CONNECT_SRC = ("'self'", "https://api.airplanes.live", "https://globe.airplanes.live", "https://maps.googleapis.com", "https://*.google-analytics.com", "https://*.analytics.google.com", "https://*.googletagmanager.com", "https://app.rybbit.io", "https://nominatim.openstreetmap.org", "https://api.planespotters.net")
    CSP_FRAME_SRC = ("'self'", "https://www.google.com")

else:
    # Development settings (SSL disabled)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_PRELOAD = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SESSION_COOKIE_HTTPONLY = True  # Enable even in dev
    CSRF_COOKIE_HTTPONLY = True  # Enable even in dev
    SESSION_COOKIE_AGE = 1800  # 30 minutes
    CSRF_COOKIE_AGE = 1800  # 30 minutes

# Allowed hosts configuration
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']

# CSRF trusted origins for Heroku and other deployments
CSRF_TRUSTED_ORIGINS = [
    'https://*.herokuapp.com',
    'https://*.heroku.com',
    'https://*.render.com',
]

# Add custom domains from environment
if os.environ.get('CUSTOM_DOMAINS'):
    custom_domains = os.environ.get('CUSTOM_DOMAINS').split(',')
    CSRF_TRUSTED_ORIGINS.extend([f'https://{domain.strip()}' for domain in custom_domains])

# Sentry configuration for error tracking
if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
            ),
            sentry_logging,
        ],
        traces_sample_rate=0.1 if IS_PRODUCTION else 1.0,
        send_default_pii=False,
        environment=ENVIRONMENT,
        release=os.environ.get('HEROKU_RELEASE_VERSION', 'unknown'),
    )


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.gis',
    'shelter',
]

# Add production apps
if IS_PRODUCTION:
    INSTALLED_APPS.extend([
        'health_check',
        'health_check.db',
        'health_check.cache',
        'health_check.storage',
    ])

# Add development apps
if DEBUG:
    INSTALLED_APPS.extend([
        'django_extensions',
    ])

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'geodjango.custom_whitenoise.SecurityWhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'geodjango.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'geodjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shelter.context_processors.google_maps_api_key',
            ],
        },
    },
]

WSGI_APPLICATION = 'geodjango.wsgi.application'

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Use dj-database-url for database configuration
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # For container deployment, use PostGIS
    if 'postgres' in DATABASES['default']['ENGINE']:
        DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
else:
    # Local development with SpatiaLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add MIME type headers
WHITENOISE_MIMETYPES = {
    '.css': 'text/css',
    '.js': 'application/javascript',
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


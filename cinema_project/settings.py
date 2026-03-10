"""
Django settings for cinema_project project.
Online Cinema Ticket Sales and Screening Management Platform
"""

from pathlib import Path
from decouple import config, Csv
import os


BASE_DIR = Path(__file__).resolve().parent.parent





SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-CHANGE-ME-IN-PRODUCTION')


DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_jinja',
    'django_extensions',
    
    
    'accounts',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.BruteForceProtectionMiddleware',
]

ROOT_URLCONF = 'cinema_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'match_extension': '.jinja2',
            'app_dirname': 'jinja2',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cinema_project.wsgi.application'




DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DB_NAME', default='Jegymester'),
        'USER': config('DB_USER', default='avnadmin'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='mysql-394960a1-sanya2004adam-bfe6.b.aivencloud.com'),
        'PORT': config('DB_PORT', default='21964'),
        'CONN_MAX_AGE': 600,          
        'CONN_HEALTH_CHECKS': True,    
        'OPTIONS': {
            'ssl': {'ssl-mode': 'REQUIRED'},
            'charset': 'utf8mb4',
        },
    }
}




AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'max_similarity': 0.7,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]




SESSION_COOKIE_HTTPONLY = True          
SESSION_COOKIE_SECURE = not DEBUG     
SESSION_COOKIE_SAMESITE = 'Lax'       
SESSION_COOKIE_AGE = 86400             
SESSION_EXPIRE_AT_BROWSER_CLOSE = False 
SESSION_SAVE_EVERY_REQUEST = True     




CSRF_COOKIE_HTTPONLY = True             
CSRF_COOKIE_SECURE = not DEBUG        
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = True               
CSRF_FAILURE_VIEW = 'core.views.csrf_failure'




SECURE_BROWSER_XSS_FILTER = True    
SECURE_CONTENT_TYPE_NOSNIFF = True   
X_FRAME_OPTIONS = 'DENY'              
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'


if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000    
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')




FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100             




LANGUAGE_CODE = 'hu-hu'

TIME_ZONE = 'Europe/Budapest'

USE_I18N = True

USE_TZ = True




STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'




DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_PREVENT_ENUMERATION = False
ACCOUNT_ADAPTER = 'accounts.adapter.CustomAccountAdapter'
ACCOUNT_SIGNUP_REDIRECT_URL = '/'
ACCOUNT_RATE_LIMITS = {
    'login_failed': '10/300s',   
}

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'account_login'




CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'




EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{asctime}] SECURITY {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',
            'formatter': 'security',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'core.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

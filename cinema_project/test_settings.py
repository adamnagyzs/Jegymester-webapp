"""
Test settings - uses SQLite in memory for fast test execution.
"""
from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


MIDDLEWARE = [m for m in MIDDLEWARE if 'BruteForce' not in m]


MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}


LOGGING = {}

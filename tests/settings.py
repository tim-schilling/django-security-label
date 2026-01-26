from __future__ import annotations

import os

SECRET_KEY = "hunter2"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "django-security-label"),
        "USER": os.environ.get("DB_USER", "django-security-label"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "django-security-label"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        # Set the default to a non-specific postgres port since we need to install
        # the anon provider
        "PORT": os.environ.get("DB_PORT", "6432"),
    },
}

TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "tests.testapp",
    "django_security_label",
    "django.contrib.auth",
    # Force django_migrations creation by having an app with migrations:
    "django.contrib.contenttypes",
]

USE_TZ = True

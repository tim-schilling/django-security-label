from __future__ import annotations

SECRET_KEY = "hunter2"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}

TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "tests.testapp",
    "django_security_label",
    # Force django_migrations creation by having an app with migrations:
    "django.contrib.contenttypes",
]

USE_TZ = True
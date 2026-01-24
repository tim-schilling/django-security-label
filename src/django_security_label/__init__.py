import os

# Support suffixing the version with a dev segment.
# This allows for building dev distributions to test
# the release process.
# See .github/workflows/test_release.yml
__version__ = VERSION = "1.2.0" + os.environ.get("DSL_VERSION_DEV", "")

default_app_config = "django_security_label.apps.DjangoSecurityLabelConfig"

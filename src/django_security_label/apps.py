from __future__ import annotations

from django.apps import AppConfig
from django.db import connections
from django.db.models.signals import pre_migrate
from django.dispatch import receiver

from django_security_label.labels import ColumnSecurityLabel
from django_security_label.operations import CreateSecurityLabelForRole


def _collect_security_label_providers(apps, plan):
    """
    Look through the loaded Django apps for models using
    `ColumnSecurityLabel` and throughout the plan being migrated for any
    possible security label providers.
    """
    providers = set()

    for model in apps.get_models():
        for index in model._meta.indexes:
            if isinstance(index, ColumnSecurityLabel):
                providers.add(index.provider)

    for migration, _ in plan:
        for operation in migration.operations:
            if isinstance(operation, CreateSecurityLabelForRole):
                providers.add(operation.provider)

    return providers


@receiver(pre_migrate, dispatch_uid="django_security_label.configure_pganon")
def configure_pganon(using, app_config, plan, **kwargs):
    """
        Configure PostgreSQL Anonymizer within the database.

    Some of these operations need a new connection after being set.
    Specifically anon.init and setting masking policies.

    Custom masking policies beyond the default `anon` will be used
    in the `migrate` command flow. We can't disconnect and reconnect since
    the migration operations may be occurring within a transaction. This
    means the best place to run this is before migrate runs. By using
    the `pre_migrate` signal, we avoid requiring the developer to manage
    this themselves. Unfortunately, this means some masking policies may
    be left stranded if not cleaned up manually.
    """
    db_name = using
    connection = connections[db_name]
    db_name = connection.settings_dict["NAME"]
    quote_name = connection.ops.quote_name
    providers = _collect_security_label_providers(app_config.apps, plan)
    with connection.cursor() as cursor:
        cursor.execute(
            f"ALTER DATABASE {quote_name(db_name)} SET session_preload_libraries = 'anon';"
        )
        cursor.execute("CREATE EXTENSION IF NOT EXISTS anon;")
        if providers:
            policies = ", ".join(sorted(providers))
            cursor.execute(
                f"ALTER DATABASE {quote_name(db_name)} SET anon.masking_policies TO '{policies}';"
            )
        cursor.execute("SELECT anon.init();")
    connection.close()
    connection.ensure_connection()


class DjangoSecurityLabelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_security_label"
    verbose_name = "Django Security Label"

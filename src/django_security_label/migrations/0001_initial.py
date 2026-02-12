from __future__ import annotations

from django.db import migrations

from django_security_label import constants
from django_security_label.operations import CreateRole, CreateSecurityLabelForRole


def set_dynamic_masking(apps, schema_editor):
    db_name = schema_editor.connection.settings_dict["NAME"]
    schema_editor.execute(
        f"ALTER DATABASE {schema_editor.quote_name(db_name)} SET anon.transparent_dynamic_masking TO true;"
    )


def preload_anon(apps, schema_editor):
    db_name = schema_editor.connection.settings_dict["NAME"]
    schema_editor.execute(
        f"ALTER DATABASE {schema_editor.quote_name(db_name)} SET session_preload_libraries = 'anon';"
    )


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.RunPython(set_dynamic_masking, migrations.RunPython.noop),
        CreateRole(constants.MASKED_READER_ROLE, inherit_from_db_user=True),
        CreateSecurityLabelForRole(
            provider="anon", role=constants.MASKED_READER_ROLE, string_literal="MASKED"
        ),
    ]

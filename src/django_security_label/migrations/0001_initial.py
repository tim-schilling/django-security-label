from __future__ import annotations

from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


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


def grant_permissions(apps, schema_editor):
    user = schema_editor.connection.settings_dict["USER"]
    schema_editor.execute(
        f"GRANT {schema_editor.quote_name(user)} to dsl_masked_reader WITH INHERIT TRUE"
    )


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.RunPython(preload_anon, migrations.RunPython.noop),
        CreateExtension("anon"),
        migrations.RunSQL("SELECT anon.init();", reverse_sql=migrations.RunSQL.noop),
        migrations.RunPython(set_dynamic_masking, migrations.RunPython.noop),
        migrations.RunSQL(
            """
            DROP ROLE IF EXISTS dsl_masked_reader;
            CREATE ROLE dsl_masked_reader LOGIN;
            SECURITY LABEL FOR anon ON ROLE dsl_masked_reader IS 'MASKED';
            """,
            """
            SECURITY LABEL FOR anon ON ROLE dsl_masked_reader IS NULL;
            DROP ROLE dsl_masked_reader;
            """,
        ),
        migrations.RunPython(grant_permissions, migrations.RunPython.noop),
    ]

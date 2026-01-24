from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


def set_dynamic_masking(apps, schema_editor):
    db_name = schema_editor.connection.settings_dict["NAME"]
    schema_editor.execute("ALTER DATABASE %(db_name)s SET anon.transparent_dynamic_masking TO true;" % {"db_name": schema_editor.quote_name(db_name)})


def preload_anon(apps, schema_editor):
    db_name = schema_editor.connection.settings_dict["NAME"]
    schema_editor.execute("ALTER DATABASE %(db_name)s SET session_preload_libraries = 'anon';" % {"db_name": schema_editor.quote_name(db_name)})


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
            GRANT pg_read_all_data to dsl_masked_reader;
            """,
            """
            SECURITY LABEL FOR anon ON ROLE dsl_masked_reader IS NULL;
            DROP ROLE dsl_masked_reader;
            """
        )
    ]

from __future__ import annotations

from functools import partial
from textwrap import dedent

from django.test import TestCase

from tests.compat import EnterContextMixin
from tests.utils import run_command, temp_migrations_module


class MakeMigrationsTests(EnterContextMixin, TestCase):
    def setUp(self):
        self.migrations_dir = self.enterContext(temp_migrations_module())

    call_command = staticmethod(partial(run_command, "makemigrations"))

    def test_dry_run(self):
        out, err, returncode = self.call_command("--dry-run", "testapp")

        assert returncode == 0
        assert not (self.migrations_dir / "max_migration.txt").exists()

    def test_creates_migration_with_security_labels(self):
        out, err, returncode = self.call_command("testapp")

        assert returncode == 0

        migration_files = list(self.migrations_dir.glob("*.py"))
        assert len(migration_files) == 2

        migration_file = next(
            f for f in migration_files if f.name != "__init__.py"
        )
        migration_content = migration_file.read_text()

        assert (
            "django_security_label.labels.AnonMaskSecurityLabel(fields=['text'], mask_function=django_security_label.labels.MaskFunction['dummy_catchphrase'], name='testapp_mas_text_6adba0_idx', provider='anon', string_literal='MASKED WITH FUNCTION anon.dummy_catchphrase()')"
        ) in migration_content
        assert (
            "django_security_label.labels.AnonMaskSecurityLabel(fields=['uuid'], mask_function=django_security_label.labels.MaskFunction['dummy_uuidv4'], name='testapp_mas_uuid_18a3e6_idx', provider='anon', string_literal='MASKED WITH FUNCTION anon.dummy_uuidv4()')"
        ) in migration_content
        assert (
            "django_security_label.labels.ColumnSecurityLabel(fields=['confidential'], name='testapp_mas_confide_030817_idx', provider='anon', string_literal='MASKED WITH VALUE $$CONFIDENTIAL$$')"
        ) in migration_content
        assert (
            "django_security_label.labels.ColumnSecurityLabel(fields=['random_int'], name='testapp_mas_random__45b12e_idx', provider='anon', string_literal='MASKED WITH FUNCTION anon.random_int_between(0,50)')"
        ) in migration_content


class MakeMigrationsRemovalTests(EnterContextMixin, TestCase):
    def setUp(self):
        self.migrations_dir = self.enterContext(temp_migrations_module())
        (self.migrations_dir / "__init__.py").write_text("")
        (self.migrations_dir / "0001_initial.py").write_text(dedent("""\
            from django.db import migrations, models
            import django_security_label.labels

            class Migration(migrations.Migration):
                initial = True
                dependencies = []
                operations = [
                    migrations.CreateModel(
                        name="MaskedColumn",
                        fields=[
                            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                            ("text", models.TextField()),
                            ("uuid", models.UUIDField()),
                            ("safe_text", models.TextField()),
                            ("safe_uuid", models.UUIDField()),
                            ("confidential", models.TextField()),
                            ("random_int", models.IntegerField()),
                        ],
                    ),
                    migrations.AddIndex(
                        model_name="maskedcolumn",
                        index=django_security_label.labels.AnonMaskSecurityLabel(fields=["safe_text"], mask_function="dummy_catchphrase()", name="maskedcolumn_safe_text_idx"),
                    ),
                    migrations.AddIndex(
                        model_name="maskedcolumn",
                        index=django_security_label.labels.AnonMaskSecurityLabel(fields=["text"], mask_function="dummy_catchphrase()", name="maskedcolumn_text_idx"),
                    ),
                    migrations.AddIndex(
                        model_name="maskedcolumn",
                        index=django_security_label.labels.AnonMaskSecurityLabel(fields=["uuid"], mask_function="dummy_uuidv4()", name="maskedcolumn_uuid_idx"),
                    ),
                    migrations.AddIndex(
                        model_name="maskedcolumn",
                        index=django_security_label.labels.ColumnSecurityLabel(fields=["confidential"], provider="anon", string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$", name="maskedcolumn_confidential_idx"),
                    ),
                    migrations.AddIndex(
                        model_name="maskedcolumn",
                        index=django_security_label.labels.ColumnSecurityLabel(fields=["random_int"], provider="anon", string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)", name="maskedcolumn_random_int_idx"),
                    ),
                ]
        """))

    call_command = staticmethod(partial(run_command, "makemigrations"))

    def test_creates_migration_removing_security_labels(self):
        out, err, returncode = self.call_command("testapp")

        assert returncode == 0

        migration_files = list(self.migrations_dir.glob("*.py"))
        migration_file = next(
            f for f in migration_files if f.name not in ("__init__.py", "0001_initial.py")
        )

        migration_content = migration_file.read_text()
        assert (
            'migrations.RemoveIndex(\n'
            '            model_name=\'maskedcolumn\',\n'
            '            name=\'maskedcolumn_safe_text_idx\',\n'
            '        )'
        ) in migration_content

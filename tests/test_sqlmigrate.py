from __future__ import annotations

from functools import partial
from textwrap import dedent

from django.test import TestCase

from tests.compat import EnterContextMixin
from tests.utils import run_command, temp_migrations_module


class SqlMigrateTests(EnterContextMixin, TestCase):
    def setUp(self):
        self.migrations_dir = self.enterContext(temp_migrations_module())
        (self.migrations_dir / "__init__.py").write_text("")
        (self.migrations_dir / "0001_initial.py").write_text(
            dedent("""\
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
        """)
        )

    call_command = staticmethod(partial(run_command, "sqlmigrate"))

    def test_forward_migration(self):
        out, err, returncode = self.call_command("testapp", "0001")

        self.assertEqual(returncode, 0)
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."text" '
            "IS 'MASKED WITH FUNCTION anon.dummy_catchphrase()'",
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."uuid" '
            "IS 'MASKED WITH FUNCTION anon.dummy_uuidv4()'",
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."confidential" '
            "IS 'MASKED WITH VALUE $$CONFIDENTIAL$$'",
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."random_int" '
            "IS 'MASKED WITH FUNCTION anon.random_int_between(0,50)'",
            out,
        )

    def test_backward_migration(self):
        out, err, returncode = self.call_command("testapp", "0001", "--backwards")

        self.assertEqual(returncode, 0)
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."text" IS NULL',
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."uuid" IS NULL',
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."confidential" IS NULL',
            out,
        )
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."random_int" IS NULL',
            out,
        )


class SqlMigrateRemovalTests(EnterContextMixin, TestCase):
    def setUp(self):
        self.migrations_dir = self.enterContext(temp_migrations_module())
        (self.migrations_dir / "__init__.py").write_text("")
        (self.migrations_dir / "0001_initial.py").write_text(
            dedent("""\
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
                        index=django_security_label.labels.AnonMaskSecurityLabel(fields=["safe_text"], mask_function="dummy_name()", name="maskedcolumn_safe_text_idx"),
                    ),
                ]
        """)
        )
        (self.migrations_dir / "0002_remove_label.py").write_text(
            dedent("""\
            from django.db import migrations

            class Migration(migrations.Migration):
                dependencies = [("testapp", "0001_initial")]
                operations = [
                    migrations.RemoveIndex(
                        model_name="maskedcolumn",
                        name="maskedcolumn_safe_text_idx",
                    ),
                ]
        """)
        )

    call_command = staticmethod(partial(run_command, "sqlmigrate"))

    def test_forward_migration_removes_label(self):
        out, err, returncode = self.call_command("testapp", "0002")

        self.assertEqual(returncode, 0)
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."safe_text" IS NULL',
            out,
        )

    def test_backward_migration_restores_label(self):
        out, err, returncode = self.call_command("testapp", "0002", "--backwards")

        self.assertEqual(returncode, 0)
        self.assertIn(
            'SECURITY LABEL FOR "anon" ON COLUMN "testapp_maskedcolumn"."safe_text" '
            "IS 'MASKED WITH FUNCTION anon.dummy_name()'",
            out,
        )

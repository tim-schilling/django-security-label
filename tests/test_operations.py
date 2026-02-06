from __future__ import annotations

from django.db import connection
from django.test import TransactionTestCase

from django_security_label import compat
from django_security_label.operations import CreateRole, CreateSecurityLabelForRole


class TestCreateRole(TransactionTestCase):
    def test_init(self):
        op = CreateRole("test_role", inherit_from_db_user=True)
        self.assertEqual(op.name, "test_role")
        self.assertTrue(op.inherit_from_db_user)

    def test_class_attributes(self):
        self.assertTrue(CreateRole.reversible)
        self.assertEqual(CreateRole.category, compat.ADDITION)

    def test_database_forwards(self):
        op = CreateRole("test_role")
        with connection.schema_editor(collect_sql=True) as schema_editor:
            op.database_forwards("app", schema_editor, None, None)
            self.assertListEqual(
                schema_editor.collected_sql,
                [
                    'DROP ROLE IF EXISTS "test_role";',
                    'CREATE ROLE "test_role" NOLOGIN;',
                ],
            )

    def test_database_forwards_with_inherit(self):
        op = CreateRole("test_role", inherit_from_db_user=True)
        db_user = connection.settings_dict["USER"]
        with connection.schema_editor(collect_sql=True) as schema_editor:
            op.database_forwards("app", schema_editor, None, None)
            self.assertListEqual(
                schema_editor.collected_sql,
                [
                    'DROP ROLE IF EXISTS "test_role";',
                    'CREATE ROLE "test_role" NOLOGIN;',
                    f'GRANT "{db_user}" TO "test_role" WITH INHERIT TRUE;',
                ],
            )

    def test_database_backwards(self):
        op = CreateRole("test_role")
        with connection.schema_editor(collect_sql=True) as schema_editor:
            op.database_backwards("app", schema_editor, None, None)
            self.assertListEqual(
                schema_editor.collected_sql,
                [
                    'DROP ROLE IF EXISTS "test_role";',
                ],
            )


class TestCreateSecurityLabelForRole(TransactionTestCase):
    def test_init(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        self.assertEqual(op.provider, "anon")
        self.assertEqual(op.role, "masked_reader")
        self.assertEqual(op.string_literal, "MASKED")

    def test_class_attributes(self):
        self.assertTrue(CreateSecurityLabelForRole.reversible)
        self.assertEqual(CreateSecurityLabelForRole.category, compat.ADDITION)

    def test_database_forwards_postgresql(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        with connection.schema_editor(collect_sql=True) as schema_editor:
            op.database_forwards("app", schema_editor, None, None)
            self.assertListEqual(
                schema_editor.collected_sql,
                [
                    "SECURITY LABEL FOR anon ON ROLE \"masked_reader\" IS 'MASKED';",
                ],
            )

    def test_database_forwards_skips_non_postgresql(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        with connection.schema_editor(collect_sql=True) as schema_editor:
            vendor = schema_editor.connection.vendor
            schema_editor.connection.vendor = "sqlite"
            try:
                op.database_forwards("app", schema_editor, None, None)
                self.assertListEqual(schema_editor.collected_sql, [])
            finally:
                schema_editor.connection.vendor = vendor

    def test_database_backwards(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        with connection.schema_editor(collect_sql=True) as schema_editor:
            op.database_backwards("app", schema_editor, None, None)
            self.assertListEqual(
                schema_editor.collected_sql,
                [
                    'SECURITY LABEL FOR anon ON ROLE "masked_reader" IS NULL;',
                ],
            )

    def test_describe(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        self.assertEqual(op.describe(), "Creates security label for role masked_reader")

    def test_migration_name_fragment(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        self.assertEqual(
            op.migration_name_fragment, "create_security_label_masked_reader"
        )

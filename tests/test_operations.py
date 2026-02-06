from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock, call

from django.db.migrations.operations.base import OperationCategory

from django_security_label.operations import CreateRole, CreateSecurityLabelForRole


class TestCreateRole(TestCase):
    def test_init(self):
        op = CreateRole("test_role", inherit_from_db_user=True)
        self.assertEqual(op.name, "test_role")
        self.assertTrue(op.inherit_from_db_user)

    def test_class_attributes(self):
        self.assertTrue(CreateRole.reversible)
        self.assertEqual(CreateRole.category, OperationCategory.ADDITION)

    def test_database_forwards(self):
        op = CreateRole("test_role")
        schema_editor = Mock()

        op.database_forwards("app", schema_editor, None, None)

        schema_editor.execute.assert_has_calls(
            [
                call("DROP ROLE IF EXISTS test_role"),
                call("CREATE ROLE test_role NOLOGIN"),
            ]
        )

    def test_database_forwards_with_inherit(self):
        op = CreateRole("test_role", inherit_from_db_user=True)
        schema_editor = Mock()
        schema_editor.connection.settings_dict = {"USER": "db_user"}
        schema_editor.quote_name.return_value = '"db_user"'

        op.database_forwards("app", schema_editor, None, None)

        self.assertEqual(schema_editor.execute.call_count, 3)
        schema_editor.execute.assert_any_call(
            'GRANT "db_user" to dsl_masked_reader WITH INHERIT TRUE'
        )

    def test_database_backwards(self):
        op = CreateRole("test_role")
        schema_editor = Mock()

        op.database_backwards("app", schema_editor, None, None)

        schema_editor.execute.assert_called_once_with("DROP ROLE IF EXISTS test_role")


class TestCreateSecurityLabelForRole(TestCase):
    def test_init(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        self.assertEqual(op.provider, "anon")
        self.assertEqual(op.role, "masked_reader")
        self.assertEqual(op.string_literal, "MASKED")

    def test_class_attributes(self):
        self.assertTrue(CreateSecurityLabelForRole.reversible)
        self.assertEqual(
            CreateSecurityLabelForRole.category, OperationCategory.ADDITION
        )

    def test_database_forwards_postgresql(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        schema_editor = Mock()
        schema_editor.connection.vendor = "postgresql"
        schema_editor.quote_name.return_value = '"masked_reader"'

        op.database_forwards("app", schema_editor, None, None)

        schema_editor.execute.assert_called_once_with(
            "SECURITY LABEL FOR anon ON ROLE \"masked_reader\" IS 'MASKED'"
        )

    def test_database_forwards_skips_non_postgresql(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        schema_editor = Mock()
        schema_editor.connection.vendor = "sqlite"

        op.database_forwards("app", schema_editor, None, None)

        schema_editor.execute.assert_not_called()

    def test_database_backwards(self):
        op = CreateSecurityLabelForRole(
            provider="anon", role="masked_reader", string_literal="MASKED"
        )
        schema_editor = Mock()
        schema_editor.quote_name.return_value = '"masked_reader"'

        op.database_backwards("app", schema_editor, None, None)

        schema_editor.execute.assert_called_once_with(
            'SECURITY LABEL FOR anon ON ROLE "masked_reader" IS NULL'
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

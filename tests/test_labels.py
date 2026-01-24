from __future__ import annotations

from unittest import TestCase
from unittest.mock import Mock

from django_security_label.labels import (
    AnonMaskSecurityLabel,
    ColumnSecurityLabel,
    MaskFunction,
)


class TestColumnSecurityLabel(TestCase):
    def test_init_with_single_field(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )
        self.assertEqual(label.provider, "test_provider")
        self.assertEqual(label.string_literal, "test_literal")
        self.assertEqual(label.fields, ["text"])

    def test_init_with_no_fields_raises_error(self):
        with self.assertRaisesRegex(ValueError, "must be used with exactly one field"):
            ColumnSecurityLabel(
                fields=[],
                provider="test_provider",
                string_literal="test_literal",
            )

    def test_init_with_multiple_fields_raises_error(self):
        with self.assertRaisesRegex(ValueError, "must be used with exactly one field"):
            ColumnSecurityLabel(
                fields=["field1", "field2"],
                provider="test_provider",
                string_literal="test_literal",
            )

    def test_get_security_label(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )
        self.assertEqual(
            label._get_security_label(),
            "SECURITY LABEL FOR %(provider)s ON COLUMN %(table)s.%(column)s IS '%(string_literal)s'",
        )

    def test_remove_security_label(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )
        self.assertEqual(
            label._remove_security_label(),
            "SECURITY LABEL FOR %(provider)s ON COLUMN %(table)s.%(column)s IS NULL",
        )

    def test_create_sql(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )

        mock_model = Mock()
        mock_model._meta.db_table = "test_table"
        mock_field = Mock()
        mock_field.column = "text_column"
        mock_model._meta.get_field.return_value = mock_field

        mock_editor = Mock()
        mock_editor.quote_name = lambda x: f'"{x}"'

        statement = label.create_sql(mock_model, mock_editor)

        self.assertEqual(
            str(statement),
            "SECURITY LABEL FOR \"test_provider\" ON COLUMN \"test_table\".\"text_column\" "
            "IS 'test_literal'",
        )

    def test_remove_sql(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )

        mock_model = Mock()
        mock_model._meta.db_table = "test_table"
        mock_field = Mock()
        mock_field.column = "text_column"
        mock_model._meta.get_field.return_value = mock_field

        mock_editor = Mock()
        mock_editor.quote_name = lambda x: f'"{x}"'

        statement = label.remove_sql(mock_model, mock_editor)

        self.assertEqual(
            str(statement),
            "SECURITY LABEL FOR \"test_provider\" ON COLUMN \"test_table\".\"text_column\" IS NULL",
        )

    def test_deconstruct(self):
        label = ColumnSecurityLabel(
            fields=["text"],
            provider="test_provider",
            string_literal="test_literal",
        )
        path, expressions, kwargs = label.deconstruct()

        self.assertEqual(path, "django_security_label.labels.ColumnSecurityLabel")
        self.assertEqual(expressions, ())
        self.assertEqual(kwargs["fields"], ["text"])
        self.assertEqual(kwargs["provider"], "test_provider")
        self.assertEqual(kwargs["string_literal"], "test_literal")


class TestMaskFunction(TestCase):
    def test_mask_function_values(self):
        self.assertEqual(MaskFunction.dummy_name, "dummy_name()")
        self.assertEqual(MaskFunction.dummy_uuidv4, "dummy_uuidv4()")
        self.assertEqual(MaskFunction.dummy_catchphrase, "dummy_catchphrase()")

    def test_mask_function_is_str_enum(self):
        self.assertIsInstance(MaskFunction.dummy_name, str)
        self.assertEqual(str(MaskFunction.dummy_name), "dummy_name()")


class TestAnonMaskSecurityLabel(TestCase):
    def test_init(self):
        label = AnonMaskSecurityLabel(
            fields=["text"],
            mask_function=MaskFunction.dummy_name,
        )
        self.assertEqual(label.provider, "anon")
        self.assertEqual(label.string_literal, "MASKED WITH FUNCTION anon.dummy_name()")
        self.assertEqual(label.fields, ["text"])

    def test_init_ignores_provider_and_string_literal_kwargs(self):
        label = AnonMaskSecurityLabel(
            fields=["text"],
            mask_function=MaskFunction.dummy_name,
            provider="ignored_provider",
            string_literal="ignored_literal",
        )
        self.assertEqual(label.provider, "anon")
        self.assertEqual(label.string_literal, "MASKED WITH FUNCTION anon.dummy_name()")

    def test_with_mask_function_string(self):
        label = AnonMaskSecurityLabel(
            fields=["text"],
            mask_function="custom_mask()",
        )
        self.assertEqual(label.string_literal, "MASKED WITH FUNCTION anon.custom_mask()")

    def test_single_field_validation(self):
        with self.assertRaisesRegex(ValueError, "must be used with exactly one field"):
            AnonMaskSecurityLabel(
                fields=["field1", "field2"],
                mask_function=MaskFunction.dummy_name,
            )

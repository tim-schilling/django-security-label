from __future__ import annotations

from enum import StrEnum

from django.db import models
from django.db.backends.ddl_references import Statement, Table


class ColumnSecurityLabel(models.Index):
    def __init__(self, *args, provider: str, string_literal: str, fields=(), **kwargs):
        self.provider = provider
        self.string_literal = string_literal
        if len(fields) != 1:
            raise ValueError(
                f"{self.__class__.__name__} must be used with exactly one field."
            )
        super().__init__(*args, fields=fields, **kwargs)

    def _get_security_label(self):
        return "SECURITY LABEL FOR %(provider)s ON COLUMN %(table)s.%(column)s IS '%(string_literal)s'"

    def _remove_security_label(self):
        return "SECURITY LABEL FOR %(provider)s ON COLUMN %(table)s.%(column)s IS NULL"

    def create_sql(self, model, schema_editor, using="", **kwargs):
        database_name = schema_editor.connection.settings_dict["NAME"]
        return Statement(
            self._get_security_label(),
            database=schema_editor.quote_name(database_name),
            table=Table(model._meta.db_table, schema_editor.quote_name),
            column=schema_editor.quote_name(
                model._meta.get_field(self.fields[0]).column
            ),
            provider=schema_editor.quote_name(self.provider),
            string_literal=self.string_literal,
        )

    def remove_sql(self, model, schema_editor, **kwargs):
        return Statement(
            self._remove_security_label(),
            table=Table(model._meta.db_table, schema_editor.quote_name),
            column=schema_editor.quote_name(
                model._meta.get_field(self.fields[0]).column
            ),
            provider=schema_editor.quote_name(self.provider),
        )

    def deconstruct(self):
        (path, expressions, kwargs) = super().deconstruct()
        kwargs["provider"] = self.provider
        kwargs["string_literal"] = self.string_literal
        return path, expressions, kwargs


class AnonymizeColumn(ColumnSecurityLabel):
    def __init__(self, *args, provider="anon", **kwargs):
        super().__init__(*args, provider=provider, **kwargs)


class MaskFunction(StrEnum):
    dummy_bic = "dummy_bic()"
    dummy_bs = "dummy_bs()"
    dummy_bs_adj = "dummy_bs_adj()"
    dummy_bs_noun = "dummy_bs_noun()"
    dummy_bs_verb = "dummy_bs_verb()"
    dummy_building_number = "dummy_building_number()"
    dummy_buzzword = "dummy_buzzword()"
    dummy_buzzword_middle = "dummy_buzzword_middle()"
    dummy_buzzword_tail = "dummy_buzzword_tail()"
    dummy_catchphrase = "dummy_catchphrase()"
    dummy_cell_number = "dummy_cell_number()"
    dummy_city_name = "dummy_city_name()"
    dummy_city_prefix = "dummy_city_prefix()"
    dummy_city_suffix = "dummy_city_suffix()"
    dummy_color = "dummy_color()"
    dummy_company_name = "dummy_company_name()"
    dummy_company_suffix = "dummy_company_suffix()"
    dummy_country_code = "dummy_country_code()"
    dummy_country_name = "dummy_country_name()"
    dummy_credit_card_number = "dummy_credit_card_number()"
    dummy_currency_code = "dummy_currency_code()"
    dummy_currency_name = "dummy_currency_name()"
    dummy_currency_symbol = "dummy_currency_symbol()"
    dummy_dir_path = "dummy_dir_path()"
    dummy_domain_suffix = "dummy_domain_suffix()"
    dummy_file_extension = "dummy_file_extension()"
    dummy_file_name = "dummy_file_name()"
    dummy_file_path = "dummy_file_path()"
    dummy_first_name = "dummy_first_name()"
    dummy_free_email = "dummy_free_email()"
    dummy_free_email_provider = "dummy_free_email_provider()"
    dummy_health_insurance_code = "dummy_health_insurance_code()"
    dummy_hex_color = "dummy_hex_color()"
    dummy_hsl_color = "dummy_hsl_color()"
    dummy_hsla_color = "dummy_hsla_color()"
    dummy_industry = "dummy_industry()"
    dummy_ip = "dummy_ip()"
    dummy_ipv4 = "dummy_ipv4()"
    dummy_ipv6 = "dummy_ipv6()"
    dummy_isbn = "dummy_isbn()"
    dummy_isbn13 = "dummy_isbn13()"
    dummy_isin = "dummy_isin()"
    dummy_last_name = "dummy_last_name()"
    dummy_latitude = "dummy_latitude()"
    dummy_licence_plate = "dummy_licence_plate()"
    dummy_longitude = "dummy_longitude()"
    dummy_mac_address = "dummy_mac_address()"
    dummy_name = "dummy_name()"
    dummy_name_with_title = "dummy_name_with_title()"
    dummy_phone_number = "dummy_phone_number()"
    dummy_post_code = "dummy_post_code()"
    dummy_profession = "dummy_profession()"
    dummy_rfc_status_code = "dummy_rfc_status_code()"
    dummy_rgb_color = "dummy_rgb_color()"
    dummy_rgba_color = "dummy_rgba_color()"
    dummy_safe_email = "dummy_safe_email()"
    dummy_secondary_address = "dummy_secondary_address()"
    dummy_secondary_address_type = "dummy_secondary_address_type()"
    dummy_state_abbr = "dummy_state_abbr()"
    dummy_state_name = "dummy_state_name()"
    dummy_street_name = "dummy_street_name()"
    dummy_street_suffix = "dummy_street_suffix()"
    dummy_suffix = "dummy_suffix()"
    dummy_timezone = "dummy_timezone()"
    dummy_title = "dummy_title()"
    dummy_user_agent = "dummy_user_agent()"
    dummy_username = "dummy_username()"
    dummy_uuidv1 = "dummy_uuidv1()"
    dummy_uuidv3 = "dummy_uuidv3()"
    dummy_uuidv4 = "dummy_uuidv4()"
    dummy_uuidv5 = "dummy_uuidv5()"
    dummy_valid_statux_code = "dummy_valid_statux_code()"
    dummy_word = "dummy_word()"
    dummy_zip_code = "dummy_zip_code()"


class MaskColumn(AnonymizeColumn):
    def __init__(self, *args, policy="anon", mask_function: str, **kwargs):
        self.policy = policy
        self.mask_function = mask_function
        kwargs.pop("string_literal", None)
        kwargs.pop("provider", None)
        string_literal = f"MASKED WITH FUNCTION anon.{self.mask_function}"
        super().__init__(
            *args, provider=self.policy, string_literal=string_literal, **kwargs
        )

    def deconstruct(self):
        (path, expressions, kwargs) = super().deconstruct()
        kwargs["policy"] = self.policy
        kwargs["mask_function"] = self.mask_function
        return path, expressions, kwargs

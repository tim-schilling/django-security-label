from __future__ import annotations

from django.db.migrations.operations.base import Operation, OperationCategory


class CreateRole(Operation):
    reversible = True
    category = OperationCategory.ADDITION

    def __init__(self, name, inherit_from_db_user=False):
        """

        :param name: The name of the role to be created.
        :param inherit_from_db_user: Whether the new role should inherit
               permissions from the DATABASES user.
        """
        self.name = name
        self.inherit_from_db_user = inherit_from_db_user

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(
            f"DROP ROLE IF EXISTS {schema_editor.quote_name(self.name)}"
        )
        schema_editor.execute(
            f"CREATE ROLE {schema_editor.quote_name(self.name)} NOLOGIN"
        )
        if self.inherit_from_db_user:
            user = schema_editor.connection.settings_dict["USER"]
            schema_editor.execute(
                f"GRANT {schema_editor.quote_name(user)} TO {schema_editor.quote_name(self.name)} WITH INHERIT TRUE"
            )

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(
            f"DROP ROLE IF EXISTS {schema_editor.quote_name(self.name)}"
        )


class CreateSecurityLabelForRole(Operation):
    reversible = True
    category = OperationCategory.ADDITION

    def __init__(self, *, provider, role, string_literal):
        self.provider = provider
        self.role = role
        self.string_literal = string_literal

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != "postgresql":
            return
        schema_editor.execute(
            f"SECURITY LABEL FOR {self.provider} ON ROLE {schema_editor.quote_name(self.role)} IS '{self.string_literal}'"
        )

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(
            f"SECURITY LABEL FOR anon ON ROLE {schema_editor.quote_name(self.role)} IS NULL"
        )

    def describe(self):
        return f"Creates security label for role {self.role}"

    @property
    def migration_name_fragment(self):
        return f"create_security_label_{self.role}"

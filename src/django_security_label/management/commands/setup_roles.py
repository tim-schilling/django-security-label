from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from django_security_label.operations import create_role, create_security_label_for_role


class Command(BaseCommand):
    help = (
        "Create Django groups and PostgreSQL roles from SECURITY_LABEL_GROUPS_TO_ROLES. "
        "Safe to run multiple times; existing roles and security labels are updated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="The Django database alias to use (default: 'default').",
        )

    def handle(self, *args, **options):
        groups_to_roles = getattr(settings, "SECURITY_LABEL_GROUPS_TO_ROLES", [])
        if not groups_to_roles:
            self.stderr.write("SECURITY_LABEL_GROUPS_TO_ROLES is not defined or empty.")
            return

        Group.objects.bulk_create(
            [Group(name=group_name) for group_name, _ in groups_to_roles],
            ignore_conflicts=True,
        )

        db_alias = options["database"]
        db_connection = connections[db_alias]
        db_roles = [db_role for _, db_role in groups_to_roles]

        self._register_masking_policies(db_connection, db_roles)

        for group_name, db_role in groups_to_roles:
            with (
                transaction.atomic(using=db_alias),
                db_connection.schema_editor(atomic=True) as schema_editor,
            ):
                create_role(schema_editor, name=db_role, inherit_from_db_user=True)
                create_security_label_for_role(
                    schema_editor,
                    provider=db_role,
                    role=db_role,
                    string_literal="MASKED",
                )
            self.stdout.write(f"Configured group '{group_name}' with role '{db_role}'")

    def _register_masking_policies(self, db_connection, db_roles):
        """The providers must be registered before SECURITY LABEL can reference them."""
        db_name = db_connection.settings_dict["NAME"]
        quote_name = db_connection.ops.quote_name
        policies = ", ".join(sorted(db_roles))
        with db_connection.cursor() as cursor:
            cursor.execute(
                f"ALTER DATABASE {quote_name(db_name)} SET anon.masking_policies TO %s",
                [policies],
            )
        # Reconnect so the new masking_policies setting takes effect.
        db_connection.close()
        db_connection.ensure_connection()

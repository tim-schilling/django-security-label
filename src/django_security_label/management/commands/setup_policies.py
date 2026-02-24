"""Create Django groups and PostgreSQL masking policies from settings.

Reads ``settings.SECURITY_LABEL_GROUPS_TO_POLICIES`` — a list of
``(group_name, policy)`` tuples — and ensures each Django
`Group` and corresponding PostgreSQL masking policy -
role pair exist.  Safe to run multiple times.

This is meant to be used with [GroupMaskingMiddleware][django_security_label.middleware.GroupMaskingMiddleware].

Usage:

    python manage.py setup_policies
    python manage.py setup_policies --database <database_name>
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import connections, transaction

from django_security_label.operations import create_role, create_security_label_for_role


class Command(BaseCommand):
    """Management command that provisions groups and roles.

    For each entry in ``SECURITY_LABEL_GROUPS_TO_POLICIES`` the command:

    1. Creates the Django group (if it doesn't exist).
    2. Creates a ``NOLOGIN`` PostgreSQL role that inherits from the
       database user.
    3. Configures the masking policy by applying a ``MASKED`` security
       label on the role so PostgreSQL Anonymizer recognises it.
    """

    help = (
        "Create Django groups and PostgreSQL masking policy-role pairs from SECURITY_LABEL_GROUPS_TO_POLICIES. "
        "Safe to run multiple times; existing groups and policies are updated, but not removed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="The Django database alias to use (default: 'default').",
        )

    def handle(self, *args, **options):
        groups_to_policies = getattr(settings, "SECURITY_LABEL_GROUPS_TO_POLICIES", [])
        if not groups_to_policies:
            self.stderr.write(
                "SECURITY_LABEL_GROUPS_TO_POLICIES is not defined or empty."
            )
            return

        Group.objects.bulk_create(
            [Group(name=group_name) for group_name, _ in groups_to_policies],
            ignore_conflicts=True,
        )

        db_alias = options["database"]
        db_connection = connections[db_alias]
        policies = [policy for _, policy in groups_to_policies]

        self._register_masking_policies(db_connection, policies)

        for group_name, policy in groups_to_policies:
            with (
                transaction.atomic(using=db_alias),
                db_connection.schema_editor(atomic=True) as schema_editor,
            ):
                create_role(schema_editor, name=policy, inherit_from_db_user=True)
                create_security_label_for_role(
                    schema_editor,
                    provider=policy,
                    role=policy,
                    string_literal="MASKED",
                )
            self.stdout.write(f"Configured group '{group_name}' with policy '{policy}'")

    def _register_masking_policies(self, db_connection, policies):
        """Register providers with ``anon.masking_policies`` before applying labels."""
        db_name = db_connection.settings_dict["NAME"]
        quote_name = db_connection.ops.quote_name
        with db_connection.cursor() as cursor:
            cursor.execute(
                f"ALTER DATABASE {quote_name(db_name)} SET anon.masking_policies TO %s",
                [", ".join(sorted(policies))],
            )
        # Reconnect so the new masking_policies setting takes effect.
        db_connection.close()
        db_connection.ensure_connection()

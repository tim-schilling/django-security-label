from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "Sets the anon.masking_policies on a database via ALTER DATABASE."

    def add_arguments(self, parser):
        parser.add_argument(
            "policies",
            nargs="+",
            type=str,
            help="One or more policy names to set (e.g. devs analysts).",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="The Django database alias to use (default: 'default').",
        )

    def handle(self, *args, **options):
        db_alias = options["database"]
        policies = ", ".join(options["policies"])
        connection = connections[db_alias]
        db_name = connection.settings_dict["NAME"]

        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER DATABASE {connection.ops.quote_name(db_name)} "
                f"SET anon.masking_policies TO %s",
                [policies],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Set anon.masking_policies to '{policies}' on database '{db_name}'."
            )
        )

from __future__ import annotations

import getpass
import uuid

from core.models import MaskedColumn
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

MIN_ROWS = 3

SAMPLE_DATA = [
    {
        "text": "Top secret project codename",
        "uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "confidential": "Income range: 50,000-99,9999",
        "number": 42,
    },
    {
        "text": "Classified budget figures",
        "uuid": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "confidential": "Income range: 100,000-199,9999",
        "number": 99,
    },
    {
        "text": "Internal employee review",
        "uuid": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "confidential": "Income range: 50,000-99,9999",
        "number": 7,
    },
]


class Command(BaseCommand):
    help = (
        "Set up example data: create groups from SECURITY_LABEL_GROUPS_TO_POLICIES, "
        "a staff user for each group, and sample MaskedColumn rows."
    )

    def handle(self, *args, **options):
        users = self._setup_groups_and_users()
        self._ensure_sample_data()
        self._print_users_table(users)
        self._print_data_table()

    def _setup_groups_and_users(self) -> list[tuple[str, str]]:
        """Returns a list of (username, group_name) for demo users."""
        users = []
        groups_to_policies = getattr(settings, "SECURITY_LABEL_GROUPS_TO_POLICIES", [])
        if not groups_to_policies:
            self.stderr.write(
                "SECURITY_LABEL_GROUPS_TO_POLICIES is not defined or empty."
            )
            return users

        core_permissions = Permission.objects.filter(
            content_type__app_label="core",
        )

        for group_name, policy in groups_to_policies:
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.set(core_permissions)
            if created:
                self.stdout.write(f"Created group '{group_name}' (policy: {policy})")
            else:
                self.stdout.write(
                    f"Group '{group_name}' already exists (role: {policy})"
                )

            username = group_name.lower()
            if not User.objects.filter(username=username).exists():
                self.stdout.write(
                    f"\nCreating staff user '{username}' for group '{group_name}':"
                )
                password = self._get_password()
                if password is None:
                    self.stderr.write(
                        f"Skipping user '{username}' due to empty password."
                    )
                    continue

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    is_staff=True,
                )
                user.groups.add(group)
                self.stdout.write(
                    f"Created staff user '{username}' in group '{group_name}'"
                )
            users.append((username, group_name))

        return users

    def _ensure_sample_data(self):
        existing = MaskedColumn.objects.count()
        if existing >= MIN_ROWS:
            self.stdout.write(
                f"\nMaskedColumn already has {existing} row(s), skipping sample data."
            )
            return

        rows_needed = MIN_ROWS - existing
        for data in SAMPLE_DATA[:rows_needed]:
            MaskedColumn.objects.create(**data)
        self.stdout.write(f"\nCreated {rows_needed} sample MaskedColumn row(s).")

    def _print_users_table(self, users: list[tuple[str, str]]):
        headers = ["username", "group"]
        col_widths = [len(h) for h in headers]
        for username, group_name in users:
            col_widths[0] = max(col_widths[0], len(username))
            col_widths[1] = max(col_widths[1], len(group_name))

        def format_row(values):
            return " | ".join(v.ljust(col_widths[i]) for i, v in enumerate(values))

        self.stdout.write(
            f"\n{'Created users':=^{sum(col_widths) + 3 * (len(headers) - 1)}}"
        )
        self.stdout.write(format_row(headers))
        self.stdout.write("-+-".join("-" * w for w in col_widths))
        for username, group_name in users:
            self.stdout.write(format_row([username, group_name]))

    def _print_data_table(self):
        rows = MaskedColumn.objects.all()
        if not rows:
            return

        headers = ["uuid", "text", "confidential", "number"]
        col_widths = [len(h) for h in headers]

        table_rows = []
        for row in rows:
            values = [
                str(row.uuid)[:12] + "...",
                row.text[:30],
                row.confidential[:30],
                str(row.number),
            ]
            table_rows.append(values)
            for i, v in enumerate(values):
                col_widths[i] = max(col_widths[i], len(v))

        def format_row(values):
            return " | ".join(v.ljust(col_widths[i]) for i, v in enumerate(values))

        self.stdout.write(
            f"\n{'Raw MaskedColumn data':=^{sum(col_widths) + 3 * (len(headers) - 1)}}"
        )
        self.stdout.write(format_row(headers))
        self.stdout.write("-+-".join("-" * w for w in col_widths))
        for values in table_rows:
            self.stdout.write(format_row(values))

        self.stdout.write(
            "\nCompare this data to what each staff user sees in the admin."
        )

    def _get_password(self) -> str | None:
        while True:
            password = getpass.getpass("Password: ")
            if not password:
                return None
            password_confirm = getpass.getpass("Password (again): ")
            if password == password_confirm:
                return password
            self.stderr.write("Passwords do not match. Please try again.")

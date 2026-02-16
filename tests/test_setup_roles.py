from __future__ import annotations

from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase, override_settings


class TestSetupRolesCommand(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._saved_policies = self._get_masking_policies()

    def tearDown(self):
        self._restore_masking_policies(self._saved_policies)
        super().tearDown()

    def _get_masking_policies(self):
        db_name = connection.settings_dict["NAME"]
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT unnest(setconfig) FROM pg_db_role_setting "
                "JOIN pg_database ON pg_database.oid = setdatabase "
                "WHERE datname = %s AND setrole = 0",
                [db_name],
            )
            for (setting,) in cursor.fetchall():
                if setting.startswith("anon.masking_policies="):
                    return setting.split("=", 1)[1]
        return None

    def _restore_masking_policies(self, policies):
        db_name = connection.settings_dict["NAME"]
        quote_name = connection.ops.quote_name
        with connection.cursor() as cursor:
            if policies:
                cursor.execute(
                    f"ALTER DATABASE {quote_name(db_name)} "
                    f"SET anon.masking_policies TO %s",
                    [policies],
                )
            else:
                cursor.execute(
                    f"ALTER DATABASE {quote_name(db_name)} RESET anon.masking_policies"
                )
        connection.close()
        connection.ensure_connection()

    def _get_db_roles(self, role_names):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
                [list(role_names)],
            )
            return {row[0] for row in cursor.fetchall()}

    def _cleanup_roles(self, role_names):
        with connection.cursor() as cursor:
            for role in role_names:
                cursor.execute(f"DROP ROLE IF EXISTS {connection.ops.quote_name(role)}")

    @override_settings(SECURITY_LABEL_GROUPS_TO_ROLES=[])
    def test_empty_setting_writes_error(self):
        stderr = StringIO()
        call_command("setup_roles", stderr=stderr)
        self.assertIn("not defined or empty", stderr.getvalue())

    def test_no_setting_writes_error(self):
        stderr = StringIO()
        with self.settings():
            call_command("setup_roles", stderr=stderr)
        self.assertIn("not defined or empty", stderr.getvalue())

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_ROLES=[
            ("Test Group A", "test_role_a"),
            ("Test Group B", "test_role_b"),
        ]
    )
    def test_creates_groups_and_db_roles(self):
        self.addCleanup(self._cleanup_roles, ["test_role_a", "test_role_b"])

        call_command("setup_roles", stdout=StringIO())

        self.assertTrue(Group.objects.filter(name="Test Group A").exists())
        self.assertTrue(Group.objects.filter(name="Test Group B").exists())
        self.assertEqual(
            self._get_db_roles(["test_role_a", "test_role_b"]),
            {"test_role_a", "test_role_b"},
        )

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_ROLES=[
            ("Test Group D", "test_role_d"),
        ]
    )
    def test_updates_existing_db_roles(self):
        self.addCleanup(self._cleanup_roles, ["test_role_d"])
        with connection.cursor() as cursor:
            cursor.execute("CREATE ROLE test_role_d NOLOGIN")

        call_command("setup_roles", stdout=StringIO())

        self.assertEqual(self._get_db_roles(["test_role_d"]), {"test_role_d"})

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_ROLES=[
            ("Test Group F", "test_role_f"),
        ]
    )
    def test_creates_groups_idempotently(self):
        self.addCleanup(self._cleanup_roles, ["test_role_f"])
        Group.objects.create(name="Test Group F")

        call_command("setup_roles", stdout=StringIO())

        self.assertEqual(Group.objects.filter(name="Test Group F").count(), 1)

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_ROLES=[
            ("Test Group G", "test_role_g"),
        ]
    )
    def test_is_idempotent(self):
        self.addCleanup(self._cleanup_roles, ["test_role_g"])

        call_command("setup_roles", stdout=StringIO())
        call_command("setup_roles", stdout=StringIO())

        self.assertTrue(Group.objects.filter(name="Test Group G").exists())
        self.assertEqual(self._get_db_roles(["test_role_g"]), {"test_role_g"})

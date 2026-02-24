from __future__ import annotations

from io import StringIO

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase, override_settings


class TestSetupPoliciesCommand(TransactionTestCase):
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
            else:  # pragma: no cover
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

    @override_settings(SECURITY_LABEL_GROUPS_TO_POLICIES=[])
    def test_empty_setting_writes_error(self):
        stderr = StringIO()
        call_command("setup_policies", stderr=stderr)
        self.assertIn("not defined or empty", stderr.getvalue())

    def test_no_setting_writes_error(self):
        stderr = StringIO()
        with self.settings():
            call_command("setup_policies", stderr=stderr)
        self.assertIn("not defined or empty", stderr.getvalue())

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_POLICIES=[
            ("Test Group A", "test_policy_a"),
            ("Test Group B", "test_policy_b"),
        ]
    )
    def test_creates_groups_and_policies(self):
        self.addCleanup(self._cleanup_roles, ["test_policy_a", "test_policy_b"])

        call_command("setup_policies", stdout=StringIO())

        self.assertTrue(Group.objects.filter(name="Test Group A").exists())
        self.assertTrue(Group.objects.filter(name="Test Group B").exists())
        self.assertEqual(
            self._get_db_roles(["test_policy_a", "test_policy_b"]),
            {"test_policy_a", "test_policy_b"},
        )

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_POLICIES=[
            ("Test Group D", "test_policy_d"),
        ]
    )
    def test_updates_existing_policies(self):
        self.addCleanup(self._cleanup_roles, ["test_policy_d"])
        with connection.cursor() as cursor:
            cursor.execute("CREATE ROLE test_role_d NOLOGIN")

        call_command("setup_policies", stdout=StringIO())

        self.assertEqual(self._get_db_roles(["test_policy_d"]), {"test_policy_d"})

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_POLICIES=[
            ("Test Group F", "test_policy_f"),
        ]
    )
    def test_creates_groups_idempotently(self):
        self.addCleanup(self._cleanup_roles, ["test_policy_f"])
        Group.objects.create(name="Test Group F")

        call_command("setup_policies", stdout=StringIO())

        self.assertEqual(Group.objects.filter(name="Test Group F").count(), 1)

    @override_settings(
        SECURITY_LABEL_GROUPS_TO_POLICIES=[
            ("Test Group G", "test_policy_g"),
        ]
    )
    def test_is_idempotent(self):
        self.addCleanup(self._cleanup_roles, ["test_policy_g"])

        call_command("setup_policies", stdout=StringIO())
        call_command("setup_policies", stdout=StringIO())

        self.assertTrue(Group.objects.filter(name="Test Group G").exists())
        self.assertEqual(self._get_db_roles(["test_policy_g"]), {"test_policy_g"})

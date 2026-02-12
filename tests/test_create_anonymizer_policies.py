from __future__ import annotations

from django.db import connection
from django.test import TestCase

from tests.utils import run_command


class TestCreateAnonymizerPolicies(TestCase):
    def _get_masking_policies(self):
        with connection.cursor() as cursor:
            db_name = connection.settings_dict["NAME"]
            cursor.execute(
                "SELECT unnest(setconfig) FROM pg_db_role_setting "
                "JOIN pg_database ON pg_database.oid = setdatabase "
                "WHERE datname = %s AND setrole = 0",
                [db_name],
            )
            for (setting,) in cursor.fetchall():
                if setting.startswith("anon.masking_policies="):
                    return setting
            return None

    def _clear_masking_policies(self):
        with connection.cursor() as cursor:
            db_name = connection.settings_dict["NAME"]
            cursor.execute(
                f"ALTER DATABASE {connection.ops.quote_name(db_name)} "
                f"RESET anon.masking_policies"
            )

    def setUp(self):
        super().setUp()
        self._clear_masking_policies()

    def tearDown(self):
        self._clear_masking_policies()
        super().tearDown()

    def test_single_policy(self):
        out, err, returncode = run_command("create_anonymizer_policies", "devtests")
        self.assertEqual(returncode, 0)
        self.assertIn("devtests", out)

        setting = self._get_masking_policies()
        self.assertIn("devtests", setting)

    def test_multiple_policies(self):
        out, err, returncode = run_command(
            "create_anonymizer_policies", "devtests", "analytics"
        )
        self.assertEqual(returncode, 0)
        self.assertIn("devtests, analytics", out)

        setting = self._get_masking_policies()
        self.assertIn("devtests", setting)
        self.assertIn("analytics", setting)

    def test_database_argument(self):
        out, err, returncode = run_command(
            "create_anonymizer_policies",
            "devtests",
            "--database=default",
        )
        self.assertEqual(returncode, 0)
        self.assertIn("devtests", out)

        setting = self._get_masking_policies()
        self.assertIn("devtests", setting)

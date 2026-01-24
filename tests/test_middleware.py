from __future__ import annotations

import uuid

from django.db import connection
from django.test import RequestFactory, TransactionTestCase

from django_security_label.middleware import MaskedReadsMiddleware
from tests.testapp.models import MaskedColumn


class TestMaskedReadsMiddleware(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Force a reconnection in your test setup to pick up anon configuration
        connection.close()
        connection.ensure_connection()

    def setUp(self):
        self.request_factory = RequestFactory()
        self.test_record = MaskedColumn.objects.create(
            text="secret_text_value",
            uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            safe_text="safe_text_value",
            safe_uuid=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            confidential="hunter2",
            random_int=999,
        )

    def test_no_user_sees_masked_data(self):
        def get_response(request):
            request.row = MaskedColumn.objects.get(pk=self.test_record.pk)
            return request

        middleware = MaskedReadsMiddleware(get_response)
        request = self.request_factory.get("/")

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertNotEqual(response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678"))
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")
        self.assertGreaterEqual(response.row.random_int, 0)
        self.assertLessEqual(response.row.random_int, 50)

    def test_unauthenticated_user_sees_masked_data(self):
        def get_response(request):
            with connection.cursor() as cursor:
                cursor.execute("select * from testapp_maskedcolumn;")
                print(f"Current DB user: {cursor.fetchall()}")
            print(MaskedColumn.objects.all().values())
            request.row = MaskedColumn.objects.get(pk=self.test_record.pk)
            return request

        middleware = MaskedReadsMiddleware(get_response)
        request = self.request_factory.get("/")
        request.user = type("User", (), {"is_authenticated": False, "is_superuser": False})()

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_authenticated_non_superuser_sees_masked_data(self):
        def get_response(request):
            request.row = MaskedColumn.objects.get(pk=self.test_record.pk)
            return request

        middleware = MaskedReadsMiddleware(get_response)
        request = self.request_factory.get("/")
        request.user = type("User", (), {"is_authenticated": True, "is_superuser": False})()

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_superuser_sees_real_data(self):
        def get_response(request):
            request.row = MaskedColumn.objects.get(pk=self.test_record.pk)
            return request

        middleware = MaskedReadsMiddleware(get_response)
        request = self.request_factory.get("/")
        request.user = type("User", (), {"is_authenticated": True, "is_superuser": True})()

        response = middleware(request)

        self.assertEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678"))
        self.assertEqual(response.row.confidential, "hunter2")
        self.assertEqual(response.row.random_int, 999)

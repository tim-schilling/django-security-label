from __future__ import annotations

import uuid
from functools import partial

from django.contrib.auth.models import Group, User
from django.db import InternalError
from django.test import RequestFactory, override_settings

from django_security_label import constants
from django_security_label.middleware import (
    GroupMaskingMiddleware,
    MaskedReadsMiddleware,
)
from tests.testapp.middleware import AnalystsMaskedReadsMiddleware
from tests.testapp.models import MaskedColumn
from tests.utils import AnonTransactionTestCase


def get_response_read(request, test_record):
    request.row = MaskedColumn.objects.get(pk=test_record.pk)
    return request


def get_response_update(request, test_record):
    MaskedColumn.objects.filter(pk=test_record.pk).update(
        safe_text="updated_via_queryset",
    )


class TestMaskedReadsMiddleware(AnonTransactionTestCase):
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
        middleware = MaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertNotEqual(
            response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")
        self.assertGreaterEqual(response.row.random_int, 0)
        self.assertLessEqual(response.row.random_int, 50)

    def test_unauthenticated_user_sees_masked_data(self):
        middleware = MaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = type(
            "User", (), {"is_authenticated": False, "is_superuser": False}
        )()

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_authenticated_non_superuser_sees_masked_data(self):
        middleware = MaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = type(
            "User", (), {"is_authenticated": True, "is_superuser": False}
        )()

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_superuser_sees_real_data(self):
        middleware = MaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = type(
            "User", (), {"is_authenticated": True, "is_superuser": True}
        )()

        response = middleware(request)

        self.assertEqual(response.row.text, "secret_text_value")
        self.assertEqual(
            response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.assertEqual(response.row.confidential, "hunter2")
        self.assertEqual(response.row.random_int, 999)

    def test_masked_user_cant_update_unlabeled_columns(self):
        middleware = MaskedReadsMiddleware(
            partial(get_response_update, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = type(
            "User", (), {"is_authenticated": True, "is_superuser": False}
        )()

        with self.assertRaises(InternalError):
            middleware(request)

        self.test_record.refresh_from_db()
        self.assertEqual(self.test_record.safe_text, "safe_text_value")


class TestAnalystsMaskedReadsMiddleware(AnonTransactionTestCase):
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

    def test_analysts_no_user_sees_masked_uuid(self):
        middleware = AnalystsMaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")

        response = middleware(request)

        # uuid uses policy="analysts" — analysts_reader IS labeled for that policy
        self.assertEqual(
            response.row.uuid,
            uuid.UUID("00000000-0000-0000-0000-000000000000"),
            str(response.row.__dict__),
        )
        # text uses the default "anon" policy — analysts_reader is NOT labeled for it
        self.assertEqual(response.row.text, "secret_text_value")
        # confidential uses the default "anon" policy — also not masked
        self.assertEqual(response.row.confidential, "hunter2")

    def test_analysts_superuser_sees_real_data(self):
        middleware = AnalystsMaskedReadsMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = type(
            "User", (), {"is_authenticated": True, "is_superuser": True}
        )()

        response = middleware(request)

        self.assertEqual(response.row.text, "secret_text_value")
        self.assertEqual(
            response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.assertEqual(response.row.confidential, "hunter2")
        self.assertEqual(response.row.random_int, 999)


GROUPS_TO_POLICIES = [
    ("Masked Readers", constants.MASKED_READER_ROLE),
    ("Analysts", "analysts_reader"),
    ("Unmasked", None),
]


@override_settings(SECURITY_LABEL_GROUPS_TO_POLICIES=GROUPS_TO_POLICIES)
class TestGroupMaskingMiddleware(AnonTransactionTestCase):
    request_factory = RequestFactory()

    def setUp(self):
        self.test_record = MaskedColumn.objects.create(
            text="secret_text_value",
            uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            safe_text="safe_text_value",
            safe_uuid=uuid.UUID("87654321-4321-8765-4321-876543218765"),
            confidential="hunter2",
            random_int=999,
        )

    def test_superuser_sees_real_data(self):
        user = User.objects.create_superuser(username="super_user", password="test")

        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = user

        response = middleware(request)

        self.assertEqual(response.row.text, "secret_text_value")
        self.assertEqual(
            response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.assertEqual(response.row.confidential, "hunter2")
        self.assertEqual(response.row.random_int, 999)

    def test_falls_back_to_masked_reader_without_matching_group(self):
        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )

        # No user on request
        request = self.request_factory.get("/")
        response = middleware(request)
        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

        # Authenticated user not in any configured group
        user = User.objects.create_user(username="no_group_user", password="test")
        request = self.request_factory.get("/")
        request.user = user
        response = middleware(request)
        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_user_in_masked_readers_group_sees_masked_data(self):
        user = User.objects.create_user(username="masked_user", password="test")
        group = Group.objects.create(name="Masked Readers")
        user.groups.add(group)

        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = user

        response = middleware(request)

        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_user_in_analysts_group_sees_analysts_masking(self):
        user = User.objects.create_user(username="analyst_user", password="test")
        group = Group.objects.create(name="Analysts")
        user.groups.add(group)

        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = user

        response = middleware(request)

        # uuid uses the "analysts" provider — masked for analysts_reader
        self.assertEqual(
            response.row.uuid,
            uuid.UUID("00000000-0000-0000-0000-000000000000"),
        )
        # text uses the "anon" provider — not masked for analysts_reader
        self.assertEqual(response.row.text, "secret_text_value")

    def test_first_matching_group_in_setting_order_wins(self):
        user = User.objects.create_user(username="multi_group_user", password="test")
        masked_group = Group.objects.create(name="Masked Readers")
        analysts_group = Group.objects.create(name="Analysts")
        user.groups.add(masked_group, analysts_group)

        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = user

        response = middleware(request)

        # "Masked Readers" is first in GROUPS_TO_POLICIES, so dsl_masked_reader applies
        self.assertNotEqual(response.row.text, "secret_text_value")
        self.assertEqual(response.row.confidential, "CONFIDENTIAL")

    def test_user_in_none_policy_group_sees_real_data(self):
        user = User.objects.create_user(username="unmasked_user", password="test")
        group = Group.objects.create(name="Unmasked")
        user.groups.add(group)

        middleware = GroupMaskingMiddleware(
            partial(get_response_read, test_record=self.test_record)
        )
        request = self.request_factory.get("/")
        request.user = user

        response = middleware(request)

        self.assertEqual(response.row.text, "secret_text_value")
        self.assertEqual(
            response.row.uuid, uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.assertEqual(response.row.confidential, "hunter2")
        self.assertEqual(response.row.random_int, 999)

    def test_masked_user_cant_update(self):
        middleware = GroupMaskingMiddleware(
            partial(get_response_update, test_record=self.test_record)
        )
        request = self.request_factory.get("/")

        with self.assertRaises(InternalError):
            middleware(request)

        self.test_record.refresh_from_db()
        self.assertEqual(self.test_record.safe_text, "safe_text_value")

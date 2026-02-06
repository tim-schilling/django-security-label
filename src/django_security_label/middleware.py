from __future__ import annotations

from django.db import InternalError, connection
from django.http import HttpRequest

from django_security_label import constants


def set_session_role(role):
    with connection.cursor() as cursor:
        cursor.execute(f"SET SESSION ROLE {connection.ops.quote_name(role)};")


def enable_masked_reads():
    set_session_role(constants.MASKED_READER_ROLE)


def disable_masked_reads():
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE;")


def use_masked_reads(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return user is None or not user.is_authenticated or not user.is_superuser


class MaskedReadsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if use_masked_reads(request):
            enable_masked_reads()
            try:
                response = self.get_response(request)
            except InternalError:
                disable_masked_reads()
                raise
            disable_masked_reads()
            return response

        return self.get_response(request)

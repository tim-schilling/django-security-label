from __future__ import annotations

from django.db import connection
from django.http import HttpRequest


def enable_masked_reads():
    with connection.cursor() as cursor:
        cursor.execute("SET SESSION ROLE dsl_masked_reader;")


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
        if enable_masking := use_masked_reads(request):
            enable_masked_reads()

        response = self.get_response(request)

        if enable_masking:
            disable_masked_reads()

        return response

from __future__ import annotations

from django.db import InternalError

from django_security_label.middleware import (
    disable_masked_reads,
    set_session_role,
    use_masked_reads,
)


class AnalystsMaskedReadsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if use_masked_reads(request):
            set_session_role("analysts_reader")
            try:
                response = self.get_response(request)
            except InternalError:
                disable_masked_reads()
                raise
            disable_masked_reads()
            return response

        return self.get_response(request)

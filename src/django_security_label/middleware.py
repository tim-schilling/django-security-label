from django.db import connection


class MaskedReadsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        use_masked_reads = (
            user is None
            or not user.is_authenticated
            or not user.is_superuser
        )

        if use_masked_reads:
            with connection.cursor() as cursor:
                cursor.execute("SET SESSION ROLE dsl_masked_reader;")

        response = self.get_response(request)

        if use_masked_reads:
            with connection.cursor() as cursor:
                cursor.execute("RESET ROLE;")

        return response

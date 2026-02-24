"""Middleware and helpers for switching PostgreSQL session roles.

The middleware classes switch the database connection to a masked reader
role for the duration of each request, so queries return anonymized data
according to the security labels defined on your models.

To write your own masking strategy, subclass one of the middleware
classes and override the decision logic, or call
[enable_masked_reads][django_security_label.middleware.enable_masked_reads]
/ [disable_masked_reads][django_security_label.middleware.disable_masked_reads]
directly in your own middleware.
"""

from __future__ import annotations

from django.conf import settings
from django.db import InternalError, connection
from django.http import HttpRequest

from django_security_label import constants


def set_session_role(role):
    """Run ``SET SESSION ROLE`` for the given PostgreSQL role name."""
    with connection.cursor() as cursor:
        cursor.execute(f"SET SESSION ROLE {connection.ops.quote_name(role)};")


def enable_masked_reads():
    """Switch the session to the default masked reader role."""
    set_session_role(constants.MASKED_READER_ROLE)


def disable_masked_reads():
    """Reset the session role back to the connection default."""
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE;")


def use_masked_reads(request: HttpRequest) -> bool:
    """Return ``True`` if this request should use the masked reader role.

    The default implementation masks reads for anonymous users and
    non-superuser authenticated users.  Override or replace this
    function to implement your own policy.
    """
    user = getattr(request, "user", None)
    return user is None or not user.is_authenticated or not user.is_superuser


class MaskedReadsMiddleware:
    """Enables masked reads for every non-superuser request.

    Uses [use_masked_reads][django_security_label.middleware.use_masked_reads]
    to decide. Subclass and override ``__call__`` or replace
    [use_masked_reads][django_security_label.middleware.use_masked_reads]
    for a custom policy.
    """

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


class GroupMaskingMiddleware:
    """Switches to a PostgreSQL role based on the user's Django group.

    Reads ``settings.SECURITY_LABEL_GROUPS_TO_ROLES`` — a list of
    ``(group_name, db_role)`` tuples — and uses the first matching group.
    Falls back to the default masked reader role.

    Set ``db_role`` to ``None`` for a group to grant unmasked reads to
    members of that group, bypassing masking entirely.

    Subclass and override
    [determine_db_role][django_security_label.middleware.GroupMaskingMiddleware.determine_db_role]
    to change the role selection logic.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def determine_db_role(self, request: HttpRequest) -> str | None:
        """Return the PostgreSQL role to use for this request.

        Iterates ``settings.SECURITY_LABEL_GROUPS_TO_ROLES`` and returns
        the ``db_role`` for the first group the user belongs to.
        Returns ``None`` to skip masking entirely and the default masked reader role if no group matches.
        """
        user = getattr(request, "user", None)
        if user is not None:
            if getattr(user, "is_superuser", False):
                return None
            user_groups = user.groups.in_bulk(field_name="name")
            for group_name, db_role in settings.SECURITY_LABEL_GROUPS_TO_ROLES:
                if group_name in user_groups:
                    return db_role
        return constants.MASKED_READER_ROLE

    def __call__(self, request):
        db_role = self.determine_db_role(request)
        if db_role is not None:
            set_session_role(db_role)
            try:
                response = self.get_response(request)
            except InternalError:
                disable_masked_reads()
                raise
            disable_masked_reads()
            return response

        return self.get_response(request)

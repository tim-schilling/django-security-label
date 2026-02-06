from __future__ import annotations

import django

if django.VERSION < (5, 1):
    ADDITION = "+"
else:
    from django.db.migrations.operations.base import OperationCategory

    ADDITION = OperationCategory.ADDITION

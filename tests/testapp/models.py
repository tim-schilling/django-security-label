from __future__ import annotations

from django.db import models

from django_security_label import labels


class MaskedColumn(models.Model):
    text = models.TextField()
    uuid = models.UUIDField()
    safe_text = models.TextField()
    safe_uuid = models.UUIDField()
    confidential = models.TextField()
    random_int = models.IntegerField()

    class Meta:
        indexes = [
            labels.AnonMaskSecurityLabel(fields=["text"], mask_function=labels.MaskFunction.dummy_catchphrase),
            labels.AnonMaskSecurityLabel(fields=["uuid"], mask_function=labels.MaskFunction.dummy_uuidv4),
            labels.ColumnSecurityLabel(fields=["confidential"], provider="anon", string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$"),
            labels.ColumnSecurityLabel(fields=["random_int"], provider="anon", string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)"),
        ]


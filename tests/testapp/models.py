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
            labels.MaskColumn(
                fields=["text"], mask_function=labels.MaskFunction.dummy_catchphrase
            ),
            labels.MaskColumn(
                fields=["uuid"], mask_function=labels.MaskFunction.dummy_uuidv4
            ),
            labels.AnonymizeColumn(
                fields=["confidential"],
                string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
            ),
            labels.AnonymizeColumn(
                fields=["random_int"],
                string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)",
            ),
        ]

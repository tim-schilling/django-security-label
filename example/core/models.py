from __future__ import annotations

from django.db import models

from django_security_label import labels


class MaskedColumn(models.Model):
    text = models.TextField()
    uuid = models.UUIDField()
    confidential = models.TextField()
    number = models.IntegerField()

    class Meta:
        indexes = [
            labels.MaskColumn(
                fields=["text"],
                policy="dsl_devs",
                mask_function=labels.MaskFunction.dummy_catchphrase,
                name="maskedcolumn_text_devs",
            ),
            labels.MaskColumn(
                fields=["text"],
                policy="dsl_analysts",
                mask_function=labels.MaskFunction.dummy_catchphrase,
                name="maskedcolumn_text_analyst",
            ),
            labels.MaskColumn(
                fields=["uuid"], mask_function=labels.MaskFunction.dummy_uuidv4
            ),
            labels.AnonymizeColumn(
                fields=["confidential"],
                provider="dsl_devs",
                string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
                name="maskedcolumn_confid_devs",
            ),
            labels.AnonymizeColumn(
                fields=["confidential"],
                provider="dsl_analysts",
                string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
                name="maskedcolumn_confid_analysts",
            ),
            labels.AnonymizeColumn(
                fields=["number"],
                provider="dsl_devs",
                string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)",
            ),
        ]

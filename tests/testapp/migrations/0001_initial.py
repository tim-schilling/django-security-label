from __future__ import annotations

from django.db import migrations, models

from django_security_label import labels
from django_security_label.operations import CreateRole, CreateSecurityLabelForRole


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("django_security_label", "0001_initial"),
    ]
    operations = [
        CreateRole("analysts_reader", inherit_from_db_user=True),
        CreateSecurityLabelForRole(
            provider="analysts",
            role="analysts_reader",
            string_literal="MASKED",
        ),
        migrations.CreateModel(
            name="MaskedColumn",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                ("uuid", models.UUIDField()),
                ("safe_text", models.TextField()),
                ("safe_uuid", models.UUIDField()),
                ("confidential", models.TextField()),
                ("random_int", models.IntegerField()),
            ],
        ),
        migrations.AddIndex(
            model_name="maskedcolumn",
            index=labels.MaskColumn(
                fields=["text"],
                mask_function=labels.MaskFunction.dummy_catchphrase,
                name="testapp_mask_text",
            ),
        ),
        migrations.AddIndex(
            model_name="maskedcolumn",
            index=labels.MaskColumn(
                fields=["uuid"],
                mask_function=labels.MaskFunction.dummy_uuidv4,
                name="testapp_mask_uuid",
            ),
        ),
        migrations.AddIndex(
            model_name="maskedcolumn",
            index=labels.AnonymizeColumn(
                fields=["uuid"],
                provider="analysts",
                string_literal="MASKED WITH VALUE $$00000000-0000-0000-0000-000000000000$$",
                name="testapp_masked_column_uuid_analysts",
            ),
        ),
        migrations.AddIndex(
            model_name="maskedcolumn",
            index=labels.AnonymizeColumn(
                fields=["confidential"],
                string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
                name="testapp_anon_confidential",
            ),
        ),
        migrations.AddIndex(
            model_name="maskedcolumn",
            index=labels.AnonymizeColumn(
                fields=["random_int"],
                string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)",
                name="testapp_anon_random_int",
            ),
        ),
    ]

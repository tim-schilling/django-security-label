# Masking Functions

The PostgreSQL Anonymizer provider [includes dozens of functions](https://postgresql-anonymizer.readthedocs.io/en/stable/masking_functions/).

## Using a predefined function

You can use a predefined function such as `fake_email`:

```python
from django_security_label import labels

labels.MaskColumn(fields=["email"], mask_function=labels.MaskFunction.fake_email)
```

## Using a custom string literal

You can also define the [string literal portion of the `SECURITY LABEL`](https://www.postgresql.org/docs/current/sql-security-label.html) directly:

```python
labels.AnonymizeColumn(
    fields=["confidential"],
    provider="anon",
    string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
)
```

# Setting Up Group-Based Masking

This guide walks through configuring different masking behavior per Django ``auth.Group`` using ``GroupMaskingMiddleware``.

Using this strategy would allow users of a group called "analysts" to view incomes, and locations, but not names. While users of group, "developers" would only see incomes.

## Define `SECURITY_LABEL_GROUPS_TO_ROLES` setting

In your settings file, define a list of group name and database role pairs. A group can only appear in this list once. The database role name will also be used for the security label provider / masking rule policy. Order is important. If a user is associated with multiple groups, the role with the first group in this list will be used.

```python
SECURITY_LABEL_GROUPS_TO_ROLES = [
    ("Analysts", "analyst"),
    ("Developers", "developer"),
]
```

## Run ``setup_roles``

Use the ``setup_roles`` management command to create the PostgreSQL roles and masking policies. If you're using multiple databases, you can customize that with the ``--database`` argument.

```bash
python -m manage setup_roles
```

This will create the ``Group`` instance if it doesn't exist.

## Define masking rules on models

With the security label providers / masking policies created in the previous step, those policies can be used in the masking rules on the model.

For example:

```python
from django.db import models
from django_security_label import labels


class Business(models.Model):
    name = models.CharField()
    income = models.IntegerField()
    location = models.CharField()

    class Meta:
        indexes = [
            labels.MaskColumn(
                fields=["name"],
                policy="analyst",
                mask_function=labels.MaskFunction.dummy_name,
                name="bus_mask_name_analyst",
            ),
            labels.MaskColumn(
                fields=["name"],
                policy="dev",
                mask_function=labels.MaskFunction.dummy_name,
                name="bus_mask_name_dev",
            ),
            labels.MaskColumn(
                fields=["location"],
                policy="dev",
                mask_function=labels.MaskFunction.dummy_city_name,
                name="bus_mask_location_dev",
            ),
        ]
```

See [Masking Functions](../how-to-guides/masking-functions.md) for more masking options.

## Make and apply migrations

Run ``makemigrations`` and ``migrate`` to apply them.

```bash
python -m manage makemigrations
python -m manage migrate
```

## Add ``GroupMaskingMiddleware`` to ``MIDDLEWARE``

Update the ``MIDDLEWARE`` setting to include ``django_security_label.middleware.GroupMaskingMiddleware``. This must come after ``AuthenticationMiddleware`` since it depends on knowing which user is making the request and what group(s) they are associated with.

## Assign users to groups

At this point, you can assign users to the relevant groups. This can be done in the Django admin or you can do this via the shell. When these users make requests to the Django application, the defined masking rules will be in effect for them.

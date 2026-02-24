# Installation

## Prerequisites

This package requires the [PostgreSQL Anonymizer](https://postgresql-anonymizer.readthedocs.io) extension to be installed on your database.

Please follow the [installation instructions](https://postgresql-anonymizer.readthedocs.io/en/stable/INSTALL/) for your environment. This will require changes to the server that runs your database, but several managed database services such as [Aiven support it out of the box](https://aiven.io/postgresql).

## Install the package

```bash
pip install django-security-label
```

## Configuration

1. Add the app to your `INSTALLED_APPS`:

    ```python
    INSTALLED_APPS = [
        # ...
        "django_security_label",
    ]
    ```

2. Enable the middleware for relevant environments:

    ```python
    MIDDLEWARE = [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        # MaskedReadsMiddleware must be after AuthenticationMiddleware because
        # AuthenticationMiddleware writes to the database.
        "django_security_label.middleware.MaskedReadsMiddleware",
    ]
    ```

    Note: The PostgreSQL role that is used for masked reads will not have the ability to insert, update or delete data on any table that has a masking security label applied to it.

3. Run the migrations. This will install the [`anon` provider](https://postgresql-anonymizer.readthedocs.io/) and configure [dynamic masking](https://postgresql-anonymizer.readthedocs.io/en/stable/dynamic_masking/). It will also create the `dsl_masked_reader` role with the same permissions as your database user.

    ```bash
    python manage.py migrate django_security_label
    ```

    You can view the SQL with: `python manage.py sqlmigrate django_security_label 0001`

4. Define your security labels on your models:

    ```python
    class MyModel(models.Model):
        text = models.TextField()
        confidential = models.TextField()
        random_int = models.IntegerField()

        class Meta:
            # Defining any security labels will prevent any changes to the table
            # when masking is enabled.
            indexes = [
                labels.MaskColumn(
                    fields=["text"], mask_function=labels.MaskFunction.dummy_catchphrase
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
    ```

5. Create migrations and add a dependency on `("django_security_label", "0001_initial")`:

    ```bash
    python manage.py makemigrations
    ```

    The dependency on `("django_security_label", "0001_initial")` will ensure that your security labels will be applied after the anon provider is installed.

    Example migration file:

    ```python
    from django.db import migrations, models
    import django_security_label.labels


    class Migration(migrations.Migration):
        initial = True

        dependencies = [
            ("django_security_label", "0001_initial"),
        ]

        operations = [
            migrations.CreateModel(
                name="MyModel",
                fields=[
                    (
                        "id",
                        models.BigAutoField(
                            auto_created=True,
                            primary_key=True,
                            serialize=False,
                            verbose_name="ID",
                        ),
                    ),
                    ("text", models.TextField()),
                    ("confidential", models.TextField()),
                    ("random_int", models.IntegerField()),
                ],
                options={
                    "indexes": [
                        django_security_label.labels.MaskColumn(
                            fields=["text"],
                            mask_function=django_security_label.labels.MaskFunction[
                                "dummy_catchphrase"
                            ],
                            name="mymodel_text_6adba0_idx",
                            provider="anon",
                            string_literal="MASKED WITH FUNCTION anon.dummy_catchphrase()",
                        ),
                        django_security_label.labels.AnonymizeColumn(
                            fields=["confidential"],
                            name="mymodel_confide_030817_idx",
                            provider="anon",
                            string_literal="MASKED WITH VALUE $$CONFIDENTIAL$$",
                        ),
                        django_security_label.labels.AnonymizeColumn(
                            fields=["random_int"],
                            name="mymodel_random__45b12e_idx",
                            provider="anon",
                            string_literal="MASKED WITH FUNCTION anon.random_int_between(0,50)",
                        ),
                    ],
                },
            ),
        ]
    ```

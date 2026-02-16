# Getting Started

This tutorial walks through the example app included in the repository to demonstrate masked reads in the Django admin.

## Running the example app

1. Run migrations:

    ```bash
    uv run python -m example.manage migrate
    ```

2. Create the PostgreSQL roles and Django groups defined in `SECURITY_LABEL_GROUPS_TO_ROLES`:

    ```bash
    uv run python example/manage.py setup_roles
    ```

3. Set up staff users and sample data:

    ```bash
    uv run python example/manage.py setup_data
    ```

    This will create a staff user for each group with permissions to manage all `core` models. You will be prompted to set a password for each user. It also ensures there are at least 3 `MaskedColumn` rows and prints a table of the raw data.

4. Run the development server:

    ```bash
    uv run python example/manage.py runserver
    ```

5. Log in as each staff user (e.g. `analysts`, `developers`) and [view the `MaskedColumn` list](http://127.0.0.1:8000/admin/core/maskedcolumn/). Compare the values shown in the admin to the raw data printed by `setup_data` to see how each role's masking rules affect the data.

## What it looks like

### Superuser / unmasked read

![Unmasked Read](../images/unmasked_read.png)

### Staff user / masked read

![Masked Read](../images/masked_read.png)

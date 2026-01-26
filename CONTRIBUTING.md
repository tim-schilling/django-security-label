# Contributing

To run the tests you must be using a PostgreSQL database that has the [`anon` provider installed](https://postgresql-anonymizer.readthedocs.io/en/latest/INSTALL/#).

You can also run the following docker container:

```bash
docker run -d -e POSTGRES_PASSWORD=django-security-label -e POSTGRES_USER=django-security-label -p 6432:5432 registry.gitlab.com/dalibo/postgresql_anonymizer
```

To run the tests:

```bash
uv sync --all-extras
uv run tox
# Or if you have tox installed as a tool
tox
```

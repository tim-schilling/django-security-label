# Contributing

## Running tests

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

To get code coverage for a single run, use:

```bash
tox -e py313-django52,coverage
```

## Documentation

The docs are built with [MkDocs](https://www.mkdocs.org/) using the
[Material](https://squidfunk.github.io/mkdocs-material/) theme and hosted on
[Read the Docs](https://readthedocs.org/). API reference pages are
auto-generated from docstrings at build time.

### Setup

Install the docs dependencies:

```bash
uv sync --group docs
uv run mkdocs serve
```

### Project structure

The docs follow the [Diataxis](https://diataxis.fr/) framework:

```
docs/
├── explanation/               # Understanding-oriented discussion
├── images/                    # Screenshots and diagrams
├── how-to-guides/             # Task-oriented recipes
├── reference/                 # Auto-generated API reference (do not edit)
├── tutorials/                 # Learning-oriented guides
├── index.md                   # Landing page
├── installation.md            # Installation and configuration
├── contribute.md              # Contributing guide (this page)
└── gen_ref_pages.py           # Script that generates reference pages
```

### API reference

Reference docs under `reference/` are **auto-generated**. Please do not edit
them by hand. They are produced at build time by `docs/gen_ref_pages.py`, which
walks `src/django_security_label/` and creates a page per module using
[mkdocstrings](https://mkdocstrings.github.io/). To improve the reference
docs, add or update the docstrings in the source code.

### Deployment

Docs are built and deployed automatically by Read the Docs on every push. The
configuration lives in `.readthedocs.yaml`.

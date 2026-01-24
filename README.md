# django-security-label

Django support for PostgreSQL security labels.

## Installation

```bash
pip install django-security-label
```

## Usage

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_security_label",
]
```

## Development

```bash
uv sync --all-extras
uv run tox
```

## Documentation

```bash
uv run mkdocs serve
```

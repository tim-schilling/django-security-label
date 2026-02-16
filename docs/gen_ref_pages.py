"""Generate the code reference pages."""

from __future__ import annotations

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

src = Path("src")

# Internal modules that aren't useful in the public API reference.
SKIP_MODULES = {"compat", "constants", "apps"}

# Per-module overrides: module identifier -> mkdocstrings options block (YAML).
# Used to exclude noisy members from the module render and re-add them
# with tighter settings.
MODULE_OVERRIDES = {
    "django_security_label.labels": {
        # Exclude MaskFunction from the module render; it's re-added below
        # with members hidden to avoid listing all 70+ enum values.
        "module_options": "    options:\n      members:\n        - ColumnSecurityLabel\n        - AnonymizeColumn\n        - MaskColumn\n",
        "extras": "::: django_security_label.labels.MaskFunction\n    options:\n      members: false\n",
    },
}

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src / "django_security_label").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        continue
    if "migrations" in parts:
        continue
    if parts[-1] in SKIP_MODULES:
        continue

    identifier = ".".join(parts)

    # Strip the leading package name and flatten management commands
    # so the nav reads e.g. "labels" instead of "django_security_label > labels".
    if "management" in parts and "commands" in parts:
        nav_parts = (parts[-1],)
    else:
        nav_parts = parts[1:]

    nav[nav_parts] = doc_path.as_posix()

    override = MODULE_OVERRIDES.get(identifier)

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write(f"::: {identifier}\n")
        if override:
            fd.write(override["module_options"])
            fd.write(f"\n{override['extras']}")
        fd.write("")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

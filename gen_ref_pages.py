"""Generate API reference pages automatically from code."""

from pathlib import Path

import mkdocs_gen_files

src = Path(__file__).parent.parent / "fastauth"

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        continue

    if not parts:
        continue

    identifier_parts = ("fastauth",) + parts

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        identifier = ".".join(identifier_parts)

        title = parts[-1].replace("_", " ").title()
        print(f"# {title}", file=fd)
        print(file=fd)

        print(f"::: {identifier}", file=fd)

    # Set edit path
    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(src.parent))

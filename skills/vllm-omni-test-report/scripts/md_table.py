"""Plain GitHub-flavored Markdown tables (no cell padding)."""

from __future__ import annotations


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    """
    Render a pipe table with a ``---`` separator row. Cells are not padded for column alignment.

    Each row must have len(row) == len(headers). Cells should not contain unescaped ``|``.
    """
    cols = len(headers)
    if not headers:
        return ""
    for row in rows:
        if len(row) != cols:
            raise ValueError(
                f"row has {len(row)} cells, expected {cols}: {row!r}"
            )

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * cols) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

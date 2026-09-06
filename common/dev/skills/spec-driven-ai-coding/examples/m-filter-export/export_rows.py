"""Dependency-free example used to exercise the spec/evidence workflow.

This is an educational CSV utility, not a drop-in production export service.
"""
from __future__ import annotations
import csv
import io
from collections.abc import Iterable, Mapping

STATUSES = {"done", "todo"}


def export_rows(rows: Iterable[Mapping[str, str]], status: str) -> str:
    """Validate all rows, then export matching rows without mutating the input.

Columns are id/name/status, in input order. Formula-leading names are prefixed
with an apostrophe for spreadsheet-oriented output. No files or network I/O.
    """
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status must be done or todo")
    validated: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("each row must be a mapping")
        if any(key not in row or not isinstance(row[key], str) for key in ("id", "name", "status")):
            raise ValueError("id, name, and status must be strings")
        if not row["id"] or not row["id"].isascii() or not all(c.isalnum() or c in "_-" for c in row["id"]):
            raise ValueError("id must contain ASCII letters, digits, underscores, or hyphens")
        if row["status"] not in STATUSES:
            raise ValueError("row status must be done or todo")
        validated.append({key: row[key] for key in ("id", "name", "status")})
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=("id", "name", "status"))
    writer.writeheader()
    for row in validated:
        if row["status"] != status:
            continue
        name = row["name"]
        if name.lstrip().startswith(("=", "+", "-", "@")) or name.startswith(("\t", "\r", "\n")):
            row["name"] = "'" + name
        writer.writerow(row)
    return buffer.getvalue()

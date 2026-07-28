import csv
from pathlib import Path

from app.models import BookRecord


def export_structured_jsonl(
    records: list[BookRecord],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                record.model_dump_json()
                + "\n"
            )

    temporary_path.replace(path)


def export_rag_jsonl(
    records: list[BookRecord],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            document = (
                record.to_rag_document()
            )

            file.write(
                document.model_dump_json()
                + "\n"
            )

    temporary_path.replace(path)


def export_csv(
    records: list[BookRecord],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    if not records:
        temporary_path.write_text(
            "",
            encoding="utf-8",
        )

        temporary_path.replace(path)
        return

    rows = [
        record.model_dump(mode="json")
        for record in records
    ]

    with temporary_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary_path.replace(path)
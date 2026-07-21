import sqlite3
from contextlib import closing
from pathlib import Path

from .base import TaskData, TaskRepository


class SQLiteTaskRepository(TaskRepository):
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._database_path = str(database_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    @staticmethod
    def _row_to_task(
        row: sqlite3.Row,
    ) -> TaskData:
        return {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
        }

    def open(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL
                        CHECK (TRIM(title) <> ''),
                    done INTEGER NOT NULL DEFAULT 0
                        CHECK (done IN (0, 1))
                )
                """
            )

            count_row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM tasks
                """
            ).fetchone()

            task_count = count_row["count"]

            if task_count == 0:
                connection.executemany(
                    """
                    INSERT INTO tasks (title, done)
                    VALUES (?, ?)
                    """,
                    [
                        ("Learn FastAPI", 1),
                        ("Build a CRUD API", 0),
                        ("Publish it to GitHub", 0),
                    ],
                )

            connection.commit()

    def close(self) -> None:
        pass

    def list_all(self) -> list[TaskData]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, title, done
                FROM tasks
                ORDER BY id
                """
            ).fetchall()

        return [
            self._row_to_task(row)
            for row in rows
        ]

    def get_by_id(
        self,
        task_id: int,
    ) -> TaskData | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, title, done
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_task(row)

    def create(
        self,
        title: str,
    ) -> TaskData:
        raise NotImplementedError(
            "Task creation will be implemented in Stage 2"
        )

    def update(
        self,
        task_id: int,
        changes: dict[str, object],
    ) -> TaskData | None:
        raise NotImplementedError(
            "Task update will be implemented in Stage 3"
        )

    def delete(
        self,
        task_id: int,
    ) -> bool:
        raise NotImplementedError(
            "Task deletion will be implemented in Stage 3"
        )
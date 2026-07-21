import sqlite3
from contextlib import closing
from pathlib import Path

from .base import TaskData, TaskRepository


class SQLiteTaskRepository(TaskRepository):
    """
    SQLite implementation of the TaskRepository interface.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self._database_path = str(database_path)

    def _connect(self) -> sqlite3.Connection:
        """
        Open a connection to the SQLite database.
        """
        connection = sqlite3.connect(
            self._database_path
        )

        # Allows access using column names:
        # row["id"], row["title"], row["done"]
        connection.row_factory = sqlite3.Row

        return connection

    @staticmethod
    def _row_to_task(
        row: sqlite3.Row,
    ) -> TaskData:
        """
        Convert a SQLite row into a task dictionary.
        """
        return {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
        }

    def open(self) -> None:
        """
        Create the tasks table if it does not exist.

        Insert three example tasks only when the table is empty.
        """
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
        """
        No permanent connection is stored.

        Every method opens and closes its own connection.
        """
        pass

    def list_all(self) -> list[TaskData]:
        """
        Return all tasks from the database.
        """
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
        """
        Return one task by its ID.

        Return None when the task does not exist.
        """
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
        """
        Insert a new task into the database and return it.
        """
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (?, 0)
                """,
                (title,),
            )

            task_id = cursor.lastrowid

            if task_id is None:
                raise RuntimeError(
                    "SQLite did not generate a task ID"
                )

            row = connection.execute(
                """
                SELECT id, title, done
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()

            connection.commit()

        if row is None:
            raise RuntimeError(
                "SQLite did not return the created task"
            )

        return self._row_to_task(row)

    def update(
        self,
        task_id: int,
        changes: dict[str, object],
    ) -> TaskData | None:
        """
        This method will be implemented in Stage 3.
        """
        raise NotImplementedError(
            "Task update will be implemented in Stage 3"
        )

    def delete(
        self,
        task_id: int,
    ) -> bool:
        """
        This method will be implemented in Stage 3.
        """
        raise NotImplementedError(
            "Task deletion will be implemented in Stage 3"
        )
import sqlite3
from contextlib import closing
from pathlib import Path

from .base import TaskData, TaskRepository


class SQLiteTaskRepository(TaskRepository):
    """
    SQLite implementation of the TaskRepository interface.

    This class is responsible for storing and retrieving tasks
    from the tasks.db SQLite database.
    """

    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        """
        Store the path of the SQLite database file.
        """
        self._database_path = str(database_path)

    def _connect(self) -> sqlite3.Connection:
        """
        Open a connection to the SQLite database.
        """
        connection = sqlite3.connect(
            self._database_path
        )

        # Allows column values to be accessed by name:
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
                        (
                            "Learn FastAPI",
                            1,
                        ),
                        (
                            "Build a CRUD API",
                            0,
                        ),
                        (
                            "Publish it to GitHub",
                            0,
                        ),
                    ],
                )

            connection.commit()

    def close(self) -> None:
        """
        No permanent database connection is kept open.

        Each method opens and closes its own connection.
        """
        pass

    def list_all(self) -> list[TaskData]:
        """
        Retrieve and return every task from the database.
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
        Retrieve one task using its ID.

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
        This method will be implemented in Stage 2.
        """
        raise NotImplementedError(
            "Task creation will be implemented in Stage 2"
        )

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
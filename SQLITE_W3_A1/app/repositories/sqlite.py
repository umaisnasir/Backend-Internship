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

        # Allows us to access columns by name:
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
        No permanent database connection is kept open.

        Each method opens and closes its own connection.
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

        Return None if the task does not exist.
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
        Insert a new task and return the created task.
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
        Update an existing task and return the updated task.

        Return None if the task does not exist.
        """
        assignments: list[str] = []
        values: list[object] = []

        if "title" in changes:
            assignments.append("title = ?")
            values.append(changes["title"])

        if "done" in changes:
            assignments.append("done = ?")
            values.append(
                int(bool(changes["done"]))
            )

        # This should not happen because the service rejects
        # an empty update request, but the guard makes the
        # repository safer if it is called directly.
        if not assignments:
            return self.get_by_id(task_id)

        values.append(task_id)

        query = f"""
            UPDATE tasks
            SET {", ".join(assignments)}
            WHERE id = ?
        """

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                query,
                values,
            )

            if cursor.rowcount == 0:
                connection.commit()
                return None

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
            return None

        return self._row_to_task(row)

    def delete(
        self,
        task_id: int,
    ) -> bool:
        """
        Delete a task from the database.

        Return True if a task was deleted.
        Return False if the task did not exist.
        """
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                DELETE FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            )

            connection.commit()

        return cursor.rowcount > 0
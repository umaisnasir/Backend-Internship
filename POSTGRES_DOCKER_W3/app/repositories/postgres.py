from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .base import TaskData, TaskRepository


class PostgresTaskRepository(TaskRepository):
    def __init__(
        self,
        database_url: str,
    ) -> None:
        self._pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=5,
            open=False,
            kwargs={
                "row_factory": dict_row
            },
        )

    def open(self) -> None:
        self._pool.open(wait=True)

    def close(self) -> None:
        self._pool.close()

    def list_all(self) -> list[TaskData]:
        with self._pool.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, title, done
                FROM tasks
                ORDER BY id
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_by_id(
        self,
        task_id: int,
    ) -> TaskData | None:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                SELECT id, title, done
                FROM tasks
                WHERE id = %s
                """,
                (task_id,),
            ).fetchone()

        return dict(row) if row else None

    def create(
        self,
        title: str,
    ) -> TaskData:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, FALSE)
                RETURNING id, title, done
                """,
                (title,),
            ).fetchone()

        if row is None:
            raise RuntimeError(
                "Postgres did not return "
                "the created task"
            )

        return dict(row)

    def update(
        self,
        task_id: int,
        changes: dict[str, object],
    ) -> TaskData | None:
        assignments: list[str] = []
        values: list[object] = []

        if "title" in changes:
            assignments.append("title = %s")
            values.append(changes["title"])

        if "done" in changes:
            assignments.append("done = %s")
            values.append(changes["done"])

        values.append(task_id)

        query = f"""
            UPDATE tasks
            SET {", ".join(assignments)}
            WHERE id = %s
            RETURNING id, title, done
        """

        with self._pool.connection() as connection:
            row = connection.execute(
                query,
                values,
            ).fetchone()

        return dict(row) if row else None

    def delete(self, task_id: int) -> bool:
        with self._pool.connection() as connection:
            row = connection.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id
                """,
                (task_id,),
            ).fetchone()

        return row is not None
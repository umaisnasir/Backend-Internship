from .models import TaskUpdate
from .repositories.base import TaskData, TaskRepository


class TaskNotFoundError(Exception):
    """
    Raised when the requested task does not exist.
    """

    pass


class InvalidTaskError(Exception):
    """
    Raised when the task request contains invalid data.
    """

    pass


class TaskService:
    """
    Contains the business logic for task operations.

    The service does not know whether tasks are stored in
    SQLite, PostgreSQL, or memory. It communicates with
    storage through the TaskRepository interface.
    """

    def __init__(
        self,
        repository: TaskRepository,
    ) -> None:
        self._repository = repository

    def list_tasks(self) -> list[TaskData]:
        """
        Return all tasks from the repository.
        """
        return self._repository.list_all()

    def get_task(
        self,
        task_id: int,
    ) -> TaskData:
        """
        Return one task by its ID.

        Raise TaskNotFoundError if the task does not exist.
        """
        task = self._repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError(
                "Task not found"
            )

        return task

    def create_task(
        self,
        title: str,
    ) -> TaskData:
        """
        Create and return a new task.
        """
        return self._repository.create(title)

    def update_task(
        self,
        task_id: int,
        changes: TaskUpdate,
    ) -> TaskData:
        """
        Update an existing task.

        Raise InvalidTaskError if the request body is empty
        or contains invalid values.

        Raise TaskNotFoundError if the task does not exist.
        """
        if not changes.model_fields_set:
            raise InvalidTaskError(
                "Request body cannot be empty"
            )

        update_values: dict[str, object] = {}

        if "title" in changes.model_fields_set:
            if (
                changes.title is None
                or not changes.title.strip()
            ):
                raise InvalidTaskError(
                    "title must not be empty"
                )

            update_values["title"] = (
                changes.title.strip()
            )

        if "done" in changes.model_fields_set:
            if changes.done is None:
                raise InvalidTaskError(
                    "done must be true or false"
                )

            update_values["done"] = changes.done

        task = self._repository.update(
            task_id,
            update_values,
        )

        if task is None:
            raise TaskNotFoundError(
                "Task not found"
            )

        return task

    def delete_task(
        self,
        task_id: int,
    ) -> None:
        """
        Delete a task.

        Raise TaskNotFoundError if the task does not exist.
        """
        deleted = self._repository.delete(task_id)

        if not deleted:
            raise TaskNotFoundError(
                "Task not found"
            )
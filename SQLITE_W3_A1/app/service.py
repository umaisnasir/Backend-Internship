from .models import TaskUpdate
from .repositories.base import TaskData, TaskRepository


class TaskNotFoundError(Exception):
    pass


class InvalidTaskError(Exception):
    pass


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(self) -> list[TaskData]:
        return self._repository.list_all()

    def get_task(self, task_id: int) -> TaskData:
        task = self._repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError(
                f"Task {task_id} not found"
            )

        return task

    def create_task(self, title: str) -> TaskData:
        return self._repository.create(title)

    def update_task(
        self,
        task_id: int,
        changes: TaskUpdate,
    ) -> TaskData:
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
                f"Task {task_id} not found"
            )

        return task

    def delete_task(self, task_id: int) -> None:
        deleted = self._repository.delete(task_id)

        if not deleted:
            raise TaskNotFoundError(
                f"Task {task_id} not found"
            )
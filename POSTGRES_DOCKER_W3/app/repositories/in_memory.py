from .base import TaskData, TaskRepository


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: list[TaskData] = [
            {
                "id": 1,
                "title": "Learn FastAPI",
                "done": True,
            },
            {
                "id": 2,
                "title": "Build a CRUD API",
                "done": False,
            },
            {
                "id": 3,
                "title": "Publish it to GitHub",
                "done": False,
            },
        ]

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def list_all(self) -> list[TaskData]:
        return [task.copy() for task in self._tasks]

    def get_by_id(self, task_id: int) -> TaskData | None:
        for task in self._tasks:
            if task["id"] == task_id:
                return task.copy()

        return None

    def create(self, title: str) -> TaskData:
        ids = [int(task["id"]) for task in self._tasks]
        next_id = max(ids, default=0) + 1

        task: TaskData = {
            "id": next_id,
            "title": title,
            "done": False,
        }

        self._tasks.append(task)
        return task.copy()

    def update(
        self,
        task_id: int,
        changes: dict[str, object],
    ) -> TaskData | None:
        for task in self._tasks:
            if task["id"] == task_id:
                task.update(changes)
                return task.copy()

        return None

    def delete(self, task_id: int) -> bool:
        for index, task in enumerate(self._tasks):
            if task["id"] == task_id:
                self._tasks.pop(index)
                return True

        return False
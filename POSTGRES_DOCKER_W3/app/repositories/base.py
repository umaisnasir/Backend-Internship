from abc import ABC, abstractmethod


TaskData = dict[str, object]


class TaskRepository(ABC):
    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def list_all(self) -> list[TaskData]:
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> TaskData | None:
        pass

    @abstractmethod
    def create(self, title: str) -> TaskData:
        pass

    @abstractmethod
    def update(
        self,
        task_id: int,
        changes: dict[str, object],
    ) -> TaskData | None:
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        pass
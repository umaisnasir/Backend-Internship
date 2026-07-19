from pydantic import BaseModel, field_validator


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        title = value.strip()

        if not title:
            raise ValueError("title must not be empty")

        return title


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None
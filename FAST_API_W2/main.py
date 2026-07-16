from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator


app = FastAPI(
    title="Task API",
    version="1.0",
    description=(
        "A beginner CRUD API for managing "
        "an in-memory to-do list."
    ),
)


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")

        return value.strip()


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


tasks = [
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


@app.exception_handler(HTTPException)
async def http_error_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    first_error = exc.errors()[0]
    field = str(first_error["loc"][-1])
    message = first_error["msg"]

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": f"Invalid {field}: {message}"},
    )


def find_task(task_id: int) -> dict:
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found",
    )


@app.get(
    "/",
    summary="Describe the API",
)
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    summary="Check whether the server is alive",
)
def health_check():
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=list[Task],
    summary="List all tasks",
)
def list_tasks():
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get one task",
)
def get_task(task_id: int):
    return find_task(task_id)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(new_task: TaskCreate):
    next_id = max(
        (task["id"] for task in tasks),
        default=0,
    ) + 1

    task = {
        "id": next_id,
        "title": new_task.title,
        "done": False,
    }

    tasks.append(task)
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update an existing task",
)
def update_task(task_id: int, changes: TaskUpdate):
    task = find_task(task_id)

    if not changes.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body cannot be empty",
        )

    if "title" in changes.model_fields_set:
        if changes.title is None or not changes.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="title must not be empty",
            )

        task["title"] = changes.title.strip()

    if "done" in changes.model_fields_set:
        if changes.done is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="done must be true or false",
            )

        task["done"] = changes.done

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an existing task",
)
def delete_task(task_id: int):
    task = find_task(task_id)
    tasks.remove(task)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request,
    Response,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import Task, TaskCreate, TaskUpdate
from .repositories.in_memory import (
    InMemoryTaskRepository,
)
from .service import (
    InvalidTaskError,
    TaskNotFoundError,
    TaskService,
)


repository = InMemoryTaskRepository()
service = TaskService(repository)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.open()

    try:
        yield
    finally:
        repository.close()


app = FastAPI(
    title="Task API",
    version="1.0",
    description=(
        "A CRUD API using service and "
        "repository layers."
    ),
    lifespan=lifespan,
)


@app.exception_handler(TaskNotFoundError)
async def not_found_handler(
    request: Request,
    exc: TaskNotFoundError,
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": str(exc)},
    )


@app.exception_handler(InvalidTaskError)
async def invalid_task_handler(
    request: Request,
    exc: InvalidTaskError,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc)},
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
        content={
            "error": f"Invalid {field}: {message}"
        },
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
    return service.list_tasks()


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get one task",
)
def get_task(task_id: int):
    return service.get_task(task_id)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(new_task: TaskCreate):
    return service.create_task(new_task.title)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update an existing task",
)
def update_task(
    task_id: int,
    changes: TaskUpdate,
):
    return service.update_task(
        task_id,
        changes,
    )


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an existing task",
)
def delete_task(task_id: int):
    service.delete_task(task_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
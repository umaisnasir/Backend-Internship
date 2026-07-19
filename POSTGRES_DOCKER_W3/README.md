# Task API — PostgreSQL and Docker

This project extends the original FastAPI CRUD task API by replacing temporary in-memory storage with PostgreSQL.

The FastAPI application and PostgreSQL database run together through Docker Compose. Task data is stored in a Docker named volume, allowing it to survive application and container restarts.

## Features

- Create, list, retrieve, update, and delete tasks
- PostgreSQL database storage
- Persistent data using a Docker named volume
- Pydantic request validation
- Structured JSON error responses
- Swagger UI documentation
- One-command startup with Docker Compose
- Service and repository architecture
- Environment-based database configuration

## Architecture

The application uses the following layers:

```text
FastAPI routes
      ↓
TaskService
      ↓
TaskRepository interface
      ↓
PostgresTaskRepository
      ↓
PostgreSQL
```

The original API was first refactored to use an `InMemoryTaskRepository`.

A `PostgresTaskRepository` was then created using the same `TaskRepository` interface. The storage implementation was switched in `app/main.py`, while the service logic and route handlers remained unchanged after the refactor.

This demonstrates that the storage layer can be replaced without rewriting the API’s business logic.

## Project structure

```text
POSTGRES_DOCKER_W3/
├── app/
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── in_memory.py
│   │   └── postgres.py
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── service.py
├── db/
│   └── init.sql
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

## Requirements

- Docker Desktop
- Docker Compose
- Git

Python does not need to be installed locally when the complete project is run through Docker.

## Environment setup

Create the real environment file from the committed example:

```powershell
Copy-Item .env.example .env
```

The `.env` file contains the PostgreSQL credentials and connection string.

Example:

```env
POSTGRES_DB=taskdb
POSTGRES_USER=taskuser
POSTGRES_PASSWORD=replace_with_local_password
DATABASE_URL=postgresql://taskuser:replace_with_local_password@db:5432/taskdb
```

Update the password values in `.env` before starting the application.

The real `.env` file is excluded from Git through `.gitignore`. Only `.env.example` is committed.

Inside Docker Compose, the database hostname is `db` because that is the PostgreSQL service name.

## Run the complete stack

From the `POSTGRES_DOCKER_W3` directory, run:

```powershell
docker compose up --build
```

This command:

- Builds the FastAPI application image
- Starts the PostgreSQL database container
- Creates the PostgreSQL named volume
- Runs the SQL initialization script on the first database initialization
- Starts the FastAPI container after PostgreSQL becomes healthy

The API is available at:

```text
http://127.0.0.1:8000
```

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

To start the containers in the background:

```powershell
docker compose up -d
```

## Check container status

```powershell
docker compose ps
```

The application and database services should both be running. The PostgreSQL service should show a healthy status.

## Stop the stack

```powershell
docker compose down
```

This removes the application and database containers but preserves the PostgreSQL named volume and stored task data.

## Reset the database

```powershell
docker compose down -v
docker compose up --build
```

Warning: the `-v` option deletes the PostgreSQL named volume and permanently removes the stored task records.

## API endpoints

| Method | Endpoint | Description | Success code |
|---|---|---|---:|
| GET | `/` | Describe the API | 200 |
| GET | `/health` | Check API health | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{task_id}` | Retrieve one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update a task | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 |

Invalid request bodies return `400 Bad Request`, while unknown task IDs return `404 Not Found` with a JSON error message.

## Example create request

```powershell
'{"title":"PostgreSQL persistence verified"}' | curl.exe -i -X POST "http://127.0.0.1:8000/tasks" -H "Content-Type: application/json" --data-binary "@-"
```

Example response:

```text
HTTP/1.1 201 Created
content-type: application/json

{"id":5,"title":"PostgreSQL persistence verified","done":false}
```

## Example update request

```powershell
'{"done":true}' | curl.exe -i -X PUT "http://127.0.0.1:8000/tasks/5" -H "Content-Type: application/json" --data-binary "@-"
```

Expected task data:

```json
{
  "id": 5,
  "title": "PostgreSQL persistence verified",
  "done": true
}
```

## Persistence proof

I created task ID `5` through `POST /tasks` and updated its `done` value to `true`.

I then stopped and removed both the FastAPI and PostgreSQL containers:

```powershell
docker compose down
```

I recreated the complete stack:

```powershell
docker compose up -d
```

After PostgreSQL became healthy, I requested the same task:

```powershell
curl.exe -i "http://127.0.0.1:8000/tasks/5"
```

The API returned `200 OK` and the original task:

```text
HTTP/1.1 200 OK
content-type: application/json

{"id":5,"title":"PostgreSQL persistence verified","done":true}
```

This proved that the task remained stored after the application and database containers were removed and recreated.

The data survived because PostgreSQL stored it in the `postgres_data` Docker named volume rather than inside the disposable database container.

## Database inspection

The records can be inspected directly inside PostgreSQL:

```powershell
docker compose exec db psql -U taskuser -d taskdb -c "SELECT id, title, done FROM tasks ORDER BY id;"
```

## SQL initialization

The table is created through:

```text
db/init.sql
```

The initialization script creates the `tasks` table and inserts the initial task records.

The script runs only when PostgreSQL initializes an empty database volume. It does not run again during a normal container restart.

## Main technologies

- Python
- FastAPI
- Pydantic
- PostgreSQL
- Psycopg
- Docker
- Docker Compose
- SQL
- Git and GitHub
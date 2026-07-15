# First FastAPI Project

A simple REST API built with Python and FastAPI. This project demonstrates basic API routing, JSON responses, health checks, automatic API documentation, and local development using Uvicorn.

## Features

- Root endpoint for confirming that the API is working
- Health-check endpoint
- JSON responses
- Interactive Swagger API documentation
- Local development server with automatic reloading

## Project Structure

```text
first-api/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## API Endpoints

### Root endpoint

```http
GET /
```

Example response:

```json
{
  "message": "My first API is working"
}
```

### Health-check endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

## Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd first-api
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

## Running the API

Start the development server:

```bash
python -m uvicorn main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## Technologies Used

- Python
- FastAPI
- Uvicorn

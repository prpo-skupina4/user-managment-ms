# user-managment-ms
User management micro service

## Features
- User registration and authentication
- JWT token-based authorization
- SQLAlchemy ORM with SQLite database
- FastAPI framework

## Installation

```bash
pip install -r requirements.txt
```

## Running the Service

```bash
uvicorn main:app --reload
```

## Running Tests

Run all tests:
```bash
pytest -v
```

Run tests with coverage:
```bash
pytest -v --cov=. --cov-report=term-missing
```

## CI/CD

This project uses GitHub Actions for continuous integration. The CI pipeline:
- Runs tests on Python 3.11
- Generates code coverage reports
- Automatically runs on pushes and pull requests to main, master, and develop branches

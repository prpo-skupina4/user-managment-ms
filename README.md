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

This project uses GitHub Actions for continuous integration and deployment.

### Continuous Integration (CI)
The CI pipeline:
- Runs tests on Python 3.11
- Generates code coverage reports
- Automatically runs on pushes and pull requests to main, master, and develop branches

### Docker Hub Release
The project automatically builds and publishes Docker images to Docker Hub when tags are pushed:
- Docker Hub repository: `adrian4096/prpo-app`
- Trigger: Push tags matching `v1.2.3` or `1.2.3` format
- Images are tagged with both the version number and `latest`

**Required Secrets:**
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token (create at https://hub.docker.com/settings/security)

**Example:**
```bash
git tag v1.2.3
git push origin v1.2.3
# This will build and push adrian4096/prpo-app:v1.2.3 and adrian4096/prpo-app:latest
```

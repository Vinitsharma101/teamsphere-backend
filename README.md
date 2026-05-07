# TeamSphere Backend

A production-ready backend for collaborative project management built with FastAPI, PostgreSQL, SQLAlchemy 2.0, RBAC, JWT cookie authentication, Docker, and a fully layered architecture. Designed to evolve from a simple CRUD prototype into an industry-grade backend service. 

---

## Features

* Cookie-based JWT authentication (access + refresh tokens)
* RBAC (Admin / Member / Viewer)
* Project & task management
* Team collaboration
* Pagination & filtering
* Secure authentication flow
* Rate limiting
* Centralized error handling
* Docker deployment
* Alembic migrations
* PostgreSQL + SQLAlchemy 2.0
* Fully tested backend (43 tests)

---

# Tech Stack

## Backend

* FastAPI
* PostgreSQL
* SQLAlchemy 2.0
* Alembic
* Pydantic v2
* PyJWT
* Passlib + bcrypt
* SlowAPI

## Testing

* Pytest
* HTTPX

## DevOps

* Docker
* Docker Compose

---

# Architecture

```txt
Routes → Services → Repositories → Models → Database
```

The project follows a clean layered architecture:

* Routes handle HTTP requests
* Services contain business logic
* Repositories manage DB operations
* Models define database structure

---

# Project Structure

```txt
app/
├── api/
│   ├── deps.py
│   └── v1/
│       ├── auth.py
│       ├── projects.py
│       ├── project_members.py
│       ├── tasks.py
│       └── router.py
├── core/
├── db/
├── middleware/
├── models/
├── repositories/
├── schemas/
├── services/
└── main.py

alembic/
tests/
Dockerfile
docker-compose.yml
requirements.txt
requirements-dev.txt
```

---

# Authentication

The backend uses:

* Access Token (15 min)
* Refresh Token (7 days)
* HttpOnly cookies
* Secure & SameSite cookie policies
* JWT token rotation
* Token type validation
* UUID-based `jti`

---

# RBAC System

| Role   | Permissions              |
| ------ | ------------------------ |
| Viewer | Read-only access         |
| Member | Create/update tasks      |
| Admin  | Manage project & members |

Additional protections:

* Cannot remove last admin
* Owner transfer required before leaving
* Assignee must belong to the project

---

# API Features

## Auth

* Signup
* Login
* Logout
* Refresh Token
* Current User

## Projects

* Create project
* Update project
* Delete project
* Transfer ownership

## Members

* Add/remove members
* Update roles
* Leave project

## Tasks

* Create/update/delete tasks
* Assign members
* Filter by:

  * Status
  * Priority
  * Assignee
* Pagination support

---

# Pagination Example

```json
{
  "items": [],
  "total": 57,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

# Security Features

* Rate limiting
* Security headers
* Request logging
* X-Request-ID support
* Secure cookies
* Centralized exception handling

---

# Running Locally

## 1. Clone the repo

```bash
git clone <your_repo_url>
cd teamsphere-backend
```

---

## 2. Create environment variables

```bash
cp .env.example .env
```

Set:

* SECRET_KEY
* DB credentials
* CORS origins

---

## 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

---

## 4. Run migrations

```bash
alembic upgrade head
```

---

## 5. Start development server

```bash
uvicorn app.main:app --reload
```

Server:

```txt
http://localhost:8000
```

Swagger Docs:

```txt
http://localhost:8000/docs
```

---

# Docker Setup

```bash
docker compose up --build
```

This will:

* Start PostgreSQL
* Apply migrations
* Launch FastAPI server

---

# Testing

Run tests:

```bash
pytest
```

Coverage:

```bash
pytest --cov=app
```

Current test suite:

* 43 passing tests

---

# Environment Variables

Example:

```env
SECRET_KEY=your_super_secret_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=teamsphere
DB_USER=postgres
DB_PASSWORD=password
```

---

# Frontend Integration

Always include credentials:

```js
fetch(url, {
  credentials: "include"
})
```

Auth flow:

1. Login/signup
2. Cookies automatically stored
3. Refresh token when access expires
4. Logout clears cookies

---

# Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok"
}
```

---

# Production Features

* Dockerized deployment
* PostgreSQL health checks
* Auto migrations
* Non-root Docker user
* Production-safe headers
* Swagger disabled in production

---

# Future Improvements

* Email verification
* Password reset
* Real-time updates
* File attachments
* Activity feeds
* Audit logs
* WebSockets
* Background jobs
* GitHub Actions CI/CD

---

# Why This Project?

This backend was built to demonstrate:

* Scalable backend architecture
* Production-grade FastAPI practices
* Secure authentication systems
* Real-world RBAC implementation
* Dockerized deployment workflows
* Clean code separation
* Testing strategies

# Author

Built with FastAPI, PostgreSQL, and modern backend engineering practices.

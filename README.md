# Event Management API

A robust, collaborative event management system built with **FastAPI**, supporting user authentication, event CRUD, sharing/collaboration, versioning, changelog, and rate limiting. Designed for extensibility, security, and performance.

---

## Features

- **User Authentication**: JWT-based registration, login, refresh, and logout.
- **Event Management**: Create, update, delete, and list events (including recurring events).
- **Collaboration**: Share events with users, assign roles/permissions.
- **Versioning**: Track and rollback event versions.
- **Changelog**: View chronological event change history and diffs.
- **Rate Limiting**: Prevent abuse with configurable request limits.
- **Caching**: Redis-backed caching for event reads and blacklisting JWTs.
- **Conflict Detection**: Prevent overlapping events for users.
- **Extensible**: Modular routers and services for easy feature addition.

---

## Tech Stack & Key Decisions

| Area                | Choice/Tool         | Reasoning                                                                                  |
|---------------------|---------------------|--------------------------------------------------------------------------------------------|
| API Framework       | FastAPI             | Modern, async, type-safe, automatic docs, great for microservices.                         |
| Auth                | JWT                 | Stateless, scalable, widely supported.                                                     |
| DB ORM              | SQLAlchemy          | Flexible, mature, supports complex queries and migrations.                                 |
| Caching/Blacklist   | Redis               | Fast, in-memory, ideal for caching and token blacklisting.                                 |
| Rate Limiting       | SlowAPI             | Integrates with FastAPI, easy to configure.                                                |
| Data Validation     | Pydantic            | Type-safe, fast, integrates with FastAPI.                                                  |
| Versioning/Changelog| Custom models       | Enables audit trails and rollback, critical for collaborative editing.                     |
| Recurrence          | python-dateutil     | Handles complex recurrence rules (RFC 5545).                                               |

**Architectural Decisions:**
- **Separation of Concerns:** Routers handle HTTP, services handle business logic, models handle DB.
- **Stateless Auth:** JWT for scalability
- **Extensible Collaboration:** Permissions and roles are modeled for future role expansion.
- **Event Versioning:** All changes are tracked for auditability and rollback.
- **Caching:** Read-heavy endpoints use Redis for performance; cache invalidation on writes.
- **Rate Limiting:** Protects API from abuse and accidental DoS.

---

## Setup

1. **Clone the repo:**
   ```sh
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and set your DB and Redis URLs, secret keys, etc.

5. **Run the app:**
   ```sh
   uvicorn main:app --reload
   ```

6. **Run Redis (if not using a managed service):**
   ```sh
   redis-server
   ```

---

## API Overview

- **Auth:** `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- **Events:** `/api/events/`, `/api/events/{id}`, `/api/events/batch`
- **Collaboration:** `/api/events/{id}/share`, `/api/events/{id}/permissions`
- **Versioning:** `/api/events/{id}/history/{version_id}`, `/api/events/{id}/rollback/{version_id}`
- **Changelog:** `/api/events/{id}/changelog`, `/api/events/{id}/diff/{version_id1}/{version_id2}`



## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Redis](https://redis.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [python-dateutil](https://dateutil.readthedocs.io/)

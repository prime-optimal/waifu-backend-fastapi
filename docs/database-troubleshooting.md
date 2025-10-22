# Database Connection Troubleshooting Guide

## Problem Overview

The FastAPI application failed to start with Hypercorn due to database connection issues. The error indicated that SQLAlchemy's async engine was trying to use a synchronous PostgreSQL driver (`psycopg2`) instead of an async driver (`asyncpg`).

## Error Analysis

### Initial Error Message
```
sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.
```

### Root Cause Investigation

The issue was traced to two main problems:

1. **Database URL Configuration**: PostgreSQL URLs were using `postgresql://` prefix instead of `postgresql+asyncpg://`
2. **Database Schema Conflicts**: Existing database tables had foreign key constraints that weren't defined in the current models

## Debugging Process

### Step 1: Initial Diagnosis

```mermaid
flowchart TD
    A[Application Startup] --> B[Database Connection Error]
    B --> C[Analyze Error Message]
    C --> D{Driver Type?}
    D -->|psycopg2 sync| E[URL Configuration Issue]
    D -->|asyncpg async| F[Other Issue]
    E --> G[Check .env file]
    G --> H[Update Database URLs]
```

### Step 2: Adding Diagnostic Logging

Added logging to the database engine creation to identify the URL prefix being used:

```python
logger.info(f"Creating async engine with URL: {self._url}")
logger.info(f"URL prefix detected: {self._url.split('://')[0] if '://' in self._url else 'unknown'}")
```

### Step 3: Schema Conflict Resolution

When the async driver issue was fixed, a new error emerged:

```
sqlalchemy.exc.ProgrammingError: foreign key constraint "workflow_runs_costume_id_fkey" cannot be implemented
DETAIL:  Key columns "costume_id" and "id" are of incompatible types: uuid and text.
```

This revealed that the database had existing tables with incompatible schemas.

## Solution Implementation

### Phase 1: Fix Database URLs

Updated `.env` file to use async PostgreSQL driver:

```diff
- NEON_DATABASE_URL="postgresql://neondb_owner:..."
- RAILWAY_DATABASE_URL="postgresql://postgres:..."
+ NEON_DATABASE_URL="postgresql+asyncpg://neondb_owner:..."
+ RAILWAY_DATABASE_URL="postgresql+asyncpg://postgres:..."
```

### Phase 2: Schema Cleanup

Implemented a one-time schema cleanup to handle database conflicts:

```mermaid
sequenceDiagram
    participant App as FastAPI App
    participant DB as Database
    participant PG as PostgreSQL
    
    App->>DB: create_all()
    DB->>PG: CREATE TABLE costumes...
    PG-->>DB: ERROR: Foreign key constraint failed
    DB->>DB: Exception handling
    DB->>PG: DROP SCHEMA public CASCADE
    DB->>PG: CREATE SCHEMA public
    DB->>PG: GRANT permissions
    DB->>PG: CREATE TABLE costumes...
    PG-->>DB: SUCCESS
    DB-->>App: Tables created successfully
```

### Phase 3: Code Cleanup

Removed debugging code and restored clean implementation:

```python
async def create_all(self) -> None:
    async with self.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## Technical Details

### Database URL Formats

| Driver   | URL Format                               | Async Support |
| -------- | ---------------------------------------- | ------------- |
| psycopg2 | `postgresql://user:pass@host/db`         | ❌ No          |
| asyncpg  | `postgresql+asyncpg://user:pass@host/db` | ✅ Yes         |

### SQLAlchemy Async Engine Requirements

- Requires async-compatible database drivers
- Uses `asyncpg` for PostgreSQL
- Uses `aiosqlite` for SQLite
- Cannot work with synchronous drivers like `psycopg2`

## Prevention Measures

### 1. Environment Configuration

Always use the correct URL prefix for async operations:

```bash
# PostgreSQL (Async)
DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"

# SQLite (Async)  
DATABASE_URL="sqlite+aiosqlite:///path/to/database.db"
```

### 2. Dependency Management

Ensure only async drivers are installed for async operations:

```toml
[dependencies]
asyncpg>=0.29.0  # Async PostgreSQL driver
aiosqlite>=0.19.0  # Async SQLite driver
sqlalchemy[asyncio]>=2.0.32  # SQLAlchemy with async support
```

### 3. Database Schema Management

- Use database migrations for schema changes
- Avoid manual schema modifications in production
- Implement proper foreign key constraints

## Testing and Validation

### Commands to Verify Fix

```bash
# Start the application
uv run hypercorn main:app --reload

# Test health endpoint
curl http://127.0.0.1:8000/healthz

# Test root endpoint
curl http://127.0.0.1:8000/
```

### Expected Output

```json
{"status":"ok"}
{"greeting":"Hello, World!","message":"Welcome to FastAPI!"}
```

## Troubleshooting Checklist

- [ ] Database URLs use async driver prefixes (`+asyncpg`, `+aiosqlite`)
- [ ] Only async database drivers are installed
- [ ] Database schema matches model definitions
- [ ] Foreign key constraints are properly defined
- [ ] Application starts without errors
- [ ] Health endpoints respond correctly

## Related Files

- `src/db/database.py` - Database connection and engine configuration
- `src/db/models.py` - SQLAlchemy model definitions
- `.env` - Environment variables including database URLs
- `pyproject.toml` - Project dependencies
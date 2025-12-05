# Code Execution Environment

## Python Execution

All Python code must be executed using one of these environments:

### Option 1: Docker (Preferred for Backend)

```bash
# Run Python commands in the backend container
docker compose exec api python <script>

# Run pytest
docker compose exec api pytest

# Access Python shell
docker compose exec api python

# Run alembic migrations
docker compose exec api alembic upgrade head
```

### Option 2: Virtual Environment (venv312)

```bash
# Activate venv312 first
venv312\Scripts\activate

# Then run Python commands
python <script>
pytest
alembic upgrade head
```

## Rules

1. **NEVER run Python commands directly** without specifying the environment
2. **For backend operations**: Prefer Docker (`docker compose exec api`)
3. **For local scripts/testing**: Use venv312 activation first
4. **Always check if containers are running** before using Docker commands
5. **When suggesting commands to users**: Always include the environment context

## Examples

### ❌ Wrong

```bash
python backend/app/main.py
pytest
pip install requests
```

### ✅ Correct

```bash
# Using Docker
docker compose exec api python backend/app/main.py
docker compose exec api pytest
docker compose exec api pip install requests

# OR using venv312
venv312\Scripts\activate
python backend/app/main.py
pytest
pip install requests
```

## Frontend Execution

Frontend commands should be run either:

- Inside the Docker container: `docker compose exec web npm run dev`
- Or locally with npm/yarn (no special environment needed)

## Database Operations

Always use Docker for database operations:

```bash
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head
docker compose exec db psql -U first6_user -d first6_db
```

.PHONY: up down logs shell-backend migrate migration test clean

# Start everything
up:
	docker compose up -d

# Stop everything
down:
	docker compose down

# Tail logs
logs:
	docker compose logs -f

# Enter backend shell (for running scripts manually)
shell-backend:
	docker compose exec api /bin/bash

# Generate a new migration (e.g., make migration msg="add_users")
migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

# Run migration
migrate:
	docker compose exec api alembic upgrade head

# Run tests
test:
	docker compose exec api pytest

# Clean up containers and volumes
clean:
	docker compose down -v

# Rebuild containers
rebuild:
	docker compose up -d --build


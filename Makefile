.PHONY: up down logs shell-backend migrate migration test clean seed seed-teams seed-players seed-games

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

# Seed all data (teams, players, games)
seed: seed-teams seed-players seed-games

# Seed teams only
seed-teams:
	docker compose exec api python scripts/seed_teams.py

# Seed players only
seed-players:
	docker compose exec api python scripts/seed_players.py

# Seed games only
seed-games:
	docker compose exec api python scripts/seed_games.py

# Clean up containers and volumes
clean:
	docker compose down -v

# Rebuild containers
rebuild:
	docker compose up -d --build


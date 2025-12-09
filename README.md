# First6 - NFL Prediction Tracking Platform

A boutique, self-hosted web application for tracking NFL "First Touchdown" and "Anytime Touchdown" predictions within a private user group.

**Status:** 🎉 MVP Complete - Production Ready  
**Last Updated:** December 8, 2025

## Features

- ✅ **Authentication** - Secure JWT-based user authentication
- ✅ **Pick Submission** - Submit, edit, and delete picks before kickoff
- ✅ **Automatic Scoring** - Picks scored automatically when games complete (FTD=3pts, ATTD=1pt)
- ✅ **Leaderboard** - Season and weekly rankings with detailed statistics
- ✅ **Admin Tools** - Manual scoring, overrides, and system monitoring
- ✅ **Real-time Updates** - Automatic leaderboard updates via polling
- ✅ **Export** - Download leaderboard data as CSV or JSON
- ✅ **Mobile Responsive** - Optimized for all devices

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Shadcn/UI + Tailwind CSS + TanStack Query
- **Backend:** FastAPI (Python) + PostgreSQL + Redis + APScheduler
- **Testing:** pytest + Hypothesis (160+ tests, 57 property-based)
- **Deployment:** Docker Compose (Self-Hosted)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for shortcuts)

### Development Setup

1. Clone the repository
2. Copy environment files:
   ```bash
   cp infra/docker/dev.env.example infra/docker/dev.env
   ```
3. Start the development environment:
   ```bash
   make up
   # or
   docker compose up -d
   ```
4. Run database migrations:
   ```bash
   make migrate
   # or
   docker compose exec api alembic upgrade head
   ```
5. Seed development data (optional):
   ```bash
   make seed
   # or seed individually:
   make seed-teams
   make seed-players
   make seed-games
   ```

### Available Commands

**Development:**

- `make up` - Start all services
- `make down` - Stop all services
- `make logs` - View logs
- `make shell-backend` - Enter backend container shell

**Database:**

- `make migrate` - Run database migrations
- `make migration msg="description"` - Create new migration
- `make seed` - Seed all development data (teams, players, games)
- `make seed-teams` - Seed NFL teams only
- `make seed-players` - Seed sample players only
- `make seed-games` - Seed sample games only

**Testing:**

- `make test` - Run all tests
- `docker compose exec api pytest` - Run backend tests
- `docker compose exec api pytest -v` - Run tests with verbose output

**Deployment:**

- `scripts\deploy_leaderboard.bat` (Windows) - Deploy leaderboard feature
- `./scripts/deploy_leaderboard.sh` (Linux/Mac) - Deploy leaderboard feature

## Project Structure

```
first6/
├── backend/          # FastAPI application
├── frontend/         # React application
├── infra/            # Infrastructure configs
└── docker-compose.yml
```

## Development

- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Documentation

- **[MVP Roadmap](First6 Docs/120725-MVP-Roadmap.md)** - Project status and roadmap
- **[Setup Guide](SETUP.md)** - Detailed setup instructions
- **[Deployment Guide](.kiro/specs/leaderboard/DEPLOYMENT.md)** - Production deployment
- **[User Guide](.kiro/specs/leaderboard/USER_GUIDE.md)** - End-user documentation
- **[Admin Guide](.kiro/specs/leaderboard/ADMIN_GUIDE.md)** - Administrator documentation
- **[API Reference](http://localhost:8000/docs)** - Interactive API documentation

## Testing

The project has comprehensive test coverage:

- **160+ automated tests**
- **57 property-based tests** using Hypothesis (100+ iterations each)
- **Unit tests** for services and API endpoints
- **Integration tests** for complete workflows
- **Performance tests** for optimization

Run tests:

```bash
# All tests
docker compose exec api pytest

# Specific feature
docker compose exec api pytest tests/test_leaderboard_properties.py

# With coverage
docker compose exec api pytest --cov=app
```

## Architecture

```
┌─────────────────┐
│   Frontend UI   │  React + TypeScript
│  (React/TS)     │  TanStack Query for data fetching
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  API Endpoints  │  FastAPI with async handlers
│  (FastAPI)      │  JWT authentication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Services      │  Business logic layer
│   (Python)      │  Scoring, leaderboard, picks
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Cache  │ │Database│  PostgreSQL with indexes
│(Redis) │ │(Postgres)│  Async queries
└────────┘ └────────┘
```

## Background Jobs

The application uses APScheduler for automated tasks:

- **Daily 1:59 AM EST** - Fetch upcoming NFL games
- **Sundays 4:30 PM EST** - Grade early games
- **Sundays 8:30 PM EST** - Grade late games

## License

Private project - All rights reserved

---

**Last Updated:** December 8, 2025  
**Version:** 1.0 (MVP Complete)

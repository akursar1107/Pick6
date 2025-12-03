# First6 - NFL Prediction Tracking Platform

A boutique, self-hosted web application for tracking NFL "First Touchdown" and "Anytime Touchdown" predictions within a private user group.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Shadcn/UI + Tailwind CSS
- **Backend:** FastAPI (Python) + PostgreSQL + Redis
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

### Available Commands

- `make up` - Start all services
- `make down` - Stop all services
- `make logs` - View logs
- `make shell-backend` - Enter backend container shell
- `make migrate` - Run database migrations
- `make migration msg="description"` - Create new migration

## Project Structure

```
first6/
├── backend/          # FastAPI application
├── frontend/         # React application
├── infra/            # Infrastructure configs
└── docker-compose.yml
```

## Development

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## License

Private project - All rights reserved


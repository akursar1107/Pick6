# First6 Setup Guide

## Prerequisites

- Docker & Docker Compose
- Make (optional, for shortcuts)
- Git

## Initial Setup

1. **Clone/Navigate to the project directory**
   ```bash
   cd C:\Users\akurs\Desktop\First6
   ```

2. **Set up environment variables**
   ```bash
   cp infra/docker/dev.env.example infra/docker/dev.env
   ```
   Edit `infra/docker/dev.env` and add your API keys and configuration.

3. **Start the development environment**
   ```bash
   make up
   # or
   docker compose up -d
   ```

4. **Run database migrations**
   ```bash
   make migrate
   # or
   docker compose exec api alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Nginx (if running): http://localhost

## Development Workflow

### Backend Development

1. **Create a new migration**
   ```bash
   make migration msg="add_new_table"
   ```

2. **Run tests**
   ```bash
   make test
   # or
   docker compose exec api pytest
   ```

3. **Access backend shell**
   ```bash
   make shell-backend
   ```

### Frontend Development

1. **Install dependencies** (if not using Docker)
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server** (if not using Docker)
   ```bash
   npm run dev
   ```

3. **Add Shadcn components**
   ```bash
   npx shadcn-ui@latest add button
   npx shadcn-ui@latest add toast
   # etc.
   ```

## Project Structure

- `backend/` - FastAPI application
- `frontend/` - React/Vite application
- `infra/` - Infrastructure configuration (Nginx, Docker)
- `docker-compose.yml` - Service orchestration

## Next Steps

1. Set up Shadcn/UI components: `npx shadcn-ui@latest init`
2. Initialize Alembic migrations: Already configured
3. Add your BallDontLie API key to `infra/docker/dev.env`
4. Start building features!

## Troubleshooting

- **Port conflicts**: Change ports in `docker-compose.yml`
- **Database connection issues**: Check `DATABASE_URL` in environment
- **Frontend not connecting to API**: Verify `VITE_API_URL` in frontend environment


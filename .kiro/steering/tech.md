# Technology Stack

## Backend

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 16 with asyncpg driver
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: python-jose, passlib with bcrypt
- **Validation**: Pydantic v2
- **Testing**: pytest with pytest-asyncio
- **Server**: Uvicorn with hot reload

### Sports Data Libraries

- nflreadpy (NFL data)
- nba_api (NBA data)
- pybaseball (MLB data)
- nhl-api-py (NHL data)

## Frontend

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5
- **Routing**: React Router v6
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query) v5
- **HTTP Client**: Axios
- **UI Components**: Shadcn/UI (Radix UI primitives)
- **Styling**: Tailwind CSS 3 with tailwindcss-animate
- **Charts**: Recharts
- **Icons**: Lucide React
- **Utilities**: clsx, tailwind-merge, class-variance-authority

## Infrastructure

- **Containerization**: Docker with Docker Compose
- **Reverse Proxy**: Nginx (Alpine)
- **Development**: Hot reload enabled for both frontend and backend

## Common Commands

### Development

```bash
# Start all services
make up
# or
docker compose up -d

# Stop all services
make down

# View logs
make logs

# Rebuild containers
make rebuild
```

### Backend

```bash
# Enter backend shell
make shell-backend

# Run database migrations
make migrate

# Create new migration
make migration msg="description"

# Run tests
make test
# or
docker compose exec api pytest
```

### Frontend

```bash
# Add Shadcn UI components
npx shadcn-ui@latest add <component-name>

# Build for production
npm run build

# Lint
npm run lint
```

## Environment Configuration

Environment variables are managed in `infra/docker/dev.env` (copy from `dev.env.example`).

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

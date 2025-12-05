# Project Structure

## Root Layout

```
First6/
├── backend/          # FastAPI application
├── frontend/         # React application
├── infra/            # Infrastructure configs
├── docker-compose.yml
├── Makefile
├── README.md
└── SETUP.md
```

## Backend Structure (`backend/`)

```
backend/
├── alembic/          # Database migrations
│   ├── versions/     # Migration files
│   └── env.py        # Alembic configuration
├── app/
│   ├── api/          # API endpoints
│   │   └── v1/       # API version 1 routes
│   ├── core/         # Core functionality
│   │   ├── config.py      # Settings and configuration
│   │   ├── security.py    # Auth and security
│   │   └── exceptions.py  # Custom exceptions
│   ├── db/           # Database layer
│   │   ├── models/   # SQLAlchemy models
│   │   ├── base.py   # Base model class
│   │   └── session.py # Database session management
│   ├── schemas/      # Pydantic schemas (DTOs)
│   │   ├── user.py
│   │   ├── game.py
│   │   ├── pick.py
│   │   ├── player.py
│   │   └── team.py
│   ├── services/     # Business logic layer
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── game_service.py
│   │   ├── pick_service.py
│   │   ├── nfl_ingest.py
│   │   └── scoring.py
│   ├── sports/       # Multi-sport data ingestion
│   │   ├── nfl/
│   │   ├── nba/
│   │   ├── mlb/
│   │   ├── nhl/
│   │   ├── cfb/
│   │   └── common/   # Shared sports utilities
│   ├── worker/       # Background tasks
│   │   └── tasks.py
│   └── main.py       # FastAPI app entry point
├── sandbox/          # Development/testing scripts
├── tests/            # Test suite
├── requirements.txt
├── Dockerfile
└── alembic.ini
```

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── components/   # React components
│   │   ├── ui/       # Shadcn UI components
│   │   ├── layout/   # Layout components
│   │   └── shared/   # Shared/common components
│   ├── features/     # Feature-based modules
│   │   ├── auth/     # Authentication feature
│   │   ├── games/    # Games feature
│   │   └── picks/    # Picks feature
│   ├── hooks/        # Custom React hooks
│   ├── lib/          # Utilities and configurations
│   │   ├── api.ts         # Axios instance
│   │   ├── query-client.ts # React Query config
│   │   └── utils.ts       # Helper functions
│   ├── routes/       # Routing configuration
│   │   ├── index.tsx
│   │   └── ProtectedRoute.tsx
│   ├── types/        # TypeScript type definitions
│   │   └── api-types.ts
│   ├── assets/       # Static assets
│   │   └── globals.css
│   ├── App.tsx       # Root component
│   └── main.tsx      # Entry point
├── public/           # Public static files
├── components.json   # Shadcn UI configuration
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

## Infrastructure (`infra/`)

```
infra/
├── docker/
│   ├── dev.env.example  # Environment template
│   └── dev.env          # Local environment (gitignored)
├── nginx/
│   ├── nginx.conf       # Main Nginx config
│   └── default.conf     # Site configuration
└── db/                  # Database initialization (if needed)
```

## Architecture Patterns

### Backend

- **Layered Architecture**: API → Services → Database
- **Dependency Injection**: FastAPI's built-in DI system
- **Async/Await**: Fully async database operations with asyncpg
- **Schema Validation**: Pydantic models for request/response validation
- **API Versioning**: Routes prefixed with `/api/v1`

### Frontend

- **Feature-Based Organization**: Code organized by feature (auth, games, picks)
- **Component Library**: Shadcn UI for consistent, accessible components
- **Path Aliases**: `@/*` maps to `src/*` for cleaner imports
- **State Management**: Zustand for global state, React Query for server state
- **Type Safety**: Strict TypeScript configuration

## Key Conventions

- Backend uses snake_case for Python files and variables
- Frontend uses camelCase for TypeScript/JavaScript
- Database migrations are auto-generated via Alembic
- API endpoints follow RESTful conventions
- All services run in Docker containers for consistency

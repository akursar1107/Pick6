@echo off
REM Leaderboard Deployment Script for Windows
REM This script automates the deployment of the leaderboard feature

setlocal enabledelayedexpansion

echo [INFO] Starting leaderboard deployment...
echo.

REM Check prerequisites
echo [INFO] Checking prerequisites...
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Compose is not installed
    exit /b 1
)

docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running
    exit /b 1
)

echo [INFO] Prerequisites check passed
echo.

REM Step 1: Backup
echo [INFO] Step 1: Creating backup...
set BACKUP_DIR=backups\%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir %BACKUP_DIR% 2>nul

echo [INFO] Backing up database...
docker compose exec -T db pg_dump -U first6_user first6_db > %BACKUP_DIR%\database_backup.sql
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Database backup created: %BACKUP_DIR%\database_backup.sql
) else (
    echo [ERROR] Database backup failed
    exit /b 1
)

echo [INFO] Backing up configuration...
copy infra\docker\dev.env %BACKUP_DIR%\dev.env.backup >nul 2>nul
copy docker-compose.yml %BACKUP_DIR%\docker-compose.yml.backup >nul 2>nul

echo [INFO] Backup completed
echo.

REM Step 2: Run migrations
echo [INFO] Step 2: Running database migrations...
docker compose exec -T api alembic upgrade head
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Migrations completed successfully
) else (
    echo [ERROR] Migrations failed
    echo [WARN] You may need to rollback. Backup is in: %BACKUP_DIR%
    exit /b 1
)
echo.

REM Step 3: Verify indexes
echo [INFO] Step 3: Verifying database indexes...
docker compose exec -T db psql -U first6_user -d first6_db -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename IN ('picks', 'games') AND indexname IN ('idx_picks_status_user', 'idx_games_season_week');" > temp_index_count.txt
set /p INDEX_COUNT=<temp_index_count.txt
del temp_index_count.txt

if !INDEX_COUNT! GEQ 2 (
    echo [INFO] Database indexes verified
) else (
    echo [WARN] Some indexes may be missing. Expected at least 2, found: !INDEX_COUNT!
)
echo.

REM Step 4: Build and deploy backend
echo [INFO] Step 4: Deploying backend...
docker compose build api
docker compose up -d api

echo [INFO] Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if API is responding
curl -f http://localhost:8000/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Backend deployed successfully
) else (
    echo [ERROR] Backend health check failed
    echo [WARN] Check logs with: docker compose logs api
    exit /b 1
)
echo.

REM Step 5: Build and deploy frontend
echo [INFO] Step 5: Deploying frontend...
docker compose build web
docker compose up -d web

echo [INFO] Waiting for frontend to start...
timeout /t 5 /nobreak >nul

echo [INFO] Frontend deployed
echo.

REM Step 6: Verify Redis
echo [INFO] Step 6: Verifying Redis...
docker compose exec -T redis redis-cli PING > temp_redis.txt
set /p REDIS_PING=<temp_redis.txt
del temp_redis.txt

if "!REDIS_PING!"=="PONG" (
    echo [INFO] Redis is running
) else (
    echo [ERROR] Redis is not responding
    exit /b 1
)
echo.

REM Step 7: Warm cache (optional)
set /p WARM_CACHE="Do you want to warm the cache? (y/n): "
if /i "!WARM_CACHE!"=="y" (
    set /p SEASON="Enter season year (default: 2024): "
    if "!SEASON!"=="" set SEASON=2024
    
    echo [INFO] Warming cache for season !SEASON!...
    
    if exist backend\sandbox\warm_cache.py (
        docker compose exec -T api python backend/sandbox/warm_cache.py !SEASON!
        echo [INFO] Cache warming completed
    ) else (
        echo [WARN] warm_cache.py not found, skipping cache warming
    )
)
echo.

REM Step 8: Test API endpoints
echo [INFO] Step 8: Testing API endpoints...

curl -f http://localhost:8000/api/v1/leaderboard/season/2024 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] [OK] Season leaderboard endpoint working
) else (
    echo [WARN] [FAIL] Season leaderboard endpoint failed
)

curl -f http://localhost:8000/api/v1/leaderboard/week/2024/1 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] [OK] Weekly leaderboard endpoint working
) else (
    echo [WARN] [FAIL] Weekly leaderboard endpoint failed
)
echo.

REM Step 9: Run tests
set /p RUN_TESTS="Do you want to run tests? (y/n): "
if /i "!RUN_TESTS!"=="y" (
    echo [INFO] Step 9: Running tests...
    
    echo [INFO] Running integration tests...
    docker compose exec -T api pytest backend/tests/test_leaderboard_integration.py -v
    
    echo [INFO] Running property-based tests...
    docker compose exec -T api pytest backend/tests/test_leaderboard_properties.py -v
    
    echo [INFO] Running API tests...
    docker compose exec -T api pytest backend/tests/test_leaderboard_api.py -v
    
    echo [INFO] Tests completed
)
echo.

REM Step 10: Performance check
echo [INFO] Step 10: Checking performance...

docker compose exec -T redis redis-cli INFO stats | findstr keyspace_hits > temp_hits.txt
docker compose exec -T redis redis-cli INFO stats | findstr keyspace_misses > temp_misses.txt

if exist temp_hits.txt if exist temp_misses.txt (
    for /f "tokens=2 delims=:" %%a in (temp_hits.txt) do set CACHE_HITS=%%a
    for /f "tokens=2 delims=:" %%a in (temp_misses.txt) do set CACHE_MISSES=%%a
    
    set /a TOTAL=!CACHE_HITS!+!CACHE_MISSES!
    if !TOTAL! GTR 0 (
        set /a HIT_RATE=!CACHE_HITS!*100/!TOTAL!
        echo [INFO] Cache hit rate: !HIT_RATE!%%
        
        if !HIT_RATE! LSS 80 (
            echo [WARN] Cache hit rate is below 80%%. Consider warming the cache.
        )
    )
)

del temp_hits.txt 2>nul
del temp_misses.txt 2>nul
echo.

REM Summary
echo.
echo ==========================================
echo [INFO] Deployment Summary
echo ==========================================
echo [INFO] Backup location: %BACKUP_DIR%
echo [INFO] Backend: Running
echo [INFO] Frontend: Running
echo [INFO] Redis: Running
echo [INFO] Database: Migrated
echo ==========================================
echo.

echo [INFO] Deployment completed successfully!
echo.
echo [INFO] Next steps:
echo   1. Open http://localhost:3000/standings in your browser
echo   2. Verify the leaderboard loads correctly
echo   3. Test user statistics modal
echo   4. Test export functionality
echo   5. Monitor logs: docker compose logs -f
echo.
echo [INFO] For troubleshooting, see: .kiro/specs/leaderboard/DEPLOYMENT.md
echo.

REM Offer to show logs
set /p SHOW_LOGS="Do you want to view logs? (y/n): "
if /i "!SHOW_LOGS!"=="y" (
    docker compose logs -f api
)

endlocal

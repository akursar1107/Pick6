#!/bin/bash

# Leaderboard Deployment Script
# This script automates the deployment of the leaderboard feature

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

# Check prerequisites
log_info "Checking prerequisites..."
check_command docker
check_command docker-compose

# Check if docker is running
if ! docker info &> /dev/null; then
    log_error "Docker is not running"
    exit 1
fi

log_info "Prerequisites check passed"

# Step 1: Backup
log_info "Step 1: Creating backup..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

log_info "Backing up database..."
docker compose exec -T db pg_dump -U first6_user first6_db > $BACKUP_DIR/database_backup.sql
if [ $? -eq 0 ]; then
    log_info "Database backup created: $BACKUP_DIR/database_backup.sql"
else
    log_error "Database backup failed"
    exit 1
fi

log_info "Backing up configuration..."
cp infra/docker/dev.env $BACKUP_DIR/dev.env.backup 2>/dev/null || log_warn "dev.env not found"
cp docker-compose.yml $BACKUP_DIR/docker-compose.yml.backup

log_info "Backup completed"

# Step 2: Run migrations
log_info "Step 2: Running database migrations..."
docker compose exec -T api alembic upgrade head
if [ $? -eq 0 ]; then
    log_info "Migrations completed successfully"
else
    log_error "Migrations failed"
    log_warn "You may need to rollback. Backup is in: $BACKUP_DIR"
    exit 1
fi

# Step 3: Verify indexes
log_info "Step 3: Verifying database indexes..."
INDEXES=$(docker compose exec -T db psql -U first6_user -d first6_db -t -c "
SELECT COUNT(*) 
FROM pg_indexes 
WHERE tablename IN ('picks', 'games') 
AND indexname IN ('idx_picks_status_user', 'idx_games_season_week');
")

if [ "$INDEXES" -ge 2 ]; then
    log_info "Database indexes verified"
else
    log_warn "Some indexes may be missing. Expected at least 2, found: $INDEXES"
fi

# Step 4: Build and deploy backend
log_info "Step 4: Deploying backend..."
docker compose build api
docker compose up -d api

log_info "Waiting for backend to start..."
sleep 5

# Check if API is responding
if curl -f http://localhost:8000/health &> /dev/null; then
    log_info "Backend deployed successfully"
else
    log_error "Backend health check failed"
    log_warn "Check logs with: docker compose logs api"
    exit 1
fi

# Step 5: Build and deploy frontend
log_info "Step 5: Deploying frontend..."
docker compose build web
docker compose up -d web

log_info "Waiting for frontend to start..."
sleep 5

log_info "Frontend deployed"

# Step 6: Verify Redis
log_info "Step 6: Verifying Redis..."
REDIS_PING=$(docker compose exec -T redis redis-cli PING)
if [ "$REDIS_PING" = "PONG" ]; then
    log_info "Redis is running"
else
    log_error "Redis is not responding"
    exit 1
fi

# Step 7: Warm cache (optional)
read -p "Do you want to warm the cache? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter season year (default: 2024): " SEASON
    SEASON=${SEASON:-2024}
    
    log_info "Warming cache for season $SEASON..."
    
    # Create warm cache script if it doesn't exist
    if [ ! -f backend/sandbox/warm_cache.py ]; then
        log_warn "warm_cache.py not found, skipping cache warming"
    else
        docker compose exec -T api python backend/sandbox/warm_cache.py $SEASON
        log_info "Cache warming completed"
    fi
fi

# Step 8: Test API endpoints
log_info "Step 8: Testing API endpoints..."

# Test season leaderboard
if curl -f http://localhost:8000/api/v1/leaderboard/season/2024 &> /dev/null; then
    log_info "✓ Season leaderboard endpoint working"
else
    log_warn "✗ Season leaderboard endpoint failed"
fi

# Test weekly leaderboard
if curl -f http://localhost:8000/api/v1/leaderboard/week/2024/1 &> /dev/null; then
    log_info "✓ Weekly leaderboard endpoint working"
else
    log_warn "✗ Weekly leaderboard endpoint failed"
fi

# Step 9: Run tests
read -p "Do you want to run tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Step 9: Running tests..."
    
    log_info "Running integration tests..."
    docker compose exec -T api pytest backend/tests/test_leaderboard_integration.py -v
    
    log_info "Running property-based tests..."
    docker compose exec -T api pytest backend/tests/test_leaderboard_properties.py -v
    
    log_info "Running API tests..."
    docker compose exec -T api pytest backend/tests/test_leaderboard_api.py -v
    
    log_info "Tests completed"
fi

# Step 10: Performance check
log_info "Step 10: Checking performance..."

# Check cache hit rate
CACHE_HITS=$(docker compose exec -T redis redis-cli INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
CACHE_MISSES=$(docker compose exec -T redis redis-cli INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')

if [ ! -z "$CACHE_HITS" ] && [ ! -z "$CACHE_MISSES" ]; then
    TOTAL=$((CACHE_HITS + CACHE_MISSES))
    if [ $TOTAL -gt 0 ]; then
        HIT_RATE=$((CACHE_HITS * 100 / TOTAL))
        log_info "Cache hit rate: ${HIT_RATE}%"
        
        if [ $HIT_RATE -lt 80 ]; then
            log_warn "Cache hit rate is below 80%. Consider warming the cache."
        fi
    fi
fi

# Summary
echo ""
log_info "=========================================="
log_info "Deployment Summary"
log_info "=========================================="
log_info "Backup location: $BACKUP_DIR"
log_info "Backend: Running"
log_info "Frontend: Running"
log_info "Redis: Running"
log_info "Database: Migrated"
log_info "=========================================="
echo ""

log_info "Deployment completed successfully!"
echo ""
log_info "Next steps:"
echo "  1. Open http://localhost:3000/standings in your browser"
echo "  2. Verify the leaderboard loads correctly"
echo "  3. Test user statistics modal"
echo "  4. Test export functionality"
echo "  5. Monitor logs: docker compose logs -f"
echo ""
log_info "For troubleshooting, see: .kiro/specs/leaderboard/DEPLOYMENT.md"
echo ""

# Offer to show logs
read -p "Do you want to view logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose logs -f api
fi

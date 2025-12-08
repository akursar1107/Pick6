# Leaderboard Deployment - Quick Start

## Overview

This directory contains all documentation and scripts needed to deploy the leaderboard feature to production.

## Documentation Files

- **DEPLOYMENT.md** - Complete deployment guide with step-by-step instructions
- **USER_GUIDE.md** - End-user documentation for using the leaderboard
- **ADMIN_GUIDE.md** - Administrator guide for managing and troubleshooting
- **DEPLOYMENT_README.md** - This file

## Deployment Scripts

Two deployment scripts are provided:

### Windows (Batch Script)

```cmd
cd First6
scripts\deploy_leaderboard.bat
```

### Linux/Mac (Bash Script)

```bash
cd First6
chmod +x scripts/deploy_leaderboard.sh
./scripts/deploy_leaderboard.sh
```

## What the Scripts Do

The deployment scripts automate the following steps:

1. **Backup** - Creates backup of database and configuration
2. **Migrations** - Runs database migrations to add required indexes
3. **Verify Indexes** - Confirms database indexes are created
4. **Deploy Backend** - Builds and deploys the API service
5. **Deploy Frontend** - Builds and deploys the web interface
6. **Verify Redis** - Checks cache service is running
7. **Warm Cache** (optional) - Pre-populates cache for better performance
8. **Test Endpoints** - Verifies API endpoints are responding
9. **Run Tests** (optional) - Executes test suite
10. **Performance Check** - Checks cache hit rate and performance

## Quick Deployment

For a quick deployment with defaults:

```bash
# Windows
scripts\deploy_leaderboard.bat

# Linux/Mac
./scripts/deploy_leaderboard.sh
```

Answer the prompts:

- Cache warming: **y** (recommended)
- Season year: **2024** (or current season)
- Run tests: **y** (recommended for first deployment)
- View logs: **n** (unless troubleshooting)

## Manual Deployment

If you prefer to deploy manually, follow the detailed steps in **DEPLOYMENT.md**.

## Pre-Deployment Checklist

Before running the deployment:

- [ ] All tests are passing
- [ ] Code has been reviewed
- [ ] Docker and Docker Compose are installed
- [ ] Docker is running
- [ ] You have database backup access
- [ ] You understand the rollback procedure

## Post-Deployment Verification

After deployment, verify:

1. **API Health**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Season Leaderboard**

   ```bash
   curl http://localhost:8000/api/v1/leaderboard/season/2024
   ```

3. **Frontend**

   - Open http://localhost:3000/standings
   - Verify leaderboard loads
   - Test user statistics modal
   - Test export functionality

4. **Performance**
   ```bash
   docker compose exec redis redis-cli INFO stats | grep keyspace
   ```
   - Cache hit rate should be > 80%

## Rollback

If issues occur, rollback using:

```bash
# Stop services
docker compose down

# Restore database
docker compose up -d db
cat backups/YYYYMMDD_HHMMSS/database_backup.sql | docker compose exec -T db psql -U first6_user first6_db

# Restart services
docker compose up -d
```

See **DEPLOYMENT.md** for detailed rollback procedures.

## Troubleshooting

### Common Issues

**Issue: Migrations fail**

- Check database connection
- Review migration logs
- See DEPLOYMENT.md troubleshooting section

**Issue: API returns 503**

- Check database is running: `docker compose ps db`
- Check Redis is running: `docker compose ps redis`
- View logs: `docker compose logs api`

**Issue: Frontend not loading**

- Check frontend logs: `docker compose logs web`
- Verify API is accessible
- Check nginx logs: `docker compose logs nginx`

**Issue: Slow performance**

- Warm the cache
- Verify indexes exist
- Check cache hit rate
- See ADMIN_GUIDE.md for performance tuning

## Support

For detailed troubleshooting:

1. Check **DEPLOYMENT.md** - Deployment issues
2. Check **ADMIN_GUIDE.md** - Performance and maintenance
3. Check **USER_GUIDE.md** - Feature usage
4. Review logs: `docker compose logs -f`

## Files in This Directory

```
.kiro/specs/leaderboard/
├── requirements.md          # Feature requirements
├── design.md               # Technical design
├── tasks.md                # Implementation tasks
├── USER_GUIDE.md           # End-user documentation
├── ADMIN_GUIDE.md          # Administrator guide
├── DEPLOYMENT.md           # Detailed deployment guide
└── DEPLOYMENT_README.md    # This file

../../scripts/
├── deploy_leaderboard.sh   # Linux/Mac deployment script
└── deploy_leaderboard.bat  # Windows deployment script
```

## Next Steps After Deployment

1. **Share Documentation**

   - Send USER_GUIDE.md to end users
   - Send ADMIN_GUIDE.md to administrators

2. **Enable Monitoring**

   - Set up log monitoring
   - Configure performance alerts
   - Monitor cache hit rate

3. **Schedule Maintenance**

   - Daily: Check error logs
   - Weekly: Database vacuum
   - Monthly: Performance review

4. **User Training**
   - Walk through USER_GUIDE.md with users
   - Demonstrate key features
   - Answer questions

## Success Criteria

Deployment is successful when:

- ✅ All migrations applied
- ✅ All tests passing
- ✅ API responding < 500ms
- ✅ Frontend loads without errors
- ✅ Cache hit rate > 80%
- ✅ Export works
- ✅ Real-time updates work
- ✅ Mobile responsive
- ✅ No errors in logs

---

**Last Updated**: December 2024
**Version**: 1.0

# Scoring System Documentation

## Overview

The Scoring System automatically grades user picks when NFL games complete, awards points based on touchdown predictions, and maintains user scores. This directory contains all documentation for the scoring system feature.

## Documentation Index

### For Users

- **[User Guide](USER_GUIDE.md)** - Complete guide for users
  - How scoring works (FTD=3, ATTD=1)
  - Viewing your scores and pick results
  - Frequently asked questions
  - Tips for success

### For Administrators

- **[Admin Guide](ADMIN_GUIDE.md)** - Complete guide for administrators
  - Manual scoring process
  - Score override process
  - Monitoring and alerts
  - Troubleshooting common issues

### For Developers

- **[Requirements Document](requirements.md)** - Feature requirements

  - User stories and acceptance criteria
  - EARS-compliant requirements
  - Glossary of terms

- **[Design Document](design.md)** - Technical design

  - Architecture and components
  - Data models
  - Correctness properties (18 properties)
  - Testing strategy
  - Error handling

- **[Implementation Plan](tasks.md)** - Task list

  - 13 major tasks with subtasks
  - Property-based tests integrated throughout
  - Task status tracking

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deployment instructions
  - Pre-deployment checklist
  - Step-by-step deployment process
  - Rollback procedure
  - Troubleshooting

## Quick Links

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

**User Endpoints:**

- `GET /api/v1/scores/user/{user_id}` - Get user's total score
- `GET /api/v1/scores/pick/{pick_id}` - Get pick result details
- `GET /api/v1/scores/game/{game_id}` - Get game scoring results

**Admin Endpoints:**

- `POST /api/v1/scores/game/{game_id}/manual` - Manual game scoring
- `PATCH /api/v1/scores/pick/{pick_id}/override` - Override pick score

**Health Check Endpoints:**

- `GET /api/v1/health/system` - Overall system health
- `GET /api/v1/health/scheduler` - Scheduler status
- `GET /api/v1/health/scoring` - Scoring statistics (admin only)

## Feature Summary

### Scoring Rules

| Prediction Type          | Points | Description                           |
| ------------------------ | ------ | ------------------------------------- |
| First Touchdown (FTD)    | 3      | Player scores first TD of game        |
| Anytime Touchdown (ATTD) | 1      | Player scores any TD during game      |
| Both FTD + ATTD          | 4      | Player scores first TD (both bonuses) |
| No Touchdown             | 0      | Player doesn't score                  |

### Scheduled Jobs

- **Daily at 1:59 AM EST**: Fetch upcoming games from nflreadpy
- **Sundays at 4:30 PM EST**: Grade early games
- **Sundays at 8:30 PM EST**: Grade late games

### Key Features

✅ Automatic scoring after games complete
✅ Real-time score updates
✅ Detailed pick result breakdowns
✅ User score tracking and leaderboards
✅ Admin override capabilities
✅ Comprehensive error handling
✅ Health monitoring and alerts
✅ 18 property-based tests for correctness

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy
- **Scheduler**: APScheduler
- **Data Source**: nflreadpy
- **Testing**: pytest with Hypothesis (property-based testing)
- **Frontend**: React with TypeScript

## Getting Started

### For Users

1. Read the [User Guide](USER_GUIDE.md)
2. Make your picks before games start
3. Check your scores after games complete
4. View detailed results for each pick

### For Administrators

1. Read the [Admin Guide](ADMIN_GUIDE.md)
2. Monitor health check endpoints
3. Review scheduled job executions
4. Handle manual scoring when needed

### For Developers

1. Review [Requirements](requirements.md) and [Design](design.md)
2. Follow the [Implementation Plan](tasks.md)
3. Run property-based tests: `docker compose exec api pytest tests/test_scoring_properties.py`
4. Deploy using [Deployment Guide](DEPLOYMENT_GUIDE.md)

## Testing

### Property-Based Tests

The scoring system includes 18 property-based tests that verify correctness properties:

```bash
# Run all property tests
docker compose exec api pytest tests/test_scoring_properties.py -v

# Run specific property test
docker compose exec api pytest tests/test_scoring_properties.py::test_property_5_ftd_points_correctness -v

# Run with verbose output
docker compose exec api pytest tests/test_scoring_properties.py -vv
```

### Integration Tests

```bash
# Run integration tests
docker compose exec api pytest tests/test_scoring_integration.py -v
```

### Manual Testing

See [Admin Guide](ADMIN_GUIDE.md) for manual testing procedures.

## Monitoring

### Health Checks

```bash
# Check system health
curl http://localhost:8000/api/v1/health/system

# Check scheduler status
curl http://localhost:8000/api/v1/health/scheduler

# Check scoring statistics (requires admin token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/health/scoring
```

### Logs

```bash
# View all logs
docker compose logs api -f

# View scheduler logs
docker compose logs api -f | grep "scheduler"

# View scoring logs
docker compose logs api -f | grep "scoring"

# View errors only
docker compose logs api | grep ERROR
```

## Troubleshooting

### Common Issues

1. **Picks not being graded**

   - Check scheduler status: `curl http://localhost:8000/api/v1/health/scheduler`
   - Review logs: `docker compose logs api | grep "grade_completed_games"`
   - See [Admin Guide - Troubleshooting](ADMIN_GUIDE.md#troubleshooting)

2. **Incorrect scores**

   - Verify game data: `GET /api/v1/scores/game/{game_id}`
   - Check pick result: `GET /api/v1/scores/pick/{pick_id}`
   - Use admin override if needed

3. **Scheduler not running**
   - Restart service: `docker compose restart api`
   - Check logs: `docker compose logs api | grep "scheduler"`
   - See [Deployment Guide - Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)

For more troubleshooting help, see:

- [Admin Guide - Troubleshooting](ADMIN_GUIDE.md#troubleshooting)
- [Deployment Guide - Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)

## Support

### Documentation

- **User Questions**: See [User Guide FAQ](USER_GUIDE.md#frequently-asked-questions)
- **Admin Questions**: See [Admin Guide](ADMIN_GUIDE.md)
- **Technical Questions**: See [Design Document](design.md)

### Contact

- **Development Team**: dev@first6.com
- **System Administrator**: admin@first6.com
- **Documentation**: https://docs.first6.com

## Contributing

When making changes to the scoring system:

1. Update relevant documentation
2. Add/update property-based tests
3. Run all tests before committing
4. Update the changelog
5. Follow deployment guide for production changes

## Changelog

### Version 1.0.0 (Initial Release)

**Features:**

- Automatic scoring with scheduled jobs
- FTD (3 points) and ATTD (1 point) scoring
- User score tracking and leaderboards
- Admin manual scoring and overrides
- Health monitoring and alerts
- Comprehensive documentation

**Testing:**

- 18 property-based tests
- Integration tests
- 100+ iterations per property test

**Documentation:**

- User guide
- Admin guide
- Deployment guide
- API documentation

## License

Copyright © 2024 First6. All rights reserved.

---

**Last Updated**: December 7, 2024

**Version**: 1.0.0

**Status**: ✅ Complete and Ready for Deployment
